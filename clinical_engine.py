from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
BG_TO_IDX = {bg: i for i, bg in enumerate(BLOOD_GROUPS)}
IDX_TO_BG = {i: bg for i, bg in enumerate(BLOOD_GROUPS)}
RBC_RECIPIENT_RULES = {'A+': ['A+', 'A-', 'O+', 'O-'], 'A-': ['A-', 'O-'], 'B+': ['B+', 'B-', 'O+', 'O-'], 'B-': ['B-', 'O-'], 'AB+': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'], 'AB-': ['AB-', 'A-', 'B-', 'O-'], 'O+': ['O+', 'O-'], 'O-': ['O-']}
RBC_DONOR_RULES = {'O-': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'], 'O+': ['O+', 'A+', 'B+', 'AB+'], 'A-': ['A-', 'A+', 'AB-', 'AB+'], 'A+': ['A+', 'AB+'], 'B-': ['B-', 'B+', 'AB-', 'AB+'], 'B+': ['B+', 'AB+'], 'AB-': ['AB-', 'AB+'], 'AB+': ['AB+']}

def build_clinical_transfusion_risk_matrix() -> np.ndarray:
    matrix = np.zeros((8, 8), dtype=np.float32)
    for i, true_bg in enumerate(BLOOD_GROUPS):
        true_abo = true_bg[:-1]
        true_rh = true_bg[-1]
        allowed_donors = RBC_RECIPIENT_RULES[true_bg]
        for j, pred_bg in enumerate(BLOOD_GROUPS):
            if i == j:
                matrix[i, j] = 0.0
                continue
            pred_abo = pred_bg[:-1]
            pred_rh = pred_bg[-1]
            is_compatible = pred_bg in allowed_donors
            if is_compatible:
                matrix[i, j] = 0.5
            else:
                abo_incompatible = pred_bg.replace('+', '').replace('-', '') not in [d.replace('+', '').replace('-', '') for d in allowed_donors if d.endswith(true_rh)]
                rh_incompatible = true_rh == '-' and pred_rh == '+'
                if abo_incompatible and rh_incompatible:
                    matrix[i, j] = 12.0
                elif abo_incompatible:
                    matrix[i, j] = 10.0
                elif rh_incompatible:
                    matrix[i, j] = 5.0
                else:
                    matrix[i, j] = 4.0
    return matrix
CLINICAL_RISK_MATRIX = build_clinical_transfusion_risk_matrix()

class AsymmetricTransfusionLoss(nn.Module):

    def __init__(self, risk_matrix: Optional[np.ndarray]=None, risk_weight: float=1.0):
        super().__init__()
        if risk_matrix is None:
            risk_matrix = CLINICAL_RISK_MATRIX
        self.register_buffer('cost_matrix', torch.tensor(risk_matrix, dtype=torch.float32))
        self.risk_weight = risk_weight

    def forward(self, pred_probs: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        eps = 1e-07
        log_probs = torch.log(pred_probs + eps)
        nll_loss = F.nll_loss(log_probs, targets)
        batch_costs = self.cost_matrix[targets]
        expected_risk = torch.sum(batch_costs * pred_probs, dim=-1)
        mean_risk_loss = torch.mean(expected_risk)
        total_loss = nll_loss + self.risk_weight * mean_risk_loss
        return total_loss

def calculate_clinical_risk(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    risks = [CLINICAL_RISK_MATRIX[int(t), int(p)] for t, p in zip(y_true, y_pred)]
    return float(np.mean(risks))

def calculate_nadler_blood_volume(height_cm: float, weight_kg: float, gender: str) -> Dict[str, Any]:
    height_m = height_cm / 100.0
    g = gender.strip().lower()
    if g in ['m', 'male', 'purush', 'man']:
        is_male = True
        tbv_liters = 0.3669 * height_m ** 3 + 0.03219 * weight_kg + 0.6041
    else:
        is_male = False
        tbv_liters = 0.3561 * height_m ** 3 + 0.03308 * weight_kg + 0.1833
    tbv_ml = tbv_liters * 1000.0
    eligible = True
    reasons = []
    if weight_kg < 50.0:
        eligible = False
        reasons.append(f'Body weight ({weight_kg:.1f} kg) is below minimum safe donor limit (50.0 kg).')
    if not eligible:
        recommended_donation_ml = 0
    elif weight_kg >= 60.0 and tbv_ml >= 4200.0:
        recommended_donation_ml = 450
    else:
        recommended_donation_ml = 350
    pct_of_tbv = recommended_donation_ml / tbv_ml * 100.0 if tbv_ml > 0 else 0.0
    if pct_of_tbv > 13.0 and eligible:
        recommended_donation_ml = 350
        pct_of_tbv = recommended_donation_ml / tbv_ml * 100.0
    return {'gender': 'Male' if is_male else 'Female', 'height_cm': height_cm, 'weight_kg': weight_kg, 'tbv_liters': round(float(tbv_liters), 2), 'tbv_ml': round(float(tbv_ml), 0), 'is_eligible_to_donate': eligible, 'eligibility_notes': '; '.join(reasons) if reasons else 'Eligible for voluntary safe blood donation.', 'recommended_donation_volume_ml': recommended_donation_ml, 'percent_volume_extracted': round(float(pct_of_tbv), 1)}

def get_transfusion_guide(blood_group: str) -> Dict[str, Any]:
    bg = blood_group.strip().upper()
    if bg not in BLOOD_GROUPS:
        return {'blood_group': bg, 'status': 'Invalid / Unknown Blood Group', 'can_donate_rbc_to': [], 'can_receive_rbc_from': [], 'clinical_badge': 'N/A'}
    donors = RBC_RECIPIENT_RULES[bg]
    recipients = RBC_DONOR_RULES[bg]
    badge = 'Standard Compatibility Profile'
    if bg == 'O-':
        badge = '★ UNIVERSAL RED BLOOD CELL DONOR (Emergency First-Line)'
    elif bg == 'AB+':
        badge = '★ UNIVERSAL RED BLOOD CELL RECIPIENT (Can accept any ABO-Rh)'
    elif bg == 'O+':
        badge = 'Most Common Donor for all Rh+ Recipients (O+, A+, B+, AB+)'
    elif bg == 'AB-':
        badge = 'Universal Plasma Donor (AB) / Rare RBC Phenotype'
    return {'blood_group': bg, 'can_donate_rbc_to': recipients, 'can_receive_rbc_from': donors, 'clinical_badge': badge, 'emergency_safe_rbc': 'O-' if bg != 'O-' else 'O- strictly'}
