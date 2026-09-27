"""
Display & Embedding Composite Generator
========================================================================================
CRITICAL ARCHITECTURAL DISTINCTION:
This module produces derived, non-authoritative RGB / false-color PNG composites.
It is strictly invoked AFTER raw multi-band processing, tiling, cloud masking, and
band math have completed.
These images are ONLY used for:
  1. Map visualization in the client web UI
  2. Visual input feeding into RemoteCLIP (which expects 3-channel RGB image tensor)
This composite is NEVER used as the source for change detection or radiometric analysis!
========================================================================================
"""

from typing import Optional, Tuple
import os
import numpy as np
from PIL import Image
from .band_stack import BandStack, SentinelBand


def create_display_composite(
    stack: BandStack,
    composite_type: str = "true_color",
    output_png_path: Optional[str] = None,
    percentile_stretch: Tuple[float, float] = (2.0, 98.0),
) -> Tuple[np.ndarray, Optional[str]]:
    """
    Renders an 8-bit 3-channel preview composite from raw multi-band data.

    composite_type options:
      - 'true_color': B04 (Red), B03 (Green), B02 (Blue)
      - 'false_color_cir': B08 (NIR), B04 (Red), B03 (Green) [Vegetation analysis]
      - 'urban_swir': B11 (SWIR), B08 (NIR), B04 (Red) [Built-up contrast]

    Tagged in metadata: 'display/embedding-input composite, derived, not authoritative'
    """
    if composite_type == "false_color_cir":
        c1 = stack.get_reflectance_float32(SentinelBand.B08)
        c2 = stack.get_reflectance_float32(SentinelBand.B04)
        c3 = stack.get_reflectance_float32(SentinelBand.B03)
    elif composite_type == "urban_swir":
        try:
            c1 = stack.get_reflectance_float32(SentinelBand.B11)
        except KeyError:
            c1 = stack.get_reflectance_float32(SentinelBand.B08)
        c2 = stack.get_reflectance_float32(SentinelBand.B08)
        c3 = stack.get_reflectance_float32(SentinelBand.B04)
    else:  # 'true_color'
        c1 = stack.get_reflectance_float32(SentinelBand.B04)  # Red
        c2 = stack.get_reflectance_float32(SentinelBand.B03)  # Green
        c3 = stack.get_reflectance_float32(SentinelBand.B02)  # Blue

    # Perform contrast stretch per channel for display clarity
    channels = []
    p_low, p_high = percentile_stretch
    for channel in [c1, c2, c3]:
        valid = channel[channel > 0]
        if len(valid) == 0:
            valid = channel.flatten()
        low = np.percentile(valid, p_low)
        high = np.percentile(valid, p_high)
        if high <= low:
            high = low + 1e-4
        stretched = np.clip((channel - low) / (high - low), 0.0, 1.0)
        # Apply standard 2.2 gamma display correction
        gamma_corrected = np.power(stretched, 1.0 / 2.2)
        uint8_chan = (gamma_corrected * 255.0).astype(np.uint8)
        channels.append(uint8_chan)

    rgb_arr = np.stack(channels, axis=-1)  # (H, W, 3)
    img = Image.fromarray(rgb_arr, mode="RGB")

    # Add non-authoritative provenance tag
    img.info["PROVENANCE"] = "display/embedding-input composite, derived, not authoritative"
    img.info["SCENE_ID"] = stack.scene_id
    img.info["COMPOSITE_TYPE"] = composite_type

    if output_png_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_png_path)), exist_ok=True)
        img.save(output_png_path, format="PNG")

    return rgb_arr, output_png_path
