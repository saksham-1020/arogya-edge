import torch
import torch.nn as nn

class ArrheniusThermodynamicLayer(nn.Module):

    def __init__(self, e_a: float=42000.0, t_ref_celsius: float=25.0):
        super().__init__()
        self.r_gas = 8.314
        self.register_buffer('e_a', torch.tensor(e_a, dtype=torch.float32))
        self.register_buffer('t_ref', torch.tensor(t_ref_celsius + 273.15, dtype=torch.float32))
        self.alpha = nn.Parameter(torch.tensor(1.0, dtype=torch.float32))
        self.bias = nn.Parameter(torch.tensor(0.0, dtype=torch.float32))

    def compute_rate_ratio(self, temp_celsius: torch.Tensor) -> torch.Tensor:
        temp_kelvin = temp_celsius + 273.15
        delta_inv_t = 1.0 / temp_kelvin - 1.0 / self.t_ref
        gamma = torch.exp(-(self.e_a / self.r_gas) * delta_inv_t)
        return torch.clamp(gamma * self.alpha + self.bias, min=0.2, max=5.0)

    def forward(self, features: torch.Tensor, temp_celsius: torch.Tensor) -> torch.Tensor:
        if temp_celsius.ndim == 1:
            temp_celsius = temp_celsius.unsqueeze(1)
        gamma = self.compute_rate_ratio(temp_celsius).unsqueeze(-1)
        return features * gamma
