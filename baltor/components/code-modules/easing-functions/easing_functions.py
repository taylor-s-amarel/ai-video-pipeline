"""Standard easing functions (Penner set) on normalised time t in [0, 1].

Thirty-one curves: linear plus in/out/in_out for sine, quad, cubic, quart,
quint, expo, circ, back, elastic and bounce. Formulas follow the widely used
Robert Penner equations in the form published at https://easings.net/.

Usage::

    from easing_functions import ease, get, sample
    ease("in_out_cubic", 0.25)        # 0.0625
    get("easeOutBack")(0.5)            # camelCase names are accepted too
    sample("out_bounce", 5)            # [0.0, ..., 1.0]
"""

from __future__ import annotations

import math
import re
from typing import Callable

C1 = 1.70158
C2 = C1 * 1.525
C3 = C1 + 1
C4 = (2 * math.pi) / 3
C5 = (2 * math.pi) / 4.5


def linear(x: float) -> float:
    return x


def in_sine(x): return 1 - math.cos((x * math.pi) / 2)
def out_sine(x): return math.sin((x * math.pi) / 2)
def in_out_sine(x): return -(math.cos(math.pi * x) - 1) / 2


def _poly(p: int):
    def ein(x): return x ** p
    def eout(x): return 1 - (1 - x) ** p
    def einout(x):
        return (2 ** (p - 1)) * x ** p if x < 0.5 else 1 - ((-2 * x + 2) ** p) / 2
    return ein, eout, einout


in_quad, out_quad, in_out_quad = _poly(2)
in_cubic, out_cubic, in_out_cubic = _poly(3)
in_quart, out_quart, in_out_quart = _poly(4)
in_quint, out_quint, in_out_quint = _poly(5)


def in_expo(x): return 0.0 if x == 0 else 2 ** (10 * x - 10)
def out_expo(x): return 1.0 if x == 1 else 1 - 2 ** (-10 * x)


def in_out_expo(x):
    if x == 0 or x == 1:
        return float(x)
    return 2 ** (20 * x - 10) / 2 if x < 0.5 else (2 - 2 ** (-20 * x + 10)) / 2


def in_circ(x): return 1 - math.sqrt(1 - x * x)
def out_circ(x): return math.sqrt(1 - (x - 1) ** 2)


def in_out_circ(x):
    if x < 0.5:
        return (1 - math.sqrt(1 - (2 * x) ** 2)) / 2
    return (math.sqrt(1 - (-2 * x + 2) ** 2) + 1) / 2


def in_back(x): return C3 * x ** 3 - C1 * x ** 2
def out_back(x): return 1 + C3 * (x - 1) ** 3 + C1 * (x - 1) ** 2


def in_out_back(x):
    if x < 0.5:
        return ((2 * x) ** 2 * ((C2 + 1) * 2 * x - C2)) / 2
    return ((2 * x - 2) ** 2 * ((C2 + 1) * (x * 2 - 2) + C2) + 2) / 2


def in_elastic(x):
    if x == 0 or x == 1:
        return float(x)
    return -(2 ** (10 * x - 10)) * math.sin((x * 10 - 10.75) * C4)


def out_elastic(x):
    if x == 0 or x == 1:
        return float(x)
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * C4) + 1


def in_out_elastic(x):
    if x == 0 or x == 1:
        return float(x)
    if x < 0.5:
        return -(2 ** (20 * x - 10) * math.sin((20 * x - 11.125) * C5)) / 2
    return (2 ** (-20 * x + 10) * math.sin((20 * x - 11.125) * C5)) / 2 + 1


def out_bounce(x):
    n1, d1 = 7.5625, 2.75
    if x < 1 / d1:
        return n1 * x * x
    if x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75
    if x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375
    x -= 2.625 / d1
    return n1 * x * x + 0.984375


def in_bounce(x): return 1 - out_bounce(1 - x)


def in_out_bounce(x):
    return (1 - out_bounce(1 - 2 * x)) / 2 if x < 0.5 else (1 + out_bounce(2 * x - 1)) / 2


EASINGS: dict[str, Callable[[float], float]] = {"linear": linear}
for _fam in ("sine", "quad", "cubic", "quart", "quint", "expo", "circ", "back", "elastic", "bounce"):
    for _mode in ("in", "out", "in_out"):
        EASINGS[f"{_mode}_{_fam}"] = globals()[f"{_mode}_{_fam}"]

OVERSHOOTING = {"in_back", "out_back", "in_out_back", "in_elastic", "out_elastic", "in_out_elastic"}


def normalise_name(name: str) -> str:
    """Accept ``in_out_cubic``, ``easeInOutCubic``, ``ease-in-out-cubic`` or ``InOutCubic``."""
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", name.strip()).lower().replace("-", "_")
    s = re.sub(r"^ease_?", "", s)
    s = s.replace("inout", "in_out")
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def get(name: str) -> Callable[[float], float]:
    key = normalise_name(name)
    if key not in EASINGS:
        raise KeyError(f"unknown easing {name!r}; known: {', '.join(sorted(EASINGS))}")
    return EASINGS[key]


def ease(name: str, t: float) -> float:
    """Evaluate easing ``name`` at ``t``; t is clamped to [0, 1]."""
    return get(name)(min(1.0, max(0.0, float(t))))


def sample(name: str, n: int) -> list[float]:
    """``n`` evenly spaced samples including both ends (n >= 2)."""
    if n < 2:
        raise ValueError("n must be at least 2")
    f = get(name)
    return [f(i / (n - 1)) for i in range(n)]


def tween(a: float, b: float, t: float, name: str = "linear") -> float:
    """Interpolate from a to b with easing ``name``."""
    return a + (b - a) * ease(name, t)
