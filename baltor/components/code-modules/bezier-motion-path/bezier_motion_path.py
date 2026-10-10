"""Constant-speed motion along a chain of cubic Bezier segments.

A path is a list of segments ``(p0, p1, p2, p3)`` of 2D points. Raw Bezier
parameters move faster on straight stretches and slower on bends; this module
builds an arc-length table so ``point_at(s)`` advances evenly in distance,
which keeps objects (paper planes, arrows, highlighted dots) moving smoothly.

Usage::

    from bezier_motion_path import BezierPath
    path = BezierPath([((0, 0), (300, -200), (700, 200), (1000, 0))])
    path.length
    x, y = path.point_at(0.5)          # halfway by distance
    angle = path.angle_at(0.5)         # heading in degrees, for rotating sprites
    pts = path.sample(60)              # 60 evenly spaced positions
"""

from __future__ import annotations

import bisect
import math


def _bez(p0, p1, p2, p3, t):
    u = 1 - t
    a, b, c, d = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def _bez_d(p0, p1, p2, p3, t):
    u = 1 - t
    a, b, c = 3 * u * u, 6 * u * t, 3 * t * t
    return (a * (p1[0] - p0[0]) + b * (p2[0] - p1[0]) + c * (p3[0] - p2[0]),
            a * (p1[1] - p0[1]) + b * (p2[1] - p1[1]) + c * (p3[1] - p2[1]))


class BezierPath:
    def __init__(self, segments, resolution: int = 256):
        if not segments:
            raise ValueError("need at least one segment")
        for a, b in zip(segments, segments[1:]):
            if tuple(a[3]) != tuple(b[0]):
                raise ValueError("segments must join end to start")
        self.segments = [tuple(tuple(map(float, p)) for p in seg) for seg in segments]
        self._table: list[tuple[float, int, float]] = []  # (cumulative length, segment, t)
        total = 0.0
        prev = self.segments[0][0]
        self._table.append((0.0, 0, 0.0))
        for si, seg in enumerate(self.segments):
            for k in range(1, resolution + 1):
                t = k / resolution
                p = _bez(*seg, t)
                total += math.dist(prev, p)
                self._table.append((total, si, t))
                prev = p
        self.length = total
        self._lengths = [row[0] for row in self._table]

    def _locate(self, s: float):
        target = min(max(s, 0.0), 1.0) * self.length
        i = bisect.bisect_left(self._lengths, target)
        if i <= 0:
            return 0, 0.0
        l0, s0, t0 = self._table[i - 1]
        l1, s1, t1 = self._table[i]
        if s1 != s0:
            t0 = 0.0
        f = 0.0 if l1 == l0 else (target - l0) / (l1 - l0)
        return s1, t0 + (t1 - t0) * f

    def point_at(self, s: float) -> tuple[float, float]:
        si, t = self._locate(s)
        return _bez(*self.segments[si], t)

    def angle_at(self, s: float) -> float:
        si, t = self._locate(s)
        dx, dy = _bez_d(*self.segments[si], t)
        return math.degrees(math.atan2(dy, dx))

    def sample(self, n: int) -> list[tuple[float, float]]:
        return [self.point_at(i / (n - 1)) for i in range(n)] if n > 1 else [self.point_at(1.0)]


def smooth_through(points) -> list[tuple]:
    """Segments through ``points`` with tangents from neighbours (Catmull-Rom to Bezier, tension 0.5)."""
    pts = [tuple(map(float, p)) for p in points]
    if len(pts) < 2:
        raise ValueError("need at least two points")
    segs = []
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else pts[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        segs.append((p1, c1, c2, p2))
    return segs
