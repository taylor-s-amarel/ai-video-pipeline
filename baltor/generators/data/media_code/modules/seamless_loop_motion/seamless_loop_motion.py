"""Perfectly looping motion for background layers.

Every function here is periodic in ``loop_s`` seconds, so a background clip
rendered for exactly one period can loop forever without a visible seam:

* ``orbit``: circular/elliptical drift (Lissajous with integer ratios)
* ``breathe``: smooth scale pulse
* ``drift_wrap``: constant-velocity scroll that wraps by exactly one tile
* ``loop_noise``: smooth noise sampled on a circle, so it repeats exactly

Usage::

    from seamless_loop_motion import orbit, breathe, drift_wrap, loop_noise, check_loop
    orbit(t, loop_s=8, rx=40, ry=25, ratio=(1, 2))
    check_loop(lambda t: orbit(t, 8), loop_s=8)
"""

from __future__ import annotations

import math


def orbit(t: float, loop_s: float, rx: float = 30.0, ry: float = 20.0, ratio=(1, 1), phase: float = 0.0):
    if int(ratio[0]) != ratio[0] or int(ratio[1]) != ratio[1]:
        raise ValueError("ratio must be integers to loop exactly")
    w = 2 * math.pi / loop_s
    return rx * math.sin(ratio[0] * w * t + phase), ry * math.sin(ratio[1] * w * t)


def breathe(t: float, loop_s: float, low: float = 1.0, high: float = 1.06) -> float:
    return low + (high - low) * (1 - math.cos(2 * math.pi * t / loop_s)) / 2


def drift_wrap(t: float, loop_s: float, tile_px: float, cycles: int = 1) -> float:
    """Offset in [0, tile_px) that scrolls ``cycles`` whole tiles per loop."""
    if int(cycles) != cycles:
        raise ValueError("cycles must be an integer")
    return (tile_px * cycles * (t / loop_s)) % tile_px


def _hash(ix: int, iy: int, seed: int) -> float:
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def _noise2(x: float, y: float, seed: int) -> float:
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = _hash(ix, iy, seed) + (_hash(ix + 1, iy, seed) - _hash(ix, iy, seed)) * ux
    b = _hash(ix, iy + 1, seed) + (_hash(ix + 1, iy + 1, seed) - _hash(ix, iy + 1, seed)) * ux
    return (a + (b - a) * uy) * 2 - 1


def loop_noise(t: float, loop_s: float, radius: float = 1.5, seed: int = 0) -> float:
    """Smooth noise in [-1, 1] that repeats exactly every ``loop_s`` (sampled on a circle)."""
    a = 2 * math.pi * t / loop_s
    return _noise2(10 + radius * math.cos(a), 10 + radius * math.sin(a), seed)


def check_loop(fn, loop_s: float, samples: int = 16, tol: float = 1e-6) -> bool:
    """True if fn(t) == fn(t + loop_s) at ``samples`` points (works for scalars and tuples)."""
    for i in range(samples):
        t = loop_s * i / samples
        a, b = fn(t), fn(t + loop_s)
        a = a if isinstance(a, tuple) else (a,)
        b = b if isinstance(b, tuple) else (b,)
        if any(abs(x - y) > tol for x, y in zip(a, b)):
            return False
    return True


def loop_frame_count(loop_s: float, fps: float) -> int:
    """Frames to render for one period; warns via ValueError if the loop is not a whole frame count."""
    n = loop_s * fps
    if abs(n - round(n)) > 1e-9:
        raise ValueError(f"{loop_s}s at {fps} fps is {n:.3f} frames; pick a loop length that is whole frames")
    return int(round(n))
