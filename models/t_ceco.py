import torch
import torch.nn as nn
from .arrhenius import ArrheniusThermodynamicLayer
from .hct_normalizer import HematocritSelfNormalizer
from .wavelet_kinetic import MicroAgglutinationKineticOperator
from .evidential import EvidentialDirichletHead

class TCECOModel(nn.Module):

    def __init__(self, time_steps: int=200, out_classes: int=8):
        super().__init__()
        self.time_steps = time_steps
        self.out_classes = out_classes
        self.hct_normalizer = HematocritSelfNormalizer(baseline_steps=15)
        self.kinetic_op = MicroAgglutinationKineticOperator(in_channels=3, out_dim=32)
        self.arrhenius_layer = ArrheniusThermodynamicLayer(e_a=42000.0, t_ref_celsius=25.0)
        self.temporal_compressor = nn.Sequential(nn.AdaptiveAvgPool1d(1), nn.Flatten())
        self.backbone = nn.Sequential(nn.Linear(38, 64), nn.BatchNorm1d(64), nn.SiLU(), nn.Linear(64, 48), nn.SiLU())
        self.antigen_head = nn.Sequential(nn.Linear(48, 16), nn.SiLU(), nn.Linear(16, 3), nn.Sigmoid())
        self.evidential_head = EvidentialDirichletHead(in_features=48, num_classes=out_classes)

    def forward(self, raw_signals: torch.Tensor, temp_celsius: torch.Tensor):
        norm_signals = self.hct_normalizer(raw_signals)
        kinetic_features = self.kinetic_op(norm_signals)
        compensated_features = self.arrhenius_layer(kinetic_features, temp_celsius)
        pooled = self.temporal_compressor(compensated_features)
        final_drop = norm_signals[:, :, -1] - norm_signals[:, :, 0]
        min_level = torch.min(norm_signals, dim=-1)[0]
        kinetic_summary = torch.cat([final_drop, min_level], dim=-1)
        fused_latent = torch.cat([pooled, kinetic_summary], dim=-1)
        latent = self.backbone(fused_latent)
        antigen_probs = self.antigen_head(latent)
        evidential_out = self.evidential_head(latent)
        return {'evidence': evidential_out['evidence'], 'alpha': evidential_out['alpha'], 'prob': evidential_out['prob'], 'uncertainty': evidential_out['uncertainty'], 'belief': evidential_out['belief'], 'antigen_probs': antigen_probs, 'latent': latent, 'normalized_signals': norm_signals}
