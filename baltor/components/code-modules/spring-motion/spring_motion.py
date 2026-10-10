"""Damped spring motion with exact (closed-form) solutions.

Models m*x'' + c*x' + k*(x - target) = 0 from x(0) = start with initial
velocity v0, covering under-, critically and over-damped springs. Use it for
springy text pops, overshooting photo entrances and settle-to-rest motion.

Usage::

    from spring_motion import Spring
    s = Spring(stiffness=180, damping=12)          # mass 1, underdamped
    s.value(0.1); s.overshoot(); s.settle_time()
    s.frames(fps=30, duration=1.0)                 # per-frame positions 0 -> 1
    Spring.from_ratio(damping_ratio=0.5, frequency_hz=3)
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Spring:
    stiffness: float = 170.0
    damping: float = 26.0
    mass: float = 1.0
    start: float = 0.0
    target: float = 1.0
    velocity: float = 0.0

    def __post_init__(self):
        if self.stiffness <= 0 or self.mass <= 0 or self.damping < 0:
            raise ValueError("stiffness and mass must be > 0 and damping >= 0")

    @classmethod
    def from_ratio(cls, damping_ratio: float, frequency_hz: float, mass: float = 1.0, **kw) -> "Spring":
        w0 = 2 * math.pi * frequency_hz
        k = mass * w0 * w0
        return cls(stiffness=k, damping=2 * damping_ratio * math.sqrt(k * mass), mass=mass, **kw)

    @property
    def omega0(self) -> float:
        return math.sqrt(self.stiffness / self.mass)

    @property
    def zeta(self) -> float:
        return self.damping / (2 * math.sqrt(self.stiffness * self.mass))

    def value(self, t: float) -> float:
        if t <= 0:
            return self.start
        y0 = self.start - self.target
        v0 = self.velocity
        w0, z = self.omega0, self.zeta
        if abs(z - 1.0) < 1e-9:
            y = (y0 + (v0 + w0 * y0) * t) * math.exp(-w0 * t)
        elif z < 1.0:
            wd = w0 * math.sqrt(1 - z * z)
            y = math.exp(-z * w0 * t) * (y0 * math.cos(wd * t) + ((v0 + z * w0 * y0) / wd) * math.sin(wd * t))
        else:
            root = math.sqrt(z * z - 1)
            r1, r2 = -w0 * (z - root), -w0 * (z + root)
            a = (v0 - r2 * y0) / (r1 - r2)
            b = y0 - a
            y = a * math.exp(r1 * t) + b * math.exp(r2 * t)
        return self.target + y

    def frames(self, fps: float, duration: float) -> list[float]:
        n = int(round(duration * fps)) + 1
        return [self.value(i / fps) for i in range(n)]

    def overshoot(self, horizon: float | None = None, steps: int = 4000) -> float:
        """Largest excursion past the target, as a fraction of the travel distance."""
        span = self.target - self.start
        if span == 0:
            return 0.0
        horizon = horizon or max(1.0, 10 / (self.zeta * self.omega0 + 1e-9))
        peak = max((self.value(horizon * i / steps) - self.target) / span for i in range(steps + 1))
        return max(0.0, peak)

    def settle_time(self, tolerance: float = 0.01, horizon: float = 30.0, step: float = 1 / 600) -> float:
        """First time after which |x - target| stays within tolerance * |travel|."""
        span = abs(self.target - self.start) or 1.0
        t, last_out = 0.0, 0.0
        while t <= horizon:
            if abs(self.value(t) - self.target) > tolerance * span:
                last_out = t
            t += step
        return last_out + step
