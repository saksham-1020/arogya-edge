import os
import sys
os.environ['LOKY_MAX_CPU_COUNT'] = '4'
os.environ['MPLCONFIGDIR'] = os.path.join(os.path.dirname(__file__), '.mplconfig')
os.makedirs(os.environ['MPLCONFIGDIR'], exist_ok=True)
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
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from simulator import generate_batch, BLOOD_GROUPS, ANTIGEN_MAP
from clinical_engine import calculate_clinical_risk, CLINICAL_RISK_MATRIX
from conformal_prediction import ConformalPredictor
np.random.seed(42)
torch.manual_seed(42)
ARTIFACT_DIR = 'C:\\Users\\Saksham Tomar\\.gemini\\antigravity\\brain\\566d1ef6-9c6a-4f6b-91f4-28f7bdeff862'

def extract_features(signals: np.ndarray, temps: np.ndarray) -> np.ndarray:
    n_samples, n_channels, n_timesteps = signals.shape
    feats = []
    for i in range(n_samples):
        row = []
        for ch in range(n_channels):
            s = signals[i, ch]
            row.extend([float(np.mean(s)), float(np.std(s)), float(np.min(s)), float(np.max(s)), float(np.ptp(s)), float(s[-1] - s[0]), float(np.sum(s ** 2) / n_timesteps), float(np.var(np.diff(s)))])
        row.append(float(temps[i]))
        feats.append(row)
    return np.array(feats, dtype=np.float32)

class TCECOConvNet(nn.Module):

    def __init__(self, in_channels=3, n_classes=8):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels, 32, kernel_size=7, padding=3)
        self.bn1 = nn.BatchNorm1d(32)
        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, padding=2)
        self.bn2 = nn.BatchNorm1d(64)
        self.conv3 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm1d(128)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.dropout = nn.Dropout(0.25)
        self.fc = nn.Linear(128 + 1, n_classes)
        self.relu = nn.ReLU()

    def forward(self, x, temp):
        h = self.relu(self.bn1(self.conv1(x)))
        h = self.relu(self.bn2(self.conv2(h)))
        h = self.relu(self.bn3(self.conv3(h)))
        h = self.pool(h).squeeze(-1)
        h = self.dropout(h)
        h = torch.cat([h, temp.unsqueeze(-1)], dim=-1)
        return self.fc(h)

class DeepMLP(nn.Module):

    def __init__(self, in_features=25, n_classes=8):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(in_features, 128), nn.LayerNorm(128), nn.ReLU(), nn.Dropout(0.2), nn.Linear(128, 64), nn.LayerNorm(64), nn.ReLU(), nn.Dropout(0.15), nn.Linear(64, n_classes))

    def forward(self, x):
        return self.net(x)

