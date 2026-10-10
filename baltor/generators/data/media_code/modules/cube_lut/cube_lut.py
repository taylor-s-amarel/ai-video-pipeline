"""Read, write and apply .cube 3D LUTs (numpy, trilinear interpolation).

The .cube text format: optional ``TITLE``, ``LUT_3D_SIZE N``, optional
``DOMAIN_MIN``/``DOMAIN_MAX``, then N^3 lines of ``R G B`` floats with red
changing fastest. ``read_cube``/``write_cube`` handle that layout, ``identity``
builds a neutral LUT, and ``apply`` maps uint8 or float images through a LUT
with trilinear interpolation. The same files work with ffmpeg's ``lut3d``
filter (``lut3d=file=look.cube``).

Usage::

    from cube_lut import read_cube, apply, identity, write_cube
    lut = read_cube(open("look.cube").read())
    graded = apply(frame_rgb_uint8, lut)
"""

from __future__ import annotations

import numpy as np


def identity(n: int = 17) -> np.ndarray:
    """Array of shape (n, n, n, 3) indexed [b, g, r] (so r varies fastest when flattened)."""
    if n < 2:
        raise ValueError("size must be >= 2")
    g = np.linspace(0.0, 1.0, n)
    b_, g_, r_ = np.meshgrid(g, g, g, indexing="ij")
    return np.stack([r_, g_, b_], -1)


def write_cube(lut: np.ndarray, title: str = "baltor look") -> str:
    n = lut.shape[0]
    if lut.shape != (n, n, n, 3):
        raise ValueError("LUT must have shape (n, n, n, 3)")
    if "\n" in title or '"' in title:
        raise ValueError("title must be one line without quotes")
    lines = [f'TITLE "{title}"', f"LUT_3D_SIZE {n}", "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0"]
    flat = lut.reshape(-1, 3)
    lines += [f"{r:.6f} {g:.6f} {b:.6f}" for r, g, b in flat]
    return "\n".join(lines) + "\n"


def read_cube(text: str) -> np.ndarray:
    size = None
    dmin, dmax = np.zeros(3), np.ones(3)
    rows = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        key = line.split()[0]
        if key == "TITLE":
            continue
        if key == "LUT_3D_SIZE":
            size = int(line.split()[1])
        elif key == "LUT_1D_SIZE":
            raise ValueError("1D LUTs are not supported by this reader")
        elif key == "DOMAIN_MIN":
            dmin = np.array([float(v) for v in line.split()[1:4]])
        elif key == "DOMAIN_MAX":
            dmax = np.array([float(v) for v in line.split()[1:4]])
        else:
            vals = line.split()
            if len(vals) != 3:
                raise ValueError(f"bad data line: {raw!r}")
            rows.append([float(v) for v in vals])
    if size is None:
        raise ValueError("missing LUT_3D_SIZE")
    if len(rows) != size ** 3:
        raise ValueError(f"expected {size ** 3} rows, found {len(rows)}")
    if np.any(dmax <= dmin):
        raise ValueError("DOMAIN_MAX must exceed DOMAIN_MIN")
    lut = np.array(rows).reshape(size, size, size, 3)
    return lut if np.allclose(dmin, 0) and np.allclose(dmax, 1) else (lut - dmin) / (dmax - dmin)


def apply(img: np.ndarray, lut: np.ndarray) -> np.ndarray:
    a = np.asarray(img)
    is_u8 = a.dtype == np.uint8
    x = a[..., :3].astype(np.float64) / (255.0 if is_u8 else 1.0)
    n = lut.shape[0]
    p = np.clip(x, 0, 1) * (n - 1)
    i0 = np.floor(p).astype(int)
    i1 = np.minimum(i0 + 1, n - 1)
    f = p - i0
    r0, g0, b0 = i0[..., 0], i0[..., 1], i0[..., 2]
    r1, g1, b1 = i1[..., 0], i1[..., 1], i1[..., 2]
    fr, fg, fb = f[..., 0:1], f[..., 1:2], f[..., 2:3]

    def L(b, g, r):
        return lut[b, g, r]

    c00 = L(b0, g0, r0) * (1 - fr) + L(b0, g0, r1) * fr
    c10 = L(b0, g1, r0) * (1 - fr) + L(b0, g1, r1) * fr
    c01 = L(b1, g0, r0) * (1 - fr) + L(b1, g0, r1) * fr
    c11 = L(b1, g1, r0) * (1 - fr) + L(b1, g1, r1) * fr
    c0 = c00 * (1 - fg) + c10 * fg
    c1 = c01 * (1 - fg) + c11 * fg
    out = c0 * (1 - fb) + c1 * fb
    if is_u8:
        out = np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)
        if a.shape[-1] == 4:
            out = np.concatenate([out, a[..., 3:4]], -1)
    return out
