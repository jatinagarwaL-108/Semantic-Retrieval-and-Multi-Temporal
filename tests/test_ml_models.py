"""
Unit and Integration Tests for ML Subsystem
"""

import numpy as np
from ml.remote_clip.model import get_remote_clip_model
from ml.remote_clip.vector_index import get_vector_index
from ml.change_detection.bit_model import get_bit_model
from ml.change_detection.classifier_head import ChangeTypeClassifier, ChangeClass
from ml.reliability_check import ReliabilityGate
from data_pipeline.band_stack import BandStack, SentinelBand


def test_remote_clip_model_inference():
    """Verify RemoteCLIP text and image embedding dimensions and similarity."""
    model = get_remote_clip_model()
    text_emb = model.encode_text("new construction near river")
    assert text_emb.shape == (512,)
    assert np.isclose(np.linalg.norm(text_emb), 1.0, atol=1e-3)

    dummy_img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    img_emb = model.encode_image(dummy_img)
    assert img_emb.shape == (512,)
    assert np.isclose(np.linalg.norm(img_emb), 1.0, atol=1e-3)


def test_vector_index_search():
    """Verify ANN search retrieval."""
    idx = get_vector_index()
    results, analysis = idx.search_by_text("new buildings near river", top_k=3)
    assert len(results) > 0
    assert "tile_id" in results[0]
    assert 0.0 <= results[0]["similarity_score"] <= 1.0


def test_bit_change_detection():
    """Verify Bitemporal Image Transformer forward pass on 4-band input."""
    model = get_bit_model()
    t1 = np.random.uniform(0.1, 0.4, (4, 128, 128)).astype(np.float32)
    t2 = np.random.uniform(0.1, 0.4, (4, 128, 128)).astype(np.float32)
    # Put strong change in middle
    t2[:, 40:80, 40:80] += 0.3
    prob = model.predict_change_probability(t1, t2)
    assert prob.shape == (128, 128)
    assert (prob >= 0.0).all() and (prob <= 1.0).all()


def test_change_type_classifier():
    """Verify multiclass classification rules and confidence."""
    classifier = ChangeTypeClassifier()
    mask = np.ones((30, 30), dtype=bool)

    # Simulate construction (high delta NDBI, low elongation)
    d_ndvi = np.full((30, 30), -0.25, dtype=np.float32)
    d_ndbi = np.full((30, 30), +0.30, dtype=np.float32)
    d_ndwi = np.full((30, 30), -0.05, dtype=np.float32)
    post_nir = np.full((30, 30), 0.20, dtype=np.float32)
    post_red = np.full((30, 30), 0.25, dtype=np.float32)

    chg_cls, conf, exp = classifier.classify_region(
        polygon_mask=mask,
        delta_ndvi_map=d_ndvi,
        delta_ndbi_map=d_ndbi,
        delta_ndwi_map=d_ndwi,
        b08_post=post_nir,
        b04_post=post_red,
        spatial_aspect_ratio=1.2,
    )
    assert chg_cls == ChangeClass.CONSTRUCTION
    assert conf > 0.70


def test_reliability_gate():
    """Verify reliability filtering for clouds and shadows."""
    gate = ReliabilityGate(max_acceptable_cloud_pct=15.0)
    h, w = 64, 64
    b = {
        SentinelBand.B02: np.full((h, w), 0.1, dtype=np.float32),
        SentinelBand.B04: np.full((h, w), 0.1, dtype=np.float32),
        SentinelBand.B08: np.full((h, w), 0.4, dtype=np.float32),
    }
    s1 = BandStack(b, crs="EPSG:4326", transform=None)
    s2 = BandStack(b, crs="EPSG:4326", transform=None)

    # Clean mask -> Reliable
    clean_mask = np.zeros((h, w), dtype=np.uint8)
    rep1 = gate.evaluate(s1, s2, quality_mask_post=clean_mask)
    assert rep1.is_reliable is True
    assert rep1.verdict == "APPROVED_AI_RESULT"

    # Heavily clouded mask -> Suppressed false alarm
    cloud_mask = np.full((h, w), 1, dtype=np.uint8)  # bit 0 = cloud
    rep2 = gate.evaluate(s1, s2, quality_mask_post=cloud_mask)
    assert rep2.is_reliable is False
    assert rep2.verdict == "SUPPRESSED_FALSE_ALARM"
