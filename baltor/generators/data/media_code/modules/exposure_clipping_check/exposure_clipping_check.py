"""Exposure checks for frames and photos: clipping, mean level, dynamic range.

Reports the share of pixels crushed to black or clipped to white (per channel
and in luma), mean and median luma, the 1st-99th percentile spread, and
simple flags: too dark, too bright, clipped highlights, crushed shadows, low
contrast. Thresholds are parameters with conservative defaults.

Usage::

    from exposure_clipping_check import analyse
    report = analyse(np.asarray(Image.open("photo.jpg").convert("RGB")))
    report["flags"]     # e.g. ['clipped_highlights']
"""

from __future__ import annotations

import numpy as np


def analyse(rgb: np.ndarray, black: int = 4, white: int = 251, max_clip: float = 0.02, dark_mean: float = 50.0,
            bright_mean: float = 205.0, min_spread: float = 60.0) -> dict:
    a = np.asarray(rgb)
    if a.ndim == 2:
        a = np.stack([a] * 3, -1)
    a = a[..., :3].astype(np.float64)
    luma = a @ np.array([0.2126, 0.7152, 0.0722])
    clipped = float((a >= white).any(axis=2).mean())
    crushed = float((a <= black).all(axis=2).mean())
    p1, p50, p99 = np.percentile(luma, [1, 50, 99])
    report = {
        "mean_luma": round(float(luma.mean()), 2), "median_luma": round(float(p50), 2),
        "p1": round(float(p1), 2), "p99": round(float(p99), 2), "spread": round(float(p99 - p1), 2),
        "clipped_fraction": round(clipped, 5), "crushed_fraction": round(crushed, 5),
        "channel_clipped": [round(float((a[..., c] >= white).mean()), 5) for c in range(3)],
    }
    flags = []
    if clipped > max_clip:
        flags.append("clipped_highlights")
    if crushed > max_clip:
        flags.append("crushed_shadows")
    if luma.mean() < dark_mean:
        flags.append("too_dark")
    if luma.mean() > bright_mean:
        flags.append("too_bright")
    if p99 - p1 < min_spread:
        flags.append("low_contrast")
    report["flags"] = flags
    return report
