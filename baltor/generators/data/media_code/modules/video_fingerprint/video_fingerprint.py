"""Video fingerprints: detect when an "new" render is really an old one.

Samples frames at fixed times (fractions of the duration), computes a 64-bit
difference hash for each, and compares fingerprints frame by frame. Two
videos match when most sampled hashes are within a few bits, which survives
re-encoding, resizing and small overlays. Use it before delivery to avoid
resending an earlier video as new work.

Usage::

    from video_fingerprint import fingerprint_video, similarity
    a = fingerprint_video("door_v1.mp4")
    b = fingerprint_video("new_upload.mp4")
    similarity(a, b)     # {'same_video': True, 'matched_fraction': 0.94, ...}
"""

from __future__ import annotations

import json
import subprocess

import numpy as np

SAMPLE_POINTS = tuple(round(0.05 + 0.9 * i / 15, 4) for i in range(16))


def dhash_gray(gray: np.ndarray) -> int:
    """dHash of a grayscale frame (resized by block averaging to 9x8)."""
    g = gray.astype(np.float64)
    H, W = g.shape
    ys = np.linspace(0, H, 9).astype(int)
    xs = np.linspace(0, W, 10).astype(int)
    small = np.array([[g[ys[r]:ys[r + 1], xs[c]:xs[c + 1]].mean() for c in range(9)] for r in range(8)])
    bits = (small[:, 1:] > small[:, :-1]).ravel()
    v = 0
    for b in bits:
        v = (v << 1) | int(b)
    return v


def fingerprint_frames(frames: list[np.ndarray]) -> list[int]:
    return [dhash_gray(f if f.ndim == 2 else f.mean(axis=2)) for f in frames]


def _duration(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def fingerprint_video(path: str, points=SAMPLE_POINTS, width: int = 72, height: int = 64) -> dict:
    dur = _duration(path)
    hashes = []
    for p in points:
        raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{p * dur:.3f}", "-i", path, "-frames:v", "1",
                              "-vf", f"scale={width}:{height},format=gray", "-f", "rawvideo", "-"],
                             capture_output=True, check=True).stdout
        if len(raw) < width * height:
            continue
        hashes.append(dhash_gray(np.frombuffer(raw[:width * height], np.uint8).reshape(height, width)))
    return {"duration": round(dur, 3), "points": list(points)[:len(hashes)], "hashes": [f"{h:016x}" for h in hashes]}


def similarity(a: dict, b: dict, max_bits: int = 10, duration_tolerance: float = 0.05, min_fraction: float = 0.8) -> dict:
    ha = [int(h, 16) for h in a["hashes"]]
    hb = [int(h, 16) for h in b["hashes"]]
    n = min(len(ha), len(hb))
    if n == 0:
        raise ValueError("empty fingerprint")
    dists = [bin(x ^ y).count("1") for x, y in zip(ha[:n], hb[:n])]
    matched = sum(1 for d in dists if d <= max_bits) / n
    dur_ok = abs(a["duration"] - b["duration"]) <= duration_tolerance * max(a["duration"], b["duration"])
    return {"same_video": matched >= min_fraction and dur_ok, "matched_fraction": round(matched, 3),
            "mean_bits": round(float(np.mean(dists)), 2), "duration_match": dur_ok}
