"""
Spatial Tiling Engine
Splits scenes into fixed-size tiles (e.g. 512x512) with overlap.
Computes UTM projection, bounding box coordinates, and tile metadata.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import rasterio
from rasterio.transform import Affine, from_origin
from rasterio.windows import Window
from .band_stack import BandStack, SentinelBand


class TileGridGenerator:
    """
    Slices large scenes or AOIs into overlapping tiles with accurate georeferencing.
    """

    def __init__(self, tile_size: int = 512, overlap: int = 32):
        self.tile_size = tile_size
        self.overlap = overlap
        self.stride = tile_size - overlap

    def generate_tiles(self, stack: BandStack) -> List[Tuple[Window, BandStack, Dict[str, Any]]]:
        """
        Extracts overlapping tiles from a BandStack.
        Returns list of (Window, BandStack, metadata).
        """
        h, w = stack.height, stack.width
        tiles = []
        tile_index = 0

        y_steps = range(0, max(1, h - self.overlap), self.stride)
        x_steps = range(0, max(1, w - self.overlap), self.stride)

        for y in y_steps:
            for x in x_steps:
                # Clamp window to boundaries
                win_w = min(self.tile_size, w - x)
                win_h = min(self.tile_size, h - y)
                window = Window(col_off=x, row_off=y, width=win_w, height=win_h)

                # Compute tile affine transform
                tile_transform = rasterio.windows.transform(window, stack.transform)

                # Extract band data
                tile_bands = {}
                for b_enum, data in stack.bands_data.items():
                    tile_bands[b_enum] = data[y : y + win_h, x : x + win_w]

                # Compute tile bounding box in CRS
                minx = tile_transform.c
                maxy = tile_transform.f
                maxx = minx + (win_w * tile_transform.a)
                miny = maxy + (win_h * tile_transform.e)

                tile_stack = BandStack(
                    bands_data=tile_bands,
                    crs=stack.crs,
                    transform=tile_transform,
                    nodata=stack.nodata,
                    scene_id=f"{stack.scene_id}_tile_{tile_index:03d}",
                    acquisition_date=stack.acquisition_date,
                )

                meta = {
                    "tile_index": tile_index,
                    "tile_id": f"{stack.scene_id}_t{tile_index:03d}",
                    "parent_scene_id": stack.scene_id,
                    "acquisition_date": stack.acquisition_date,
                    "window": {"col_off": x, "row_off": y, "width": win_w, "height": win_h},
                    "bounds": [minx, miny, maxx, maxy],
                    "crs": str(stack.crs),
                    "geojson_geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [minx, miny],
                            [maxx, miny],
                            [maxx, maxy],
                            [minx, maxy],
                            [minx, miny],
                        ]],
                    },
                }

                tiles.append((window, tile_stack, meta))
                tile_index += 1

        return tiles
