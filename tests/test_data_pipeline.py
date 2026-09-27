"""
Unit and Integration Tests for Data Pipeline
"""

import os
import numpy as np
from data_pipeline.band_stack import BandStack, SentinelBand
from data_pipeline.cloud_mask import CloudMaskEngine
from data_pipeline.radiometry import RadiometricNormalizer
from data_pipeline.band_math import SpectralIndices, compute_band_difference
from data_pipeline.co_registration import CoRegistrationChecker


def test_band_stack_float32_preservation():
    """Verify that multi-band reflectance is kept as float32 and not quantized to 8-bit RGB."""
    bands = {
        SentinelBand.B02: np.random.uniform(0.01, 0.40, (64, 64)).astype(np.float32),
        SentinelBand.B03: np.random.uniform(0.01, 0.40, (64, 64)).astype(np.float32),
        SentinelBand.B04: np.random.uniform(0.01, 0.40, (64, 64)).astype(np.float32),
        SentinelBand.B08: np.random.uniform(0.01, 0.80, (64, 64)).astype(np.float32),
    }
    stack = BandStack(bands_data=bands, crs="EPSG:4326", transform=None, scene_id="test_scene")
    refl_b08 = stack.get_reflectance_float32(SentinelBand.B08)
    assert refl_b08.dtype == np.float32
    assert refl_b08.shape == (64, 64)
    assert np.max(refl_b08) <= 1.5


def test_cloud_mask_engine():
    """Verify s2cloudless and quality mask generation."""
    h, w = 64, 64
    bands = {
        SentinelBand.B02: np.full((h, w), 0.70, dtype=np.float32),  # Bright white cloud
        SentinelBand.B03: np.full((h, w), 0.70, dtype=np.float32),
        SentinelBand.B04: np.full((h, w), 0.70, dtype=np.float32),
        SentinelBand.B08: np.full((h, w), 0.75, dtype=np.float32),
        SentinelBand.B11: np.full((h, w), 0.20, dtype=np.float32),
    }
    stack = BandStack(bands_data=bands, crs="EPSG:4326", transform=None)
    engine = CloudMaskEngine(cloud_prob_threshold=0.4)
    q_mask, meta = engine.generate_quality_mask(stack)
    assert meta["cloud_cover_percent"] > 90.0
    assert (q_mask & 1 > 0).all()


def test_spectral_indices_and_band_difference():
    """Verify NDVI, NDBI, NDWI and band differences."""
    h, w = 32, 32
    bands_pre = {
        SentinelBand.B02: np.full((h, w), 0.05, dtype=np.float32),
        SentinelBand.B03: np.full((h, w), 0.08, dtype=np.float32),
        SentinelBand.B04: np.full((h, w), 0.04, dtype=np.float32),
        SentinelBand.B08: np.full((h, w), 0.50, dtype=np.float32),  # High vegetation
        SentinelBand.B11: np.full((h, w), 0.15, dtype=np.float32),
    }
    bands_post = {
        SentinelBand.B02: np.full((h, w), 0.15, dtype=np.float32),
        SentinelBand.B03: np.full((h, w), 0.18, dtype=np.float32),
        SentinelBand.B04: np.full((h, w), 0.20, dtype=np.float32),
        SentinelBand.B08: np.full((h, w), 0.22, dtype=np.float32),  # Vegetation cleared / built-up
        SentinelBand.B11: np.full((h, w), 0.35, dtype=np.float32),
    }
    pre_stack = BandStack(bands_pre, crs="EPSG:4326", transform=None)
    post_stack = BandStack(bands_post, crs="EPSG:4326", transform=None)

    pre_ndvi = SpectralIndices.compute_ndvi(pre_stack)
    post_ndvi = SpectralIndices.compute_ndvi(post_stack)
    assert np.mean(pre_ndvi) > 0.80
    assert np.mean(post_ndvi) < 0.10

    diff_maps, stats = compute_band_difference(pre_stack, post_stack)
    assert "B04" in diff_maps
    assert "delta_NDVI" in diff_maps
    assert np.mean(diff_maps["delta_NDVI"]) < -0.70


def test_co_registration_checker():
    """Verify sub-pixel registration shift detection."""
    h, w = 128, 128
    np.random.seed(42)
    base_nir = np.random.uniform(0.1, 0.6, (h, w)).astype(np.float32)

    # Identical pair -> should be aligned
    stack1 = BandStack({SentinelBand.B08: base_nir}, crs="EPSG:4326", transform=None)
    stack2 = BandStack({SentinelBand.B08: base_nir.copy()}, crs="EPSG:4326", transform=None)

    checker = CoRegistrationChecker(max_allowed_shift_pixels=1.0)
    aligned, report = checker.check_alignment(stack1, stack2)
    assert aligned is True
    assert report["total_shift_pixels"] < 0.5
