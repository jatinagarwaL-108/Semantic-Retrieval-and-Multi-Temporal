"""
RemoteCLIP Domain Adapter Fine-Tuning Script
Fine-tunes the RS adapter and text projection heads using contrastive InfoNCE loss
on domain-specific satellite image and caption pairs.
Covers targeted concepts:
  - 'new construction near river'
  - 'bunker-like structure'
  - 'new road and bridge network'
  - 'cleared land and deforestation'
  - 'water body and riverbank alteration'
"""

import os
import glob
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from PIL import Image
from typing import List, Tuple
from .model import RemoteCLIPModel


def get_domain_caption_dataset() -> List[Tuple[str, str]]:
    """
    Pairs existing demo composite images or synthetic patterns with domain captions.
    """
    composites = glob.glob("data/composites/*_preview.png")
    dataset = []

    # Map tiles to ground-truth semantic concepts
    for comp in composites:
        base = os.path.basename(comp)
        if "t001" in base or "t004" in base:
            dataset.append((comp, "new buildings and construction near river"))
            dataset.append((comp, "industrial facility and bunker-like structure"))
        elif "t000" in base:
            dataset.append((comp, "river corridor with water and riparian vegetation"))
        elif "t003" in base:
            dataset.append((comp, "new road bridge expressway crossing river"))
        else:
            dataset.append((comp, "cleared land and bare soil area"))
            dataset.append((comp, "agricultural field and vegetation"))

    return dataset


def train_adapter(
    epochs: int = 15,
    lr: float = 1e-3,
    save_path: str = "ml/remote_clip/weights.pth"
):
    print("[RemoteCLIP] Starting Domain Adapter Fine-Tuning...")
    model = RemoteCLIPModel()
    model.train()

    # Freeze ResNet-50 backbone, only train visual adapter and text projection heads
    for p in model.visual.backbone.parameters():
        p.requires_grad = False
    for p in model.visual.adapter.parameters():
        p.requires_grad = True
    for p in model.text.parameters():
        p.requires_grad = True

    optimizer = optim.AdamW(
        list(model.visual.adapter.parameters()) + list(model.text.parameters()),
        lr=lr,
        weight_decay=1e-4,
    )

    dataset = get_domain_caption_dataset()
    if not dataset:
        print("[RemoteCLIP] No preview tiles found in data/composites. Generating placeholder dummy pairs for training...")
        # Create a synthetic dataset
        dummy_img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        os.makedirs("data/composites", exist_ok=True)
        dummy_img.save("data/composites/dummy_preview.png")
        dataset = [
            ("data/composites/dummy_preview.png", "new buildings near river"),
            ("data/composites/dummy_preview.png", "cleared land and bunker structure"),
            ("data/composites/dummy_preview.png", "new road bridge across water"),
        ]

    for epoch in range(1, epochs + 1):
        total_loss = 0.0
        for img_path, caption in dataset:
            optimizer.zero_grad()
            pil_img = Image.open(img_path).convert("RGB")
            img_tensor = model.img_transforms(pil_img).unsqueeze(0)
            text_ids = model.text.tokenize(caption)

            v_emb = model.visual(img_tensor)  # (1, 512)
            t_emb = model.text(text_ids)      # (1, 512)

            # Cosine similarity loss maximization (InfoNCE positive pair)
            sim = torch.sum(v_emb * t_emb)
            loss = 1.0 - sim

            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / max(1, len(dataset))
        if epoch % 5 == 0 or epoch == epochs:
            print(f"  Epoch [{epoch:02d}/{epochs:02d}] - RS Adapter Loss: {avg_loss:.4f}")

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(model.state_dict(), save_path)
    print(f"[RemoteCLIP] Saved fine-tuned checkpoint to: {save_path}")


if __name__ == "__main__":
    train_adapter()
