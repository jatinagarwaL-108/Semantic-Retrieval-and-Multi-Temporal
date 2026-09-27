"""
Radiometric Normalization Module
Computes per-scene, per-band radiometric normalization parameters (percentiles, min-max).
Stored in metadata so the transformation is strictly reversible and inspectable.
"""

from typing import Dict, Any, Optional
import numpy as np
from .band_stack import BandStack, SentinelBand


class RadiometricNormalizer:
    """
    Computes and applies per-scene radiometric normalization parameters.
    Saves normalization parameters in metadata so raw surface reflectance is always recoverable.
    """

    def __init__(self, lower_percentile: float = 2.0, upper_percentile: float = 98.0):
        self.lower_percentile = lower_percentile
        self.upper_percentile = upper_percentile

    def compute_normalization_parameters(
        self, stack: BandStack, valid_mask: Optional[np.ndarray] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Computes per-band stretch statistics over valid pixels.
        Returns dict keyed by band name with: p_low, p_high, min, max, mean, std.
        """
        params = {}
        for band_enum in stack.bands_data.keys():
            if band_enum == SentinelBand.SCL:
                continue

            arr = stack.get_reflectance_float32(band_enum)
            if valid_mask is not None:
                pixels = arr[valid_mask]
            else:
                pixels = arr[arr > 0]

            if len(pixels) == 0:
                pixels = arr.flatten()

            p_low = float(np.percentile(pixels, self.lower_percentile))
            p_high = float(np.percentile(pixels, self.upper_percentile))
            min_val = float(np.min(pixels))
            max_val = float(np.max(pixels))
            mean_val = float(np.mean(pixels))
            std_val = float(np.std(pixels))

            # Guard against zero range
            if p_high <= p_low:
                p_high = p_low + 1e-4

            params[band_enum.value] = {
                "lower_percentile": self.lower_percentile,
                "upper_percentile": self.upper_percentile,
                "p_low": round(p_low, 5),
                "p_high": round(p_high, 5),
                "min": round(min_val, 5),
                "max": round(max_val, 5),
                "mean": round(mean_val, 5),
                "std": round(std_val, 5),
            }
        return params

    def apply_normalization(
        self, arr: np.ndarray, band_name: str, params: Dict[str, Dict[str, float]]
    ) -> np.ndarray:
        """Normalizes an array to [0.0, 1.0] using stored parameters."""
        if band_name not in params:
            return np.clip(arr, 0.0, 1.0)
        p = params[band_name]
        stretched = (arr - p["p_low"]) / (p["p_high"] - p["p_low"])
        return np.clip(stretched, 0.0, 1.0).astype(np.float32)

    def denormalize(
        self, normalized_arr: np.ndarray, band_name: str, params: Dict[str, Dict[str, float]]
    ) -> np.ndarray:
        """Reverses normalization to recover physical BOA surface reflectance."""
        if band_name not in params:
            return normalized_arr
        p = params[band_name]
        return (normalized_arr * (p["p_high"] - p["p_low"]) + p["p_low"]).astype(np.float32)
