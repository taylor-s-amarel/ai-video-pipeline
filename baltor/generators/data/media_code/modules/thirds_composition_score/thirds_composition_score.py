"""Score subject placement against rule-of-thirds and centre composition.

Given the subject's centre (from a face/subject detector or the saliency
crop module) in normalised coordinates, reports the distance to the nearest
thirds intersection and to the centre, a 0-1 score for each, and the crop
offset that would move the subject onto the best point while keeping a crop
window inside the image.

Usage::

    from thirds_composition_score import score, reposition_crop
    score((0.62, 0.41))      # {'thirds': 0.9..., 'centre': ..., 'nearest_point': (0.667, 0.333)}
    reposition_crop(subject=(1400, 900), image=(4000, 3000), crop=(1688, 3000), target=(1/3, 1/3))
"""

from __future__ import annotations

import math

THIRDS = [(x, y) for x in (1 / 3, 2 / 3) for y in (1 / 3, 2 / 3)]


def score(subject, falloff: float = 0.25) -> dict:
    sx, sy = subject
    if not (0 <= sx <= 1 and 0 <= sy <= 1):
        raise ValueError("subject must be in normalised [0, 1] coordinates")
    d_pts = [(math.dist((sx, sy), p), p) for p in THIRDS]
    d, p = min(d_pts)
    dc = math.dist((sx, sy), (0.5, 0.5))
    return {"thirds": round(max(0.0, 1 - d / falloff), 4), "centre": round(max(0.0, 1 - dc / falloff), 4),
            "nearest_point": (round(p[0], 4), round(p[1], 4)), "distance": round(d, 4)}


def reposition_crop(subject, image, crop, target=(0.5, 1 / 3)) -> tuple[float, float]:
    """Top-left (x, y) of a ``crop`` (w, h) window that puts ``subject`` (px) at ``target`` (fraction), clamped."""
    (px, py), (iw, ih), (cw, ch) = subject, image, crop
    if cw > iw or ch > ih:
        raise ValueError("crop is larger than the image")
    x = min(max(px - target[0] * cw, 0.0), iw - cw)
    y = min(max(py - target[1] * ch, 0.0), ih - ch)
    return x, y


def achieved_position(subject, crop_xy, crop) -> tuple[float, float]:
    return (subject[0] - crop_xy[0]) / crop[0], (subject[1] - crop_xy[1]) / crop[1]
