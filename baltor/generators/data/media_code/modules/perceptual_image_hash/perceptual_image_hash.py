"""Perceptual image hashes (aHash, dHash, pHash) with numpy and Pillow.

Perceptual hashes stay nearly the same when an image is resized, recompressed
or slightly recoloured, so the Hamming distance between hashes finds
duplicates and near-duplicates (the same photo used twice, a thumbnail
re-exported, an old frame reused).

* ``ahash``: average hash (8x8 mean threshold)
* ``dhash``: difference hash (horizontal gradients on 9x8)
* ``phash``: DCT hash (32x32 DCT, low 8x8 frequencies vs median)

Hashes are 64-bit Python ints; ``hamming`` counts differing bits.

Usage::

    from perceptual_image_hash import phash, hamming
    hamming(phash(Image.open("a.jpg")), phash(Image.open("b.jpg"))) <= 10   # likely the same picture
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image


def _gray(img: Image.Image, size) -> np.ndarray:
    return np.asarray(img.convert("L").resize(size, Image.Resampling.LANCZOS), dtype=np.float64)


def _bits(mask: np.ndarray) -> int:
    v = 0
    for b in mask.ravel():
        v = (v << 1) | int(bool(b))
    return v


def ahash(img: Image.Image) -> int:
    g = _gray(img, (8, 8))
    return _bits(g > g.mean())


def dhash(img: Image.Image) -> int:
    g = _gray(img, (9, 8))
    return _bits(g[:, 1:] > g[:, :-1])


def _dct_matrix(n: int) -> np.ndarray:
    m = np.zeros((n, n))
    for k in range(n):
        for i in range(n):
            m[k, i] = math.cos(math.pi * (2 * i + 1) * k / (2 * n))
    m[0] *= 1 / math.sqrt(n)
    m[1:] *= math.sqrt(2 / n)
    return m


_D32 = _dct_matrix(32)


def phash(img: Image.Image) -> int:
    g = _gray(img, (32, 32))
    dct = _D32 @ g @ _D32.T
    low = dct[:8, :8].ravel()
    med = np.median(low[1:])  # skip the DC term
    return _bits(low > med)


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def to_hex(h: int) -> str:
    return f"{h:016x}"


def find_near_duplicates(hashes: dict, max_distance: int = 8) -> list[tuple]:
    """Pairs (name_a, name_b, distance) within ``max_distance`` bits."""
    names = sorted(hashes)
    out = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d = hamming(hashes[a], hashes[b])
            if d <= max_distance:
                out.append((a, b, d))
    return out
