"""Deterministic 2D particle emitter (dust, sparks, confetti, embers).

Particles are spawned at ``rate`` per second from a point or box with a seeded
random generator, so the same seed always gives the same animation. Positions
use the closed-form solution for constant gravity with linear drag, so any
frame can be evaluated directly (random access, no simulation state).
Size and opacity follow simple life curves; opacity is capped at 0.98.

Usage::

    from particle_emitter import Emitter
    em = Emitter(rate=40, lifetime=2.5, origin=(540, 1700), spread=(400, 20),
                 velocity=(0, -220), velocity_jitter=(60, 60), gravity=(0, 30), seed=7)
    parts = em.state(t=3.2)               # list of dicts: x, y, size, opacity, age
    img = em.render(t=3.2, size=(1080, 1920), color=(255, 230, 180))
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw


@dataclass
class Emitter:
    rate: float = 30.0
    lifetime: float = 2.0
    origin: tuple = (0.0, 0.0)
    spread: tuple = (0.0, 0.0)          # half-size of the spawn box
    velocity: tuple = (0.0, -100.0)
    velocity_jitter: tuple = (30.0, 30.0)
    gravity: tuple = (0.0, 0.0)
    drag: float = 0.0                   # 1/s, linear
    size: tuple = (3.0, 8.0)            # min, max radius at birth
    shrink: bool = True
    max_opacity: float = 0.98
    seed: int = 0
    horizon: float = 600.0              # seconds of particles to pre-generate

    def __post_init__(self):
        if self.rate <= 0 or self.lifetime <= 0:
            raise ValueError("rate and lifetime must be > 0")
        if not 0 <= self.max_opacity <= 0.98:
            raise ValueError("max_opacity must be within [0, 0.98]")
        n = int(math.ceil(self.rate * self.horizon))
        rng = np.random.default_rng(self.seed)
        self._birth = np.arange(n) / self.rate
        self._p0 = np.stack([self.origin[0] + rng.uniform(-1, 1, n) * self.spread[0],
                             self.origin[1] + rng.uniform(-1, 1, n) * self.spread[1]], 1)
        self._v0 = np.stack([self.velocity[0] + rng.normal(0, 1, n) * self.velocity_jitter[0],
                             self.velocity[1] + rng.normal(0, 1, n) * self.velocity_jitter[1]], 1)
        self._r0 = rng.uniform(self.size[0], self.size[1], n)
        self._phase = rng.uniform(0, 2 * math.pi, n)

    def _positions(self, age: np.ndarray, idx: np.ndarray) -> np.ndarray:
        g = np.asarray(self.gravity, float)
        v0, p0 = self._v0[idx], self._p0[idx]
        a = age[:, None]
        if self.drag <= 0:
            return p0 + v0 * a + 0.5 * g * a * a
        k = self.drag
        e = np.exp(-k * a)
        return p0 + (v0 - g / k) * (1 - e) / k + g / k * a

    def state(self, t: float) -> list[dict]:
        if t < 0:
            return []
        alive = (self._birth <= t) & (self._birth > t - self.lifetime)
        idx = np.nonzero(alive)[0]
        age = t - self._birth[idx]
        pos = self._positions(age, idx)
        life = age / self.lifetime
        fade = np.minimum(1.0, np.minimum(life / 0.1, (1 - life) / 0.3))
        opacity = np.clip(fade, 0, 1) * self.max_opacity
        radius = self._r0[idx] * ((1 - 0.6 * life) if self.shrink else 1.0)
        return [{"x": float(x), "y": float(y), "size": float(r), "opacity": float(o), "age": float(a)}
                for (x, y), r, o, a in zip(pos, radius, opacity, age)]

    def render(self, t: float, size, color=(255, 255, 255)) -> Image.Image:
        img = Image.new("RGBA", tuple(size), (0, 0, 0, 0))
        layer = ImageDraw.Draw(img, "RGBA")
        for p in self.state(t):
            r = p["size"]
            layer.ellipse([p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r],
                          fill=(*color[:3], int(255 * p["opacity"])))
        return img
