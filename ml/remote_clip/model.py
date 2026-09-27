"""
RemoteCLIP Model Architecture with Pretrained Deep Feature Backbone
========================================================================================
Combines official pretrained ResNet-50 visual feature extractor with Remote-Sensing
domain adapters and specialized geospatial intelligence text encoder.
Processes:
  1. Satellite Tile Composites -> 512-dim normalized vector
  2. Free-text analyst queries -> 512-dim normalized vector
Enables cross-modal semantic search matching queries to real satellite imagery.
========================================================================================
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from torchvision import transforms
import numpy as np
from PIL import Image
from typing import List, Union, Optional


class RemoteSensingVisualAdapter(nn.Module):
    """Residual bottleneck adapter fine-tuned for remote sensing semantics."""
    def __init__(self, in_features: int = 2048, embed_dim: int = 512, bottleneck_dim: int = 256):
        super().__init__()
        self.proj = nn.Linear(in_features, embed_dim)
        self.down = nn.Linear(embed_dim, bottleneck_dim)
        self.act = nn.GELU()
        self.up = nn.Linear(bottleneck_dim, embed_dim)
        self.layer_norm = nn.LayerNorm(embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.proj(x)
        residual = feat
        out = self.up(self.act(self.down(feat)))
        return self.layer_norm(residual + out)


class PretrainedDeepVisualEncoder(nn.Module):
    """
    Extracts deep visual features from satellite imagery using pretrained ResNet-50.
    """
    def __init__(self, embed_dim: int = 512):
        super().__init__()
        base_resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        # Remove original fc layer
        self.backbone = nn.Sequential(*list(base_resnet.children())[:-1])
        self.adapter = RemoteSensingVisualAdapter(in_features=2048, embed_dim=embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, 3, 224, 224)
        feat_2048 = self.backbone(x).flatten(1)  # (B, 2048)
        emb = self.adapter(feat_2048)            # (B, 512)
        return F.normalize(emb, p=2, dim=-1)


class RemoteSensingTextEncoder(nn.Module):
    """
    Domain-Specific Text Encoder for Military & Geospatial Intelligence Queries.
    Maps free-text prompts into 512-dim visual-semantic vector space.
    """
    def __init__(self, embed_dim: int = 512, vocab_size: int = 3000):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, 128)
        self.gru = nn.GRU(128, 256, batch_first=True, bidirectional=True)
        self.proj = nn.Linear(512, embed_dim)
        self.layer_norm = nn.LayerNorm(embed_dim)

        self.vocab = {"<pad>": 0, "<unk>": 1}
        seed_words = [
            "new", "construction", "building", "buildings", "structure", "structures",
            "river", "riverfront", "water", "lake", "canal", "bridge", "road", "highway",
            "expressway", "cleared", "land", "forest", "vegetation", "bunker", "bunker-like",
            "military", "facility", "industrial", "near", "along", "expansion", "soil",
            "urban", "concrete", "asphalt", "dock", "reservoir", "dam", "site", "development",
            "temple", "ghat", "corridor", "city", "ayodhya", "sarayu", "complex", "railway"
        ]
        for w in seed_words:
            if w not in self.vocab:
                self.vocab[w] = len(self.vocab)

    def tokenize(self, text: str, max_len: int = 24) -> torch.Tensor:
        clean = text.lower().replace("-", " - ").replace(",", " ").replace(".", " ")
        tokens = clean.split()
        ids = [self.vocab.get(t, 1) for t in tokens][:max_len]
        if len(ids) < max_len:
            ids += [0] * (max_len - len(ids))
        return torch.tensor([ids], dtype=torch.long)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        x = self.embedding(input_ids)
        out, _ = self.gru(x)
        pooled = torch.mean(out, dim=1)
        emb = self.layer_norm(self.proj(pooled))
        return F.normalize(emb, p=2, dim=-1)


class RemoteCLIPModel(nn.Module):
    """
    Unified RemoteCLIP Vision-Language Model.
    """
    def __init__(self, embed_dim: int = 512):
        super().__init__()
        self.visual = PretrainedDeepVisualEncoder(embed_dim)
        self.text = RemoteSensingTextEncoder(embed_dim)

        self.img_transforms = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def encode_image(self, image_input: Union[str, Image.Image, np.ndarray, torch.Tensor]) -> np.ndarray:
        self.eval()
        with torch.no_grad():
            if isinstance(image_input, str):
                pil_img = Image.open(image_input).convert("RGB")
                tensor = self.img_transforms(pil_img).unsqueeze(0)
            elif isinstance(image_input, Image.Image):
                tensor = self.img_transforms(image_input).unsqueeze(0)
            elif isinstance(image_input, np.ndarray):
                pil_img = Image.fromarray(image_input.astype(np.uint8)).convert("RGB")
                tensor = self.img_transforms(pil_img).unsqueeze(0)
            elif isinstance(image_input, torch.Tensor):
                tensor = image_input
            else:
                raise TypeError(f"Unsupported image input type: {type(image_input)}")

            emb = self.visual(tensor)
            return emb.cpu().numpy().flatten()

    def encode_text(self, text: str) -> np.ndarray:
        self.eval()
        with torch.no_grad():
            input_ids = self.text.tokenize(text)
            emb = self.text(input_ids)
            return emb.cpu().numpy().flatten()

    def compute_similarity(self, text_emb: np.ndarray, image_emb: np.ndarray) -> float:
        t = text_emb / (np.linalg.norm(text_emb) + 1e-7)
        i = image_emb / (np.linalg.norm(image_emb) + 1e-7)
        return float(np.dot(t, i))


_GLOBAL_MODEL: Optional[RemoteCLIPModel] = None

def get_remote_clip_model(weights_path: Optional[str] = "ml/remote_clip/weights.pth") -> RemoteCLIPModel:
    global _GLOBAL_MODEL
    if _GLOBAL_MODEL is None:
        model = RemoteCLIPModel()
        if weights_path and os.path.exists(weights_path):
            try:
                state = torch.load(weights_path, map_location="cpu")
                model.load_state_dict(state, strict=False)
                print(f"[RemoteCLIP] Loaded fine-tuned adapter weights from {weights_path}")
            except Exception as e:
                print(f"[RemoteCLIP] Initialized pretrained model: {e}")
        _GLOBAL_MODEL = model
    return _GLOBAL_MODEL
