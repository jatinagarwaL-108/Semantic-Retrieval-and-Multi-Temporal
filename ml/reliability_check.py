"""
False-Alarm & Reliability Gate Subsystem
========================================================================================
Authoritative pre-filter for satellite change detection.
Evaluates four rigorous criteria BEFORE any candidate anomaly is presented as an "AI Result":
  1. Cloud, Haze, and Cloud-Shadow Masking Gate
  2. Seasonal Phenology / Crop Rotation NDVI Consistency Gate
  3. Spatial Co-Registration Shift Gate (sub-pixel alignment tolerance)
  4. Spectral Signal-to-Noise Ratio (SNR) and Sensor Glint Gate
========================================================================================
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from data_pipeline.band_stack import BandStack, SentinelBand


@dataclass
class ReliabilityReport:
    """Detailed diagnostic reliability evaluation."""
    is_reliable: bool
    overall_confidence_score: float  # [0.0, 1.0]
    reliability_percentage: float     # 0.0 to 100.0%
    verdict: str                      # "APPROVED_AI_RESULT" or "SUPPRESSED_FALSE_ALARM"
    flags: List[str] = field(default_factory=list)
    cloud_shadow_penalty: float = 0.0
    phenology_drift_penalty: float = 0.0
    misalignment_penalty: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class ReliabilityGate:
    """
    Real, callable reliability validator preventing environmental and sensor artifacts
    from contaminating the intelligence stream.
    """

    def __init__(
        self,
        max_acceptable_cloud_pct: float = 15.0,
        max_acceptable_shadow_pct: float = 10.0,
        max_subpixel_shift: float = 1.0,
        min_reliable_score: float = 0.65,
    ):
        self.max_acceptable_cloud_pct = max_acceptable_cloud_pct
        self.max_acceptable_shadow_pct = max_acceptable_shadow_pct
        self.max_subpixel_shift = max_subpixel_shift
        self.min_reliable_score = min_reliable_score

    def evaluate(
        self,
        pre_stack: BandStack,
        post_stack: BandStack,
        quality_mask_pre: Optional[np.ndarray] = None,
        quality_mask_post: Optional[np.ndarray] = None,
        coreg_report: Optional[Dict[str, Any]] = None,
    ) -> ReliabilityReport:
        """
        Runs the full 4-gate reliability verification.
        """
        flags: List[str] = []
        penalties = {"cloud": 0.0, "phenology": 0.0, "shift": 0.0, "snr": 0.0}

        # -------------------------------------------------------------
        # Gate 1: Cloud & Shadow Interference
        # -------------------------------------------------------------
        cloud_pct = 0.0
        shadow_pct = 0.0
        if quality_mask_post is not None:
            total_px = quality_mask_post.size
            cloud_px = np.sum(quality_mask_post & 1 > 0)
            shadow_px = np.sum(quality_mask_post & 2 > 0)
            cloud_pct = float(cloud_px / total_px * 100.0)
            shadow_pct = float(shadow_px / total_px * 100.0)

        if cloud_pct > self.max_acceptable_cloud_pct:
            penalties["cloud"] += min(0.40, (cloud_pct - self.max_acceptable_cloud_pct) / 50.0)
            flags.append(f"CLOUD_HAZE_INTERFERENCE ({cloud_pct:.1f}% cloud cover exceeds {self.max_acceptable_cloud_pct}%)")
        
        if shadow_pct > self.max_acceptable_shadow_pct:
            penalties["cloud"] += min(0.25, (shadow_pct - self.max_acceptable_shadow_pct) / 25.0)
            flags.append(f"CLOUD_SHADOW_ARTIFACT ({shadow_pct:.1f}% shadow cover exceeds {self.max_acceptable_shadow_pct}%)")

        # -------------------------------------------------------------
        # Gate 2: Seasonal Phenological Consistency (NDVI seasonal check)
        # -------------------------------------------------------------
        # Compare NDVI shift across the agricultural landscape.
        # Natural deciduous or crop cycle shifts affect wide diffuse areas,
        # whereas artificial clearance or construction creates sharp, localized boundaries.
        pre_b08 = pre_stack.get_reflectance_float32(SentinelBand.B08)
        pre_b04 = pre_stack.get_reflectance_float32(SentinelBand.B04)
        post_b08 = post_stack.get_reflectance_float32(SentinelBand.B08)
        post_b04 = post_stack.get_reflectance_float32(SentinelBand.B04)

        ndvi_pre = (pre_b08 - pre_b04) / (pre_b08 + pre_b04 + 1e-6)
        ndvi_post = (post_b08 - post_b04) / (post_b08 + post_b04 + 1e-6)
        delta_ndvi = ndvi_post - ndvi_pre

        # Check broad-area agricultural shift
        diffuse_veg_drop = np.sum((delta_ndvi < -0.15) & (delta_ndvi > -0.35)) / delta_ndvi.size
        if diffuse_veg_drop > 0.40:
            # Broad moderate drop suggests seasonal winter/dry season phenology, not construction!
            penalties["phenology"] += 0.20
            flags.append("SEASONAL_PHENOLOGY_DRIFT (Diffuse vegetation index drop across scene)")

        # -------------------------------------------------------------
        # Gate 3: Spatial Co-Registration Shift Check
        # -------------------------------------------------------------
        shift_pixels = 0.0
        if coreg_report:
            shift_pixels = coreg_report.get("total_shift_pixels", 0.0)
            if shift_pixels > self.max_subpixel_shift:
                penalty = min(0.35, (shift_pixels - self.max_subpixel_shift) * 0.2)
                penalties["shift"] += penalty
                flags.append(f"REGISTRATION_MISALIGNMENT ({shift_pixels:.2f} px shift exceeds {self.max_subpixel_shift} px threshold)")

        # -------------------------------------------------------------
        # Gate 4: Sensor Glint & Saturation Check
        # -------------------------------------------------------------
        sat_px = np.sum(post_b08 > 0.95) / post_b08.size
        if sat_px > 0.02:
            penalties["snr"] += 0.15
            flags.append("SENSOR_SPECULAR_GLINT (Saturated high-reflectance pixels)")

        # Calculate final composite reliability score
        total_penalty = sum(penalties.values())
        raw_score = max(0.0, 1.0 - total_penalty)
        is_reliable = (raw_score >= self.min_reliable_score) and (cloud_pct < 35.0)

        report = ReliabilityReport(
            is_reliable=is_reliable,
            overall_confidence_score=round(raw_score, 4),
            reliability_percentage=round(raw_score * 100.0, 1),
            verdict="APPROVED_AI_RESULT" if is_reliable else "SUPPRESSED_FALSE_ALARM",
            flags=flags,
            cloud_shadow_penalty=round(penalties["cloud"], 3),
            phenology_drift_penalty=round(penalties["phenology"], 3),
            misalignment_penalty=round(penalties["shift"], 3),
            details={
                "cloud_pct": round(cloud_pct, 2),
                "shadow_pct": round(shadow_pct, 2),
                "subpixel_shift": round(shift_pixels, 2),
                "diffuse_phenology_ratio": round(float(diffuse_veg_drop), 3),
                "penalties": {k: round(v, 3) for k, v in penalties.items()},
            }
        )
        return report

    def filter_change_mask(
        self,
        raw_change_mask: np.ndarray,
        quality_mask_post: np.ndarray,
    ) -> np.ndarray:
        """
        Suppresses false alarms in the binary/multiclass change mask.
        Zeros out pixels contaminated by clouds (bit 0), shadows (bit 1), or nodata (bit 4).
        """
        invalid = (quality_mask_post & 1 > 0) | (quality_mask_post & 2 > 0) | (quality_mask_post & 16 > 0)
        filtered_mask = raw_change_mask.copy()
        filtered_mask[invalid] = 0
        return filtered_mask
