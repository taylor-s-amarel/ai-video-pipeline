"""Screen video for flashing that may exceed the WCAG general flash threshold.

WCAG 2.x defines a general flash as a pair of opposing changes in relative
luminance of 10% or more of maximum relative luminance where the darker
image is below 0.80; content should not flash more than three times in any
one-second period (Success Criterion 2.3.1). The threshold also involves
the flashing area (a 341 x 256 pixel block on a 1024 x 768 screen stands in
for 10 degrees of visual field).

This screen approximates that by tracking mean relative luminance per tile
(tiles sized to about that visual-field fraction), counting flashes per
tile, and reporting any one-second window with more than three. It is a
screening heuristic for catching problems early, not a certified analysis
(dedicated tools exist for compliance testing).

Usage::

    from flash_risk_screen import screen_frames
    report = screen_frames(frames_rgb, fps=30)   # {'risk': bool, 'max_flashes_per_s': 4, 'windows': [...]}
"""

from __future__ import annotations

import numpy as np


def relative_luminance(rgb: np.ndarray) -> np.ndarray:
    c = rgb.astype(np.float64) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722


def tile_series(frames: np.ndarray, tiles=(3, 3)) -> np.ndarray:
    """(T, tiles_y * tiles_x) mean relative luminance per tile."""
    lum = np.stack([relative_luminance(f) for f in frames])
    T, H, W = lum.shape
    ty, tx = tiles
    hs, ws = H // ty, W // tx
    cropped = lum[:, :hs * ty, :ws * tx].reshape(T, ty, hs, tx, ws)
    return cropped.mean(axis=(2, 4)).reshape(T, ty * tx)


def transitions(series: np.ndarray, min_change: float = 0.10, darker_below: float = 0.80) -> list[int]:
    """Frame indices of qualifying luminance transitions (hysteresis on ``min_change``).

    A transition qualifies when it changes by at least ``min_change`` and the darker of
    its two states is below ``darker_below``. Two opposing transitions make one flash.
    """
    out: list[int] = []
    ext = float(series[0])
    lo = hi = ext
    trend = 0
    for i in range(1, len(series)):
        v = float(series[i])
        if trend == 0:
            lo, hi = min(lo, v), max(hi, v)
            if v - lo >= min_change:
                trend, ext = 1, v
                if lo < darker_below:
                    out.append(i)
            elif hi - v >= min_change:
                trend, ext = -1, v
                if v < darker_below:
                    out.append(i)
        elif trend == 1:
            if v > ext:
                ext = v
            elif ext - v >= min_change:
                if v < darker_below:
                    out.append(i)
                trend, ext = -1, v
        else:
            if v < ext:
                ext = v
            elif v - ext >= min_change:
                if ext < darker_below:
                    out.append(i)
                trend, ext = 1, v
    return out


def flash_events(series: np.ndarray, min_change: float = 0.10, darker_below: float = 0.80) -> list[int]:
    """Frame indices where a flash (a pair of opposing qualifying transitions) completes."""
    tr = transitions(series, min_change, darker_below)
    return tr[1::2]


def screen_frames(frames: np.ndarray, fps: float, tiles=(3, 3), max_flashes: int = 3) -> dict:
    series = tile_series(frames, tiles)
    window = max(1, int(round(fps)))
    worst = 0.0
    windows = []
    for t in range(series.shape[1]):
        tr = transitions(series[:, t])
        for i, e in enumerate(tr):
            n_tr = sum(1 for x in tr[i:] if x - e < window)
            flashes = n_tr / 2
            worst = max(worst, flashes)
            if flashes > max_flashes:
                windows.append({"tile": t, "start_s": round(e / fps, 3), "flashes": flashes})
    return {"risk": worst > max_flashes, "max_flashes_per_s": worst, "windows": windows}
