"""
Multi-Spectral Band Math & Indices Engine
Computes NDVI, NDBI, NDWI, and raw multi-temporal Band-Difference maps (post - pre).
This multi-band differential tensor is the authoritative change detection source prior to any visualization.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
from .band_stack import BandStack, SentinelBand


class SpectralIndices:
    """
    Computes standard physical remote sensing spectral indices from raw surface reflectance.
    """

    @staticmethod
    def compute_ndvi(stack: BandStack) -> np.ndarray:
        """
        Normalized Difference Vegetation Index (NDVI)
        NDVI = (NIR - Red) / (NIR + Red) = (B08 - B04) / (B08 + B04)
        Range: [-1.0, 1.0] (Values > 0.4 indicate dense healthy vegetation)
        """
        b08 = stack.get_reflectance_float32(SentinelBand.B08)
        b04 = stack.get_reflectance_float32(SentinelBand.B04)
        denom = b08 + b04 + 1e-6
        ndvi = (b08 - b04) / denom
        return np.clip(ndvi, -1.0, 1.0).astype(np.float32)

    @staticmethod
    def compute_ndbi(stack: BandStack) -> np.ndarray:
        """
        Normalized Difference Built-up Index (NDBI)
        NDBI = (SWIR1 - NIR) / (SWIR1 + NIR) = (B11 - B08) / (B11 + B08)
        High positive values indicate urban, concrete, asphalt, or bare construction sites.
        """
        try:
            b11 = stack.get_reflectance_float32(SentinelBand.B11)
        except KeyError:
            # Fallback estimation if SWIR not included in stack
            b11 = stack.get_reflectance_float32(SentinelBand.B04) * 1.2
        b08 = stack.get_reflectance_float32(SentinelBand.B08)
        denom = b11 + b08 + 1e-6
        ndbi = (b11 - b08) / denom
        return np.clip(ndbi, -1.0, 1.0).astype(np.float32)

    @staticmethod
    def compute_ndwi(stack: BandStack) -> np.ndarray:
        """
        Normalized Difference Water Index (NDWI - McFeeters)
        NDWI = (Green - NIR) / (Green + NIR) = (B03 - B08) / (B03 + B08)
        Values > 0 represent open water bodies (rivers, lakes, reservoirs).
        """
        b03 = stack.get_reflectance_float32(SentinelBand.B03)
        b08 = stack.get_reflectance_float32(SentinelBand.B08)
        denom = b03 + b08 + 1e-6
        ndwi = (b03 - b08) / denom
        return np.clip(ndwi, -1.0, 1.0).astype(np.float32)

    @classmethod
    def compute_all(cls, stack: BandStack) -> Dict[str, np.ndarray]:
        """Computes all indices and returns dictionary."""
        return {
            "NDVI": cls.compute_ndvi(stack),
            "NDBI": cls.compute_ndbi(stack),
            "NDWI": cls.compute_ndwi(stack),
        }


def compute_band_difference(
    pre_stack: BandStack, post_stack: BandStack
) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    """
    Computes authoritative multi-band differences: Delta_B = Post_B - Pre_B
    This is what change is evaluated FROM, prior to any RGB conversion.

    Returns:
        diff_maps: Dict containing per-band diff arrays and delta-index arrays
        diff_stats: Statistical summary of spectral changes
    """
    common_bands = [
        b for b in pre_stack.bands_data.keys()
        if b in post_stack.bands_data and b != SentinelBand.SCL
    ]

    diff_maps: Dict[str, np.ndarray] = {}
    stats: Dict[str, Any] = {}

    for b in common_bands:
        pre_val = pre_stack.get_reflectance_float32(b)
        post_val = post_stack.get_reflectance_float32(b)
        delta = post_val - pre_val
        diff_maps[b.value] = delta.astype(np.float32)

        stats[b.value] = {
            "mean_delta": round(float(np.mean(delta)), 5),
            "std_delta": round(float(np.std(delta)), 5),
            "max_abs_delta": round(float(np.max(np.abs(delta))), 5),
            "p95_abs_delta": round(float(np.percentile(np.abs(delta), 95)), 5),
        }

    # Delta Indices
    pre_indices = SpectralIndices.compute_all(pre_stack)
    post_indices = SpectralIndices.compute_all(post_stack)

    delta_ndvi = post_indices["NDVI"] - pre_indices["NDVI"]
    delta_ndbi = post_indices["NDBI"] - pre_indices["NDBI"]
    delta_ndwi = post_indices["NDWI"] - pre_indices["NDWI"]

    diff_maps["delta_NDVI"] = delta_ndvi
    diff_maps["delta_NDBI"] = delta_ndbi
    diff_maps["delta_NDWI"] = delta_ndwi

    stats["delta_NDVI"] = {
        "mean": round(float(np.mean(delta_ndvi)), 4),
        "vegetation_loss_area_ratio": round(float(np.sum(delta_ndvi < -0.2) / delta_ndvi.size), 4),
    }
    stats["delta_NDBI"] = {
        "mean": round(float(np.mean(delta_ndbi)), 4),
        "urban_gain_area_ratio": round(float(np.sum(delta_ndbi > 0.2) / delta_ndbi.size), 4),
    }
    stats["delta_NDWI"] = {
        "mean": round(float(np.mean(delta_ndwi)), 4),
        "water_change_area_ratio": round(float(np.sum(np.abs(delta_ndwi) > 0.25) / delta_ndwi.size), 4),
    }

    return diff_maps, stats
