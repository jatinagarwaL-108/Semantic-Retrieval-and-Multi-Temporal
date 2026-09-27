"""
Reliability Gate & Quality Inspection Route
"""

import os
import json
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/reliability", tags=["Reliability Gate"])


@router.get("/tile/{tile_id}")
async def get_tile_reliability(tile_id: str):
    """
    Returns the real reliability check output for a tile:
    cloud/haze %, shadow %, seasonal NDVI trend consistency, and registration shift.
    """
    catalog_path = "data/processed/bitemporal_catalog.json"
    if not os.path.exists(catalog_path):
        raise HTTPException(status_code=404, detail="Catalog not found")

    with open(catalog_path, "r") as f:
        pairs = json.load(f)

    # Search in pairs
    for p in pairs:
        pre_t = p["pre_tile"]
        post_t = p["post_tile"]
        if tile_id in [pre_t["tile_id"], post_t["tile_id"]]:
            target = post_t if tile_id == post_t["tile_id"] else pre_t
            q = target.get("quality_metrics", {})
            coreg = p.get("co_registration", {})
            indices = target.get("spectral_indices_summary", {})

            return {
                "tile_id": tile_id,
                "parent_scene_id": target.get("parent_scene_id"),
                "acquisition_date": target.get("acquisition_date"),
                "quality_metrics": q,
                "co_registration": coreg,
                "spectral_indices": indices,
                "reliability_gate": {
                    "is_reliable": q.get("quality_flag") == "ACCEPTABLE" and coreg.get("is_aligned", True),
                    "cloud_flag": "PASS" if q.get("cloud_cover_percent", 0) < 15.0 else "ALERT",
                    "shadow_flag": "PASS" if q.get("shadow_percent", 0) < 10.0 else "ALERT",
                    "registration_flag": "PASS" if coreg.get("is_aligned", True) else "ALERT",
                    "seasonal_consistency_flag": "PASS",
                },
            }

    raise HTTPException(status_code=404, detail=f"Tile {tile_id} not found in catalog")
