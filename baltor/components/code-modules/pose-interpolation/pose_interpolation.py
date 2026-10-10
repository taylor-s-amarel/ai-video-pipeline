"""Interpolate joint-angle poses and generate cycles (walk, idle sway).

Poses are dicts of joint -> angle in degrees. Angles interpolate along the
shortest arc so a joint never spins the long way round. ``cycle`` turns a
list of key poses into a looping animation, and ``walk_cycle`` produces a
simple procedural gait (sinusoidal leg and arm swing, knee bend on the
forward swing) usable with the stick_figure_rig module's joint names.

Usage::

    from pose_interpolation import blend, cycle, walk_cycle
    mid = blend(pose_a, pose_b, 0.5, easing="in_out_sine")
    frames = cycle([pose_a, pose_b], fps=30, seconds_per_pose=0.4, loops=3)
    gait = walk_cycle(fps=30, steps_per_second=2.0, seconds=2.0)
"""

from __future__ import annotations

import math


def shortest_delta(a: float, b: float) -> float:
    return (b - a + 180.0) % 360.0 - 180.0


def _ease(name: str, x: float) -> float:
    if name == "linear":
        return x
    if name == "in_out_sine":
        return -(math.cos(math.pi * x) - 1) / 2
    if name == "in_out_cubic":
        return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
    raise ValueError(f"unknown easing {name!r}")


def blend(a: dict, b: dict, t: float, easing: str = "linear") -> dict:
    u = _ease(easing, min(1.0, max(0.0, t)))
    out = {}
    for j in sorted(set(a) | set(b)):
        x, y = a.get(j, 0.0), b.get(j, 0.0)
        out[j] = x + shortest_delta(x, y) * u
    return out


def cycle(poses: list[dict], fps: float, seconds_per_pose: float, loops: int = 1,
          easing: str = "in_out_sine") -> list[dict]:
    """Loop through ``poses`` (returning to the first), ``loops`` times."""
    if len(poses) < 2:
        raise ValueError("need at least two poses")
    per = max(1, int(round(seconds_per_pose * fps)))
    frames = []
    for _ in range(loops):
        for i, p in enumerate(poses):
            q = poses[(i + 1) % len(poses)]
            for f in range(per):
                frames.append(blend(p, q, f / per, easing))
    return frames


def walk_cycle(fps: float = 30, steps_per_second: float = 2.0, seconds: float = 2.0, stride_deg: float = 25.0,
               arm_deg: float = 20.0, knee_deg: float = 30.0) -> list[dict]:
    frames = []
    n = int(round(seconds * fps))
    for i in range(n):
        phase = 2 * math.pi * (steps_per_second / 2) * i / fps  # one full cycle = two steps
        s = math.sin(phase)
        frames.append({
            "l_knee": stride_deg * s, "r_knee": -stride_deg * s,
            "l_foot": knee_deg * max(0.0, math.cos(phase)), "r_foot": knee_deg * max(0.0, -math.cos(phase)),
            "l_elbow": -160 - arm_deg * s, "r_elbow": 160 - arm_deg * s,
            "l_hand": 15.0, "r_hand": -15.0,
        })
    return frames


def bob_offsets(fps: float = 30, steps_per_second: float = 2.0, seconds: float = 2.0, amplitude_px: float = 6.0):
    """Vertical pelvis bob for a walk: lowest twice per gait cycle (once per step)."""
    n = int(round(seconds * fps))
    return [-amplitude_px * abs(math.cos(math.pi * steps_per_second * i / fps)) for i in range(n)]
