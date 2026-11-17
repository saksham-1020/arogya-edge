import os
import time
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from simulator import generate_batch, BLOOD_GROUPS, ANTIGEN_MAP
from clinical_engine import calculate_clinical_risk, CLINICAL_RISK_MATRIX
from conformal_prediction import ConformalPredictor
np.random.seed(42)
torch.manual_seed(42)

def extract_features_from_signals(signals: np.ndarray, temps: np.ndarray) -> np.ndarray:
    n_samples, n_channels, n_timesteps = signals.shape
    features = []
    for i in range(n_samples):
        sample_feat = []
        for ch in range(n_channels):
            sig = signals[i, ch]
            mean_val = np.mean(sig)
            std_val = np.std(sig)
            min_val = np.min(sig)
            max_val = np.max(sig)
            diff_val = np.diff(sig)
            max_slope = np.max(np.abs(diff_val))
            delta = sig[-1] - sig[0]
            energy = np.sum(sig ** 2) / n_timesteps
            sample_feat.extend([mean_val, std_val, min_val, max_val, max_slope, delta, energy])
        sample_feat.append(float(temps[i]))
        features.append(sample_feat)
    return np.array(features, dtype=np.float32)

class MobileNet1D(nn.Module):

    def __init__(self, in_channels: int=3, num_classes: int=8):
        super().__init__()
        self.stem = nn.Sequential(nn.Conv1d(in_channels, 16, kernel_size=5, stride=2, padding=2), nn.BatchNorm1d(16), nn.ReLU())
        self.dw1 = nn.Conv1d(16, 16, kernel_size=5, stride=2, padding=2, groups=16)
        self.pw1 = nn.Conv1d(16, 32, kernel_size=1)
        self.bn1 = nn.BatchNorm1d(32)
        self.act1 = nn.ReLU()
        self.dw2 = nn.Conv1d(32, 32, kernel_size=5, stride=2, padding=2, groups=32)
        self.pw2 = nn.Conv1d(32, 64, kernel_size=1)
        self.bn2 = nn.BatchNorm1d(64)
        self.act2 = nn.ReLU()
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.classifier = nn.Linear(64, num_classes)

    def forward(self, x):
        h = self.stem(x)
        h = self.act1(self.bn1(self.pw1(self.dw1(h))))
        h = self.act2(self.bn2(self.pw2(self.dw2(h))))
        h = self.pool(h).squeeze(-1)
        logits = self.classifier(h)
        return torch.softmax(logits, dim=-1)

class SimpleTCECOModel(nn.Module):

    def __init__(self, in_channels: int=3, num_classes: int=8):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels, 24, kernel_size=7, stride=2, padding=3)
        self.bn1 = nn.BatchNorm1d(24)
        self.conv2 = nn.Conv1d(24, 48, kernel_size=5, stride=2, padding=2)
        self.bn2 = nn.BatchNorm1d(48)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Sequential(nn.Linear(48, 32), nn.ReLU(), nn.Linear(32, num_classes))

    def forward(self, x):
        h = torch.relu(self.bn1(self.conv1(x)))
        h = torch.relu(self.bn2(self.conv2(h)))
        h = self.pool(h).squeeze(-1)
        logits = self.fc(h)
        return torch.softmax(logits, dim=-1)

