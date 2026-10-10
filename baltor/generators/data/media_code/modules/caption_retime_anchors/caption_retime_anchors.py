"""Fix caption drift with a linear time map from two anchor points.

When captions start in sync and drift steadily (a different frame rate, a
different cut with a fixed offset, or speech sped up uniformly), mapping
``t' = a * t + b`` fixes every cue. Give two anchors (caption time, true
time) near the start and end and the map is solved exactly; give more and it
is fitted by least squares with a residual report.

Usage::

    from caption_retime_anchors import fit, apply, fps_factor
    m = fit([(10.0, 10.4), (300.0, 312.9)])
    fixed = apply(cues, m)
    fps_factor(25, 24000/1001)    # scale for captions timed at 25 fps played at 23.976
"""

from __future__ import annotations


def fit(anchors: list[tuple[float, float]]) -> dict:
    if len(anchors) < 2:
        raise ValueError("need at least two anchors")
    n = len(anchors)
    sx = sum(a for a, _ in anchors)
    sy = sum(b for _, b in anchors)
    sxx = sum(a * a for a, _ in anchors)
    sxy = sum(a * b for a, b in anchors)
    den = n * sxx - sx * sx
    if abs(den) < 1e-12:
        raise ValueError("anchors must be at different times")
    a = (n * sxy - sx * sy) / den
    b = (sy - a * sx) / n
    residuals = [b_ - (a * a_ + b) for a_, b_ in anchors]
    return {"scale": a, "offset": b, "max_residual_s": max(abs(r) for r in residuals)}


def map_time(t: float, m: dict) -> float:
    return max(0.0, m["scale"] * t + m["offset"])


def apply(cues: list[dict], m: dict) -> list[dict]:
    return [{**c, "start": round(map_time(c["start"], m), 3), "end": round(map_time(c["end"], m), 3)} for c in cues]


def shift(cues: list[dict], seconds: float) -> list[dict]:
    return apply(cues, {"scale": 1.0, "offset": seconds})


def fps_factor(timed_at_fps: float, played_at_fps: float) -> float:
    """Scale for cues counted in frames at one rate but played at another."""
    if timed_at_fps <= 0 or played_at_fps <= 0:
        raise ValueError("fps must be > 0")
    return timed_at_fps / played_at_fps
