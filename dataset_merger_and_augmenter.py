import os
import sys
import glob
import shutil
import random
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any
BIG_DATA_ROOT = os.path.join(os.path.dirname(__file__), 'dataset', 'big_data_blood_slides')
CLASSES = ['Well_A_Clumped', 'Well_A_Smooth', 'Well_B_Clumped', 'Well_B_Smooth', 'Well_D_Clumped', 'Well_D_Smooth']

def setup_directory_structure():
    splits = ['train', 'valid', 'test']
    for s in splits:
        os.makedirs(os.path.join(BIG_DATA_ROOT, 'images', s), exist_ok=True)
        os.makedirs(os.path.join(BIG_DATA_ROOT, 'labels', s), exist_ok=True)
    print(f'[+] Big Data Directory initialized at: {BIG_DATA_ROOT}')

def augment_image_and_boxes(image: np.ndarray, boxes: List[Tuple[int, float, float, float, float]], aug_id: int) -> Tuple[np.ndarray, List[Tuple[int, float, float, float, float]]]:
    h, w = image.shape[:2]
    aug_img = image.copy()
    alpha = np.random.uniform(0.85, 1.2)
    beta = np.random.randint(-25, 25)
    aug_img = cv2.convertScaleAbs(aug_img, alpha=alpha, beta=beta)
    temp_shift = np.random.choice(['warm', 'cool', 'neutral'])
    if temp_shift == 'warm':
        aug_img[:, :, 2] = np.clip(aug_img[:, :, 2].astype(np.int16) + 15, 0, 255).astype(np.uint8)
        aug_img[:, :, 0] = np.clip(aug_img[:, :, 0].astype(np.int16) - 10, 0, 255).astype(np.uint8)
    elif temp_shift == 'cool':
        aug_img[:, :, 0] = np.clip(aug_img[:, :, 0].astype(np.int16) + 15, 0, 255).astype(np.uint8)
    if np.random.rand() < 0.35:
        ksize = np.random.choice([3, 5])
        aug_img = cv2.GaussianBlur(aug_img, (ksize, ksize), 0)
    if np.random.rand() < 0.3:
        noise = np.random.normal(0, 8, aug_img.shape).astype(np.int16)
        aug_img = np.clip(aug_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    angle = np.random.uniform(-8.0, 8.0)
    center = (w // 2, h // 2)
    rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    aug_img = cv2.warpAffine(aug_img, rot_mat, (w, h), borderMode=cv2.BORDER_REFLECT)
    rad = np.deg2rad(-angle)
    cos_a, sin_a = (np.cos(rad), np.sin(rad))
    new_boxes = []
    for cls_id, x_c, y_c, bw, bh in boxes:
        abs_x = x_c * w - center[0]
        abs_y = y_c * h - center[1]
        rot_x = abs_x * cos_a - abs_y * sin_a + center[0]
        rot_y = abs_x * sin_a + abs_y * cos_a + center[1]
        norm_x = np.clip(rot_x / w, 0.05, 0.95)
        norm_y = np.clip(rot_y / h, 0.05, 0.95)
        new_boxes.append((cls_id, norm_x, norm_y, bw, bh))
    return (aug_img, new_boxes)

def generate_yolo_yaml_config(output_yaml_path: str='blood_group_yolo.yaml'):
    content = f"path: {os.path.abspath(BIG_DATA_ROOT).replace('\\', '/')}\ntrain: images/train\nval: images/valid\ntest: images/test\n\nnc: 6\nnames: ['Well_A_Clumped', 'Well_A_Smooth', 'Well_B_Clumped', 'Well_B_Smooth', 'Well_D_Clumped', 'Well_D_Smooth']\n"
    with open(output_yaml_path, 'w') as f:
        f.write(content)
    print(f'[+] YOLOv8 Configuration file generated at: {output_yaml_path}')

def download_roboflow_instructions():
    print('\n' + '=' * 80)
    print('  HOW TO DOWNLOAD THE 3,757 ROBOFLOW BLOOD GROUP DATASET DIRECTLY')
    print('=' * 80)
    print('Method 1: Direct Web Export (One Click)')
    print('  1. Visit: https://universe.roboflow.com/minor-project-5th-semester/blood-group-detection-4yvdx')
    print("  2. Click 'Download Dataset' -> Select Format: 'YOLOv8'")
    print('  3. Download the .zip file and extract it into: dataset/big_data_blood_slides/')
    print('\nMethod 2: Python Roboflow API (Automated)')
    print('  Run in Python:')
    print('  >>> from roboflow import Roboflow')
    print("  >>> rf = Roboflow(api_key='YOUR_FREE_API_KEY')")
    print("  >>> project = rf.workspace('minor-project-5th-semester').project('blood-group-detection-4yvdx')")
    print("  >>> dataset = project.version(1).download('yolov8')")
    print('=' * 80 + '\n')
if __name__ == '__main__':
    setup_directory_structure()
    generate_yolo_yaml_config()
    download_roboflow_instructions()
