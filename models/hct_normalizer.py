import torch
import torch.nn as nn

class HematocritSelfNormalizer(nn.Module):

    def __init__(self, baseline_steps: int=15):
        super().__init__()
        self.baseline_steps = baseline_steps
        self.hct_estimator = nn.Sequential(nn.Linear(3, 8), nn.GELU(), nn.Linear(8, 3), nn.Sigmoid())

    def forward(self, raw_signals: torch.Tensor) -> torch.Tensor:
        baseline = torch.mean(raw_signals[:, :, :self.baseline_steps], dim=-1, keepdim=True)
        delta_s = raw_signals - baseline
        b_flat = baseline.squeeze(-1)
        hct_scale = 0.5 + self.hct_estimator(b_flat).unsqueeze(-1)
        normalized_trajectory = delta_s / (hct_scale + 1e-06)
        return normalized_trajectory
