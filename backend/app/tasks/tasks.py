"""
Celery Task Definitions for Preprocessing, Embedding, and Change Detection
"""

from typing import Dict, Any
from .celery_app import celery_app
from data_pipeline.pipeline import DataPipeline
from ml.remote_clip.vector_index import get_vector_index
from data_pipeline.band_stack import BandStack
from ml.change_detection.inference import ChangeDetectionEngine


if celery_app is not None:
    @celery_app.task(name="tasks.process_scene_async")
    def process_scene_async(cog_path: str):
        pipeline = DataPipeline()
        tiles = pipeline.process_single_scene(cog_path)
        idx = get_vector_index()
        idx.index_all_tiles_from_catalog()
        return {"processed_tiles": len(tiles)}

    @celery_app.task(name="tasks.run_bitemporal_cd_async")
    def run_bitemporal_cd_async(pre_cog: str, post_cog: str):
        pre_stack = BandStack.read_cog(pre_cog)
        post_stack = BandStack.read_cog(post_cog)
        engine = ChangeDetectionEngine()
        results, rel = engine.run_detection(pre_stack, post_stack)
        return {
            "features_detected": len(results["features"]),
            "reliability_score": rel.overall_confidence_score,
            "results": results,
        }
