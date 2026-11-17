import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from simulator import generate_batch, BLOOD_GROUPS
from models import TCECOModel, LandsteinerAxiomLoss
from models.evidential import EvidentialDirichletHead

def train_tceco(epochs: int=15, batches_per_epoch: int=30, batch_size: int=64, lr: float=0.002):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'[+] Initializing T-CECO Training on Device: {device}')
    model = TCECOModel(time_steps=200, out_classes=8).to(device)
    total_params = sum((p.numel() for p in model.parameters() if p.requires_grad))
    print(f'[+] Total Model Parameters: {total_params:,} (~{round(total_params * 4 / 1024, 2)} KB FP32 / ~{round(total_params / 1024, 2)} KB Int8)')
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=0.0001)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    axiom_loss_fn = LandsteinerAxiomLoss(weight=0.2).to(device)
    bce_loss_fn = nn.BCELoss()
    ce_loss_fn = nn.NLLLoss()
    best_acc = 0.0
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        correct = 0
        total_samples = 0
        for b in range(batches_per_epoch):
            batch = generate_batch(batch_size=batch_size, time_steps=200)
            signals = torch.tensor(batch['signals'], dtype=torch.float32, device=device)
            temps = torch.tensor(batch['temperatures'], dtype=torch.float32, device=device)
            targets = torch.tensor(batch['class_indices'], dtype=torch.int64, device=device)
            antigens = torch.tensor(batch['antigens'], dtype=torch.float32, device=device)
            target_one_hot = torch.zeros(batch_size, 8, device=device)
            target_one_hot.scatter_(1, targets.unsqueeze(1), 1.0)
            optimizer.zero_grad()
            out = model(signals, temps)
            l_evid = EvidentialDirichletHead.evidential_loss(out['alpha'], target_one_hot, epoch=epoch, kl_weight=0.02)
            l_nll = ce_loss_fn(torch.log(out['prob'] + 1e-07), targets)
            l_antigen = bce_loss_fn(out['antigen_probs'], antigens)
            l_axiom = axiom_loss_fn(out['prob'], out['antigen_probs'])
            loss = l_evid + 0.8 * l_nll + 1.2 * l_antigen + l_axiom
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            preds = torch.argmax(out['prob'], dim=-1)
            correct += (preds == targets).sum().item()
            total_samples += batch_size
        scheduler.step()
        train_acc = correct / total_samples * 100.0
        avg_loss = total_loss / batches_per_epoch
        model.eval()
        with torch.no_grad():
            test_batch = generate_batch(batch_size=128, time_steps=200)
            t_sig = torch.tensor(test_batch['signals'], dtype=torch.float32, device=device)
            t_temp = torch.tensor(test_batch['temperatures'], dtype=torch.float32, device=device)
            t_targets = torch.tensor(test_batch['class_indices'], dtype=torch.int64, device=device)
            t_out = model(t_sig, t_temp)
            t_preds = torch.argmax(t_out['prob'], dim=-1)
            test_acc = (t_preds == t_targets).sum().item() / 128 * 100.0
            mean_uncertainty = t_out['uncertainty'].mean().item()
        print(f'Epoch [{epoch:02d}/{epochs:02d}] Loss: {avg_loss:.4f} | Train Acc: {train_acc:.2f}% | Test Acc: {test_acc:.2f}% | Mean Uncertainty: {mean_uncertainty:.4f}')
        if test_acc >= best_acc:
            best_acc = test_acc
            save_path = os.path.join(os.path.dirname(__file__), 'tceco_checkpoint.pt')
            torch.save(model.state_dict(), save_path)
    print(f'\n[+] Training Complete! Best Test Accuracy: {best_acc:.2f}%')
    print(f'[+] Model checkpoint saved to: tceco_checkpoint.pt')
if __name__ == '__main__':
    train_tceco(epochs=12, batches_per_epoch=30, batch_size=64)
