"""
Scenes & Bitemporal Catalog Routes
"""

import os
import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

router = APIRouter(prefix="/scenes", tags=["Scenes & AOI"])


@router.get("/catalog")
async def get_bitemporal_catalog():
    """Returns all pre-processed bitemporal tile pairs with geometry and metadata."""
    catalog_path = "data/processed/bitemporal_catalog.json"
    if not os.path.exists(catalog_path):
        return []

    with open(catalog_path, "r") as f:
        pairs = json.load(f)
    return pairs


@router.get("/aoi-summary")
async def get_aoi_summary():
    """Returns overview of available AOIs, baseline dates, and source sensors."""
    return {
        "aoi_name": "Ayodhya_Sarayu_Corridor",
        "description": "Strategic Riverfront Corridor & Infrastructure Hub",
        "utm_zone": "EPSG:32644 (UTM Zone 44N)",
        "sensor": "Sentinel-2 Multi-Spectral Instrument (MSI) Level-2A BOA",
        "available_timeframes": [
            {"label": "2024 Baseline", "date": "2024-03-23", "scene_id": "S2B_MSIL2A_20240323_Ayodhya_Sarayu_Corridor"},
            {"label": "2025 Current", "date": "2025-12-13", "scene_id": "S2B_MSIL2A_20251213_Ayodhya_Sarayu_Corridor"},
        ],
        "center_coordinates": [82.20, 26.80],  # Lon, Lat
        "bounding_box_utm": [620000, 2959880, 630240, 2970120],
        "tile_count": 9,
    }
