"""Volume-preserving squash and stretch from motion.

Stretch along the direction of travel in proportion to speed and squash on
impact, while keeping area constant (sx * sy == 1), the classic animation
principle for bouncing balls, popping icons and landing characters.

Usage::

    from squash_stretch_scale import stretch_from_velocity, impact_squash, bounce_track
    sx, sy, angle = stretch_from_velocity(vx=0, vy=900, k=0.0006, max_stretch=1.4)
    impact_squash(t_since_impact=0.03, strength=0.3)
    track = bounce_track(height_px=400, bounces=3, fps=30)   # y offsets + scales per frame
"""

from __future__ import annotations

import math


def stretch_from_velocity(vx: float, vy: float, k: float = 0.0005, max_stretch: float = 1.35):
    """Return (scale_along, scale_across, angle_deg) with scale_along * scale_across == 1."""
    speed = math.hypot(vx, vy)
    s = min(max_stretch, 1.0 + k * speed)
    angle = math.degrees(math.atan2(vy, vx)) if speed else 0.0
    return s, 1.0 / s, angle


def impact_squash(t_since_impact: float, strength: float = 0.3, recover: float = 0.12):
    """(scale_x, scale_y) for a vertical impact: flatten then spring back over ``recover`` s."""
    if t_since_impact < 0 or t_since_impact >= recover:
        return 1.0, 1.0
    p = t_since_impact / recover
    # damped half-cosine: full squash at impact, slight overshoot, settle
    amount = strength * math.cos(p * math.pi * 1.5) * (1 - p)
    sy = max(0.2, 1.0 - amount)
    return 1.0 / sy, sy


def bounce_track(height_px: float, bounces: int = 3, fps: float = 30, restitution: float = 0.55,
                 gravity_px: float = 3000.0, squash: float = 0.3) -> list[dict]:
    """Frames of a dropped object: ``y`` above the floor, and volume-preserving scale."""
    if not 0 < restitution < 1:
        raise ValueError("restitution must be in (0, 1)")
    frames: list[dict] = []
    t = 0.0
    dt = 1.0 / fps
    y, v = float(height_px), 0.0
    impacts = 0
    last_impact = None
    while impacts <= bounces:
        v -= gravity_px * dt
        y += v * dt
        if y <= 0:
            y = 0.0
            v = -v * restitution
            impacts += 1
            last_impact = t
        if last_impact is not None and t - last_impact < 0.12:
            sx, sy = impact_squash(t - last_impact, squash * (restitution ** (impacts - 1)))
        else:
            sx_, sy_, _ = stretch_from_velocity(0, v)
            sx, sy = sy_, sx_  # vertical travel: stretch y
        frames.append({"t": round(t, 6), "y": y, "sx": sx, "sy": sy})
        t += dt
        if t > 30:
            break
    return frames
