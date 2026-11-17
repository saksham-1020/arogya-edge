import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image
from simulator import BLOOD_GROUPS, ANTIGEN_MAP

def analyze_well_image(well_crop: Image.Image) -> float:
    gray = np.array(well_crop.convert('L'), dtype=np.float32)
    h, w = gray.shape
    cy, cx = (h // 2, w // 2)
    y, x = np.ogrid[:h, :w]
    mask = (x - cx) ** 2 + (y - cy) ** 2 <= (min(cx, cy) - 5) ** 2
    well_pixels = gray[mask]
    texture_std = np.std(well_pixels)
    return float(texture_std)

def classify_strip_image(image_path: str):
    if not os.path.exists(image_path):
        print(f'[-] Image not found: {image_path}')
        return
    strip = Image.open(image_path)
    well_centers_x = [110, 250, 390]
    well_center_y = 120
    radius = 45
    well_names = ['Well-A (Anti-A)', 'Well-B (Anti-B)', 'Well-D (Anti-D / Rh)']
    antigen_detected = []
    heterogeneity_scores = []
    print('\n' + '=' * 65)
    print(f'  COMPUTER VISION IMAGE ANALYSIS: {os.path.basename(image_path)}')
    print('=' * 65)
    for i in range(3):
        cx = well_centers_x[i]
        cy = well_center_y
        crop_box = (cx - radius, cy - radius, cx + radius, cy + radius)
        well_crop = strip.crop(crop_box)
        texture_score = analyze_well_image(well_crop)
        heterogeneity_scores.append(texture_score)
        is_agglutinated = texture_score > 45.0
        antigen_detected.append(1 if is_agglutinated else 0)
        state_str = 'Agglutination POSITIVE (Granular Clumps Detected)' if is_agglutinated else 'Agglutination NEGATIVE (Smooth Uniform Blood)'
        print(f'  • {well_names[i]}: {state_str} [Texture Score: {texture_score:.1f}]')
    detected_tuple = tuple(antigen_detected)
    predicted_bg = 'Unknown / Inconclusive'
    for bg, profile in ANTIGEN_MAP.items():
        if tuple(profile) == detected_tuple:
            predicted_bg = bg
            break
    print('-' * 65)
    print(f'  >>> DIAGNOSED BLOOD GROUP FROM IMAGE: {predicted_bg}')
    print(f'  >>> PROFILE MATCH: Anti-A={antigen_detected[0]}, Anti-B={antigen_detected[1]}, Anti-D={antigen_detected[2]}')
    print('=' * 65)
    return predicted_bg
if __name__ == '__main__':
    images_dir = os.path.join(os.path.dirname(__file__), 'dataset', 'images')
    if len(sys.argv) > 1:
        classify_strip_image(sys.argv[1])
    else:
        sample_files = [f for f in os.listdir(images_dir) if f.endswith('.png')][:3]
        for f in sample_files:
            classify_strip_image(os.path.join(images_dir, f))
