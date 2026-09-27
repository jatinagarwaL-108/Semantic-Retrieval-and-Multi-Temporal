"""
Co-Registration Verification Module
Performs sub-pixel cross-correlation shift check between bitemporal tiles.
Flags misaligned pairs to prevent false change detections caused by spatial shifts.
"""

from typing import Dict, Any, Tuple
import numpy as np
from scipy import signal
from .band_stack import BandStack, SentinelBand


class CoRegistrationChecker:
    """
    Evaluates spatial co-registration between pre- and post-event Sentinel-2 tiles.
    Uses Phase Correlation / Normalized Cross-Correlation on the high-contrast NIR band.
    """

    def __init__(self, max_allowed_shift_pixels: float = 1.0, min_correlation: float = 0.50):
        self.max_allowed_shift_pixels = max_allowed_shift_pixels
        self.min_correlation = min_correlation

    def check_alignment(
        self, pre_stack: BandStack, post_stack: BandStack, search_window_size: int = 128
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Computes 2D cross-correlation on central window of NIR (B08) band.
        Returns:
            is_aligned: boolean indicating if registration is within safe tolerance
            report: detailed shift metrics and diagnostic flags
        """
        # Use NIR band for feature alignment (sharpest geographical boundaries)
        b_pre = pre_stack.get_reflectance_float32(SentinelBand.B08)
        b_post = post_stack.get_reflectance_float32(SentinelBand.B08)

        h, w = b_pre.shape
        cy, cx = h // 2, w // 2
        half_win = min(search_window_size // 2, cy, cx)

        # Extract central chips
        patch_pre = b_pre[cy - half_win : cy + half_win, cx - half_win : cx + half_win]
        patch_post = b_post[cy - half_win : cy + half_win, cx - half_win : cx + half_win]

        # Subtract local means
        patch_pre_norm = patch_pre - np.mean(patch_pre)
        patch_post_norm = patch_post - np.mean(patch_post)
        std_pre = np.std(patch_pre) + 1e-6
        std_post = np.std(patch_post) + 1e-6

        # Normalized cross correlation via FFT
        corr = signal.correlate2d(
            patch_post_norm / std_post, patch_pre_norm / std_pre, mode="same", boundary="symm"
        )
        corr /= patch_pre.size

        # Find peak
        max_idx = np.unravel_index(np.argmax(corr), corr.shape)
        center_y = (corr.shape[0] - 1) // 2
        center_x = (corr.shape[1] - 1) // 2

        shift_y = float(max_idx[0] - center_y)
        shift_x = float(max_idx[1] - center_x)
        total_shift = float(np.sqrt(shift_x**2 + shift_y**2))
        peak_corr = float(corr[max_idx])

        # Sub-pixel parabolic refinement if peak not on boundary
        if (
            0 < max_idx[0] < corr.shape[0] - 1
            and 0 < max_idx[1] < corr.shape[1] - 1
        ):
            dy = (corr[max_idx[0] + 1, max_idx[1]] - corr[max_idx[0] - 1, max_idx[1]]) / (
                2 * (2 * corr[max_idx] - corr[max_idx[0] + 1, max_idx[1]] - corr[max_idx[0] - 1, max_idx[1]] + 1e-6)
            )
            dx = (corr[max_idx[0], max_idx[1] + 1] - corr[max_idx[0], max_idx[1] - 1]) / (
                2 * (2 * corr[max_idx] - corr[max_idx[0], max_idx[1] + 1] - corr[max_idx[0], max_idx[1] - 1] + 1e-6)
            )
            shift_y += float(dy)
            shift_x += float(dx)
            total_shift = float(np.sqrt(shift_x**2 + shift_y**2))

        is_aligned = bool(
            total_shift <= self.max_allowed_shift_pixels and peak_corr >= self.min_correlation
        )

        report = {
            "shift_x_pixels": round(shift_x, 3),
            "shift_y_pixels": round(shift_y, 3),
            "total_shift_pixels": round(total_shift, 3),
            "peak_correlation": round(peak_corr, 4),
            "max_allowed_shift_pixels": self.max_allowed_shift_pixels,
            "min_correlation_threshold": self.min_correlation,
            "is_aligned": is_aligned,
            "status": "ALIGNED" if is_aligned else "MISALIGNED_WARNING",
            "warning": None if is_aligned else f"Tile pair misregistered by {total_shift:.2f} px (> {self.max_allowed_shift_pixels} px threshold)",
        }

        return is_aligned, report
