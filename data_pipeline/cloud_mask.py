"""
Cloud, Shadow, Haze, and Quality Masking Module
Combines s2cloudless-style spectral probability with Sentinel-2 SCL (Scene Classification Layer).
Persists continuous probability + discrete categorical quality flags as inspectable metadata.
"""

from typing import Dict, Any, Tuple
import numpy as np
from .band_stack import BandStack, SentinelBand


# Sentinel-2 SCL Classes (ESA Standard)
SCL_NO_DATA = 0
SCL_SATURATED = 1
SCL_CAST_SHADOW = 2
SCL_CLOUD_SHADOW = 3
SCL_VEGETATION = 4
SCL_BARE_SOIL = 5
SCL_WATER = 6
SCL_UNCLASSIFIED = 7
SCL_CLOUD_MED_PROB = 8
SCL_CLOUD_HIGH_PROB = 9
SCL_THIN_CIRRUS = 10
SCL_SNOW = 11


class CloudMaskEngine:
    """
    Computes cloud probability, shadow detection, and quality masks.
    Retains all pixel flags for UI quality check inspection without premature pixel discarding.
    """

    def __init__(self, cloud_prob_threshold: float = 0.40):
        self.cloud_prob_threshold = cloud_prob_threshold

    def compute_s2cloudless_probability(self, stack: BandStack) -> np.ndarray:
        """
        Computes a continuous cloud probability map [0.0, 1.0] from raw bands.
        Utilizes spectral signatures: high visible (B02, B04), high NIR (B08),
        and low SWIR/cirrus ratios characteristic of clouds.
        """
        b02 = stack.get_reflectance_float32(SentinelBand.B02)
        b03 = stack.get_reflectance_float32(SentinelBand.B03)
        b04 = stack.get_reflectance_float32(SentinelBand.B04)
        b08 = stack.get_reflectance_float32(SentinelBand.B08)
        
        # Safe handling for SWIR if available
        try:
            b11 = stack.get_reflectance_float32(SentinelBand.B11)
        except KeyError:
            b11 = b04 * 0.8

        # Apparent brightness in visible spectrum
        vis_brightness = (b02 + b03 + b04) / 3.0

        # Whiteness index (clouds have flat, neutral visible spectrum)
        whiteness = 1.0 - (
            np.abs(b02 - vis_brightness)
            + np.abs(b03 - vis_brightness)
            + np.abs(b04 - vis_brightness)
        ) / (vis_brightness + 1e-5)
        whiteness = np.clip(whiteness, 0.0, 1.0)

        # Clouds are bright in visible and NIR, but relatively cold/absorbing in SWIR
        # NDSI-like cloud contrast: (B03 - B11) / (B03 + B11 + 1e-5)
        swir_contrast = (b03 - b11) / (b03 + b11 + 1e-5)

        # Composite cloud probability score
        raw_prob = (0.45 * np.clip(vis_brightness / 0.4, 0, 1)) + (0.35 * whiteness) + (0.20 * np.clip(swir_contrast + 0.2, 0, 1))
        cloud_prob = np.clip(raw_prob, 0.0, 1.0)
        return cloud_prob.astype(np.float32)

    def generate_quality_mask(self, stack: BandStack) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Generates binary masks and summary quality metrics.
        Returns:
            quality_mask: uint8 array (bits: 1=cloud, 2=shadow, 4=water, 8=snow, 16=nodata)
            metadata: dictionary of quality statistics
        """
        h, w = stack.height, stack.width
        cloud_prob = self.compute_s2cloudless_probability(stack)

        # Check SCL layer if available
        has_scl = SentinelBand.SCL in stack.bands_data
        if has_scl:
            scl = stack.get_band(SentinelBand.SCL).astype(np.int32)
            scl_cloud = np.isin(scl, [SCL_CLOUD_MED_PROB, SCL_CLOUD_HIGH_PROB, SCL_THIN_CIRRUS])
            scl_shadow = np.isin(scl, [SCL_CAST_SHADOW, SCL_CLOUD_SHADOW])
            scl_water = (scl == SCL_WATER)
            scl_snow = (scl == SCL_SNOW)
            scl_nodata = (scl == SCL_NO_DATA)
        else:
            scl_cloud = np.zeros((h, w), dtype=bool)
            scl_shadow = np.zeros((h, w), dtype=bool)
            scl_water = np.zeros((h, w), dtype=bool)
            scl_snow = np.zeros((h, w), dtype=bool)
            scl_nodata = np.zeros((h, w), dtype=bool)

        b08 = stack.get_reflectance_float32(SentinelBand.B08)
        b02 = stack.get_reflectance_float32(SentinelBand.B02)
        b03 = stack.get_reflectance_float32(SentinelBand.B03)

        # Combined cloud decision:
        if has_scl:
            # Respect authoritative ESA SCL ground classes (Vegetation, Bare Soil, Water)
            ground_truth_clear = np.isin(scl, [SCL_VEGETATION, SCL_BARE_SOIL, SCL_WATER])
            is_cloud = scl_cloud | ((cloud_prob >= 0.70) & (~ground_truth_clear))
            is_shadow = scl_shadow
        else:
            is_cloud = (cloud_prob >= self.cloud_prob_threshold)
            spectral_shadow = (b08 < 0.08) & (b02 < 0.08) & (~is_cloud)
            is_shadow = spectral_shadow

        # Water: NDWI > 0.05
        ndwi = (b03 - b08) / (b03 + b08 + 1e-6)
        is_water = scl_water | (ndwi > 0.15)

        total_pixels = h * w
        cloud_pct = float(np.sum(is_cloud) / total_pixels * 100.0)
        shadow_pct = float(np.sum(is_shadow) / total_pixels * 100.0)
        water_pct = float(np.sum(is_water) / total_pixels * 100.0)
        nodata_pct = float(np.sum(scl_nodata) / total_pixels * 100.0)

        # Bitmask composition
        # Bit 0: Cloud (1)
        # Bit 1: Shadow (2)
        # Bit 2: Water (4)
        # Bit 3: Snow (8)
        # Bit 4: NoData (16)
        quality_mask = np.zeros((h, w), dtype=np.uint8)
        quality_mask[is_cloud] |= 1
        quality_mask[is_shadow] |= 2
        quality_mask[is_water] |= 4
        quality_mask[scl_snow] |= 8
        quality_mask[scl_nodata] |= 16

        metadata = {
            "cloud_cover_percent": round(cloud_pct, 2),
            "shadow_percent": round(shadow_pct, 2),
            "water_percent": round(water_pct, 2),
            "nodata_percent": round(nodata_pct, 2),
            "usable_data_percent": round(100.0 - cloud_pct - shadow_pct - nodata_pct, 2),
            "mean_cloud_probability": round(float(np.mean(cloud_prob)), 3),
            "quality_flag": "ACCEPTABLE" if (cloud_pct < 20.0 and shadow_pct < 10.0) else "DEGRADED",
        }

        return quality_mask, metadata
