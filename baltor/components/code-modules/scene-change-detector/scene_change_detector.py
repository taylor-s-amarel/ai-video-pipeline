"""Detect hard cuts in a video from colour-histogram changes (numpy).

For each frame, a soft-binned 3-channel histogram (``bins`` per channel) is
compared with the previous frame using half the L1 distance (0 = same,
1 = disjoint). A cut is reported where the distance exceeds both an absolute
``threshold`` and ``k`` times the local median (so steady motion and slow
fades do not trigger), with a minimum gap between cuts.

Use it to find shot boundaries in source footage, check that a render has
the planned number of cuts, or measure average shot length (pacing).

Usage::

    from scene_change_detector import detect, shot_lengths
    cuts = detect(frames_rgb, fps=30)          # frames: (N, H, W, 3) uint8
    shot_lengths(cuts, total_frames=len(frames_rgb), fps=30)
"""

from __future__ import annotations

import numpy as np


def histogram(frame: np.ndarray, bins: int = 16) -> np.ndarray:
    """Soft-binned (linear interpolation) per-channel histogram, normalised to sum 1.

    Soft binning makes the distance change smoothly as colours drift, so a
    slow fade never jumps a whole bin at once.
    """
    f = frame if frame.ndim == 3 else frame[..., None]
    hs = []
    for c in range(f.shape[2]):
        pos = f[..., c].astype(np.float64).ravel() * bins / 256.0 - 0.5
        lo = np.floor(pos)
        w_hi = pos - lo
        lo_i = np.clip(lo, 0, bins - 1).astype(np.int64)
        hi_i = np.clip(lo + 1, 0, bins - 1).astype(np.int64)
        h = np.bincount(lo_i, weights=1 - w_hi, minlength=bins) + np.bincount(hi_i, weights=w_hi, minlength=bins)
        hs.append(h)
    h = np.concatenate(hs)
    return h / h.sum()


def distances(frames, bins: int = 16) -> np.ndarray:
    prev = None
    out = []
    for fr in frames:
        h = histogram(fr, bins)
        if prev is not None:
            out.append(0.5 * np.abs(h - prev).sum())
        prev = h
    return np.array(out)


def detect(frames, fps: float = 30, threshold: float = 0.35, k: float = 3.0, window: int = 15,
           min_gap_s: float = 0.25, bins: int = 16) -> list[dict]:
    d = distances(frames, bins)
    cuts = []
    last = -10 ** 9
    for i, v in enumerate(d):
        lo, hi = max(0, i - window), min(len(d), i + window + 1)
        neigh = np.delete(d[lo:hi], i - lo)
        med = float(np.median(neigh)) if len(neigh) else 0.0
        frame_idx = i + 1
        if v > threshold and v > k * med and (frame_idx - last) / fps >= min_gap_s:
            cuts.append({"frame": frame_idx, "time_s": round(frame_idx / fps, 4), "score": round(float(v), 4)})
            last = frame_idx
    return cuts


def shot_lengths(cuts: list[dict], total_frames: int, fps: float) -> dict:
    bounds = [0] + [c["frame"] for c in cuts] + [total_frames]
    lengths = [(b - a) / fps for a, b in zip(bounds, bounds[1:]) if b > a]
    return {"shots": len(lengths), "mean_s": round(float(np.mean(lengths)), 3),
            "min_s": round(min(lengths), 3), "max_s": round(max(lengths), 3), "lengths_s": [round(x, 3) for x in lengths]}
