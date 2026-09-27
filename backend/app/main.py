"""
MiraeNova Backend Application Entrypoint
========================================================================================
Offline Air-Gapped Satellite Intelligence API
Smart India Hackathon 2026 - Problem Statement 26227
========================================================================================
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.app.config import settings
from backend.app.routes import search, scenes, change_detection, reliability, analyst, audit, tiles
from ml.remote_clip.vector_index import get_vector_index

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Offline Air-Gapped Satellite Intelligence & Multi-Temporal Change Detection Platform",
)

# Enable CORS for frontend web client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static composite previews if directory exists
if os.path.exists("data/composites"):
    app.mount("/static/composites", StaticFiles(directory="data/composites"), name="composites")

# Register API routes
app.include_router(search.router, prefix=settings.API_V1_STR)
app.include_router(scenes.router, prefix=settings.API_V1_STR)
app.include_router(change_detection.router, prefix=settings.API_V1_STR)
app.include_router(reliability.router, prefix=settings.API_V1_STR)
app.include_router(analyst.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(tiles.router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    print(f"[{settings.PROJECT_NAME}] Starting up in Air-Gapped / Offline Mode...")
    # Initialize vector index
    idx = get_vector_index()
    if not idx.tile_ids and os.path.exists("data/processed/bitemporal_catalog.json"):
        idx.index_all_tiles_from_catalog()
    print(f"[{settings.PROJECT_NAME}] Ready. System operational on {settings.API_V1_STR}")


@app.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "system": "MiraeNova Satellite Intelligence Platform",
        "version": settings.VERSION,
        "mode": "AIR_GAPPED_OFFLINE",
        "components": {
            "data_pipeline": "OPERATIONAL",
            "remote_clip_retrieval": "OPERATIONAL",
            "bit_change_detection": "OPERATIONAL",
            "reliability_gate": "OPERATIONAL",
            "tamper_proof_audit": "OPERATIONAL",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
