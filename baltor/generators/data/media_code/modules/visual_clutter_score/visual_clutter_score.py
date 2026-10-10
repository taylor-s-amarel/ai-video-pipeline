"""Measure how busy a frame looks, to catch "too much useless, busy text".

Two cheap, explainable measures on a grayscale frame:

* edge density: share of pixels whose gradient magnitude exceeds a threshold
  (text, thin lines and texture all raise it);
* local contrast variance: mean of per-tile standard deviations.

``clutter_score`` combines them into 0-100 (higher = busier) and
``compare`` reports how much an overlay (captions, labels, stickers) adds on
top of the clean background. Thresholds for "too busy" should be calibrated
on frames you have approved; ``calibrate`` derives a limit from them.

Usage::

    from visual_clutter_score import clutter_score, compare, calibrate
    clutter_score(frame_gray)
    compare(background_gray, composited_gray)    # {'base': 22.1, 'with_overlays': 41.7, 'added': 19.6}
"""

from __future__ import annotations

import numpy as np


def _gray(img: np.ndarray) -> np.ndarray:
    a = np.asarray(img, dtype=np.float32)
    if a.ndim == 3:
        a = a[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    return a


def edge_density(img: np.ndarray, threshold: float = 40.0) -> float:
    g = _gray(img)
    gy, gx = np.gradient(g)
    return float((np.hypot(gx, gy) > threshold).mean())


def tile_contrast(img: np.ndarray, tile: int = 32) -> float:
    g = _gray(img)
    h, w = (g.shape[0] // tile) * tile, (g.shape[1] // tile) * tile
    if h == 0 or w == 0:
        return float(g.std())
    t = g[:h, :w].reshape(h // tile, tile, w // tile, tile)
    return float(t.std(axis=(1, 3)).mean())


def clutter_score(img: np.ndarray, edge_threshold: float = 40.0, tile: int = 32) -> float:
    e = edge_density(img, edge_threshold)          # 0..1, typical 0.01-0.3
    c = tile_contrast(img, tile) / 128.0            # 0..~1
    return round(100.0 * min(1.0, 0.7 * min(1.0, e / 0.3) + 0.3 * min(1.0, c)), 2)


def compare(base: np.ndarray, composited: np.ndarray, **kw) -> dict:
    b, c = clutter_score(base, **kw), clutter_score(composited, **kw)
    return {"base": b, "with_overlays": c, "added": round(c - b, 2)}


def calibrate(approved_scores: list[float], margin: float = 5.0) -> float:
    """A 'too busy' limit: the 90th percentile of approved frames plus a margin."""
    if not approved_scores:
        raise ValueError("need scores from approved frames")
    return round(float(np.percentile(approved_scores, 90)) + margin, 2)
