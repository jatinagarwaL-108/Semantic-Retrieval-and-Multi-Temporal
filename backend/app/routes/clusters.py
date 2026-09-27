"""
Spatial & Semantic Clustering Route
========================================================================================
Unsupervised clustering of candidate sites across the satellite AOI using 
RemoteCLIP embeddings and geodetic centroids.
Provides both `/api/clusters/discover` and alias `/api/discover-clusters`.
========================================================================================
"""

from typing import Tuple, Optional, List, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from ml.remote_clip.cluster import TerrainClusterEngine

router = APIRouter(tags=["Spatial Clusters"])


class ClusterDiscoverRequest(BaseModel):
    reference_location: Tuple[float, float] = Field(
        default=(82.20, 26.80),
        description="Lon, Lat geodetic reference point"
    )
    radius_km: float = Field(default=25.0, description="Spatial search radius in km")
    n_clusters: int = Field(default=4, description="Target cluster count")


@router.post("/clusters/discover")
@router.post("/discover-clusters")
async def discover_clusters(req: Optional[ClusterDiscoverRequest] = None):
    """
    Performs unsupervised clustering over real 512-dim RemoteCLIP embeddings
    and spatial geolocations across the AOI.
    """
    if req is None:
        req = ClusterDiscoverRequest()

    engine = TerrainClusterEngine(n_clusters=req.n_clusters)
    clusters = engine.discover_clusters(
        reference_coord=req.reference_location,
        radius_km=req.radius_km
    )

    return {
        "status": "SUCCESS",
        "reference_location": list(req.reference_location),
        "radius_km": req.radius_km,
        "total_clusters": len(clusters),
        "algorithm": "K-Means on RemoteCLIP 512-dim Embeddings & Geodetic Anchors",
        "clusters": clusters,
    }


@router.get("/clusters/discover")
@router.get("/discover-clusters")
async def get_clusters(lon: float = 82.20, lat: float = 26.80, radius_km: float = 25.0, n_clusters: int = 4):
    """
    GET convenience endpoint for unsupervised cluster discovery.
    """
    engine = TerrainClusterEngine(n_clusters=n_clusters)
    clusters = engine.discover_clusters(
        reference_coord=(lon, lat),
        radius_km=radius_km
    )

    return {
        "status": "SUCCESS",
        "reference_location": [lon, lat],
        "radius_km": radius_km,
        "total_clusters": len(clusters),
        "algorithm": "K-Means on RemoteCLIP 512-dim Embeddings & Geodetic Anchors",
        "clusters": clusters,
    }
