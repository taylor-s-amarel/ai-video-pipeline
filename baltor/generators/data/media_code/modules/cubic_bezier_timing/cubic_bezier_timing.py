"""CSS-style cubic-bezier timing functions.

Solves x(s) = t for the curve parameter s with Newton steps and a bisection
fallback, then returns y(s). The named presets are the CSS Easing Functions
keywords: ease (0.25, 0.1, 0.25, 1), ease-in (0.42, 0, 1, 1), ease-out
(0, 0, 0.58, 1), ease-in-out (0.42, 0, 0.58, 1) and linear.

Usage::

    from cubic_bezier_timing import CubicBezier, preset
    CubicBezier(0.34, 1.56, 0.64, 1)(0.5)   # an overshooting "back" style curve
    preset("ease")(0.5)                     # about 0.8024
"""

from __future__ import annotations

from dataclasses import dataclass

PRESETS = {
    "linear": (0.0, 0.0, 1.0, 1.0),
    "ease": (0.25, 0.1, 0.25, 1.0),
    "ease-in": (0.42, 0.0, 1.0, 1.0),
    "ease-out": (0.0, 0.0, 0.58, 1.0),
    "ease-in-out": (0.42, 0.0, 0.58, 1.0),
}


@dataclass(frozen=True)
class CubicBezier:
    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self):
        if not (0.0 <= self.x1 <= 1.0 and 0.0 <= self.x2 <= 1.0):
            raise ValueError("x1 and x2 must be within [0, 1] so the curve is a function of time")

    @staticmethod
    def _coord(s: float, p1: float, p2: float) -> float:
        # Bernstein form with P0 = 0 and P3 = 1
        return 3 * (1 - s) ** 2 * s * p1 + 3 * (1 - s) * s * s * p2 + s ** 3

    @staticmethod
    def _deriv(s: float, p1: float, p2: float) -> float:
        return 3 * (1 - s) ** 2 * p1 + 6 * (1 - s) * s * (p2 - p1) + 3 * s * s * (1 - p2)

    def solve_s(self, t: float, eps: float = 1e-9) -> float:
        s = t
        for _ in range(8):
            x = self._coord(s, self.x1, self.x2) - t
            if abs(x) < eps:
                return s
            d = self._deriv(s, self.x1, self.x2)
            if abs(d) < 1e-7:
                break
            s -= x / d
        lo, hi = 0.0, 1.0
        s = min(max(t, lo), hi)
        for _ in range(100):
            x = self._coord(s, self.x1, self.x2)
            if abs(x - t) < eps:
                break
            if x < t:
                lo = s
            else:
                hi = s
            s = (lo + hi) / 2
        return s

    def __call__(self, t: float) -> float:
        t = min(1.0, max(0.0, float(t)))
        if t in (0.0, 1.0):
            return t
        return self._coord(self.solve_s(t), self.y1, self.y2)

    def css(self) -> str:
        return f"cubic-bezier({self.x1:g}, {self.y1:g}, {self.x2:g}, {self.y2:g})"


def preset(name: str) -> CubicBezier:
    try:
        return CubicBezier(*PRESETS[name])
    except KeyError:
        raise KeyError(f"unknown preset {name!r}; known: {', '.join(PRESETS)}") from None


def parse_css(text: str) -> CubicBezier:
    """Parse ``cubic-bezier(a, b, c, d)`` or a preset keyword."""
    text = text.strip()
    if text in PRESETS:
        return preset(text)
    if not (text.startswith("cubic-bezier(") and text.endswith(")")):
        raise ValueError(f"not a cubic-bezier() value: {text!r}")
    parts = [float(p) for p in text[len("cubic-bezier("):-1].split(",")]
    if len(parts) != 4:
        raise ValueError("cubic-bezier() takes four numbers")
    return CubicBezier(*parts)


def sample(curve: CubicBezier, n: int) -> list[float]:
    return [curve(i / (n - 1)) for i in range(n)]
