"""Pick a crop window that keeps the interesting part of a frame (numpy).

Saliency here is a simple, dependency-free score: gradient magnitude (edges
and texture) plus colour distinctness (distance from the frame's mean
colour), blurred a little. ``best_window`` slides a window of the target
aspect over the saliency map using an integral image and returns the window
with the most saliency, with a mild preference for the centre. For video,
``track`` smooths the window centre over time so the virtual camera does not
jitter.

Usage::

    from saliency_crop_window import saliency, best_window, track
    x, y, w, h = best_window(frame_rgb, aspect=9 / 16)
    centres = track([best_window(f, 9 / 16) for f in frames], smoothing=0.85)
"""

from __future__ import annotations

import numpy as np


def _box_blur(a: np.ndarray, r: int) -> np.ndarray:
    if r <= 0:
        return a
    k = 2 * r + 1
    p = np.pad(a, r, mode="edge")
    c = p.cumsum(0)
    c = np.vstack([np.zeros((1, c.shape[1])), c])
    v = (c[k:] - c[:-k]) / k
    c = v.cumsum(1)
    c = np.hstack([np.zeros((c.shape[0], 1)), c])
    return (c[:, k:] - c[:, :-k]) / k


def saliency(frame: np.ndarray, blur: int = 2) -> np.ndarray:
    f = frame.astype(np.float64)
    gray = f.mean(axis=2) if f.ndim == 3 else f
    gy, gx = np.gradient(gray)
    grad = np.hypot(gx, gy)
    if f.ndim == 3:
        mean = f.reshape(-1, f.shape[2]).mean(axis=0)
        distinct = np.linalg.norm(f - mean, axis=2)
    else:
        distinct = np.abs(gray - gray.mean())
    s = grad / (grad.max() + 1e-9) + distinct / (distinct.max() + 1e-9)
    return _box_blur(s, blur)


def best_window(frame: np.ndarray, aspect: float, scale: float = 1.0, center_bias: float = 0.15,
                step: int = 2) -> tuple[int, int, int, int]:
    H, W = frame.shape[:2]
    if W / H > aspect:
        h = int(H * scale)
        w = int(round(h * aspect))
    else:
        w = int(W * scale)
        h = int(round(w / aspect))
    w, h = min(w, W), min(h, H)
    s = saliency(frame)
    ii = np.pad(s.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    best, best_score = (0, 0), -1.0
    total = ii[-1, -1] + 1e-9
    for y in range(0, H - h + 1, step):
        for x in range(0, W - w + 1, step):
            score = (ii[y + h, x + w] - ii[y, x + w] - ii[y + h, x] + ii[y, x]) / total
            cx, cy = (x + w / 2) / W - 0.5, (y + h / 2) / H - 0.5
            score -= center_bias * (cx * cx + cy * cy)
            if score > best_score:
                best, best_score = (x, y), score
    return best[0], best[1], w, h


def track(windows: list[tuple], smoothing: float = 0.85, max_step: float | None = None) -> list[tuple]:
    """Exponentially smooth window positions (same size) over time; optional max pixels per frame."""
    if not 0 <= smoothing < 1:
        raise ValueError("smoothing must be within [0, 1)")
    out = []
    sx, sy = float(windows[0][0]), float(windows[0][1])
    for x, y, w, h in windows:
        nx = smoothing * sx + (1 - smoothing) * x
        ny = smoothing * sy + (1 - smoothing) * y
        if max_step is not None:
            nx = sx + max(-max_step, min(max_step, nx - sx))
            ny = sy + max(-max_step, min(max_step, ny - sy))
        sx, sy = nx, ny
        out.append((int(round(sx)), int(round(sy)), w, h))
    return out
