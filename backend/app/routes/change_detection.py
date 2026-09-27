"""
Multi-Temporal Change Detection Routes
"""

import os
import json
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from data_pipeline.band_stack import BandStack
from ml.change_detection.inference import ChangeDetectionEngine

router = APIRouter(prefix="/change-detection", tags=["Change Detection"])

# In-memory job cache for fast demo access
JOB_CACHE: Dict[str, Dict[str, Any]] = {}


class ChangeDetectionJobRequest(BaseModel):
    pre_tile_cog: str
    post_tile_cog: str
    quality_mask_path: Optional[str] = None
    prob_threshold: float = 0.45


def execute_job(job_id: str, pre_cog: str, post_cog: str, q_mask_path: Optional[str]):
    JOB_CACHE[job_id]["status"] = "PROCESSING"
    try:
        pre_stack = BandStack.read_cog(pre_cog)
        post_stack = BandStack.read_cog(post_cog)
        q_mask = None
        if q_mask_path and os.path.exists(q_mask_path):
            import numpy as np
            q_mask = np.load(q_mask_path)

        engine = ChangeDetectionEngine()
        geojson_results, rel_report = engine.run_detection(
            pre_stack=pre_stack,
            post_stack=post_stack,
            quality_mask_post=q_mask,
        )

        geojson_results["properties"]["pre_tile_id"] = os.path.splitext(os.path.basename(pre_cog))[0]
        geojson_results["properties"]["post_tile_id"] = os.path.splitext(os.path.basename(post_cog))[0]

        JOB_CACHE[job_id]["status"] = "COMPLETED"
        JOB_CACHE[job_id]["results"] = geojson_results
        JOB_CACHE[job_id]["reliability"] = {
            "is_reliable": rel_report.is_reliable,
            "confidence_score": rel_report.overall_confidence_score,
            "reliability_percentage": rel_report.reliability_percentage,
            "verdict": rel_report.verdict,
            "flags": rel_report.flags,
            "details": rel_report.details,
        }
    except Exception as e:
        JOB_CACHE[job_id]["status"] = "FAILED"
        JOB_CACHE[job_id]["error"] = str(e)


@router.post("/jobs")
async def submit_change_detection_job(
    req: ChangeDetectionJobRequest, background_tasks: BackgroundTasks
):
    """Submits an asynchronous change detection job."""
    if not os.path.exists(req.pre_tile_cog) or not os.path.exists(req.post_tile_cog):
        raise HTTPException(status_code=404, detail="One or more COG tile paths not found")

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    JOB_CACHE[job_id] = {
        "job_id": job_id,
        "status": "QUEUED",
        "pre_tile": req.pre_tile_cog,
        "post_tile": req.post_tile_cog,
    }

    # Run in background
    background_tasks.add_task(
        execute_job, job_id, req.pre_tile_cog, req.post_tile_cog, req.quality_mask_path
    )

    return {"job_id": job_id, "status": "QUEUED"}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Retrieves status and results of a change detection job."""
    if job_id not in JOB_CACHE:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return JOB_CACHE[job_id]


@router.get("/pair-instant/{pair_tile_index}")
async def analyze_pair_instant(pair_tile_index: int = 0):
    """
    Direct synchronous endpoint for fast interactive UI review on real satellite tiles.
    """
    catalog_path = "data/processed/bitemporal_catalog.json"
    if not os.path.exists(catalog_path):
        raise HTTPException(status_code=404, detail="Catalog not found")

    with open(catalog_path, "r") as f:
        catalog = json.load(f)

    if pair_tile_index < 0 or pair_tile_index >= len(catalog):
        pair_tile_index = 0

    pair = catalog[pair_tile_index]
    pre_cog = pair["pre_tile"]["cog_path"]
    post_cog = pair["post_tile"]["cog_path"]
    q_mask_file = pair["post_tile"].get("quality_mask_path")

    job_id = f"instant_t{pair_tile_index:03d}_{os.path.basename(pre_cog)}"
    if job_id in JOB_CACHE and JOB_CACHE[job_id]["status"] == "COMPLETED":
        return JOB_CACHE[job_id]

    JOB_CACHE[job_id] = {"job_id": job_id, "status": "PROCESSING"}
    execute_job(job_id, pre_cog, post_cog, q_mask_file)
    return JOB_CACHE[job_id]
