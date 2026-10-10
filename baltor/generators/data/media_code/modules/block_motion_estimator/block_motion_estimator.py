"""Estimate global camera motion between two frames by block matching (numpy).

Splits the previous frame into blocks, finds each block's best match in the
next frame within a search range (sum of absolute differences), and takes
the median motion vector as the global pan. Useful to verify that a Ken
Burns pan actually moves the intended direction, to measure background
drift, or to estimate shake for stabilisation.

Usage::

    from block_motion_estimator import block_vectors, global_motion
    dx, dy, confidence = global_motion(prev_gray, next_gray, block=16, search=8)
"""

from __future__ import annotations

import numpy as np


def block_vectors(prev: np.ndarray, nxt: np.ndarray, block: int = 16, search: int = 8,
                  min_texture: float = 4.0) -> list[tuple[int, int, int, int]]:
    """(x, y, dx, dy) for each textured block; dx/dy move content from prev to nxt."""
    if prev.shape != nxt.shape or prev.ndim != 2:
        raise ValueError("expected two grayscale frames of the same shape")
    a, b = prev.astype(np.int32), nxt.astype(np.int32)
    H, W = a.shape
    out = []
    for y in range(search, H - block - search + 1, block):
        for x in range(search, W - block - search + 1, block):
            ref = a[y:y + block, x:x + block]
            if ref.std() < min_texture:
                continue  # flat blocks give unreliable matches
            best, best_v = None, (0, 0)
            for dy in range(-search, search + 1):
                for dx in range(-search, search + 1):
                    cand = b[y + dy:y + dy + block, x + dx:x + dx + block]
                    sad = int(np.abs(cand - ref).sum())
                    if best is None or sad < best or (sad == best and abs(dx) + abs(dy) < abs(best_v[0]) + abs(best_v[1])):
                        best, best_v = sad, (dx, dy)
            out.append((x, y, best_v[0], best_v[1]))
    return out


def global_motion(prev: np.ndarray, nxt: np.ndarray, **kw) -> tuple[float, float, float]:
    vecs = block_vectors(prev, nxt, **kw)
    if not vecs:
        return 0.0, 0.0, 0.0
    dxs = np.array([v[2] for v in vecs])
    dys = np.array([v[3] for v in vecs])
    mdx, mdy = float(np.median(dxs)), float(np.median(dys))
    agree = float(np.mean((np.abs(dxs - mdx) <= 1) & (np.abs(dys - mdy) <= 1)))
    return mdx, mdy, round(agree, 3)


def describe(dx: float, dy: float, dead_zone: float = 0.5) -> str:
    parts = []
    if dx > dead_zone:
        parts.append("content moves right (camera pans left)")
    elif dx < -dead_zone:
        parts.append("content moves left (camera pans right)")
    if dy > dead_zone:
        parts.append("content moves down (camera tilts up)")
    elif dy < -dead_zone:
        parts.append("content moves up (camera tilts down)")
    return "; ".join(parts) or "static"
