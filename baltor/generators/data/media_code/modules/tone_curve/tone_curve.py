"""Tone curves from control points (monotone cubic), as LUTs and ffmpeg curves.

Control points ``[(x, y), ...]`` in [0, 1] define a curve; interpolation uses
Fritsch-Carlson monotone cubic Hermite splines, so a curve whose points rise
never overshoots or dips (no banding from accidental inversions). Build a
256-entry LUT for numpy, apply per channel or on all channels, or export
the points as an ffmpeg ``curves`` filter string.

Usage::

    from tone_curve import Curve, PRESETS
    c = Curve([(0, 0.04), (0.25, 0.2), (0.75, 0.82), (1, 0.97)])     # gentle S with lifted blacks
    out = c.apply(img_uint8)
    vf = c.ffmpeg()                  # "curves=all='0/0.04 0.25/0.2 0.75/0.82 1/0.97'"
"""

from __future__ import annotations

import numpy as np

PRESETS = {
    "linear": [(0, 0), (1, 1)],
    "soft_s": [(0, 0), (0.25, 0.21), (0.75, 0.79), (1, 1)],
    "strong_s": [(0, 0), (0.25, 0.16), (0.75, 0.84), (1, 1)],
    "lifted_blacks": [(0, 0.06), (0.5, 0.52), (1, 1)],
    "faded": [(0, 0.08), (0.5, 0.5), (1, 0.92)],
    "brighten_mids": [(0, 0), (0.5, 0.6), (1, 1)],
}


class Curve:
    def __init__(self, points):
        pts = sorted((float(x), float(y)) for x, y in points)
        if len(pts) < 2:
            raise ValueError("need at least two points")
        xs = [p[0] for p in pts]
        if len(set(xs)) != len(xs):
            raise ValueError("x values must be distinct")
        if xs[0] < 0 or xs[-1] > 1 or any(not 0 <= p[1] <= 1 for p in pts):
            raise ValueError("points must be within [0, 1]")
        self.x = np.array(xs)
        self.y = np.array([p[1] for p in pts])
        h = np.diff(self.x)
        d = np.diff(self.y) / h
        m = np.zeros_like(self.y)
        m[0], m[-1] = d[0], d[-1]
        for i in range(1, len(self.x) - 1):
            m[i] = 0.0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2
        for i in range(len(d)):
            if d[i] == 0:
                m[i] = m[i + 1] = 0.0
            else:
                a, b = m[i] / d[i], m[i + 1] / d[i]
                s = a * a + b * b
                if s > 9:
                    t = 3 / np.sqrt(s)
                    m[i], m[i + 1] = t * a * d[i], t * b * d[i]
        self.m = m

    def __call__(self, v):
        v = np.clip(np.asarray(v, dtype=np.float64), 0, 1)
        out = np.interp(v, self.x, self.y)  # outside the point range: flat
        i = np.clip(np.searchsorted(self.x, v) - 1, 0, len(self.x) - 2)
        inside = (v >= self.x[0]) & (v <= self.x[-1])
        x0, x1 = self.x[i], self.x[i + 1]
        h = x1 - x0
        t = np.where(h > 0, (v - x0) / h, 0)
        h00, h10 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t
        h01, h11 = -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
        herm = h00 * self.y[i] + h10 * h * self.m[i] + h01 * self.y[i + 1] + h11 * h * self.m[i + 1]
        return np.clip(np.where(inside, herm, out), 0, 1)

    def lut(self) -> np.ndarray:
        return np.clip(self(np.arange(256) / 255.0) * 255 + 0.5, 0, 255).astype(np.uint8)

    def apply(self, img: np.ndarray, channels=(0, 1, 2)) -> np.ndarray:
        out = np.asarray(img).copy()
        table = self.lut()
        for c in channels:
            out[..., c] = table[out[..., c]]
        return out

    def ffmpeg(self, channel: str = "all") -> str:
        if channel not in ("all", "master", "red", "green", "blue"):
            raise ValueError("channel must be all, master, red, green or blue")
        pts = " ".join(f"{x:g}/{y:g}" for x, y in zip(self.x, self.y))
        return f"curves={channel}='{pts}'"
