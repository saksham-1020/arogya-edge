import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import torch
import numpy as np
from simulator import generate_single_sample, BLOOD_GROUPS
from models import TCECOModel, CausalAuditor

def load_system():
    checkpoint_path = os.path.join(os.path.dirname(__file__), 'tceco_checkpoint.pt')
    if not os.path.exists(checkpoint_path):
        print('[-] Checkpoint not found. Running training first...')
        from train import train_tceco
        train_tceco(epochs=12, batches_per_epoch=25, batch_size=64)
    device = torch.device('cpu')
    model = TCECOModel(time_steps=200, out_classes=8)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()
    auditor = CausalAuditor(uncertainty_threshold=0.12)
    return (model, auditor)

def evaluate_patient(model, auditor, blood_group, temp, hct, weak=False, bubble=False, label='Patient Test'):
    sample = generate_single_sample(blood_group=blood_group, temp_celsius=temp, hematocrit=hct, is_weak_variant=weak, has_bubble_artifact=bubble, time_steps=200)
    sig_tensor = torch.tensor(sample['signals'], dtype=torch.float32).unsqueeze(0)
    temp_tensor = torch.tensor([temp], dtype=torch.float32)
    with torch.no_grad():
        out = model(sig_tensor, temp_tensor)
        probs = out['prob'].squeeze(0).numpy()
        pred_idx = int(np.argmax(probs))
        antigen_probs = out['antigen_probs'].squeeze(0).numpy()
        uncertainty = float(out['uncertainty'].item())
        baseline = sample['signals'][:, :15].mean(axis=-1)
        min_val = sample['signals'].min(axis=-1)
        kinetic_depths = baseline - min_val
        cert = auditor.audit(predicted_idx=pred_idx, probs=probs, antigen_probs=antigen_probs, uncertainty=uncertainty, temperature=temp, channel_kinetic_depths=kinetic_depths)
    print(f'\n>>> {label}')
    print(f"    Parameters: Temp={temp:.1f}°C | Hematocrit={hct:.1f}% | Subtype={('Weak D' if weak else 'Standard')}")
    print(f"    [GROUND TRUTH]: {blood_group}  ====>  [MODEL PREDICTION]: {cert['predicted_blood_group']}")
    print(f"    Clinical Status: {cert['overall_status']}")
    print(f"    Epistemic Confidence: {cert['epistemic_confidence']} | Uncertainty (u): {cert['uncertainty_index']}")
    print(f"    ICD-11 Code: {cert['icd11_clinical_code']}")
    print(f"    Emergency Transfusion: {cert['transfusion_protocol']}")
    print('    Channel Signals:')
    for ch in cert['channel_evidence']:
        print(f"      • {ch['channel']}: {ch['state']} (p={ch['antigen_probability']:.3f}, Drop={ch['kinetic_depth_mv']} mV, Margin={ch['counterfactual_safety_margin']})")
    print(f"    Fail-Safe Interlock: {cert['medico_legal_audit']['fail_safe_interlock']}")
    print('-' * 80)

def run_random_patients(n=5):
    model, auditor = load_system()
    print('\n' + '=' * 80)
    print(f'      GENERATING {n} RANDOM EMERGENCY PATIENT SAMPLES (REAL-TIME TEST)')
    print('=' * 80)
    for i in range(1, n + 1):
        bg = np.random.choice(BLOOD_GROUPS)
        temp = float(np.random.uniform(12.0, 46.0))
        hct = float(np.random.uniform(20.0, 58.0))
        weak = np.random.rand() < 0.2
        bubble = np.random.rand() < 0.1
        evaluate_patient(model, auditor, bg, temp, hct, weak, bubble, label=f'Random Patient #{i}')

def run_benchmark():
    model, auditor = load_system()
    test_scenarios = [{'bg': 'B+', 'temp': 28.0, 'hct': 42.0, 'weak': False, 'bubble': False, 'desc': 'Standard Clinical Baseline'}, {'bg': 'O+', 'temp': 30.0, 'hct': 19.5, 'weak': False, 'bubble': False, 'desc': 'Severe Anemic Rural Patient (HCT 19.5%)'}, {'bg': 'AB+', 'temp': 46.5, 'hct': 44.0, 'weak': False, 'bubble': False, 'desc': 'Indian Summer Heatwave (46.5°C in MP)'}, {'bg': 'A+', 'temp': 25.0, 'hct': 40.0, 'weak': True, 'bubble': False, 'desc': "Rare 'Weak D' Subtype Variant"}, {'bg': 'A-', 'temp': 26.0, 'hct': 38.0, 'weak': False, 'bubble': True, 'desc': 'Bubble / Sensor Occlusion Artifact'}]
    print('\n' + '=' * 80)
    print('      T-CECO: 5 STANDARD BENCHMARK CLINICAL STRESS-TESTS')
    print('=' * 80)
    for i, sc in enumerate(test_scenarios, 1):
        evaluate_patient(model, auditor, sc['bg'], sc['temp'], sc['hct'], sc['weak'], sc['bubble'], label=f"Benchmark #{i}: {sc['desc']}")
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'benchmark':
        run_benchmark()
    else:
        run_random_patients(n=4)