def run_benchmark():
    print('=' * 80)
    print('      Q1 MULTI-MODEL BENCHMARK: 5 ALGORITHMS FOR CLINICAL BLOOD TYPING')
    print('=' * 80)
    total_samples = 4000
    print(f'[1/5] Synthesizing {total_samples} clinical edge-case blood samples...')
    raw = generate_batch(batch_size=total_samples, time_steps=200)
    signals = raw['signals']
    temperatures = raw['temperatures']
    labels = raw['class_indices']
    print('[2/5] Extracting kinetic statistical features for classical ML models...')
    X_feat = extract_features_from_signals(signals, temperatures)
    idx_train = slice(0, 2200)
    idx_cal = slice(2200, 3000)
    idx_test = slice(3000, 4000)
    X_tr_feat, y_tr = (X_feat[idx_train], labels[idx_train])
    X_cal_feat, y_cal = (X_feat[idx_cal], labels[idx_cal])
    X_te_feat, y_te = (X_feat[idx_test], labels[idx_test])
    X_tr_sig = signals[idx_train]
    X_cal_sig = signals[idx_cal]
    X_te_sig = signals[idx_test]
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'      Execution Device: {device}')
    t_tr_sig = torch.tensor(X_tr_sig, dtype=torch.float32)
    t_tr_y = torch.tensor(y_tr, dtype=torch.int64)
    train_loader = DataLoader(TensorDataset(t_tr_sig, t_tr_y), batch_size=64, shuffle=True)
    t_cal_sig = torch.tensor(X_cal_sig, dtype=torch.float32, device=device)
    t_te_sig = torch.tensor(X_te_sig, dtype=torch.float32, device=device)
    results = {}
    confusion_matrices = {}
    print('\n[+] Training Model 1: T-CECO (Physics-Guided Lightweight 1D-CNN)...')
    m_tceco = SimpleTCECOModel().to(device)
    opt1 = optim.AdamW(m_tceco.parameters(), lr=0.003)
    loss_fn = nn.CrossEntropyLoss()
    m_tceco.train()
    for ep in range(12):
        for bx, by in train_loader:
            bx, by = (bx.to(device), by.to(device))
            opt1.zero_grad()
            out = m_tceco(bx)
            loss = loss_fn(torch.log(out + 1e-07), by)
            loss.backward()
            opt1.step()
    m_tceco.eval()
    start_t = time.perf_counter()
    with torch.no_grad():
        p_cal_tceco = m_tceco(t_cal_sig).cpu().numpy()
        p_te_tceco = m_tceco(t_te_sig).cpu().numpy()
    lat_tceco = (time.perf_counter() - start_t) / len(y_te) * 1000.0
    preds_tceco = np.argmax(p_te_tceco, axis=-1)
    results['T-CECO (Proposed)'] = {'cal_probs': p_cal_tceco, 'test_probs': p_te_tceco, 'preds': preds_tceco, 'latency_ms': lat_tceco}
    print('[+] Training Model 2: MobileNet-1D (Depthwise Separable CNN)...')
    m_mob = MobileNet1D().to(device)
    opt2 = optim.AdamW(m_mob.parameters(), lr=0.003)
    m_mob.train()
    for ep in range(12):
        for bx, by in train_loader:
            bx, by = (bx.to(device), by.to(device))
            opt2.zero_grad()
            out = m_mob(bx)
            loss = loss_fn(torch.log(out + 1e-07), by)
            loss.backward()
            opt2.step()
    m_mob.eval()
    start_t = time.perf_counter()
    with torch.no_grad():
        p_cal_mob = m_mob(t_cal_sig).cpu().numpy()
        p_te_mob = m_mob(t_te_sig).cpu().numpy()
    lat_mob = (time.perf_counter() - start_t) / len(y_te) * 1000.0
    preds_mob = np.argmax(p_te_mob, axis=-1)
    results['MobileNet-1D'] = {'cal_probs': p_cal_mob, 'test_probs': p_te_mob, 'preds': preds_mob, 'latency_ms': lat_mob}
    print('[+] Training Model 3: Random Forest Classifier (100 Trees)...')
    rf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    rf.fit(X_tr_feat, y_tr)
    start_t = time.perf_counter()
    p_cal_rf = rf.predict_proba(X_cal_feat)
    p_te_rf = rf.predict_proba(X_te_feat)
    lat_rf = (time.perf_counter() - start_t) / len(y_te) * 1000.0
    preds_rf = np.argmax(p_te_rf, axis=-1)
    results['Random Forest'] = {'cal_probs': p_cal_rf, 'test_probs': p_te_rf, 'preds': preds_rf, 'latency_ms': lat_rf}
    print('[+] Training Model 4: HistGradientBoosting Classifier...')
    gb = HistGradientBoostingClassifier(max_iter=100, max_depth=6, random_state=42)
    gb.fit(X_tr_feat, y_tr)
    start_t = time.perf_counter()
    p_cal_gb = gb.predict_proba(X_cal_feat)
    p_te_gb = gb.predict_proba(X_te_feat)
    lat_gb = (time.perf_counter() - start_t) / len(y_te) * 1000.0
    preds_gb = np.argmax(p_te_gb, axis=-1)
    results['Gradient Boosting'] = {'cal_probs': p_cal_gb, 'test_probs': p_te_gb, 'preds': preds_gb, 'latency_ms': lat_gb}
    print('[+] Training Model 5: Support Vector Machine (RBF-Kernel SVC)...')
    mean_f = np.mean(X_tr_feat, axis=0, keepdims=True)
    std_f = np.std(X_tr_feat, axis=0, keepdims=True) + 1e-07
    X_tr_f_norm = (X_tr_feat - mean_f) / std_f
    X_cal_f_norm = (X_cal_feat - mean_f) / std_f
    X_te_f_norm = (X_te_feat - mean_f) / std_f
    svm = SVC(kernel='rbf', C=2.0, probability=True, random_state=42)
    svm.fit(X_tr_f_norm, y_tr)
    start_t = time.perf_counter()
    p_cal_svm = svm.predict_proba(X_cal_f_norm)
    p_te_svm = svm.predict_proba(X_te_f_norm)
    lat_svm = (time.perf_counter() - start_t) / len(y_te) * 1000.0
    preds_svm = np.argmax(p_te_svm, axis=-1)
    results['Support Vector Machine'] = {'cal_probs': p_cal_svm, 'test_probs': p_te_svm, 'preds': preds_svm, 'latency_ms': lat_svm}
    print('\n[3/5] Evaluating Metrics & Conformal Coverage (1 - alpha = 99.0%)...')
    benchmark_summary = []
    for name, data in results.items():
        preds = data['preds']
        acc = accuracy_score(y_te, preds) * 100.0
        prec, rec, f1, _ = precision_recall_fscore_support(y_te, preds, average='macro', zero_division=0)
        risk = calculate_clinical_risk(y_te, preds)
        cp = ConformalPredictor(alpha=0.01)
        cp.calibrate(data['cal_probs'], y_cal)
        cp_eval = cp.evaluate_batch(data['test_probs'], y_te)
        cm = confusion_matrix(y_te, preds, labels=range(8))
        confusion_matrices[name] = cm
        summary_row = {'Model': name, 'Accuracy (%)': round(acc, 2), 'Precision (%)': round(prec * 100.0, 2), 'Recall (%)': round(rec * 100.0, 2), 'F1-Score (%)': round(f1 * 100.0, 2), 'Transfusion Risk (Loss)': round(risk, 4), 'Latency (ms)': round(data['latency_ms'], 3), 'Conformal Coverage 99% (%)': round(cp_eval['empirical_coverage_pct'], 2), 'Singleton Efficiency (%)': round(cp_eval['singleton_efficiency_pct'], 2)}
        benchmark_summary.append(summary_row)
    print('[4/5] Generating publication-quality Confusion Matrix Heatmaps...')
    fig, axes = plt.subplots(1, 5, figsize=(28, 5))
    model_names = list(results.keys())
    for idx, name in enumerate(model_names):
        ax = axes[idx]
        cm = confusion_matrices[name]
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=idx == 4, xticklabels=BLOOD_GROUPS, yticklabels=BLOOD_GROUPS, ax=ax)
        ax.set_title(f"{name}\nAcc: {benchmark_summary[idx]['Accuracy (%)']}%", fontsize=11, fontweight='bold')
        ax.set_xlabel('Predicted Phenotype', fontsize=9)
        if idx == 0:
            ax.set_ylabel('True Ground Truth', fontsize=9)
        else:
            ax.set_ylabel('')
    plt.suptitle('Clinical Phenotype Confusion Matrix Across 5 AI Architectures (N = 1,000 Unseen Samples)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    cm_plot_path = 'benchmark_confusion_matrix_heatmap.png'
    plt.savefig(cm_plot_path, dpi=300)
    plt.close()
    print(f'      Saved: {cm_plot_path}')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    m_labels = [r['Model'] for r in benchmark_summary]
    acc_vals = [r['Accuracy (%)'] for r in benchmark_summary]
    risk_vals = [r['Transfusion Risk (Loss)'] for r in benchmark_summary]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    bars1 = ax1.bar(m_labels, acc_vals, color=colors, width=0.55)
    ax1.set_ylim(min(acc_vals) - 2.0, 100.5)
    ax1.set_ylabel('Test Accuracy (%)', fontweight='bold')
    ax1.set_title('Classification Accuracy Comparison', fontweight='bold')
    ax1.grid(axis='y', linestyle='--', alpha=0.6)
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.15, f'{yval:.2f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax1.tick_params(axis='x', rotation=20)
    bars2 = ax2.bar(m_labels, risk_vals, color=colors, width=0.55)
    ax2.set_ylabel('Clinical Transfusion Risk Penalty (Lower is Safer)', fontweight='bold')
    ax2.set_title('Asymmetric Clinical Risk (Fatal Mismatch Penalty)', fontweight='bold')
    ax2.grid(axis='y', linestyle='--', alpha=0.6)
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.01, f'{yval:.4f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax2.tick_params(axis='x', rotation=20)
    plt.tight_layout()
    bar_plot_path = 'benchmark_models_comparison.png'
    plt.savefig(bar_plot_path, dpi=300)
    plt.close()
    print(f'      Saved: {bar_plot_path}')
    print('\n' + '=' * 115)
    print('                    Q1 JOURNAL MULTI-MODEL BENCHMARK TABLE')
    print('=' * 115)
    header = '| Model Architecture | Accuracy (%) | Precision (%) | Recall (%) | F1-Score (%) | Transfusion Risk | Latency (ms) | CP 99% Coverage |'
    sep = '|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|'
    print(header)
    print(sep)
    for r in benchmark_summary:
        print(f"| **{r['Model']}** | {r['Accuracy (%)']:.2f}% | {r['Precision (%)']:.2f}% | {r['Recall (%)']:.2f}% | {r['F1-Score (%)']:.2f}% | {r['Transfusion Risk (Loss)']:.4f} | {r['Latency (ms)']:.2f} ms | {r['Conformal Coverage 99% (%)']:.2f}% |")
    print('=' * 115)
    with open('benchmark_results.json', 'w') as f:
        json.dump(benchmark_summary, f, indent=4)
    print('\n[5/5] Benchmark completed successfully! All artifacts exported.')
if __name__ == '__main__':
    run_benchmark()
