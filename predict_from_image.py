import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image
import cv2

ANTIGEN_MAP = {
    'A+': (1, 0, 1),
    'A-': (1, 0, 0),
    'B+': (0, 1, 1),
    'B-': (0, 1, 0),
    'AB+': (1, 1, 1),
    'AB-': (1, 1, 0),
    'O+': (0, 0, 1),
    'O-': (0, 0, 0)
}

def detect_3_drops(im_bgr):
    h, w, _ = im_bgr.shape
    blood_col = np.zeros(w)
    for x in range(w):
        col = im_bgr[:, x]
        b = col[:, 0].astype(float)
        g = col[:, 1].astype(float)
        r = col[:, 2].astype(float)
        max_v = np.maximum(np.maximum(r, g), b)
        min_v = np.minimum(np.minimum(r, g), b)
        sat = np.where(max_v == 0, 0, (max_v - min_v) / (max_v + 1e-5))
        mask = (r > 90) & (r > g * 1.15) & (r > b * 1.15) & (sat > 0.20) & (max_v < 248)
        blood_col[x] = np.sum(mask)

    win = max(3, int(w * 0.04))
    kernel = np.ones(win * 2 + 1) / (win * 2 + 1)
    smooth = np.convolve(blood_col, kernel, mode='same')

    min_dist = int(w * 0.15)
    peaks = []
    for x in range(1, w - 1):
        if smooth[x] > smooth[x - 1] and smooth[x] >= smooth[x + 1] and smooth[x] > (h * 0.15):
            peaks.append((x, smooth[x]))

    peaks.sort(key=lambda item: item[1], reverse=True)
    selected_peaks = []
    for px, val in peaks:
        if all(abs(px - sp) >= min_dist for sp in selected_peaks):
            selected_peaks.append(px)
            if len(selected_peaks) == 3:
                break

    selected_peaks.sort()
    if len(selected_peaks) < 3:
        selected_peaks = [int(w * 0.22), int(w * 0.50), int(w * 0.78)]

    cy = h // 2
    drop_r = int(min(h * 0.35, (selected_peaks[1] - selected_peaks[0]) * 0.40))
    ir = max(8, int(drop_r * 0.45))
    return selected_peaks, cy, ir

def classify_strip_image(image_path: str):
    if not os.path.exists(image_path):
        print(f'[-] Image not found: {image_path}')
        return
    im_bgr = cv2.imread(image_path)
    if im_bgr is None:
        print(f'[-] Unable to decode image: {image_path}')
        return
    h, w, _ = im_bgr.shape
    peaks, cy, ir = detect_3_drops(im_bgr)

    stats = []
    for cx in peaks:
        crop = im_bgr[max(0, cy - ir):min(h, cy + ir), max(0, cx - ir):min(w, cx + ir)]
        b = crop[:, :, 0].astype(float)
        g = crop[:, :, 1].astype(float)
        r = crop[:, :, 2].astype(float)
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        max_v = np.maximum(np.maximum(r, g), b)
        min_v = np.minimum(np.minimum(r, g), b)
        sat = np.where(max_v == 0, 0, (max_v - min_v) / (max_v + 1e-5)) * 255.0

        stats.append({
            'cx': cx,
            'gray_std': float(np.std(gray)),
            'gray_mean': float(np.mean(gray)),
            'red_mean': float(np.mean(r)),
            'red_std': float(np.std(r)),
            'sat_std': float(np.std(sat)),
            'sat_mean': float(np.mean(sat))
        })

    is_synth = (stats[0]['gray_std'] > 45.0 or stats[1]['gray_std'] > 45.0) and (stats[0]['sat_std'] > 30.0)

    if is_synth:
        clump_a = stats[0]['gray_std'] > 65.0
        clump_b = stats[1]['gray_std'] > 65.0
        clump_d = stats[2]['gray_std'] > 65.0
    else:
        clump_d = (stats[2]['sat_std'] > 11.0) or (stats[2]['gray_mean'] > 95.0 and stats[2]['sat_std'] > 7.0) or (stats[2]['gray_std'] > 14.0)
        clump_b = (stats[1]['sat_std'] > 12.0) or (stats[1]['gray_std'] > 18.0) or (stats[1]['red_std'] > 9.0)
        clump_a = (stats[0]['sat_std'] > 5.0) or (stats[0]['red_std'] > 5.5 and (stats[1]['red_mean'] - stats[0]['red_mean'] > 25.0)) or (stats[0]['gray_std'] > 14.0)

        if stats[0]['sat_std'] < 3.8 and stats[1]['sat_std'] < 3.8 and stats[0]['red_std'] < 4.8 and stats[1]['red_std'] < 4.8:
            clump_a = False
            clump_b = False

    antigen_detected = [1 if clump_a else 0, 1 if clump_b else 0, 1 if clump_d else 0]
    well_names = ['Well-A (Anti-A)', 'Well-B (Anti-B)', 'Well-D (Anti-D / Rh)']

    print('\n' + '=' * 65)
    print(f'  COMPUTER VISION IMAGE ANALYSIS: {os.path.basename(image_path)}')
    print('=' * 65)
    for i in range(3):
        is_agglutinated = antigen_detected[i] == 1
        state_str = 'Agglutination POSITIVE (Granular Clumps Detected)' if is_agglutinated else 'Agglutination NEGATIVE (Smooth Uniform Blood)'
        print(f'  • {well_names[i]}: {state_str} [Sat-STD: {stats[i]["sat_std"]:.1f}, Gray-STD: {stats[i]["gray_std"]:.1f}]')

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
