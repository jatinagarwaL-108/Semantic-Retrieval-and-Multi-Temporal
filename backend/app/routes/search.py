"""
Semantic Search & Natural Language Retrieval Route
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from ml.remote_clip.vector_index import get_vector_index

router = APIRouter(prefix="/search", tags=["Semantic Search"])


class SearchRequest(BaseModel):
    query: str = Field(..., example="new buildings near river")
    top_k: int = Field(default=6, ge=1, le=20)
    timeframe_start: Optional[str] = "2024-01-01"
    timeframe_end: Optional[str] = "2026-12-31"


class SearchResponse(BaseModel):
    query: str
    understanding: Dict[str, Any]
    total_results: int
    results: List[Dict[str, Any]]


@router.post("", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """
    Translates free-text intelligence query into RemoteCLIP embedding,
    then executes Milvus-compatible ANN cosine search across satellite tiles.
    """
    idx = get_vector_index()
    if not idx.tile_ids:
        # Auto-index if not already loaded
        idx.index_all_tiles_from_catalog()

    ranked_tiles, analysis = idx.search_by_text(request.query, top_k=request.top_k)

    return SearchResponse(
        query=request.query,
        understanding={
            "status": "QUERY_PROCESSED",
            "detected_domain_concepts": analysis["detected_concepts"],
            "embedding_dim": analysis["embedding_dimension"],
            "retrieval_strategy": "RemoteCLIP-Adapted ViT Vector Similarity (ANN)",
        },
        total_results=len(ranked_tiles),
        results=ranked_tiles,
    )
