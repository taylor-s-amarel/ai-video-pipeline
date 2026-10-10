"""Amplitude-driven mouth animation for narrated characters (numpy).

When phoneme timing is not available, mouth openness can follow the speech
loudness. ``mouth_openness`` computes a per-video-frame RMS envelope, gates
out the noise floor, normalises against a high percentile and smooths with
separate attack and release times. ``mouth_shapes`` quantises openness to
Rhubarb-style shape letters (X rest, B small, C medium, D wide). Opening
from rest is immediate; every open shape is held at least ``min_hold_s`` so
the mouth does not flicker.

Usage::

    from amplitude_lip_sync import mouth_openness, mouth_shapes
    open_ = mouth_openness(samples, sample_rate=24000, fps=30)
    shapes = mouth_shapes(open_, fps=30)       # ['X', 'B', 'C', ...] one per frame
"""

from __future__ import annotations

import math

import numpy as np


def frame_rms(samples: np.ndarray, sample_rate: int, fps: float) -> np.ndarray:
    x = np.asarray(samples, dtype=np.float64)
    if x.ndim == 2:
        x = x.mean(axis=1)
    hop = sample_rate / fps
    n = int(math.ceil(len(x) / hop))
    out = np.zeros(n)
    for i in range(n):
        a, b = int(round(i * hop)), int(round((i + 1) * hop))
        seg = x[a:b]
        out[i] = math.sqrt(float(np.mean(seg * seg))) if len(seg) else 0.0
    return out


def mouth_openness(samples, sample_rate: int, fps: float = 30, gate_db: float = -45.0,
                   percentile: float = 95.0, attack_s: float = 0.03, release_s: float = 0.09) -> np.ndarray:
    rms = frame_rms(samples, sample_rate, fps)
    db = 20 * np.log10(np.maximum(rms, 1e-12))
    ref = np.percentile(db[db > gate_db], percentile) if np.any(db > gate_db) else 0.0
    norm = np.clip((db - gate_db) / max(1e-6, ref - gate_db), 0.0, 1.0)
    norm[db <= gate_db] = 0.0
    a_coef = 1 - math.exp(-1.0 / (attack_s * fps)) if attack_s > 0 else 1.0
    r_coef = 1 - math.exp(-1.0 / (release_s * fps)) if release_s > 0 else 1.0
    out = np.zeros_like(norm)
    level = 0.0
    for i, v in enumerate(norm):
        level += (v - level) * (a_coef if v > level else r_coef)
        out[i] = level
    return out


def mouth_shapes(openness, fps: float = 30, thresholds=(0.12, 0.4, 0.7), letters=("X", "B", "C", "D"),
                 min_hold_s: float = 0.06) -> list[str]:
    if len(letters) != len(thresholds) + 1:
        raise ValueError("need one more letter than thresholds")
    raw = [letters[int(np.searchsorted(thresholds, v, side="right"))] for v in openness]
    hold = max(1, int(round(min_hold_s * fps)))
    rest = letters[0]
    out: list[str] = []
    run = 0
    for s in raw:
        # opening from rest is immediate; any other shape is held at least ``hold`` frames
        if out and s != out[-1] and out[-1] != rest and run < hold:
            out.append(out[-1])
            run += 1
        elif out and s == out[-1]:
            out.append(s)
            run += 1
        else:
            out.append(s)
            run = 1
    return out


def cues(shapes: list[str], fps: float) -> list[tuple[float, str]]:
    """Collapse per-frame letters into (start_time, letter) changes."""
    out = []
    for i, s in enumerate(shapes):
        if not out or out[-1][1] != s:
            out.append((round(i / fps, 6), s))
    return out
