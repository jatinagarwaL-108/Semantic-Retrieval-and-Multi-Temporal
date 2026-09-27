"""
Integration Tests for Backend API Endpoints
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["components"]["data_pipeline"] == "OPERATIONAL"


def test_aoi_summary():
    res = client.get("/api/scenes/aoi-summary")
    assert res.status_code == 200
    data = res.json()
    assert "Sarayu" in data["aoi_name"]


def test_semantic_search():
    payload = {"query": "new buildings near river", "top_k": 3}
    res = client.post("/api/search", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] > 0
    assert "tile_id" in data["results"][0]


def test_instant_change_detection():
    res = client.get("/api/change-detection/pair-instant/1")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert "results" in data
    assert len(data["results"]["features"]) > 0


def test_tile_preview():
    res = client.get("/api/tiles/S2A_MSIL2A_20240315_Sarayu_Riverfront_AOI_t001/preview")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"


def test_analyst_review_and_audit_trail():
    review_payload = {
        "analyst_user": "Captain_Vikram_Rathore",
        "tile_pair_id": "S2A_t001_VS_S2B_t001",
        "change_id": "CHG_001",
        "decision": "CONFIRM_REAL_CHANGE",
        "change_type": "CONSTRUCTION",
        "confidence_percent": 94.5,
        "evidence": {"area_hectares": 1.25, "coords": [415500, 2962000]},
        "analyst_notes": "Confirmed concrete foundation and superstructure near river corridor.",
    }
    res = client.post("/api/analyst/review", json=review_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "RECORDED_IN_IMMUTABLE_LEDGER"
    assert "block_hash" in data["block"]

    # Verify audit trail
    audit_res = client.get("/api/audit-trail")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["is_valid"] is True
    assert audit_data["total_records"] >= 1


def test_system_status_telemetry():
    res = client.get("/api/system-status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "operational"
    assert "BIT" in data["ai_model"]
    assert "RemoteCLIP" in data["embedding_model"]
    assert data["audit_integrity_verified"] is True
    assert len(data["spectral_bands"]) >= 6


def test_unsupervised_cluster_discovery():
    res = client.post("/api/clusters/discover", json={"reference_location": [82.20, 26.80], "radius_km": 25.0})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert len(data["clusters"]) >= 1
    c0 = data["clusters"][0]
    assert "cluster_id" in c0
    assert "severity" in c0
    assert "similarity" in c0

    # Also test alias
    res_alias = client.post("/api/discover-clusters", json={"reference_location": [82.20, 26.80]})
    assert res_alias.status_code == 200


def test_export_intelligence_report():
    res = client.get("/api/analyst/export-report/instant_t000")
    assert res.status_code == 200
    data = res.json()
    assert "DEFENSE RESTRICTED" in data["classification"]
    assert "report_id" in data
    assert "digital_seal_sha256" in data["cryptographic_verification"]
    assert len(data["polygon_inventory"]) >= 1
    assert "markdown_report" in data

