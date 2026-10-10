"""Analytic two-bone inverse kinematics in 2D (arms and legs).

Given a root (shoulder/hip), a target (hand/foot), the two bone lengths and
which way the joint bends, ``solve`` returns the middle joint (elbow/knee),
the end point and both absolute bone angles. Unreachable targets are handled
by pointing the straightened limb at the target; targets too close are pushed
out to the minimum reach.

Usage::

    from two_bone_ik import solve
    sol = solve(root=(0, 0), target=(60, 80), l1=60, l2=55, bend=1)
    sol["joint"], sol["end"], sol["angle1_deg"], sol["angle2_deg"], sol["reached"]
"""

from __future__ import annotations

import math


def solve(root, target, l1: float, l2: float, bend: int = 1) -> dict:
    if l1 <= 0 or l2 <= 0:
        raise ValueError("bone lengths must be > 0")
    if bend not in (1, -1):
        raise ValueError("bend must be 1 or -1")
    rx, ry = root
    dx, dy = target[0] - rx, target[1] - ry
    dist = math.hypot(dx, dy)
    base = math.atan2(dy, dx) if dist > 1e-12 else 0.0
    max_reach, min_reach = l1 + l2, abs(l1 - l2)
    reached = min_reach - 1e-9 <= dist <= max_reach + 1e-9
    d = min(max(dist, min_reach + 1e-9), max_reach)
    # law of cosines for the angle at the root between the limb line and bone 1
    cos_a = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d) if d > 0 else 1.0
    a = math.acos(max(-1.0, min(1.0, cos_a)))
    ang1 = base - bend * a
    jx, jy = rx + l1 * math.cos(ang1), ry + l1 * math.sin(ang1)
    if reached and dist > 0:
        ex, ey = target
    else:
        ex, ey = rx + d * math.cos(base), ry + d * math.sin(base)
    ang2 = math.atan2(ey - jy, ex - jx)
    return {"joint": (jx, jy), "end": (ex, ey), "angle1_deg": math.degrees(ang1),
            "angle2_deg": math.degrees(ang2), "bend_deg": math.degrees(ang2 - ang1), "reached": reached}


def chain_points(root, sol: dict) -> list[tuple[float, float]]:
    return [tuple(root), sol["joint"], sol["end"]]
