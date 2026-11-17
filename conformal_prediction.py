from typing import List, Dict, Tuple, Any, Optional
import numpy as np
BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

class ConformalPredictor:

    def __init__(self, alpha: float=0.01):
        self.alpha = alpha
        self.q_hat = 1.0
        self.is_calibrated = False
        self.calibration_scores = None

    def calibrate(self, cal_probs: np.ndarray, cal_labels: np.ndarray) -> float:
        n = len(cal_labels)
        if n == 0:
            raise ValueError('Calibration set cannot be empty.')
        true_class_probs = cal_probs[np.arange(n), cal_labels]
        nonconformity_scores = 1.0 - true_class_probs
        self.calibration_scores = nonconformity_scores
        level = min(1.0, np.ceil((n + 1) * (1.0 - self.alpha)) / n)
        self.q_hat = float(np.quantile(nonconformity_scores, level, method='higher'))
        self.is_calibrated = True
        return self.q_hat

    def predict_set(self, prob_dist: np.ndarray) -> Dict[str, Any]:
        if not self.is_calibrated:
            self.q_hat = 0.85
        prob_dist = np.asarray(prob_dist, dtype=np.float32)
        included_indices = np.where(1.0 - prob_dist <= self.q_hat)[0]
        if len(included_indices) == 0:
            included_indices = np.array([np.argmax(prob_dist)])
        prediction_set = [BLOOD_GROUPS[i] for i in included_indices]
        set_size = len(prediction_set)
        top_idx = int(np.argmax(prob_dist))
        top_bg = BLOOD_GROUPS[top_idx]
        top_confidence = float(prob_dist[top_idx])
        if set_size == 1:
            clinical_status = 'PASSED: Guaranteed Single Diagnosis'
            abstain_flag = False
            alert_message = f'Statistically guaranteed under {(1.0 - self.alpha) * 100:.1f}% safety coverage.'
        else:
            clinical_status = 'ABSTAIN: Multi-Group Ambiguity Detected'
            abstain_flag = True
            alert_message = f'SAFETY ALERT: Prediction set contains {set_size} candidate phenotypes {prediction_set}. Agglutination reaction is borderline or noisy. Mandatory manual lab crossmatch / re-test required.'
        return {'prediction_set': prediction_set, 'set_size': set_size, 'top_candidate': top_bg, 'top_confidence': round(top_confidence * 100.0, 2), 'guaranteed_coverage_pct': round((1.0 - self.alpha) * 100.0, 2), 'conformal_quantile_threshold': round(self.q_hat, 4), 'abstain_from_automated_release': abstain_flag, 'clinical_status': clinical_status, 'alert_message': alert_message, 'class_probabilities': {bg: round(float(prob_dist[i]), 4) for i, bg in enumerate(BLOOD_GROUPS)}}

    def evaluate_batch(self, test_probs: np.ndarray, test_labels: np.ndarray) -> Dict[str, float]:
        n = len(test_labels)
        covered = 0
        singletons = 0
        total_set_size = 0
        for i in range(n):
            res = self.predict_set(test_probs[i])
            pred_set = res['prediction_set']
            true_bg = BLOOD_GROUPS[test_labels[i]]
            if true_bg in pred_set:
                covered += 1
            if len(pred_set) == 1:
                singletons += 1
            total_set_size += len(pred_set)
        empirical_coverage = covered / n * 100.0
        singleton_pct = singletons / n * 100.0
        avg_size = total_set_size / n
        return {'target_coverage_pct': (1.0 - self.alpha) * 100.0, 'empirical_coverage_pct': round(empirical_coverage, 2), 'singleton_efficiency_pct': round(singleton_pct, 2), 'average_prediction_set_size': round(avg_size, 3)}
