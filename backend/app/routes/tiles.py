"""
Dynamic Tile & Visualization Rendering Routes (Titiler / Rasterio On-The-Fly Renderer)
========================================================================================
CRITICAL ARCHITECTURAL CONFORMANCE:
Authoritative COG files are stored as multi-band surface reflectance.
This endpoint dynamically composites 3-band visual RGB, false-color NIR, or NDVI heatmaps
ON-THE-FLY at query time for map consumption.
RGB is never stored as the authoritative analysis source.
========================================================================================
"""

import os
import io
import numpy as np
from PIL import Image
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, FileResponse

from data_pipeline.band_stack import BandStack, SentinelBand
from data_pipeline.display_composite import create_display_composite

router = APIRouter(prefix="/tiles", tags=["Dynamic Tile Rendering"])


@router.get("/{tile_id}/preview")
async def get_tile_preview_png(tile_id: str):
    """Returns cached or dynamically generated true-color RGB preview PNG."""
    png_path = f"data/composites/{tile_id}_preview.png"
    if os.path.exists(png_path):
        return FileResponse(png_path, media_type="image/png")

    # Generate dynamically from authoritative multi-band COG
    cog_path = f"data/processed/{tile_id}.tif"
    if not os.path.exists(cog_path):
        raise HTTPException(status_code=404, detail=f"Tile {tile_id} COG not found")

    stack = BandStack.read_cog(cog_path)
    rgb, _ = create_display_composite(stack, composite_type="true_color")
    img = Image.fromarray(rgb)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@router.get("/{tile_id}/cir")
async def get_tile_cir_png(tile_id: str):
    """Returns Color Infrared (CIR False-Color: B08, B04, B03) preview PNG."""
    png_path = f"data/composites/{tile_id}_cir.png"
    if os.path.exists(png_path):
        return FileResponse(png_path, media_type="image/png")

    cog_path = f"data/processed/{tile_id}.tif"
    if not os.path.exists(cog_path):
        raise HTTPException(status_code=404, detail=f"Tile {tile_id} COG not found")

    stack = BandStack.read_cog(cog_path)
    rgb, _ = create_display_composite(stack, composite_type="false_color_cir")
    img = Image.fromarray(rgb)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@router.get("/{tile_id}/ndvi-map")
async def get_tile_ndvi_colormap(tile_id: str):
    """Generates dynamic on-the-fly NDVI color-mapped image."""
    cog_path = f"data/processed/{tile_id}.tif"
    if not os.path.exists(cog_path):
        raise HTTPException(status_code=404, detail=f"Tile {tile_id} COG not found")

    stack = BandStack.read_cog(cog_path)
    b08 = stack.get_reflectance_float32(SentinelBand.B08)
    b04 = stack.get_reflectance_float32(SentinelBand.B04)
    ndvi = (b08 - b04) / (b08 + b04 + 1e-6)

    # Colormap: low NDVI (brown/red), medium (yellow), high (deep green)
    norm_ndvi = np.clip((ndvi + 0.2) / 1.0, 0.0, 1.0)
    h, w = ndvi.shape
    rgb_arr = np.zeros((h, w, 3), dtype=np.uint8)

    # Simplified viridis/terrain colormap
    rgb_arr[:, :, 0] = ((1.0 - norm_ndvi) * 220).astype(np.uint8)
    rgb_arr[:, :, 1] = (norm_ndvi * 210 + 30).astype(np.uint8)
    rgb_arr[:, :, 2] = (np.sin(norm_ndvi * np.pi) * 80).astype(np.uint8)

    img = Image.fromarray(rgb_arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
