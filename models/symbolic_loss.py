import torch
import torch.nn as nn
import torch.nn.functional as F
ANTIGEN_MATRIX = torch.tensor([[1.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 1.0], [0.0, 1.0, 0.0], [1.0, 1.0, 1.0], [1.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, 0.0]], dtype=torch.float32)

class LandsteinerAxiomLoss(nn.Module):

    def __init__(self, weight: float=0.3):
        super().__init__()
        self.weight = weight
        self.register_buffer('antigen_matrix', ANTIGEN_MATRIX)

    def forward(self, class_probs: torch.Tensor, antigen_probs: torch.Tensor) -> torch.Tensor:
        a_p = antigen_probs.unsqueeze(1)
        target_matrix = self.antigen_matrix.unsqueeze(0)
        match_prob = a_p * target_matrix + (1.0 - a_p) * (1.0 - target_matrix)
        theoretical_class_prob = torch.prod(match_prob, dim=-1)
        consistency_loss = F.mse_loss(class_probs, theoretical_class_prob)
        return self.weight * consistency_loss
