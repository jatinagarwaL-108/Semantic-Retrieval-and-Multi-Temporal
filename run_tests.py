"""
MiraeNova Test Suite Runner
Runs unit and integration tests without external test runner dependencies.
"""

import sys
import traceback

def run_all():
    from tests.test_data_pipeline import (
        test_band_stack_float32_preservation,
        test_cloud_mask_engine,
        test_spectral_indices_and_band_difference,
        test_co_registration_checker,
    )
    from tests.test_ml_models import (
        test_remote_clip_model_inference,
        test_vector_index_search,
        test_bit_change_detection,
        test_change_type_classifier,
        test_reliability_gate,
    )

    tests = [
        ("Pipeline: BandStack Float32 Preservation", test_band_stack_float32_preservation),
        ("Pipeline: CloudMask Engine & SCL", test_cloud_mask_engine),
        ("Pipeline: Spectral Indices & Band Difference", test_spectral_indices_and_band_difference),
        ("Pipeline: Co-Registration Shift Check", test_co_registration_checker),
        ("ML: RemoteCLIP Model Inference", test_remote_clip_model_inference),
        ("ML: Vector Index ANN Search", test_vector_index_search),
        ("ML: BIT 4-Band Change Detection", test_bit_change_detection),
        ("ML: Change Type Classifier (Learned+Heuristic)", test_change_type_classifier),
        ("ML: Reliability Gate & False Alarm Filter", test_reliability_gate),
    ]

    try:
        from tests.test_backend_api import (
            test_health_endpoint,
            test_aoi_summary,
            test_semantic_search,
            test_instant_change_detection,
            test_tile_preview,
            test_analyst_review_and_audit_trail,
            test_system_status_telemetry,
            test_unsupervised_cluster_discovery,
            test_export_intelligence_report,
        )
        tests.extend([
            ("Backend API: Health Endpoint", test_health_endpoint),
            ("Backend API: AOI Summary Catalog", test_aoi_summary),
            ("Backend API: Semantic Search", test_semantic_search),
            ("Backend API: Change Detection Execution", test_instant_change_detection),
            ("Backend API: Dynamic Tile Preview Rendering", test_tile_preview),
            ("Backend API: Analyst Review & Tamper-Proof Audit", test_analyst_review_and_audit_trail),
            ("Backend API: System Telemetry & Hardware Diagnostics", test_system_status_telemetry),
            ("Backend API: Unsupervised Spatial & Semantic Clustering", test_unsupervised_cluster_discovery),
            ("Backend API: Defense Intelligence Signed Brief Export", test_export_intelligence_report),
        ])

    except Exception as e:
        print(f"Warning loading backend tests: {e}")

    passed = 0
    failed = 0
    print("\n==================== RUNNING MIRAENOVA TEST SUITE ====================")
    for name, fn in tests:
        try:
            fn()
            print(f" [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f" [FAIL] {name}: {e}")
            traceback.print_exc()
            failed += 1

    print("======================================================================")
    print(f"Results: {passed} passed, {failed} failed.")
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_all()