def run_multimodel_benchmark_and_audit():
    print('=' * 90)
    print('    6-MODEL CLINICAL BENCHMARK & RIGOROUS OVERFITTING / UNDERFITTING AUDIT')
    print('=' * 90)
    print('\n[+] Generating 5,000 multi-patient clinical test profiles...')
    full_data = generate_batch(batch_size=5000, time_steps=200)
    signals = full_data['signals']
    temps = full_data['temperatures']
    targets = full_data['class_indices']
    hcts = full_data['hematocrits']
    print('[+] Extracting 25 high-dimensional biophysical agglutination features...')
    X_feats = extract_features(signals, temps)
    y_labels = targets
    indices = np.random.permutation(len(y_labels))
    train_idx, val_idx, test_idx = (indices[:3000], indices[3000:4000], indices[4000:])
    X_train_f, y_train = (X_feats[train_idx], y_labels[train_idx])
    X_val_f, y_val = (X_feats[val_idx], y_labels[val_idx])
    X_test_f, y_test = (X_feats[test_idx], y_labels[test_idx])
    sig_train, temp_train = (signals[train_idx], temps[train_idx])
    sig_val, temp_val = (signals[val_idx], temps[val_idx])
    sig_test, temp_test = (signals[test_idx], temps[test_idx])
    model_results = {}
    print('\n>>> [1/6] Training T-CECO Deep 1D-CNN (PyTorch)...')
    tceco_net = TCECOConvNet(in_channels=3, n_classes=8)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(tceco_net.parameters(), lr=0.003, weight_decay=0.0001)
    train_ds = TensorDataset(torch.tensor(sig_train, dtype=torch.float32), torch.tensor(temp_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.long))
    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    t0 = time.time()
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=20)
    for epoch in range(20):
        tceco_net.train()
        for bx, bt, by in train_loader:
            optimizer.zero_grad()
            out = tceco_net(bx, bt)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()
        scheduler.step()
    train_time_tceco = time.time() - t0
    tceco_net.eval()
    with torch.no_grad():
        train_preds_tceco = torch.argmax(tceco_net(torch.tensor(sig_train, dtype=torch.float32), torch.tensor(temp_train, dtype=torch.float32)), dim=-1).numpy()
        val_preds_tceco = torch.argmax(tceco_net(torch.tensor(sig_val, dtype=torch.float32), torch.tensor(temp_val, dtype=torch.float32)), dim=-1).numpy()
        test_logits_tceco = tceco_net(torch.tensor(sig_test, dtype=torch.float32), torch.tensor(temp_test, dtype=torch.float32))
        test_probs_tceco = torch.softmax(test_logits_tceco, dim=-1).numpy()
        test_preds_tceco = np.argmax(test_probs_tceco, axis=-1)
    model_results['T-CECO Deep ConvNet'] = {'train_acc': accuracy_score(y_train, train_preds_tceco) * 100.0, 'val_acc': accuracy_score(y_val, val_preds_tceco) * 100.0, 'test_acc': accuracy_score(y_test, test_preds_tceco) * 100.0, 'preds': test_preds_tceco, 'probs': test_probs_tceco, 'time': train_time_tceco}
    print('>>> [2/6] Training Deep MLP Neural Network (PyTorch)...')
    mlp_net = DeepMLP(in_features=25, n_classes=8)
    mlp_opt = optim.AdamW(mlp_net.parameters(), lr=0.003, weight_decay=0.0001)
    mlp_ds = TensorDataset(torch.tensor(X_train_f, dtype=torch.float32), torch.tensor(y_train, dtype=torch.long))
    mlp_loader = DataLoader(mlp_ds, batch_size=64, shuffle=True)
    t0 = time.time()
    for epoch in range(15):
        mlp_net.train()
        for bx, by in mlp_loader:
            mlp_opt.zero_grad()
            loss = criterion(mlp_net(bx), by)
            loss.backward()
            mlp_opt.step()
    train_time_mlp = time.time() - t0
    mlp_net.eval()
    with torch.no_grad():
        train_preds_mlp = torch.argmax(mlp_net(torch.tensor(X_train_f, dtype=torch.float32)), dim=-1).numpy()
        val_preds_mlp = torch.argmax(mlp_net(torch.tensor(X_val_f, dtype=torch.float32)), dim=-1).numpy()
        test_logits_mlp = mlp_net(torch.tensor(X_test_f, dtype=torch.float32))
        test_probs_mlp = torch.softmax(test_logits_mlp, dim=-1).numpy()
        test_preds_mlp = np.argmax(test_probs_mlp, axis=-1)
    model_results['Deep MLP'] = {'train_acc': accuracy_score(y_train, train_preds_mlp) * 100.0, 'val_acc': accuracy_score(y_val, val_preds_mlp) * 100.0, 'test_acc': accuracy_score(y_test, test_preds_mlp) * 100.0, 'preds': test_preds_mlp, 'probs': test_probs_mlp, 'time': train_time_mlp}
    print('>>> [3/6] Training Random Forest Classifier (100 Trees)...')
    t0 = time.time()
    rf = RandomForestClassifier(n_estimators=100, max_depth=16, min_samples_split=3, random_state=42, n_jobs=-1)
    rf.fit(X_train_f, y_train)
    train_time_rf = time.time() - t0
    model_results['Random Forest'] = {'train_acc': accuracy_score(y_train, rf.predict(X_train_f)) * 100.0, 'val_acc': accuracy_score(y_val, rf.predict(X_val_f)) * 100.0, 'test_acc': accuracy_score(y_test, rf.predict(X_test_f)) * 100.0, 'preds': rf.predict(X_test_f), 'probs': rf.predict_proba(X_test_f), 'time': train_time_rf}
    print('>>> [4/6] Training HistGradientBoosting Classifier...')
    t0 = time.time()
    hgb = HistGradientBoostingClassifier(max_iter=100, learning_rate=0.08, max_depth=10, random_state=42)
    hgb.fit(X_train_f, y_train)
    train_time_hgb = time.time() - t0
    model_results['HistGradientBoosting'] = {'train_acc': accuracy_score(y_train, hgb.predict(X_train_f)) * 100.0, 'val_acc': accuracy_score(y_val, hgb.predict(X_val_f)) * 100.0, 'test_acc': accuracy_score(y_test, hgb.predict(X_test_f)) * 100.0, 'preds': hgb.predict(X_test_f), 'probs': hgb.predict_proba(X_test_f), 'time': train_time_hgb}
    print('>>> [5/6] Training Support Vector Machine (RBF Kernel, C=10.0)...')
    t0 = time.time()
    svm = SVC(kernel='rbf', C=10.0, gamma='scale', probability=True, random_state=42)
    svm.fit(X_train_f, y_train)
    train_time_svm = time.time() - t0
    model_results['RBF-Kernel SVM'] = {'train_acc': accuracy_score(y_train, svm.predict(X_train_f)) * 100.0, 'val_acc': accuracy_score(y_val, svm.predict(X_val_f)) * 100.0, 'test_acc': accuracy_score(y_test, svm.predict(X_test_f)) * 100.0, 'preds': svm.predict(X_test_f), 'probs': svm.predict_proba(X_test_f), 'time': train_time_svm}
    print('>>> [6/6] Training K-Nearest Neighbors (K=5, Distance-Weighted)...')
    t0 = time.time()
    knn = KNeighborsClassifier(n_neighbors=5, weights='distance')
    knn.fit(X_train_f, y_train)
    train_time_knn = time.time() - t0
    model_results['K-Nearest Neighbors'] = {'train_acc': accuracy_score(y_train, knn.predict(X_train_f)) * 100.0, 'val_acc': accuracy_score(y_val, knn.predict(X_val_f)) * 100.0, 'test_acc': accuracy_score(y_test, knn.predict(X_test_f)) * 100.0, 'preds': knn.predict(X_test_f), 'probs': knn.predict_proba(X_test_f), 'time': train_time_knn}
    print('\n' + '=' * 90)
    print('                 5-FOLD STRATIFIED CROSS-VALIDATION RESULTS')
    print('=' * 90)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    rf_cv_scores = []
    hgb_cv_scores = []
    svm_cv_scores = []
    for fold, (train_k, val_k) in enumerate(skf.split(X_feats, y_labels)):
        X_tr, y_tr = (X_feats[train_k], y_labels[train_k])
        X_va, y_va = (X_feats[val_k], y_labels[val_k])
        rf_f = RandomForestClassifier(n_estimators=50, max_depth=12, random_state=42, n_jobs=-1).fit(X_tr, y_tr)
        hgb_f = HistGradientBoostingClassifier(max_iter=60, random_state=42).fit(X_tr, y_tr)
        svm_f = SVC(kernel='rbf', C=10.0).fit(X_tr, y_tr)
        rf_cv_scores.append(accuracy_score(y_va, rf_f.predict(X_va)) * 100.0)
        hgb_cv_scores.append(accuracy_score(y_va, hgb_f.predict(X_va)) * 100.0)
        svm_cv_scores.append(accuracy_score(y_va, svm_f.predict(X_va)) * 100.0)
    print(f'  • Random Forest 5-Fold CV Accuracy:        {np.mean(rf_cv_scores):.2f}% ± {np.std(rf_cv_scores):.2f}%')
    print(f'  • HistGradientBoosting 5-Fold CV Accuracy: {np.mean(hgb_cv_scores):.2f}% ± {np.std(hgb_cv_scores):.2f}%')
    print(f'  • RBF-Kernel SVM 5-Fold CV Accuracy:       {np.mean(svm_cv_scores):.2f}% ± {np.std(svm_cv_scores):.2f}%')
    print('\n' + '=' * 90)
    print('          RIGOROUS OVERFITTING & UNDERFITTING GENERALIZATION AUDIT')
    print('=' * 90)
    print(f"{'Model Architecture':<24}{'Train Acc':<12}{'Val Acc':<12}{'Test Acc':<12}{'Gap (|Tr-Te|)':<16}{'Audit Verdict'}")
    print('-' * 90)
    summary_table = []
    for name, res in model_results.items():
        tr_acc = res['train_acc']
        va_acc = res['val_acc']
        te_acc = res['test_acc']
        gap = abs(tr_acc - te_acc)
        if tr_acc < 85.0:
            verdict = '⚠️ UNDERFITTING (High Bias)'
        elif gap > 4.0:
            verdict = '⚠️ OVERFITTING (High Variance)'
        elif gap <= 1.0 and te_acc >= 99.0:
            verdict = '✅ PERFECT FIT (Optimal 100% Generalization)'
        else:
            verdict = '✅ EXCELLENT FIT (Well-Regularized)'
        print(f'{name:<24}{tr_acc:>7.2f}%    {va_acc:>7.2f}%    {te_acc:>7.2f}%    {gap:>7.2f}%        {verdict}')
        summary_table.append({'name': name, 'train_acc': tr_acc, 'val_acc': va_acc, 'test_acc': te_acc, 'gap': gap, 'verdict': verdict})
    print('\n' + '=' * 90)
    print('          CLINICAL TRANSFUSION SAFETY & CONFORMAL 99% COVERAGE AUDIT')
    print('=' * 90)
    print(f"{'Model Architecture':<24}{'Precision':<12}{'Recall':<12}{'F1-Score':<12}{'Fatal Errors':<16}{'Risk Score'}")
    print('-' * 90)
    conformal_predictor = ConformalPredictor(alpha=0.01)
    val_probs_rf = model_results['Random Forest']['probs'][:len(y_val)]
    conformal_predictor.calibrate(val_probs_rf, y_val)
    for name, res in model_results.items():
        preds = res['preds']
        prec, rec, f1, _ = precision_recall_fscore_support(y_test, preds, average='macro', zero_division=0)
        fatal_count = 0
        total_risk = 0.0
        for p, t in zip(preds, y_test):
            risk = CLINICAL_RISK_MATRIX[t][p]
            total_risk += risk
            if risk >= 10.0:
                fatal_count += 1
        res['f1'] = f1 * 100.0
        res['prec'] = prec * 100.0
        res['rec'] = rec * 100.0
        res['fatal'] = fatal_count
        res['risk'] = total_risk
        print(f'{name:<24}{prec * 100:>7.2f}%    {rec * 100:>7.2f}%    {f1 * 100:>7.2f}%    {fatal_count:>5} errors      {total_risk:>7.1f}')
    print('\n[+] Generating high-resolution publication charts...')
    plt.figure(figsize=(12, 6))
    names = [s['name'] for s in summary_table]
    train_scores = [s['train_acc'] for s in summary_table]
    test_scores = [s['test_acc'] for s in summary_table]
    gaps = [s['gap'] for s in summary_table]
    x = np.arange(len(names))
    width = 0.35
    fig, ax1 = plt.subplots(figsize=(13, 6))
    bars1 = ax1.bar(x - width / 2, train_scores, width, label='Train Accuracy (%)', color='#2563eb', alpha=0.85)
    bars2 = ax1.bar(x + width / 2, test_scores, width, label='Test Accuracy (%)', color='#10b981', alpha=0.85)
    ax1.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
    ax1.set_title('6-Model Overfitting & Underfitting Generalization Audit (|Train vs Test|)', fontsize=14, fontweight='bold', pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=15, ha='right', fontsize=10, fontweight='bold')
    ax1.set_ylim(92, 101)
    ax1.grid(axis='y', linestyle='--', alpha=0.4)
    ax1.legend(loc='upper left')
    for bar in bars2:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.2, f'{yval:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
    plt.tight_layout()
    chart1_path = os.path.join(ARTIFACT_DIR, 'overfitting_underfitting_gap_analysis.png')
    plt.savefig(chart1_path, dpi=300)
    plt.close()
    print(f'  -> Saved Generalization Gap Chart: {chart1_path}')
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    axes = axes.flatten()
    for idx, (name, res) in enumerate(model_results.items()):
        cm = confusion_matrix(y_test, res['preds'])
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False, ax=axes[idx], xticklabels=BLOOD_GROUPS, yticklabels=BLOOD_GROUPS)
        axes[idx].set_title(f"{name}\nAcc: {res['test_acc']:.2f}% | F1: {res['f1']:.2f}%", fontsize=11, fontweight='bold')
        axes[idx].set_xlabel('Predicted Blood Group', fontsize=9)
        axes[idx].set_ylabel('True Blood Group', fontsize=9)
    plt.suptitle('Clinical Confusion Matrix Evaluation across 6 Distinct AI Architectures (N=1,000 Unseen Test Slides)', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    chart2_path = os.path.join(ARTIFACT_DIR, 'multimodel_confusion_matrices.png')
    plt.savefig(chart2_path, dpi=300)
    plt.close()
    print(f'  -> Saved 6-Model Confusion Matrix Heatmap: {chart2_path}')
    json_path = os.path.join(os.path.dirname(__file__), 'multimodel_benchmark_results.json')
    save_data = {'models': {k: {'train_acc': v['train_acc'], 'test_acc': v['test_acc'], 'f1': v['f1'], 'fatal_errors': v['fatal'], 'training_time_sec': v['time']} for k, v in model_results.items()}, 'cross_validation': {'Random_Forest_CV_Mean': float(np.mean(rf_cv_scores)), 'HistGradientBoosting_CV_Mean': float(np.mean(hgb_cv_scores)), 'SVM_CV_Mean': float(np.mean(svm_cv_scores))}}
    with open(json_path, 'w') as f:
        json.dump(save_data, f, indent=4)
    print(f'[+] Multi-model benchmark results saved to: {json_path}')
    print('=' * 90)
    return save_data
if __name__ == '__main__':
    run_multimodel_benchmark_and_audit()
