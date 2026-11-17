import torch
import torch.nn as nn
import torch.nn.functional as F

class MicroAgglutinationKineticOperator(nn.Module):

    def __init__(self, in_channels: int=3, out_dim: int=32):
        super().__init__()
        self.conv_micro = nn.Conv1d(in_channels, 18, kernel_size=5, padding=2, groups=in_channels)
        self.conv_med = nn.Conv1d(in_channels, 18, kernel_size=15, padding=7, groups=in_channels)
        self.conv_macro = nn.Conv1d(in_channels, 18, kernel_size=31, padding=15, groups=in_channels)
        diff_k = torch.tensor([-1.0, 0.0, 1.0], dtype=torch.float32).view(1, 1, 3)
        self.register_buffer('diff_kernel', diff_k.repeat(in_channels, 1, 1))
        self.mixer = nn.Sequential(nn.Conv1d(57, out_dim, kernel_size=1), nn.BatchNorm1d(out_dim), nn.SiLU())

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        f_micro = self.conv_micro(x)
        f_med = self.conv_med(x)
        f_macro = self.conv_macro(x)
        f_diff = F.conv1d(x, self.diff_kernel, padding=1, groups=x.shape[1])
        multi_scale = torch.cat([f_micro, f_med, f_macro, f_diff], dim=1)
        return self.mixer(multi_scale)
