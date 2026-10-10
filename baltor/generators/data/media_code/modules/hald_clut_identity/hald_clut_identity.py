"""Hald CLUT images: grade a still in any editor, apply the grade to video.

A Hald CLUT of level L is an L^3 x L^3 image containing every colour of an
L^2-step cube. Export the identity image, apply your grade to it in an image
editor (curves, colour balance, a film emulation preset), save it losslessly
(PNG), then apply the edited image to footage with ffmpeg's ``haldclut``
filter or with ``apply`` here.

Usage::

    from hald_clut_identity import identity_image, apply, ffmpeg_graph
    identity_image(8).save("hald8_identity.png")      # 512x512
    graph = ffmpeg_graph()   # use with: ffmpeg -i video.mp4 -i graded_hald.png -filter_complex <graph> ...
"""

from __future__ import annotations

import numpy as np
from PIL import Image


def identity_array(level: int = 8) -> np.ndarray:
    if not 2 <= level <= 16:
        raise ValueError("level must be within 2-16")
    n = level * level              # steps per channel
    side = level ** 3
    idx = np.arange(side * side)
    r = idx % n
    g = (idx // n) % n
    b = idx // (n * n)
    rgb = np.stack([r, g, b], -1).astype(np.float64) * 255.0 / (n - 1)
    return np.clip(rgb + 0.5, 0, 255).astype(np.uint8).reshape(side, side, 3)


def identity_image(level: int = 8) -> Image.Image:
    return Image.fromarray(identity_array(level), "RGB")


def to_lut(hald: np.ndarray) -> np.ndarray:
    """Hald image -> LUT array (n, n, n, 3) indexed [b, g, r], floats 0-1."""
    side = hald.shape[0]
    level = round(side ** (1 / 3))
    if level ** 3 != side or hald.shape[1] != side:
        raise ValueError("not a Hald CLUT image (side must be level^3)")
    n = level * level
    return hald[..., :3].reshape(n, n, n, 3).astype(np.float64) / 255.0


def apply(img: np.ndarray, hald: np.ndarray) -> np.ndarray:
    lut = to_lut(hald)
    n = lut.shape[0]
    x = img[..., :3].astype(np.float64) / 255.0 * (n - 1)
    i0 = np.floor(x).astype(int)
    i1 = np.minimum(i0 + 1, n - 1)
    f = x - i0
    out = np.zeros(img.shape[:2] + (3,))
    for db in (0, 1):
        for dg in (0, 1):
            for dr in (0, 1):
                w = ((f[..., 0] if dr else 1 - f[..., 0]) * (f[..., 1] if dg else 1 - f[..., 1]) *
                     (f[..., 2] if db else 1 - f[..., 2]))
                bi = i1[..., 2] if db else i0[..., 2]
                gi = i1[..., 1] if dg else i0[..., 1]
                ri = i1[..., 0] if dr else i0[..., 0]
                out += w[..., None] * lut[bi, gi, ri]
    return np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)


def ffmpeg_graph(video_label: str = "[0:v]", hald_label: str = "[1:v]", out_label: str = "[graded]") -> str:
    return f"{video_label}{hald_label}haldclut{out_label}"
