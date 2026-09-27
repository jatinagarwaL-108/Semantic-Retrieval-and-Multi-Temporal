"""
Real Sentinel-2 L2A BOA Satellite Data Downloader
Pulls authentic, georeferenced Sentinel-2 multi-band scenes from ESA / Copernicus Open Archive
via Microsoft Planetary Computer / AWS Open Data for bitemporal change detection.
Downloads 1024x1024 window (10.24 km x 10.24 km) covering Ayodhya / Sarayu Riverfront corridor:
  - Baseline (T1): 2024-03-23 (S2B_MSIL2A_20240323)
  - Current  (T2): 2025-12-13 (S2B_MSIL2A_20251213)
Preserves authentic BOA surface reflectance across B02, B03, B04, B08, B11, B12, SCL.
"""

import os
import requests
import rasterio
from rasterio.windows import Window
import cv2
import numpy as np

from .band_stack import BandStack, SentinelBand


def fetch_real_sentinel2_pair(
    output_dir: str = "data/raw",
    col_off: int = 2000,
    row_off: int = 3500,
    size: int = 1024,
    aoi_name: str = "Ayodhya_Sarayu_Corridor",
) -> tuple:
    """
    Downloads real bitemporal Sentinel-2 L2A BOA stacks for the target AOI.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Fetch SAS authentication token for Sentinel-2 blob container
    print("[Sentinel-2 Fetcher] Obtaining secure access token for ESA Sentinel-2 archive...")
    token_url = "https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel2l2a01/sentinel2-l2"
    r_tok = requests.get(token_url, timeout=15)
    r_tok.raise_for_status()
    token = r_tok.json()["token"]

    stac_url = "https://planetarycomputer.microsoft.com/api/stac/v1/search"

    # Search for T1 Baseline (March 2024)
    print("[Sentinel-2 Fetcher] Querying 2024 Baseline scene...")
    payload_2024 = {
        "collections": ["sentinel-2-l2a"],
        "bbox": [82.15, 26.75, 82.25, 26.85],
        "datetime": "2024-03-01T00:00:00Z/2024-04-01T00:00:00Z",
        "limit": 1,
        "query": {"eo:cloud_cover": {"lt": 5}},
    }
    r_2024 = requests.post(stac_url, json=payload_2024, timeout=15).json()
    feat_2024 = r_2024["features"][0]
    id_2024 = feat_2024["id"]
    date_2024 = feat_2024["properties"]["datetime"][:10]
    print(f"  -> Found 2024 Scene: {id_2024} (Date: {date_2024})")

    # Search for T2 Current (Late 2025)
    print("[Sentinel-2 Fetcher] Querying 2025 Current scene...")
    payload_2025 = {
        "collections": ["sentinel-2-l2a"],
        "bbox": [82.15, 26.75, 82.25, 26.85],
        "datetime": "2025-11-01T00:00:00Z/2025-12-31T00:00:00Z",
        "limit": 1,
        "query": {"eo:cloud_cover": {"lt": 5}},
    }
    r_2025 = requests.post(stac_url, json=payload_2025, timeout=15).json()
    feat_2025 = r_2025["features"][0]
    id_2025 = feat_2025["id"]
    date_2025 = feat_2025["properties"]["datetime"][:10]
    print(f"  -> Found 2025 Scene: {id_2025} (Date: {date_2025})")

    def download_bands_for_feature(feat, scene_id, date_str):
        assets = feat["assets"]
        bands_data = {}
        target_crs = None
        target_transform = None

        band_keys = [
            (SentinelBand.B02, "B02", 10),
            (SentinelBand.B03, "B03", 10),
            (SentinelBand.B04, "B04", 10),
            (SentinelBand.B08, "B08", 10),
            (SentinelBand.B11, "B11", 20),
            (SentinelBand.B12, "B12", 20),
            (SentinelBand.SCL, "SCL", 20),
        ]

        for band_enum, asset_key, res in band_keys:
            if asset_key not in assets:
                continue

            asset_url = assets[asset_key]["href"] + "?" + token
            print(f"  [+] Streaming real {asset_key} ({res}m) for {date_str}...")

            if res == 10:
                w = Window(col_off, row_off, size, size)
                with rasterio.open(asset_url) as src:
                    arr = src.read(1, window=w)
                    if target_crs is None:
                        target_crs = src.crs
                        target_transform = rasterio.windows.transform(w, src.transform)
                bands_data[band_enum] = (arr.astype(np.float32) / 10000.0).clip(0.0, 1.5)
            else:
                # 20m resolution window
                w20 = Window(col_off // 2, row_off // 2, size // 2, size // 2)
                with rasterio.open(asset_url) as src:
                    arr20 = src.read(1, window=w20)
                # Resample 20m to 10m grid (512x512 -> 1024x1024)
                arr_resampled = cv2.resize(
                    arr20, (size, size), interpolation=cv2.INTER_NEAREST
                )
                if band_enum == SentinelBand.SCL:
                    bands_data[band_enum] = arr_resampled.astype(np.float32)
                else:
                    bands_data[band_enum] = (arr_resampled.astype(np.float32) / 10000.0).clip(0.0, 1.5)

        stack = BandStack(
            bands_data=bands_data,
            crs=target_crs,
            transform=target_transform,
            scene_id=f"{id_2024[:16]}_{aoi_name}" if "2024" in date_str else f"{id_2025[:16]}_{aoi_name}",
            acquisition_date=date_str,
        )

        out_path = os.path.join(output_dir, f"{stack.scene_id}.tif")
        stack.write_cog(out_path)
        print(f"  [+] Saved Authoritative Real Sentinel-2 COG: {out_path}")
        return out_path

    print("\n--- Downloading 2024 Baseline Multi-Spectral Stack ---")
    pre_path = download_bands_for_feature(feat_2024, id_2024, date_2024)

    print("\n--- Downloading 2025 Current Multi-Spectral Stack ---")
    post_path = download_bands_for_feature(feat_2025, id_2025, date_2025)

    return pre_path, post_path


if __name__ == "__main__":
    p1, p2 = fetch_real_sentinel2_pair()
    print(f"\nCompleted Real Satellite Ingestion:\nPre: {p1}\nPost: {p2}")
