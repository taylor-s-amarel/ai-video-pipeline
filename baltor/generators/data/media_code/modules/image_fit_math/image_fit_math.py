"""Geometry for fitting images into frames: cover, contain, even sizes, DPI-free.

Pure functions (no image library needed) that every compositor needs:

* ``fit(src, box, mode)`` for ``cover``, ``contain``, ``fill`` and ``width``
  modes returning the scaled size and the placement offset;
* ``crop_for_cover(src, box, focus)`` the source crop rectangle that a cover
  fit shows;
* ``even(n)`` / ``even_size`` because yuv420p video needs even dimensions;
* ``upscale_factor`` to warn when a photo will be enlarged (soft results).

Usage::

    from image_fit_math import fit, crop_for_cover, upscale_factor
    fit((4000, 3000), (1080, 1920), "cover")        # {'size': (2560, 1920), 'offset': (-740, 0), 'scale': 0.64}
"""

from __future__ import annotations


def even(n: float, mode: str = "down") -> int:
    n = int(round(n)) if mode == "round" else int(n)
    if n % 2:
        n = n - 1 if mode in ("down", "round") else n + 1
    return max(2, n)


def even_size(w: float, h: float) -> tuple[int, int]:
    return even(w, "round"), even(h, "round")


def fit(src, box, mode: str = "contain", anchor=(0.5, 0.5)) -> dict:
    sw, sh = src
    bw, bh = box
    if min(sw, sh, bw, bh) <= 0:
        raise ValueError("sizes must be positive")
    if mode == "cover":
        s = max(bw / sw, bh / sh)
    elif mode == "contain":
        s = min(bw / sw, bh / sh)
    elif mode == "width":
        s = bw / sw
    elif mode == "fill":
        return {"size": (bw, bh), "offset": (0, 0), "scale": (bw / sw, bh / sh)}
    else:
        raise ValueError("mode must be cover, contain, width or fill")
    w, h = round(sw * s), round(sh * s)
    ox = round((bw - w) * anchor[0])
    oy = round((bh - h) * anchor[1])
    return {"size": (w, h), "offset": (ox, oy), "scale": round(s, 6)}


def crop_for_cover(src, box, focus=(0.5, 0.5)) -> tuple[float, float, float, float]:
    """Source rectangle (x, y, w, h) shown by a cover fit centred on ``focus``."""
    sw, sh = src
    bw, bh = box
    aspect = bw / bh
    if sw / sh > aspect:
        h, w = sh, sh * aspect
    else:
        w, h = sw, sw / aspect
    x = min(max(focus[0] * sw - w / 2, 0), sw - w)
    y = min(max(focus[1] * sh - h / 2, 0), sh - h)
    return x, y, w, h


def upscale_factor(src, box, mode: str = "cover") -> float:
    """> 1 means the source is enlarged (expect softness above about 1.25)."""
    s = fit(src, box, mode)["scale"]
    return s if isinstance(s, float) else max(s)
