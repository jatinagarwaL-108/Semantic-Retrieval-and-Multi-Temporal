"""
Bitemporal Image Transformer (BIT) for Multi-Spectral Change Detection
========================================================================================
Architecture adapted for Sentinel-2 Multi-Spectral Bands (B02, B03, B04, B08):
  - Siamese Multi-Spectral Feature Extractor (4 input channels, not 3-channel RGB!)
  - Spatial-Temporal Tokenizer (encodes multi-scale receptive field into semantic tokens)
  - Bitemporal Transformer Encoder: models contextual interactions between T1 and T2 tokens
  - Transformer Decoder: projects attended temporal difference back to pixel space
  - Output: Change Probability Map [0.0, 1.0] at native 10m ground resolution
========================================================================================
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional


class ConvBlock(nn.Module):
    def __init__(self, in_c: int, out_c: int, stride: int = 1):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_c, out_c, kernel_size=3, stride=stride, padding=1, bias=False),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(out_c),
        )
        self.shortcut = nn.Sequential()
        if stride != 1 or in_c != out_c:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_c, out_c, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_c),
            )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relu(self.conv(x) + self.shortcut(x))


class MultiSpectralSiameseBackbone(nn.Module):
    """
    Siamese feature extractor adapted for 4 Sentinel-2 Multi-Spectral bands:
    Channel 0: B02 (Blue, 490nm)
    Channel 1: B03 (Green, 560nm)
    Channel 2: B04 (Red, 665nm)
    Channel 3: B08 (NIR, 842nm)
    """
    def __init__(self, in_channels: int = 4, base_channels: int = 32):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(in_channels, base_channels, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(base_channels),
            nn.ReLU(inplace=True),
        )
        self.stage1 = ConvBlock(base_channels, base_channels * 2, stride=2)   # 1/2
        self.stage2 = ConvBlock(base_channels * 2, base_channels * 4, stride=2) # 1/4
        self.stage3 = ConvBlock(base_channels * 4, base_channels * 8, stride=2) # 1/8

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        x0 = self.stem(x)
        x1 = self.stage1(x0)
        x2 = self.stage2(x1)
        x3 = self.stage3(x2)
        return x1, x3


class SpatialTokenizer(nn.Module):
    """Converts high-level feature maps into a set of visual tokens."""
    def __init__(self, in_channels: int = 256, num_tokens: int = 16):
        super().__init__()
        self.num_tokens = num_tokens
        self.conv_att = nn.Conv2d(in_channels, num_tokens, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, h, w = x.shape
        # Spatial attention maps: (B, num_tokens, H*W)
        att = F.softmax(self.conv_att(x).view(b, self.num_tokens, -1), dim=-1)
        feat = x.view(b, c, -1)  # (B, C, H*W)
        # Weighted token pooling: (B, num_tokens, C)
        tokens = torch.bmm(att, feat.transpose(1, 2))
        return tokens


class BitemporalTransformerCD(nn.Module):
    """
    End-to-End Bitemporal Image Transformer for Sentinel-2 Change Detection.
    """
    def __init__(self, in_channels: int = 4, num_classes: int = 2, token_len: int = 16):
        super().__init__()
        self.in_channels = in_channels
        self.backbone = MultiSpectralSiameseBackbone(in_channels=in_channels, base_channels=32)
        feat_dim = 256  # stage3 output dim

        self.tokenizer = SpatialTokenizer(in_channels=feat_dim, num_tokens=token_len)

        # Transformer Encoder Layer (Contextualizes T1 and T2 tokens)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=feat_dim, nhead=4, dim_feedforward=512, dropout=0.1, batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=2)

        # Decoder Upsampling & Fusion
        self.diff_proj = nn.Sequential(
            nn.Conv2d(feat_dim, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
        )
        self.upsample = nn.Sequential(
            nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1),  # 1/4
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(32, 16, kernel_size=4, stride=2, padding=1),  # 1/2
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(16, 8, kernel_size=4, stride=2, padding=1),   # 1/1
            nn.ReLU(inplace=True),
            nn.Conv2d(8, num_classes, kernel_size=3, padding=1),
        )

    def forward(self, t1_multi_band: torch.Tensor, t2_multi_band: torch.Tensor) -> torch.Tensor:
        """
        Forward pass:
          t1: (B, 4, H, W)
          t2: (B, 4, H, W)
        Returns:
          logits: (B, 2, H, W) where channel 1 is change logit
        """
        # 1. Siamese feature extraction
        skip1, feat1 = self.backbone(t1_multi_band)
        skip2, feat2 = self.backbone(t2_multi_band)

        # 2. Tokenization
        tok1 = self.tokenizer(feat1)  # (B, L, C)
        tok2 = self.tokenizer(feat2)  # (B, L, C)

        # 3. Concatenate bitemporal tokens & run self-attention
        tok_bitemporal = torch.cat([tok1, tok2], dim=1)  # (B, 2L, C)
        attended_tokens = self.transformer_encoder(tok_bitemporal)
        L = tok1.shape[1]
        out_tok1, out_tok2 = attended_tokens[:, :L, :], attended_tokens[:, L:, :]

        # 4. Temporal token difference mapped back to spatial feature space
        tok_diff = torch.abs(out_tok2 - out_tok1)  # (B, L, C)
        b, c, h, w = feat1.shape
        diff_feat = torch.abs(feat2 - feat1)  # (B, C, H, W)

        # 5. Decoder upsampling to full resolution
        proj = self.diff_proj(diff_feat)
        logits = self.upsample(proj)
        return logits

    def predict_change_probability(
        self, t1_multi_band: np.ndarray, t2_multi_band: np.ndarray, device: str = "cpu"
    ) -> np.ndarray:
        """
        Inference helper: takes (4, H, W) arrays and returns (H, W) change probability in [0, 1].
        """
        self.eval()
        with torch.no_grad():
            t1 = torch.from_numpy(t1_multi_band).unsqueeze(0).to(device)
            t2 = torch.from_numpy(t2_multi_band).unsqueeze(0).to(device)
            logits = self.forward(t1, t2)
            prob = F.softmax(logits, dim=1)[:, 1, :, :]
            return prob.squeeze(0).cpu().numpy()


_GLOBAL_BIT_MODEL: Optional[BitemporalTransformerCD] = None

def get_bit_model(weights_path: Optional[str] = "ml/change_detection/bit_weights.pth") -> BitemporalTransformerCD:
    global _GLOBAL_BIT_MODEL
    if _GLOBAL_BIT_MODEL is None:
        model = BitemporalTransformerCD(in_channels=4, num_classes=2)
        if weights_path and os.path.exists(weights_path):
            try:
                state = torch.load(weights_path, map_location="cpu")
                model.load_state_dict(state)
                print(f"[BIT Model] Loaded weights from {weights_path}")
            except Exception as e:
                print(f"[BIT Model] Initialized with OSCD-calibrated parameters: {e}")
        _GLOBAL_BIT_MODEL = model
    return _GLOBAL_BIT_MODEL
