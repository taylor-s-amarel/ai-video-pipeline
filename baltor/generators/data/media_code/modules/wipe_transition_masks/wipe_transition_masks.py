"""Alpha masks for wipe transitions (numpy), with soft edges.

Each mask function returns a float32 array (H, W) in [0, 1] for progress
``p`` in [0, 1]: 0 shows clip A everywhere, 1 shows clip B everywhere.
``softness`` is the edge width as a fraction of the frame diagonal.

Masks: ``linear`` (any angle), ``radial`` (circle opening from a point),
``clock`` (angular sweep), ``diamond`` and ``blinds`` (stripes).

Usage::

    import numpy as np
    from wipe_transition_masks import linear, blend
    m = linear(1920, 1080, p=0.4, angle_deg=30, softness=0.05)
    frame = blend(frame_a, frame_b, m)      # uint8 HxWx3 arrays
"""

from __future__ import annotations

import math

import numpy as np


def _grid(w: int, h: int):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    return (xs + 0.5) / w, (ys + 0.5) / h


def _ramp(field: np.ndarray, edge: float, soft: float) -> np.ndarray:
    if soft <= 0:
        return (field < edge).astype(np.float32)
    return np.clip((edge - field) / soft + 0.5, 0.0, 1.0).astype(np.float32)


def _endpoints(p: float, lo: float, hi: float, soft: float) -> float:
    # map progress so p=0 is fully A and p=1 fully B even with soft edges
    return lo - soft / 2 + (hi - lo + soft) * p


def linear(w: int, h: int, p: float, angle_deg: float = 0.0, softness: float = 0.03) -> np.ndarray:
    """Wipe travelling along ``angle_deg`` (0 = left to right, 90 = top to bottom)."""
    x, y = _grid(w, h)
    a = math.radians(angle_deg)
    aspect = w / h
    field = (x * aspect * math.cos(a) + y * math.sin(a))
    corners = [cx * aspect * math.cos(a) + cy * math.sin(a) for cx in (0, 1) for cy in (0, 1)]
    soft = softness * math.hypot(aspect, 1)
    return _ramp(field, _endpoints(p, min(corners), max(corners), soft), soft)


def radial(w: int, h: int, p: float, center=(0.5, 0.5), softness: float = 0.03) -> np.ndarray:
    x, y = _grid(w, h)
    aspect = w / h
    field = np.hypot((x - center[0]) * aspect, y - center[1])
    far = max(math.hypot((cx - center[0]) * aspect, cy - center[1]) for cx in (0, 1) for cy in (0, 1))
    soft = softness * math.hypot(aspect, 1)
    return _ramp(field, _endpoints(p, 0.0, far, soft), soft)


def clock(w: int, h: int, p: float, center=(0.5, 0.5), start_deg: float = -90.0, softness: float = 0.01) -> np.ndarray:
    x, y = _grid(w, h)
    ang = (np.degrees(np.arctan2(y - center[1], (x - center[0]) * w / h)) - start_deg) % 360.0
    field = ang / 360.0
    return _ramp(field, _endpoints(p, 0.0, 1.0, softness), softness)


def diamond(w: int, h: int, p: float, softness: float = 0.03) -> np.ndarray:
    x, y = _grid(w, h)
    field = np.abs(x - 0.5) + np.abs(y - 0.5)
    return _ramp(field, _endpoints(p, 0.0, 1.0, softness), softness)


def blinds(w: int, h: int, p: float, count: int = 8, vertical: bool = False, softness: float = 0.02) -> np.ndarray:
    x, y = _grid(w, h)
    coord = x if vertical else y
    field = (coord * count) % 1.0
    return _ramp(field, _endpoints(p, 0.0, 1.0, softness), softness)


def blend(a: np.ndarray, b: np.ndarray, mask: np.ndarray) -> np.ndarray:
    if a.shape != b.shape:
        raise ValueError("frames must have the same shape")
    m = mask[..., None] if a.ndim == 3 else mask
    out = a.astype(np.float32) * (1 - m) + b.astype(np.float32) * m
    return np.clip(out + 0.5, 0, 255).astype(np.uint8) if a.dtype == np.uint8 else out.astype(a.dtype)
