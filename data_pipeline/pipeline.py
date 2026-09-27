"""
MiraeNova End-to-End Data Preprocessing Pipeline
========================================================================================
CLI and Celery-callable workflow executing strict scientific stages:
  1. Tiling with overlap and georeferencing
  2. Cloud / shadow / quality masking (s2cloudless + SCL)
  3. Per-scene radiometric normalization parameter computation
  4. Multi-band math (NDVI, NDBI, NDWI) and multi-temporal band differences
  5. Sub-pixel co-registration verification
  6. Derived display/embedding composite generation (strictly tagged non-authoritative)
  7. Metadata & provenance assembly
========================================================================================
"""

import os
import json
import argparse
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from .band_stack import BandStack, SentinelBand
from .tiling import TileGridGenerator
from .cloud_mask import CloudMaskEngine
from .radiometry import RadiometricNormalizer
from .band_math import SpectralIndices, compute_band_difference
from .co_registration import CoRegistrationChecker
from .display_composite import create_display_composite


class DataPipeline:
    def __init__(
        self,
        tile_size: int = 512,
        tile_overlap: int = 32,
        processed_dir: str = "data/processed",
        composite_dir: str = "data/composites",
    ):
        self.tile_size = tile_size
        self.tile_overlap = tile_overlap
        self.processed_dir = processed_dir
        self.composite_dir = composite_dir

        self.tiler = TileGridGenerator(tile_size=tile_size, overlap=tile_overlap)
        self.cloud_engine = CloudMaskEngine(cloud_prob_threshold=0.40)
        self.normalizer = RadiometricNormalizer(lower_percentile=2.0, upper_percentile=98.0)
        self.coreg_checker = CoRegistrationChecker(max_allowed_shift_pixels=1.0)

        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(composite_dir, exist_ok=True)

    def process_single_scene(self, cog_path: str) -> List[Dict[str, Any]]:
        """
        Executes stages 1-3, 6, and metadata generation for a single multi-band COG scene.
        """
        print(f"[Pipeline] Ingesting authoritative multi-band COG: {cog_path}")
        stack = BandStack.read_cog(cog_path)

        # 1. Tiling
        raw_tiles = self.tiler.generate_tiles(stack)
        processed_tiles_meta = []

        for window, tile_stack, meta in raw_tiles:
            tile_id = meta["tile_id"]
            tile_cog_path = os.path.join(self.processed_dir, f"{tile_id}.tif")

            # Write multi-band tile COG (No RGB collapse!)
            tile_stack.write_cog(tile_cog_path)

            # 2. Cloud and Quality Masking
            quality_mask, quality_meta = self.cloud_engine.generate_quality_mask(tile_stack)
            mask_path = os.path.join(self.processed_dir, f"{tile_id}_quality_mask.npy")
            np.save(mask_path, quality_mask)

            # 3. Radiometric Normalization Parameters
            valid_mask = (quality_mask & 1 == 0) & (quality_mask & 16 == 0)
            norm_params = self.normalizer.compute_normalization_parameters(tile_stack, valid_mask)

            # 4. Spectral Indices
            indices = SpectralIndices.compute_all(tile_stack)
            indices_meta = {
                "mean_ndvi": round(float(np.mean(indices["NDVI"])), 4),
                "mean_ndbi": round(float(np.mean(indices["NDBI"])), 4),
                "mean_ndwi": round(float(np.mean(indices["NDWI"])), 4),
            }

            # 6. Derived Display Composite (Tag: display/embedding-input composite, derived, not authoritative)
            display_png_path = os.path.join(self.composite_dir, f"{tile_id}_preview.png")
            create_display_composite(
                tile_stack, composite_type="true_color", output_png_path=display_png_path
            )

            false_color_png_path = os.path.join(self.composite_dir, f"{tile_id}_cir.png")
            create_display_composite(
                tile_stack, composite_type="false_color_cir", output_png_path=false_color_png_path
            )

            # 7. Metadata Assembly
            tile_record = {
                "tile_id": tile_id,
                "parent_scene_id": stack.scene_id,
                "acquisition_date": stack.acquisition_date,
                "crs": str(stack.crs),
                "bounds": meta["bounds"],
                "window": meta["window"],
                "geojson_geometry": meta["geojson_geometry"],
                "cog_path": os.path.abspath(tile_cog_path),
                "quality_mask_path": os.path.abspath(mask_path),
                "display_preview_png": os.path.abspath(display_png_path),
                "false_color_png": os.path.abspath(false_color_png_path),
                "quality_metrics": quality_meta,
                "radiometric_normalization": norm_params,
                "spectral_indices_summary": indices_meta,
                "authoritative_bands": [b.value for b in tile_stack.bands_data.keys()],
            }
            processed_tiles_meta.append(tile_record)

        return processed_tiles_meta

    def process_bitemporal_pair(
        self, pre_scene_cog: str, post_scene_cog: str
    ) -> List[Dict[str, Any]]:
        """
        Executes end-to-end multi-temporal pair processing including co-registration
        and authoritative band difference calculation.
        """
        print(f"[Pipeline] Processing Bitemporal Pair:\n  Pre:  {pre_scene_cog}\n  Post: {post_scene_cog}")
        pre_tiles = self.process_single_scene(pre_scene_cog)
        post_tiles = self.process_single_scene(post_scene_cog)

        paired_results = []
        # Match tiles by index
        for t_pre, t_post in zip(pre_tiles, post_tiles):
            pre_stack = BandStack.read_cog(t_pre["cog_path"])
            post_stack = BandStack.read_cog(t_post["cog_path"])

            # 5. Co-Registration Verification
            is_aligned, coreg_report = self.coreg_checker.check_alignment(pre_stack, post_stack)

            # 4. Multi-Band Difference Computation (Authority on Change)
            diff_maps, diff_stats = compute_band_difference(pre_stack, post_stack)
            diff_file = os.path.join(self.processed_dir, f"{t_pre['tile_id']}_{t_post['tile_id']}_banddiff.npy")
            np.save(diff_file, diff_maps)

            pair_record = {
                "pair_id": f"{t_pre['tile_id']}_VS_{t_post['tile_id']}",
                "pre_tile": t_pre,
                "post_tile": t_post,
                "bounds": t_pre["bounds"],
                "geojson_geometry": t_pre["geojson_geometry"],
                "co_registration": coreg_report,
                "band_difference_stats": diff_stats,
                "band_difference_file": os.path.abspath(diff_file),
            }
            paired_results.append(pair_record)

        # Save catalog JSON
        catalog_path = os.path.join(self.processed_dir, "bitemporal_catalog.json")
        with open(catalog_path, "w") as f:
            json.dump(paired_results, f, indent=2)

        print(f"[Pipeline] Successfully processed {len(paired_results)} bitemporal tile pairs.")
        return paired_results


def run_cli():
    parser = argparse.ArgumentParser(description="MiraeNova Raw Sentinel-2 Data Pipeline")
    parser.add_argument("--pre", type=str, help="Path to pre-event multi-band COG")
    parser.add_argument("--post", type=str, help="Path to post-event multi-band COG")
    parser.add_argument("--tile-size", type=int, default=512, help="Tile size in pixels")
    args = parser.parse_args()

    pipeline = DataPipeline(tile_size=args.tile_size)
    if args.pre and args.post:
        pipeline.process_bitemporal_pair(args.pre, args.post)
    elif args.pre:
        pipeline.process_single_scene(args.pre)
    else:
        # Run demo mode
        from .seed_demo_data import generate_synthetic_sentinel2_pair
        p_pre, p_post = generate_synthetic_sentinel2_pair()
        pipeline.process_bitemporal_pair(p_pre, p_post)


if __name__ == "__main__":
    run_cli()
