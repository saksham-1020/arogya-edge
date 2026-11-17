import os
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import uniform_filter
import cv2
from simulator import BLOOD_GROUPS, ANTIGEN_MAP
WELL_NAMES = ['Well-A (Anti-A)', 'Well-B (Anti-B)', 'Well-D (Anti-D / Rh)']

def analyze_well_crop(well_crop: Image.Image) -> float:
    gray = np.array(well_crop.convert('L'), dtype=np.float32)
    h, w = gray.shape
    cy, cx = (h // 2, w // 2)
    y, x = np.ogrid[:h, :w]
    mask = (x - cx) ** 2 + (y - cy) ** 2 <= (min(cx, cy) - 4) ** 2
    well_pixels = gray[mask]
    if len(well_pixels) == 0:
        return 0.0
    return float(np.std(well_pixels))

def find_wells_smart(orig_img: Image.Image) -> List[Tuple[int, int, int]]:
    img_np = np.array(orig_img.convert('RGB'))
    h, w = img_np.shape[:2]
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    min_r = int(min(h, w) * 0.1)
    max_r = int(min(h, w) * 0.32)
    min_dist = int(w * 0.18)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.0, minDist=min_dist, param1=55, param2=20, minRadius=min_r, maxRadius=max_r)
    wells = []
    if circles is not None:
        c_list = np.round(circles[0, :]).astype(int)
        c_list = sorted(c_list, key=lambda c: c[0])
        if len(c_list) >= 3:
            for i in range(len(c_list) - 2):
                c0, c1, c2 = (c_list[i], c_list[i + 1], c_list[i + 2])
                if abs(c0[1] - c1[1]) < h * 0.15 and abs(c1[1] - c2[1]) < h * 0.15:
                    wells = [(int(c[0]), int(c[1]), int(c[2])) for c in [c0, c1, c2]]
                    break
    if len(wells) != 3:
        scale_x = w / 500.0
        scale_y = h / 200.0
        cx_a = int(110 * scale_x)
        cx_b = int(250 * scale_x)
        cx_d = int(390 * scale_x)
        cy = int(120 * scale_y)
        r = int(45 * min(scale_x, scale_y))
        wells = [(cx_a, cy, r), (cx_b, cy, r), (cx_d, cy, r)]
    return wells

def generate_counterfactual_explanation(predicted_bg: str, antigen_scores: List[float], threshold: float=45.0) -> Dict[str, Any]:
    predicted_profile = ANTIGEN_MAP.get(predicted_bg, [0, 0, 0])
    counterfactuals = []
    channel_labels = ['Anti-A (A antigen)', 'Anti-B (B antigen)', 'Anti-D (Rh factor)']
    for i in range(3):
        flipped_profile = list(predicted_profile)
        flipped_profile[i] = 1 - flipped_profile[i]
        target_bg = 'Unknown'
        for bg, prof in ANTIGEN_MAP.items():
            if prof == flipped_profile:
                target_bg = bg
                break
        current_state = 'Positive (Agglutination Clumped)' if predicted_profile[i] == 1 else 'Negative (Smooth Unclumped)'
        flipped_state = 'Negative' if predicted_profile[i] == 1 else 'Positive'
        current_val = float(antigen_scores[i])
        delta_needed = abs(current_val - threshold)
        if predicted_profile[i] == 1:
            rationale = f"Well '{channel_labels[i]}' exhibited granular clumping (score: {current_val:.1f} >= {threshold:.1f}). What-If: If antibody binding were absent (score reduced by {delta_needed:.1f} below {threshold:.1f}), the diagnosis would pivot from {predicted_bg} to {target_bg}."
        else:
            rationale = f"Well '{channel_labels[i]}' remained clear & unclumped (score: {current_val:.1f} < {threshold:.1f}). What-If: If true agglutination occurred here (score increased by {delta_needed:.1f} above {threshold:.1f}), the diagnosis would pivot from {predicted_bg} to {target_bg}."
        counterfactuals.append({'target_channel': channel_labels[i], 'original_state': current_state, 'counterfactual_state': flipped_state, 'resulting_blood_group': target_bg, 'perturbation_margin_required': round(delta_needed, 1), 'explanation': rationale})
    return {'current_diagnosis': predicted_bg, 'antigen_reaction_scores': [round(float(s), 1) for s in antigen_scores], 'counterfactual_scenarios': counterfactuals}

