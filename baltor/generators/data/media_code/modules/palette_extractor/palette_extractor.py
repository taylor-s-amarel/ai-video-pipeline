"""Extract a colour palette from an image with k-means (numpy only).

Pixels are downsampled, optionally converted to a perceptual space (OKLab)
so clusters match how colours look, then clustered with k-means++
initialisation and a fixed seed (same image -> same palette). Returns
colours sorted by how much of the image they cover, as hex with shares.

Useful to theme captions, panels and backgrounds from the main photo.

Usage::

    from palette_extractor import extract
    extract(np.asarray(Image.open("photo.jpg").convert("RGB")), k=5)
    # [{'hex': '#1E3A5F', 'share': 0.41}, ...]
"""

from __future__ import annotations

import numpy as np

M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
               [0.0883024619, 0.2817188376, 0.6299787005]])
M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
               [0.0259040371, 0.7827717662, -0.8086757660]])


def to_oklab(rgb01: np.ndarray) -> np.ndarray:
    lin = np.where(rgb01 <= 0.04045, rgb01 / 12.92, ((rgb01 + 0.055) / 1.055) ** 2.4)
    return np.cbrt(lin @ M1.T) @ M2.T


def kmeans(x: np.ndarray, k: int, seed: int = 0, iters: int = 30) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    centres = [x[rng.integers(len(x))]]
    for _ in range(1, k):
        d2 = np.min(((x[:, None, :] - np.array(centres)[None]) ** 2).sum(-1), axis=1)
        if d2.sum() == 0:
            centres.append(x[rng.integers(len(x))])
        else:
            centres.append(x[rng.choice(len(x), p=d2 / d2.sum())])
    c = np.array(centres, dtype=np.float64)
    for _ in range(iters):
        labels = np.argmin(((x[:, None, :] - c[None]) ** 2).sum(-1), axis=1)
        new = np.array([x[labels == i].mean(0) if np.any(labels == i) else c[i] for i in range(k)])
        if np.allclose(new, c):
            break
        c = new
    labels = np.argmin(((x[:, None, :] - c[None]) ** 2).sum(-1), axis=1)
    return c, labels


def extract(img: np.ndarray, k: int = 5, max_pixels: int = 20000, perceptual: bool = True, seed: int = 0) -> list[dict]:
    if k < 1:
        raise ValueError("k must be >= 1")
    px = np.asarray(img)[..., :3].reshape(-1, 3).astype(np.float64) / 255.0
    if len(px) > max_pixels:
        step = int(np.ceil(len(px) / max_pixels))
        px = px[::step]
    k = min(k, len(np.unique(px, axis=0)))
    feats = to_oklab(px) if perceptual else px
    _, labels = kmeans(feats, k, seed)
    out = []
    for i in range(k):
        members = px[labels == i]
        if len(members) == 0:
            continue
        rgb = np.clip(members.mean(0) * 255 + 0.5, 0, 255).astype(int)
        out.append({"hex": "#" + "".join(f"{v:02X}" for v in rgb), "rgb": tuple(int(v) for v in rgb),
                    "share": round(len(members) / len(px), 4)})
    return sorted(out, key=lambda d: -d["share"])
