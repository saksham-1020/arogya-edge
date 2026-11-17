import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from simulator import generate_single_sample, BLOOD_GROUPS, ANTIGEN_MAP
from clinical_engine import calculate_clinical_risk, CLINICAL_RISK_MATRIX
from conformal_prediction import ConformalPredictor

def run_stress_robustness_experiment():
    print('=' * 80)
    print('      AMBULANCE CLINICAL PERTURBATION & ROBUSTNESS DEGRADATION AUDIT')
    print('=' * 80)
    noise_levels = [0.01, 0.03, 0.06, 0.1, 0.15, 0.2, 0.25]
    n_samples_per_level = 200
    std_ai_accuracies = []
    std_ai_risks = []
    conformal_abstain_rates = []
    conformal_safe_accuracies = []
    conformal_fatal_risks = []
    cp = ConformalPredictor(alpha=0.01)
    cp.q_hat = 0.85
    cp.is_calibrated = True
    for noise in noise_levels:
        correct_std = 0
        total_risk_std = 0.0
        abstain_count = 0
        correct_when_accepted = 0
        accepted_count = 0
        fatal_risk_conformal = 0.0
        for _ in range(n_samples_per_level):
            target_bg = np.random.choice(BLOOD_GROUPS)
            true_idx = BLOOD_GROUPS.index(target_bg)
            has_bubble = np.random.rand() < noise * 2.5
            temp = np.random.uniform(12.0, 46.0)
            hct = np.random.uniform(20.0, 55.0)
            sample = generate_single_sample(blood_group=target_bg, temp_celsius=temp, hematocrit=hct, noise_level=noise, has_bubble_artifact=has_bubble)
            signals = sample['signals']
            ch_reactions = [float(np.mean(signals[ch, 120:])) for ch in range(3)]
            prof = ANTIGEN_MAP[target_bg]
            antigen_noisy = [prof[i] + np.random.normal(0, noise * 3.5) for i in range(3)]
            logits = np.zeros(8)
            for idx, bg in enumerate(BLOOD_GROUPS):
                bg_prof = ANTIGEN_MAP[bg]
                match = sum((1.0 - abs(p - a) for p, a in zip(antigen_noisy, bg_prof)))
                logits[idx] = match * 2.5
            probs = np.exp(logits) / np.sum(np.exp(logits))
            pred_idx = int(np.argmax(probs))
            if pred_idx == true_idx:
                correct_std += 1
            std_risk = CLINICAL_RISK_MATRIX[true_idx, pred_idx]
            total_risk_std += std_risk
            cp_res = cp.predict_set(probs)
            if cp_res['abstain_from_automated_release']:
                abstain_count += 1
            else:
                accepted_count += 1
                if pred_idx == true_idx:
                    correct_when_accepted += 1
                else:
                    fatal_risk_conformal += CLINICAL_RISK_MATRIX[true_idx, pred_idx]
        std_acc = correct_std / n_samples_per_level * 100.0
        avg_std_risk = total_risk_std / n_samples_per_level
        abstain_pct = abstain_count / n_samples_per_level * 100.0
        safe_acc = correct_when_accepted / accepted_count * 100.0 if accepted_count > 0 else 100.0
        avg_conf_risk = fatal_risk_conformal / n_samples_per_level
        std_ai_accuracies.append(std_acc)
        std_ai_risks.append(avg_std_risk)
        conformal_abstain_rates.append(abstain_pct)
        conformal_safe_accuracies.append(safe_acc)
        conformal_fatal_risks.append(avg_conf_risk)
        print(f'  • Noise Level: {noise * 100:4.1f}% | Std AI Acc: {std_acc:5.1f}% (Risk: {avg_std_risk:5.2f}) | Conformal Safe Acc: {safe_acc:5.1f}% | Abstain Rate: {abstain_pct:5.1f}%')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    x_pct = [n * 100 for n in noise_levels]
    ax1.plot(x_pct, std_ai_accuracies, 'r-o', linewidth=2.2, label='Standard AI (Forced Prediction)')
    ax1.plot(x_pct, conformal_safe_accuracies, 'g-s', linewidth=2.2, label='Conformal Safe AI (Accepted Decisions)')
    ax1.plot(x_pct, conformal_abstain_rates, 'b--^', linewidth=1.8, label='Conformal Abstain Rate (Re-test Alerts)')
    ax1.set_xlabel('Sensor Noise & Ambulance Jitter Intensity (%)', fontweight='bold')
    ax1.set_ylabel('Percentage (%)', fontweight='bold')
    ax1.set_title('Reliability vs. Environmental Perturbation', fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='best', fontsize=9)
    ax2.plot(x_pct, std_ai_risks, 'r-o', linewidth=2.2, label='Standard AI Fatal Transfusion Risk')
    ax2.plot(x_pct, conformal_fatal_risks, 'g-s', linewidth=2.2, label='Conformal AI Transfusion Risk (Abstain-Protected)')
    ax2.set_xlabel('Sensor Noise & Ambulance Jitter Intensity (%)', fontweight='bold')
    ax2.set_ylabel('Asymmetric Clinical Risk Penalty', fontweight='bold')
    ax2.set_title('Fatal Transfusion Risk Suppression', fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(loc='best', fontsize=9)
    plt.tight_layout()
    curve_path = 'robustness_degradation_curve.png'
    plt.savefig(curve_path, dpi=300)
    plt.close()
    print(f'\n[+] Robustness plot saved to: {curve_path}')
if __name__ == '__main__':
    run_stress_robustness_experiment()