def generate_cassette_heatmap(image_path: str, output_heatmap_path: str='gradcam_agglutination_heatmap.png', threshold: float=45.0) -> Dict[str, Any]:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f'Image not found at {image_path}')
    orig_img = Image.open(image_path).convert('RGB')
    width, height = orig_img.size
    wells = find_wells_smart(orig_img)
    gray = np.array(orig_img.convert('L'), dtype=np.float32)
    mean = uniform_filter(gray, size=5)
    sq_mean = uniform_filter(gray ** 2, size=5)
    local_std = np.sqrt(np.maximum(0.0, sq_mean - mean ** 2))
    well_metrics = []
    antigen_detected = []
    y_coords, x_coords = np.ogrid[:height, :width]
    total_mask = np.zeros((height, width), dtype=bool)
    heatmap_energy = np.zeros((height, width), dtype=np.float32)
    for i, (cx, cy, radius) in enumerate(wells):
        crop_box = (max(0, cx - radius), max(0, cy - radius), min(width, cx + radius), min(height, cy + radius))
        well_crop = orig_img.crop(crop_box)
        texture_score = analyze_well_crop(well_crop)
        is_agglutinated = texture_score > threshold
        dist_sq = (x_coords - cx) ** 2 + (y_coords - cy) ** 2
        well_mask = dist_sq <= radius ** 2
        total_mask |= well_mask
        if is_agglutinated:
            norm_val = np.clip(local_std[well_mask] / 35.0, 0.45, 1.0)
            heatmap_energy[well_mask] = norm_val
        else:
            norm_val = np.clip(local_std[well_mask] / 70.0, 0.05, 0.25)
            heatmap_energy[well_mask] = norm_val
        antigen_detected.append(1 if is_agglutinated else 0)
        well_metrics.append({'well': WELL_NAMES[i], 'agglutination_score': round(texture_score, 1), 'status': 'Agglutinated (Positive)' if is_agglutinated else 'Smooth (Negative)', 'is_positive': is_agglutinated})
    detected_tuple = tuple(antigen_detected)
    predicted_bg = 'Unknown'
    for bg, profile in ANTIGEN_MAP.items():
        if tuple(profile) == detected_tuple:
            predicted_bg = bg
            break
    r = np.clip(1.5 - np.abs(heatmap_energy * 4.0 - 3.0), 0.0, 1.0)
    g = np.clip(1.5 - np.abs(heatmap_energy * 4.0 - 2.0), 0.0, 1.0)
    b = np.clip(1.5 - np.abs(heatmap_energy * 4.0 - 1.0), 0.0, 1.0)
    heatmap_rgb = (np.stack([r, g, b], axis=-1) * 255).astype(np.uint8)
    orig_np = np.array(orig_img, dtype=np.float32)
    blend_np = orig_np.copy()
    alpha = 0.5
    blend_np[total_mask] = (1.0 - alpha) * orig_np[total_mask] + alpha * heatmap_rgb[total_mask]
    result_img = Image.fromarray(np.uint8(blend_np))
    draw = ImageDraw.Draw(result_img)
    for i, (cx, cy, radius) in enumerate(wells):
        score = well_metrics[i]['agglutination_score']
        is_pos = well_metrics[i]['is_positive']
        outline_color = (220, 20, 20) if is_pos else (30, 180, 50)
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=outline_color, width=3)
        status_text = 'POS' if is_pos else 'NEG'
        draw.text((cx - 28, cy + radius + 4), f'{status_text} ({score:.0f})', fill=outline_color)
    result_img.save(output_heatmap_path)
    return {'output_path': output_heatmap_path, 'predicted_blood_group': predicted_bg, 'antigen_profile': antigen_detected, 'well_metrics': well_metrics}
