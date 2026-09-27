"""
Change Detection Inference & Vectorization Engine
Executes:
  1. Multi-band tensor extraction (B02, B03, B04, B08)
  2. Bitemporal Image Transformer forward pass
  3. Reliability Gate verification (cloud/shadow masking)
  4. Contour extraction & polygon vectorization
  5. Multi-class semantic categorization
  6. Emits structured GeoJSON FeatureCollection with confidence metrics
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import cv2
import rasterio
from rasterio.transform import Affine

from data_pipeline.band_stack import BandStack, SentinelBand
from data_pipeline.band_math import SpectralIndices
from .bit_model import get_bit_model
from .classifier_head import ChangeTypeClassifier, ChangeClass, CLASS_COLORS
from ml.reliability_check import ReliabilityGate, ReliabilityReport


class ChangeDetectionEngine:
    def __init__(self, prob_threshold: float = 0.45, min_area_pixels: int = 15):
        self.prob_threshold = prob_threshold
        self.min_area_pixels = min_area_pixels
        self.bit_model = get_bit_model()
        self.classifier = ChangeTypeClassifier()
        self.reliability_gate = ReliabilityGate()

    def run_detection(
        self,
        pre_stack: BandStack,
        post_stack: BandStack,
        quality_mask_post: Optional[np.ndarray] = None,
        coreg_report: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], ReliabilityReport]:
        """
        Executes end-to-end multi-temporal change analysis on multi-spectral stacks.
        """
        # 1. Multi-Spectral Tensor Extraction (4 channels: B02, B03, B04, B08)
        bands = [SentinelBand.B02, SentinelBand.B03, SentinelBand.B04, SentinelBand.B08]
        t1_tensor = pre_stack.get_subset_tensor(bands)  # (4, H, W)
        t2_tensor = post_stack.get_subset_tensor(bands)  # (4, H, W)

        # 2. BIT Model Forward Pass
        raw_change_prob = self.bit_model.predict_change_probability(t1_tensor, t2_tensor)

        # Also blend with direct spectral difference magnitude to guarantee sensitivity on physical indices
        pre_idx = SpectralIndices.compute_all(pre_stack)
        post_idx = SpectralIndices.compute_all(post_stack)
        d_ndvi = post_idx["NDVI"] - pre_idx["NDVI"]
        d_ndbi = post_idx["NDBI"] - pre_idx["NDBI"]
        d_ndwi = post_idx["NDWI"] - pre_idx["NDWI"]

        spectral_magnitude = np.sqrt(d_ndvi**2 + d_ndbi**2 + d_ndwi**2)
        # Combined learned + spectral change probability
        combined_prob = (0.55 * raw_change_prob) + (0.45 * np.clip(spectral_magnitude * 1.8, 0, 1))

        # 3. Reliability Gate Evaluation
        rel_report = self.reliability_gate.evaluate(
            pre_stack=pre_stack,
            post_stack=post_stack,
            quality_mask_post=quality_mask_post,
            coreg_report=coreg_report,
        )

        # Filter out clouds and shadows
        if quality_mask_post is not None:
            filtered_prob = self.reliability_gate.filter_change_mask(combined_prob, quality_mask_post)
        else:
            filtered_prob = combined_prob

        # Binary change mask
        binary_mask = (filtered_prob >= self.prob_threshold).astype(np.uint8)

        # Morphological opening/closing to clean noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        clean_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)
        clean_mask = cv2.morphologyEx(clean_mask, cv2.MORPH_CLOSE, kernel)

        # 4. Extract Connected Polygons
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(clean_mask, connectivity=8)

        features = []
        summary_counts = {
            ChangeClass.CONSTRUCTION.value: 0,
            ChangeClass.ROAD.value: 0,
            ChangeClass.WATER.value: 0,
            ChangeClass.CLEARANCE.value: 0,
        }
        total_changed_hectares = 0.0

        b08_post = post_stack.get_reflectance_float32(SentinelBand.B08)
        b04_post = post_stack.get_reflectance_float32(SentinelBand.B04)

        for label_idx in range(1, num_labels):
            area_px = int(stats[label_idx, cv2.CC_STAT_AREA])
            if area_px < self.min_area_pixels:
                continue

            poly_mask = (labels == label_idx)

            # Spatial geometry
            width_px = stats[label_idx, cv2.CC_STAT_WIDTH]
            height_px = stats[label_idx, cv2.CC_STAT_HEIGHT]
            aspect_ratio = max(width_px, height_px) / (min(width_px, height_px) + 1e-3)

            # Classify change type
            change_cls, confidence, explanation = self.classifier.classify_region(
                polygon_mask=poly_mask,
                delta_ndvi_map=d_ndvi,
                delta_ndbi_map=d_ndbi,
                delta_ndwi_map=d_ndwi,
                b08_post=b08_post,
                b04_post=b04_post,
                spatial_aspect_ratio=aspect_ratio,
            )

            # Area in hectares and square meters (Sentinel-2 10m pixels: 1 px = 100 m^2 = 0.01 hectares)
            area_sqm = int(area_px * 100)
            area_hectares = round(area_px * 0.01, 2)
            total_changed_hectares += area_hectares
            summary_counts[change_cls.value] += 1

            # Convert pixel coordinates to geographic coordinates
            contours, _ = cv2.findContours(
                poly_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            if not contours:
                continue

            contour = contours[0]
            # Simplify contour to avoid overly dense vertices
            epsilon = 0.01 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            geo_coords = []
            for pt in approx:
                px, py = pt[0][0], pt[0][1]
                gx, gy = rasterio.transform.xy(post_stack.transform, py, px)
                geo_coords.append([round(gx, 2), round(gy, 2)])
            
            # Close polygon loop
            if len(geo_coords) > 2 and geo_coords[0] != geo_coords[-1]:
                geo_coords.append(geo_coords[0])

            # Centroid
            cx_px, cy_px = centroids[label_idx]
            gx_c, gy_c = rasterio.transform.xy(post_stack.transform, cy_px, cx_px)

            severity = explanation.get("severity", "medium")
            tactical_summary = explanation.get("tactical_summary", "")

            feature = {
                "type": "Feature",
                "id": f"chg_{label_idx:03d}",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [geo_coords],
                },
                "properties": {
                    "change_id": f"CHG_{label_idx:03d}",
                    "change_type": change_cls.value,
                    "severity": severity,
                    "tactical_summary": tactical_summary,
                    "confidence_score": round(confidence, 3),
                    "confidence_percent": round(confidence * 100.0, 1),
                    "area_pixels": area_px,
                    "area_sqm": area_sqm,
                    "area_hectares": area_hectares,
                    "color_hex": CLASS_COLORS[change_cls],
                    "centroid": [round(gx_c, 2), round(gy_c, 2)],
                    "first_seen_date": post_stack.acquisition_date,
                    "baseline_date": pre_stack.acquisition_date,
                    "reliability_score": rel_report.overall_confidence_score,
                    "reliability_flags": rel_report.flags,
                    "explanation": explanation,
                },
            }
            features.append(feature)

        severity_counts = {
            "high": sum(1 for f in features if f["properties"].get("severity") == "high"),
            "medium": sum(1 for f in features if f["properties"].get("severity") == "medium"),
            "low": sum(1 for f in features if f["properties"].get("severity") == "low"),
        }

        geojson_result = {
            "type": "FeatureCollection",
            "features": features,
            "properties": {
                "total_detections": len(features),
                "total_changed_hectares": round(total_changed_hectares, 2),
                "total_changed_sqm": int(round(total_changed_hectares * 10000.0)),
                "breakdown": summary_counts,
                "severity_breakdown": severity_counts,
                "pre_scene_id": pre_stack.scene_id,
                "post_scene_id": post_stack.scene_id,
                "pre_date": pre_stack.acquisition_date,
                "post_date": post_stack.acquisition_date,
            },
        }


        return geojson_result, rel_report
