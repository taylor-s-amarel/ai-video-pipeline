"""WCAG contrast ratio, readable text colour and minimum backing opacity.

* ``relative_luminance`` and ``contrast_ratio`` follow the WCAG 2.x
  definitions (sRGB linearisation, (L1 + 0.05) / (L2 + 0.05));
* ``grade`` reports AA/AAA for normal and large text (4.5/3 and 7/4.5);
* ``best_text_color`` picks the candidate with the highest worst-case
  contrast over sampled background colours (moving video has many);
* ``min_backing_opacity`` finds the smallest tint opacity for a backing panel
  (frosted glass) so text reaches a target ratio over every sampled colour.

Usage::

    from wcag_contrast import contrast_ratio, best_text_color, min_backing_opacity
    contrast_ratio("#FFD21F", "#000000")                     # ~14.6
    best_text_color(["#87CEEB", "#1E3A5F"], ["#FFFFFF", "#000000", "#FFD21F"])
    min_backing_opacity("#FFD21F", "#101418", ["#87CEEB", "#F5F5DC"], target=4.5)
"""

from __future__ import annotations


def parse(color) -> tuple[float, float, float]:
    if isinstance(color, str):
        h = color.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) != 6:
            raise ValueError(f"bad colour {color!r}")
        return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    r, g, b = color[:3]
    return (r / 255.0, g / 255.0, b / 255.0) if max(r, g, b) > 1 else (float(r), float(g), float(b))


def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(color) -> float:
    r, g, b = parse(color)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(a, b) -> float:
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def grade(ratio: float) -> dict:
    return {"AA_normal": ratio >= 4.5, "AA_large": ratio >= 3.0, "AAA_normal": ratio >= 7.0,
            "AAA_large": ratio >= 4.5}


def best_text_color(backgrounds, candidates=("#FFFFFF", "#000000")) -> tuple[str, float]:
    best, best_min = None, -1.0
    for c in candidates:
        worst = min(contrast_ratio(c, bg) for bg in backgrounds)
        if worst > best_min:
            best, best_min = c, worst
    return best, best_min


def mix(fg, bg, alpha: float) -> tuple[float, float, float]:
    f, b = parse(fg), parse(bg)
    return tuple(alpha * x + (1 - alpha) * y for x, y in zip(f, b))


def min_backing_opacity(text, tint, backgrounds, target: float = 4.5, step: float = 0.01) -> float | None:
    """Smallest tint opacity (0-1) giving ``target`` contrast over all backgrounds, or None if impossible."""
    a = 0.0
    while a <= 1.0 + 1e-9:
        if all(contrast_ratio(text, mix(tint, bg, a)) >= target for bg in backgrounds):
            return round(a, 4)
        a += step
    return None
