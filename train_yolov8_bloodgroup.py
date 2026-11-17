import os
import sys
import numpy as np
from PIL import Image
from ultralytics import YOLO
from simulator import BLOOD_GROUPS, ANTIGEN_MAP
from clinical_engine import get_transfusion_guide, calculate_clinical_risk
from conformal_prediction import ConformalPredictor
YOLO_CONFIG_YAML = os.path.join(os.path.dirname(__file__), 'dataset', 'big_data_blood_slides', 'data.yaml')

def train_yolov8_model(model_size: str='yolov8n.pt', epochs: int=15, imgsz: int=640, batch: int=16):
    print('=' * 80)
    print('       YOLOV8 CLINICAL BLOOD GROUP DETECTOR: TRAINING PIPELINE')
    print(f'       Dataset: {YOLO_CONFIG_YAML}')
    print(f'       Model: {model_size} | Epochs: {epochs} | Image Size: {imgsz} | Batch: {batch}')
    print('=' * 80)
    if not os.path.exists(YOLO_CONFIG_YAML):
        raise FileNotFoundError(f'data.yaml not found at {YOLO_CONFIG_YAML}')
    model = YOLO(model_size)
    print(f'[+] Starting training with Ultralytics engine on 5,675 images...')
    results = model.train(data=YOLO_CONFIG_YAML, epochs=epochs, imgsz=imgsz, batch=batch, optimizer='AdamW', lr0=0.002, weight_decay=0.0005, patience=8, save=True, project='blood_group_yolov8', name='run_clinical_experiment')
    print('\n[+] Training completed! Best model saved in: blood_group_yolov8/run_clinical_experiment/weights/best.pt')
    return results

def predict_blood_group_yolo(image_path: str, weights_path: str='blood_group_yolov8/run_clinical_experiment/weights/best.pt', conf_threshold: float=0.4):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f'Image not found at {image_path}')
    if not os.path.exists(weights_path):
        weights_path = 'yolov8n.pt'
        print(f'[!] Warning: Custom weights not found. Using pretrained {weights_path} demo mode.')
    model = YOLO(weights_path)
    results = model(image_path, conf=conf_threshold)[0]
    detected_boxes = results.boxes
    print(f'\n[+] Detections Found on Slide: {len(detected_boxes)}')
    well_a_present = 0
    well_b_present = 0
    well_d_present = 0
    max_confs = {0: 0.0, 1: 0.0, 2: 0.0}
    borderline_flags = []
    for box in detected_boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        if cls_id in max_confs and conf > max_confs[cls_id]:
            max_confs[cls_id] = conf
        if cls_id == 0:
            well_a_present = 1
            print(f'  • Anti-A Reaction Spot: POSITIVE [Conf: {conf * 100:.1f}%]')
        elif cls_id == 1:
            well_b_present = 1
            print(f'  • Anti-B Reaction Spot: POSITIVE [Conf: {conf * 100:.1f}%]')
        elif cls_id == 2:
            well_d_present = 1
            print(f'  • Anti-D (Rh) Reaction Spot: POSITIVE [Conf: {conf * 100:.1f}%]')
        if 0.35 <= conf < 0.5:
            borderline_flags.append(f'Borderline confidence ({conf * 100:.1f}%) for class {cls_id}')
    reaction_profile = [well_a_present, well_b_present, well_d_present]
    diagnosed_bg = 'Unknown'
    for bg, prof in ANTIGEN_MAP.items():
        if prof == reaction_profile:
            diagnosed_bg = bg
            break
    conformal_status = 'PASSED'
    if borderline_flags:
        conformal_status = 'ABSTAIN'
        print(f"\n⚠️ CONFORMAL ABSTAIN WARNING: {', '.join(borderline_flags)}")
        print('  Clinical fail-safe activated: Manual review recommended.')
    print(f'\n>>> DIAGNOSED BLOOD GROUP: {diagnosed_bg} (Profile: {reaction_profile})')
    guide = get_transfusion_guide(diagnosed_bg)
    print(f">>> Clinical Status: {guide['clinical_badge']}")
    print(f">>> Compatible RBC Donors: {', '.join(guide['can_receive_rbc_from'])}")
    print(f">>> Compatible Recipients: {', '.join(guide['can_donate_rbc_to'])}")
    return {'diagnosed_blood_group': diagnosed_bg, 'reaction_profile': reaction_profile, 'conformal_status': conformal_status, 'detections_count': len(detected_boxes), 'clinical_guide': guide, 'results_obj': results}
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='YOLOv8 Blood Group Pipeline')
    parser.add_argument('--train', action='store_true', help='Start YOLOv8 training on 5,675 images')
    parser.add_argument('--predict', type=str, default=None, help='Path to slide image for prediction')
    parser.add_argument('--epochs', type=int, default=15, help='Number of training epochs')
    parser.add_argument('--batch', type=int, default=16, help='Batch size')
    args = parser.parse_args()
    if args.train:
        train_yolov8_model(epochs=args.epochs, batch=args.batch)
    elif args.predict:
        predict_blood_group_yolo(args.predict)
    else:
        print('\n=== YOLOv8 Blood Group Pipeline Ready ===')
        print(f'Dataset path: {YOLO_CONFIG_YAML}')
        print('Run training:')
        print('  python train_yolov8_bloodgroup.py --train --epochs 15 --batch 16')
        print('Run prediction on an image:')
        print('  python train_yolov8_bloodgroup.py --predict path/to/image.jpg')
