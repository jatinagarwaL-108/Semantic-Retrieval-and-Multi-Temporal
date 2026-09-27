"""
Sentinel-2 Multi-Band Stack Manager
Maintains strict scientific integrity: multi-band BOA surface reflectance (B02, B03, B04, B08, B11, B12, SCL).
No early conversion or quantization to 8-bit RGB.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.enums import Resampling
import os


class SentinelBand(str, Enum):
    B02 = "B02"  # Blue (490 nm) - 10m
    B03 = "B03"  # Green (560 nm) - 10m
    B04 = "B04"  # Red (665 nm) - 10m
    B08 = "B08"  # NIR (842 nm) - 10m
    B11 = "B11"  # SWIR-1 (1610 nm) - 20m
    B12 = "B12"  # SWIR-2 (2190 nm) - 20m
    SCL = "SCL"  # Scene Classification Layer - 20m


STANDARD_BAND_ORDER = [
    SentinelBand.B02,
    SentinelBand.B03,
    SentinelBand.B04,
    SentinelBand.B08,
    SentinelBand.B11,
    SentinelBand.B12,
    SentinelBand.SCL,
]

BAND_DESCRIPTIONS = {
    SentinelBand.B02: "Blue (490nm, 10m)",
    SentinelBand.B03: "Green (560nm, 10m)",
    SentinelBand.B04: "Red (665nm, 10m)",
    SentinelBand.B08: "NIR (842nm, 10m)",
    SentinelBand.B11: "SWIR-1 (1610nm, 20m->10m)",
    SentinelBand.B12: "SWIR-2 (2190nm, 20m->10m)",
    SentinelBand.SCL: "Scene Classification Layer",
}


class BandStack:
    """
    Encapsulates a multi-spectral Sentinel-2 tile/scene stack.
    Maintains raw reflectance values (float32 [0.0, 1.0] surface reflectance
    or uint16 digital numbers with DN/10000 scaling).
    """

    def __init__(
        self,
        bands_data: Dict[Union[SentinelBand, str], np.ndarray],
        crs: Union[str, rasterio.crs.CRS],
        transform: Affine,
        nodata: Optional[float] = None,
        scene_id: str = "unknown_scene",
        acquisition_date: str = "2026-01-01",
    ):
        self.bands_data: Dict[SentinelBand, np.ndarray] = {}
        for k, v in bands_data.items():
            band_enum = SentinelBand(k) if isinstance(k, str) else k
            self.bands_data[band_enum] = v

        self.crs = crs if isinstance(crs, rasterio.crs.CRS) else rasterio.crs.CRS.from_string(crs)
        self.transform = transform
        self.nodata = nodata
        self.scene_id = scene_id
        self.acquisition_date = acquisition_date

        # Verify shapes
        first_shape = next(iter(self.bands_data.values())).shape
        self.height, self.width = first_shape[0], first_shape[1]
        for b, arr in self.bands_data.items():
            if arr.shape != (self.height, self.width):
                raise ValueError(f"Band {b} shape {arr.shape} does not match {first_shape}")

    def get_band(self, band: Union[SentinelBand, str]) -> np.ndarray:
        band_enum = SentinelBand(band) if isinstance(band, str) else band
        if band_enum not in self.bands_data:
            raise KeyError(f"Band {band_enum.value} is not present in stack")
        return self.bands_data[band_enum]

    def get_reflectance_float32(self, band: Union[SentinelBand, str]) -> np.ndarray:
        """
        Returns surface reflectance scaled in [0.0, 1.0].
        If band is integer DN or unscaled float DN (e.g. 0-10000), converts to float32 [0.0, 1.0].
        For SCL, returns categorical integer class.
        """
        arr = self.get_band(band)
        if band == SentinelBand.SCL:
            return arr.astype(np.float32)
        if np.issubdtype(arr.dtype, np.integer) or np.nanmax(arr) > 10.0:
            # Sentinel-2 L2A scaling factor is 10000
            return np.clip(arr.astype(np.float32) / 10000.0, 0.0, 1.5)
        return arr.astype(np.float32)

    def get_subset_tensor(self, bands: List[Union[SentinelBand, str]]) -> np.ndarray:
        """
        Extracts multi-channel float32 array of shape (C, H, W).
        Used as direct input to multi-spectral ML models (e.g. BIT ChangeFormer).
        """
        arrays = [self.get_reflectance_float32(b) for b in bands]
        return np.stack(arrays, axis=0)

    def write_cog(self, output_path: str, band_order: Optional[List[SentinelBand]] = None) -> str:
        """
        Writes multi-band Cloud-Optimized GeoTIFF (COG).
        Retains all raw multi-spectral bands with block tiling and compression.
        Never collapses to 3-channel RGB.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if band_order is None:
            band_order = [b for b in STANDARD_BAND_ORDER if b in self.bands_data]

        count = len(band_order)
        profile = {
            "driver": "GTiff",
            "height": self.height,
            "width": self.width,
            "count": count,
            "dtype": np.float32,
            "crs": self.crs,
            "transform": self.transform,
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
            "compress": "deflate",
            "interleave": "pixel",
        }

        with rasterio.open(output_path, "w", **profile) as dst:
            for idx, b in enumerate(band_order, start=1):
                data = self.get_reflectance_float32(b)
                dst.write(data, idx)
                dst.set_band_description(idx, f"{b.value}: {BAND_DESCRIPTIONS.get(b, '')}")

            dst.update_tags(
                SCENE_ID=self.scene_id,
                ACQUISITION_DATE=self.acquisition_date,
                BANDS=",".join(b.value for b in band_order),
                PROCESSING_LEVEL="Sentinel-2 L2A BOA",
                AUTHORITATIVE="TRUE",
            )
        return output_path

    @classmethod
    def read_cog(cls, cog_path: str) -> "BandStack":
        """Reads a multi-band COG and reconstructs BandStack."""
        with rasterio.open(cog_path) as src:
            tags = src.tags()
            bands_str = tags.get("BANDS", "")
            if bands_str:
                band_names = [SentinelBand(b.strip()) for b in bands_str.split(",") if b.strip()]
            else:
                band_names = STANDARD_BAND_ORDER[:src.count]

            bands_data = {}
            for idx, band_enum in enumerate(band_names, start=1):
                bands_data[band_enum] = src.read(idx)

            return cls(
                bands_data=bands_data,
                crs=src.crs,
                transform=src.transform,
                nodata=src.nodata,
                scene_id=tags.get("SCENE_ID", os.path.basename(cog_path)),
                acquisition_date=tags.get("ACQUISITION_DATE", "unknown"),
            )
