"""Looping rain and snow overlays (Pillow), deterministic and seamless.

Every drop or flake falls a whole number of wraps per loop, so a clip
rendered for exactly ``loop_s`` seconds tiles in time with no visible jump.
Rain draws slanted streaks (length from speed and shutter), snow draws soft
discs that sway sideways. Opacity is capped at 0.98.

Usage::

    from precipitation_overlay import Precipitation
    rain = Precipitation(kind="rain", count=400, size=(1080, 1920), loop_s=2.0, wind_deg=12, seed=1)
    frame = rain.render(t=0.5)            # RGBA image, transparent background
    snow = Precipitation(kind="snow", count=250, size=(1080, 1920), loop_s=6.0)
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw


class Precipitation:
    def __init__(self, kind: str = "rain", count: int = 300, size=(1080, 1920), loop_s: float = 2.0,
                 wind_deg: float = 10.0, seed: int = 0, color=(220, 230, 255), max_opacity: float = 0.6,
                 shutter: float = 1 / 60):
        if kind not in ("rain", "snow"):
            raise ValueError("kind must be 'rain' or 'snow'")
        if not 0 <= max_opacity <= 0.98:
            raise ValueError("max_opacity must be within [0, 0.98]")
        if loop_s <= 0 or count < 0:
            raise ValueError("loop_s must be > 0 and count >= 0")
        self.kind, self.size, self.loop_s = kind, tuple(size), loop_s
        self.wind = math.radians(wind_deg)
        self.color, self.max_opacity, self.shutter = color, max_opacity, shutter
        rng = np.random.default_rng(seed)
        w, h = self.size
        self.margin = 0.15 * h
        span = h + 2 * self.margin
        if kind == "rain":
            wraps = rng.integers(3, 7, count)       # whole wraps per loop -> exact loop
            self.depth = rng.uniform(0.4, 1.0, count)
        else:
            wraps = rng.integers(1, 3, count)
            self.depth = rng.uniform(0.3, 1.0, count)
        self.speed = wraps * span / loop_s           # px/s along the fall direction
        self.x0 = rng.uniform(-0.2 * w, 1.2 * w, count)
        self.y0 = rng.uniform(0, span, count)
        self.phase = rng.uniform(0, 2 * math.pi, count)
        self.sway_cycles = rng.integers(1, 3, count)
        self.span = span

    def positions(self, t: float) -> np.ndarray:
        w, _ = self.size
        dist = self.y0 + self.speed * t
        y = (dist % self.span) - self.margin
        x = self.x0 + math.tan(self.wind) * (dist % self.span)
        if self.kind == "snow":
            x = x + 18 * self.depth * np.sin(2 * math.pi * self.sway_cycles * t / self.loop_s + self.phase)
        x = (x + 0.2 * w) % (1.4 * w) - 0.2 * w
        return np.stack([x, y], 1)

    def render(self, t: float) -> Image.Image:
        img = Image.new("RGBA", self.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        pos = self.positions(t)
        for (x, y), depth, v in zip(pos, self.depth, self.speed):
            a = int(255 * self.max_opacity * depth)
            if self.kind == "rain":
                length = max(4.0, v * self.shutter * depth)
                dx, dy = math.sin(self.wind) * length, math.cos(self.wind) * length
                d.line([(x - dx, y - dy), (x, y)], fill=(*self.color, a), width=max(1, int(round(2 * depth))))
            else:
                r = 2 + 4 * depth
                d.ellipse([x - r, y - r, x + r, y + r], fill=(*self.color, a))
        return img
