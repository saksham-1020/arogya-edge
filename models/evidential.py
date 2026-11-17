import torch
import torch.nn as nn
import torch.nn.functional as F

class EvidentialDirichletHead(nn.Module):

    def __init__(self, in_features: int, num_classes: int=8):
        super().__init__()
        self.num_classes = num_classes
        self.fc = nn.Sequential(nn.Linear(in_features, 64), nn.SiLU(), nn.Linear(64, num_classes))

    def forward(self, x: torch.Tensor):
        logits = self.fc(x)
        evidence = F.softplus(logits)
        alpha = evidence + 1.0
        s = torch.sum(alpha, dim=-1, keepdim=True)
        prob = alpha / s
        uncertainty = self.num_classes / s
        belief = evidence / s
        return {'evidence': evidence, 'alpha': alpha, 'prob': prob, 'uncertainty': uncertainty.squeeze(-1), 'belief': belief}

    @staticmethod
    def evidential_loss(alpha: torch.Tensor, target_one_hot: torch.Tensor, epoch: int=1, kl_weight: float=0.05) -> torch.Tensor:
        s = torch.sum(alpha, dim=-1, keepdim=True)
        prob = alpha / s
        err = torch.sum((target_one_hot - prob) ** 2, dim=-1, keepdim=True)
        var = torch.sum(alpha * (s - alpha) / (s * s * (s + 1.0)), dim=-1, keepdim=True)
        loss_mse = torch.mean(err + var)
        alpha_tilde = target_one_hot + (1.0 - target_one_hot) * alpha
        s_tilde = torch.sum(alpha_tilde, dim=-1, keepdim=True)
        kl = torch.lgamma(s_tilde) - torch.sum(torch.lgamma(alpha_tilde), dim=-1, keepdim=True) - torch.lgamma(torch.tensor(alpha.shape[-1], dtype=torch.float32, device=alpha.device)) + torch.sum((alpha_tilde - 1.0) * (torch.digamma(alpha_tilde) - torch.digamma(s_tilde)), dim=-1, keepdim=True)
        annealing = min(1.0, epoch / 10.0) * kl_weight
        loss_kl = torch.mean(annealing * kl)
        return loss_mse + loss_kl
