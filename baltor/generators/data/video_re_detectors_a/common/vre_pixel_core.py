"""vre_pixel_core: shared helpers for the video_re pixel detectors (geometry, quality, colour, effects).

Every detector package ships an identical copy of this file. It holds:

* decoding with ffmpeg/ffprobe (subprocesses; frames are held in memory only and never written to disk),
* pure-numpy image operations (blur, gradients, phase correlation, colour conversion, k-means,
  connected components, persistent-edge rectangles, static edge bars, a fallback cut detector),
* the result envelope (``baltor.video-detection/v1``) and a shared command-line runner.

Conventions
-----------
* Frames are ``uint8`` arrays shaped ``(N, H, W, 3)`` (RGB). Single images are ``(H, W, 3)``.
* Grey/luma values are float32 on the 0-255 scale. Luma is Rec.709 Y' computed on gamma-encoded RGB.
* Pixel positions are ``x`` (column) and ``y`` (row), origin top-left; a bbox is ``[x, y, w, h]``.
* Nothing here needs scipy/OpenCV. numpy is the only import-time dependency.

MIT licence. Part of the Baltor public-good video_re detector set.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np

CORE_VERSION = "1.0.0"
ENVELOPE_SPEC = "baltor.video-detection/v1"
HERE = Path(__file__).resolve().parent

# --------------------------------------------------------------------------------------------- tools


def tool_versions() -> dict:
    out = {"numpy": np.__version__, "vre_pixel_core": CORE_VERSION}
    exe = shutil.which("ffmpeg")
    if exe:
        try:
            first = subprocess.run([exe, "-hide_banner", "-version"], capture_output=True, text=True,
                                   timeout=20).stdout.splitlines()[0]
            m = re.search(r"ffmpeg version (\S+)", first)
            out["ffmpeg"] = m.group(1) if m else first[:60]
        except Exception:  # noqa: BLE001
            out["ffmpeg"] = "present"
    return out


class Unavailable(RuntimeError):
    """A required external tool (ffmpeg/ffprobe) is missing."""


def _fraction(text: str | None) -> float | None:
    if not text or text in {"0/0", "N/A"}:
        return None
    try:
        if "/" in text:
            a, b = text.split("/", 1)
            return float(a) / float(b) if float(b) else None
        return float(text)
    except ValueError:
        return None


def probe(path: str) -> dict:
    """ffprobe metadata of the first video stream, with display size after rotation."""
    exe = shutil.which("ffprobe")
    if not exe:
        raise Unavailable("ffprobe is not installed")
    proc = subprocess.run([exe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
                          capture_output=True, text=True, timeout=120)
    if proc.returncode:
        raise RuntimeError(f"ffprobe failed: {proc.stderr.strip()[:300]}")
    data = json.loads(proc.stdout or "{}")
    streams = data.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    if v is None:
        raise RuntimeError("no video stream")
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    rotation = 0
    for sd in v.get("side_data_list") or []:
        if "rotation" in sd:
            rotation = int(float(sd["rotation"]))
    if not rotation and (v.get("tags") or {}).get("rotate"):
        rotation = int(float(v["tags"]["rotate"]))
    if abs(rotation) % 180 == 90:
        w, h = h, w
    pix_fmt = v.get("pix_fmt") or ""
    m = re.search(r"p(\d+)(le|be)$", pix_fmt)
    bit_depth = int(v.get("bits_per_raw_sample") or (m.group(1) if m else 8))
    fmt = data.get("format", {})
    duration = _fraction(v.get("duration")) or _fraction(fmt.get("duration"))
    return {
        "width": w, "height": h, "rotation": rotation,
        "fps": _fraction(v.get("avg_frame_rate")) or _fraction(v.get("r_frame_rate")),
        "r_frame_rate": _fraction(v.get("r_frame_rate")),
        "avg_frame_rate": _fraction(v.get("avg_frame_rate")),
        "duration_s": duration,
        "nb_frames": int(v["nb_frames"]) if str(v.get("nb_frames", "")).isdigit() else None,
        "codec": v.get("codec_name"), "pix_fmt": pix_fmt, "bit_depth": bit_depth,
        "color_range": v.get("color_range"), "color_space": v.get("color_space"),
        "color_primaries": v.get("color_primaries"), "color_transfer": v.get("color_transfer"),
        "field_order": v.get("field_order"),
        "has_audio": any(s.get("codec_type") == "audio" for s in streams),
    }


def _even(x: float) -> int:
    return max(2, int(round(x / 2.0)) * 2)


def decode_video(path: str, info: dict | None = None, width: int | None = 320, fps: float | None = 2.0,
                 max_frames: int | None = 120, start_s: float = 0.0, duration_s: float | None = None,
                 crop: tuple[int, int] | None = None, crop_align: int = 2, mode: str = "rgb24"):
    """Decode frames with ffmpeg into memory.

    width: analysis width (aspect kept, even); None keeps native size. fps: sampling rate through the
    ``fps`` filter; None decodes every frame with its own timestamp (passthrough). crop: (w, h) centre crop
    at native resolution applied *instead of* scaling (offsets aligned to ``crop_align`` px, e.g. 16 to keep
    the codec's 8x8 grid). mode: ``rgb24`` -> (N,H,W,3) uint8; ``y`` -> raw luma codes of the Y plane with
    no range conversion, (N,H,W) uint8 or uint16 for >8-bit sources.
    Returns (frames, times_s, info).
    """
    exe = shutil.which("ffmpeg")
    if not exe:
        raise Unavailable("ffmpeg is not installed")
    info = info or probe(path)
    W, H = int(info["width"]), int(info["height"])
    filters = []
    if fps:
        filters.append(f"fps={float(fps):g}")
    if crop:
        cw, ch = min(int(crop[0]), W), min(int(crop[1]), H)
        cw, ch = cw - cw % 2, ch - ch % 2
        x0 = ((W - cw) // 2) // crop_align * crop_align
        y0 = ((H - ch) // 2) // crop_align * crop_align
        filters.append(f"crop={cw}:{ch}:{x0}:{y0}")
        out_w, out_h = cw, ch
    elif width and width < W:
        out_w = _even(width)
        out_h = _even(H * out_w / W)
        filters.append(f"scale={out_w}:{out_h}:flags=area")
    else:
        out_w, out_h = W - W % 2, H - H % 2
        if (out_w, out_h) != (W, H):
            filters.append(f"crop={out_w}:{out_h}:0:0")
    filters.append("showinfo")
    if mode == "y":
        hi = int(info.get("bit_depth") or 8) > 8
        pix = "yuv420p10le" if hi else "yuv420p"
        bpp = 2 if hi else 1
        frame_bytes = (out_w * out_h + 2 * ((out_w + 1) // 2) * ((out_h + 1) // 2)) * bpp
    else:
        pix, bpp = "rgb24", 1
        frame_bytes = out_w * out_h * 3
    cmd = [exe, "-hide_banner", "-nostats", "-v", "info"]
    if start_s:
        cmd += ["-ss", f"{start_s:.3f}"]
    cmd += ["-i", path]
    if duration_s:
        cmd += ["-t", f"{duration_s:.3f}"]
    if not fps:
        cmd += ["-fps_mode", "passthrough"]
    cmd += ["-vf", ",".join(filters), "-an", "-sn"]
    if max_frames:
        cmd += ["-frames:v", str(int(max_frames))]
    cmd += ["-f", "rawvideo", "-pix_fmt", pix, "-"]
    proc = subprocess.run(cmd, capture_output=True, timeout=1800)
    if proc.returncode:
        raise RuntimeError(f"ffmpeg decode failed: {proc.stderr.decode(errors='replace').strip()[-300:]}")
    raw = proc.stdout
    n = len(raw) // frame_bytes
    stamps = [float(m) for m in re.findall(rb"pts_time:\s*([-0-9.e+]+)", proc.stderr)]
    if mode == "y":
        dtype = np.uint16 if bpp == 2 else np.uint8
        arr = np.frombuffer(raw[: n * frame_bytes], dtype=dtype).reshape(n, frame_bytes // bpp)
        frames = arr[:, : out_w * out_h].reshape(n, out_h, out_w).copy()
    else:
        frames = np.frombuffer(raw[: n * frame_bytes], dtype=np.uint8).reshape(n, out_h, out_w, 3).copy()
    info = dict(info)
    info["analysis_size"] = [int(out_w), int(out_h)]
    info["analysis_scale"] = 1.0 if crop else float(W) / float(out_w)
    if len(stamps) >= n:
        times = np.array(stamps[:n], dtype=np.float64) + float(start_s or 0.0)
    else:
        rate = float(fps or info.get("fps") or 25.0)
        times = np.arange(n, dtype=np.float64) / rate + float(start_s or 0.0)
    return frames, times, info


# --------------------------------------------------------------------------------------------- basic ops


def as_float(img) -> np.ndarray:
    return np.asarray(img, dtype=np.float32)


def luma(rgb) -> np.ndarray:
    """Rec.709 luma Y' of gamma-encoded RGB, float32 0-255. Accepts (...,3)."""
    a = np.asarray(rgb, dtype=np.float32)
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def gray_frames(frames) -> np.ndarray:
    f = np.asarray(frames)
    return luma(f) if f.shape[-1] == 3 else f.astype(np.float32)


def _take(a: np.ndarray, axis: int, start: int, stop: int) -> np.ndarray:
    idx = [slice(None)] * a.ndim
    idx[axis] = slice(start, stop)
    return a[tuple(idx)]


def conv1d(a: np.ndarray, kernel, axis: int) -> np.ndarray:
    """Correlate along one axis with reflect padding (edge padding when the axis is too short)."""
    a = np.asarray(a, dtype=np.float32)
    k = np.asarray(kernel, dtype=np.float32)
    r = len(k) // 2
    n = a.shape[axis]
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r, len(k) - 1 - r)
    p = np.pad(a, pad, mode="reflect" if n > len(k) else "edge")
    out = np.zeros(a.shape, dtype=np.float32)
    for i, w in enumerate(k):
        if w:
            out += w * _take(p, axis, i, i + n)
    return out


def gaussian_kernel(sigma: float) -> np.ndarray:
    r = max(1, int(math.ceil(3.0 * sigma)))
    x = np.arange(-r, r + 1, dtype=np.float32)
    k = np.exp(-0.5 * (x / max(sigma, 1e-6)) ** 2)
    return k / k.sum()


def box_blur(img, radius: int, axes=(-2, -1)) -> np.ndarray:
    """Mean over a (2r+1) window along the given axes, edge padded. O(1) per pixel via cumulative sums."""
    out = np.asarray(img, dtype=np.float32)
    if radius <= 0:
        return out.copy()
    for ax in axes:
        ax = ax % out.ndim
        n = out.shape[ax]
        pad = [(0, 0)] * out.ndim
        pad[ax] = (radius + 1, radius)
        p = np.pad(out, pad, mode="edge").astype(np.float64)
        c = np.cumsum(p, axis=ax)
        out = ((_take(c, ax, 2 * radius + 1, 2 * radius + 1 + n) - _take(c, ax, 0, n)) / (2 * radius + 1)).astype(np.float32)
    return out


def blur(img, sigma: float, axes=(-2, -1)) -> np.ndarray:
    """Gaussian blur on the given axes. Above sigma 6 a three-pass box approximation is used."""
    a = np.asarray(img, dtype=np.float32)
    if sigma <= 0:
        return a.copy()
    if sigma > 6:
        # three box passes with the same variance (Kovesi 2010): w = sqrt(12 s^2 / 3 + 1)
        r = max(1, int(round((math.sqrt(4.0 * sigma * sigma + 1.0) - 1.0) / 2.0)))
        out = a
        for _ in range(3):
            out = box_blur(out, r, axes)
        return out
    k = gaussian_kernel(sigma)
    out = a
    for ax in axes:
        out = conv1d(out, k, ax % a.ndim)
    return out


def blur_rgb(img, sigma: float) -> np.ndarray:
    """Gaussian blur of (...,H,W,3) arrays on the spatial axes."""
    return blur(img, sigma, axes=(-3, -2))


def gradients(gray) -> tuple[np.ndarray, np.ndarray]:
    """Sobel gradients (gx, gy) on the last two axes, divided by 8 so a unit step gives about 0.5."""
    g = np.asarray(gray, dtype=np.float32)
    sm = np.array([1, 2, 1], np.float32)
    df = np.array([-1, 0, 1], np.float32)
    gx = conv1d(conv1d(g, df, g.ndim - 1), sm, g.ndim - 2) / 8.0
    gy = conv1d(conv1d(g, df, g.ndim - 2), sm, g.ndim - 1) / 8.0
    return gx, gy


def grad_mag(gray) -> np.ndarray:
    gx, gy = gradients(gray)
    return np.hypot(gx, gy)


def laplacian(gray) -> np.ndarray:
    g = np.asarray(gray, dtype=np.float32)
    p = np.pad(g, [(0, 0)] * (g.ndim - 2) + [(1, 1), (1, 1)], mode="edge")
    return (p[..., :-2, 1:-1] + p[..., 2:, 1:-1] + p[..., 1:-1, :-2] + p[..., 1:-1, 2:] - 4 * p[..., 1:-1, 1:-1])


def downscale(img, factor: int) -> np.ndarray:
    """Block-mean downscale of the first two (spatial) axes of (H,W) or (H,W,C)."""
    a = np.asarray(img, dtype=np.float32)
    if factor <= 1:
        return a
    h, w = a.shape[0] // factor * factor, a.shape[1] // factor * factor
    a = a[:h, :w]
    shp = (h // factor, factor, w // factor, factor) + a.shape[2:]
    return a.reshape(shp).mean(axis=(1, 3))


def resize_bilinear(img, out_h: int, out_w: int) -> np.ndarray:
    """Bilinear resize of the first two axes (pixel-centre aligned)."""
    a = np.asarray(img, dtype=np.float32)
    h, w = a.shape[:2]
    ys = (np.arange(out_h) + 0.5) * h / out_h - 0.5
    xs = (np.arange(out_w) + 0.5) * w / out_w - 0.5
    ys = np.clip(ys, 0, h - 1)
    xs = np.clip(xs, 0, w - 1)
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    y1 = np.minimum(y0 + 1, h - 1)
    x1 = np.minimum(x0 + 1, w - 1)
    wy = (ys - y0).astype(np.float32)
    wx = (xs - x0).astype(np.float32)
    if a.ndim == 3:
        wy = wy[:, None, None]
        wx = wx[None, :, None]
    else:
        wy = wy[:, None]
        wx = wx[None, :]
    top = a[y0][:, x0] * (1 - wx) + a[y0][:, x1] * wx
    bot = a[y1][:, x0] * (1 - wx) + a[y1][:, x1] * wx
    return top * (1 - wy) + bot * wy


def warp_affine_scale(img, scale: float, cx: float | None = None, cy: float | None = None,
                      dx: float = 0.0, dy: float = 0.0) -> np.ndarray:
    """Sample img at ((x - cx - dx)/scale + cx, ...): zoom by `scale` about (cx, cy), then translate. Bilinear."""
    a = np.asarray(img, dtype=np.float32)
    h, w = a.shape[:2]
    cx = (w - 1) / 2.0 if cx is None else cx
    cy = (h - 1) / 2.0 if cy is None else cy
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    sx = (xx - cx - dx) / scale + cx
    sy = (yy - cy - dy) / scale + cy
    return sample_bilinear(a, sx, sy)


def sample_bilinear(a: np.ndarray, sx: np.ndarray, sy: np.ndarray) -> np.ndarray:
    h, w = a.shape[:2]
    sx = np.clip(sx, 0, w - 1.001)
    sy = np.clip(sy, 0, h - 1.001)
    x0 = np.floor(sx).astype(int)
    y0 = np.floor(sy).astype(int)
    fx = sx - x0
    fy = sy - y0
    if a.ndim == 3:
        fx = fx[..., None]
        fy = fy[..., None]
    return (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy)
            + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy)


def dilate(mask, r: int) -> np.ndarray:
    """Binary dilation with a (2r+1) square."""
    m = np.asarray(mask, dtype=bool)
    if r <= 0:
        return m.copy()
    return box_blur(m.astype(np.float32), r, axes=(0, 1)) > 1e-6


def erode(mask, r: int) -> np.ndarray:
    m = np.asarray(mask, dtype=bool)
    if r <= 0:
        return m.copy()
    return box_blur(m.astype(np.float32), r, axes=(0, 1)) > 1 - 1e-6


def distance_from(mask, max_d: int) -> np.ndarray:
    """Approximate (octagonal) distance in px from the True pixels of mask, capped at max_d+1."""
    m = np.asarray(mask, dtype=bool)
    dist = np.full(m.shape, max_d + 1, dtype=np.float32)
    dist[m] = 0
    cur = m.copy()
    for d in range(1, max_d + 1):
        p = np.pad(cur, 1)
        grow = p[1:-1, :-2] | p[1:-1, 2:] | p[:-2, 1:-1] | p[2:, 1:-1]
        if d % 2 == 0:
            grow |= p[:-2, :-2] | p[:-2, 2:] | p[2:, :-2] | p[2:, 2:]
        new = grow & ~cur
        dist[new] = d
        cur |= new
    return dist


# --------------------------------------------------------------------------------------------- frequency


def hann2d(h: int, w: int) -> np.ndarray:
    return np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)


def phase_correlation(a, b, window: bool = True) -> tuple[float, float, float]:
    """Translation (dx, dy) such that b(x, y) ~ a(x - dx, y - dy), and the correlation peak (0-1).

    Sub-pixel accuracy from a parabolic fit around the peak. Shifts beyond half the size wrap.
    """
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    a = a - a.mean()
    b = b - b.mean()
    if window:
        win = hann2d(*a.shape)
        a = a * win
        b = b * win
    fa = np.fft.fft2(a)
    fb = np.fft.fft2(b)
    r = np.conj(fa) * fb
    r /= np.abs(r) + 1e-9
    c = np.fft.ifft2(r).real
    h, w = c.shape
    iy, ix = np.unravel_index(int(np.argmax(c)), c.shape)
    peak = float(c[iy, ix])

    def sub(cm, c0, cp):
        den = cm - 2 * c0 + cp
        return 0.0 if abs(den) < 1e-12 else 0.5 * (cm - cp) / den

    dx = ix + sub(c[iy, (ix - 1) % w], c[iy, ix], c[iy, (ix + 1) % w])
    dy = iy + sub(c[(iy - 1) % h, ix], c[iy, ix], c[(iy + 1) % h, ix])
    if dx > w / 2:
        dx -= w
    if dy > h / 2:
        dy -= h
    return float(dx), float(dy), peak


def global_motion(gray_frames, max_side: int = 256) -> tuple[np.ndarray, np.ndarray]:
    """Frame-to-frame translation (dx, dy) in px of the given frames and the phase-correlation peaks.

    Returns (shifts (N-1, 2), peaks (N-1,)). Frames larger than max_side are block-downscaled for speed and
    the shifts are scaled back.
    """
    g = np.asarray(gray_frames, dtype=np.float32)
    factor = max(1, int(math.ceil(max(g.shape[1:]) / max_side)))
    small = np.stack([downscale(f, factor) for f in g]) if factor > 1 else g
    shifts, peaks = [], []
    for i in range(1, len(small)):
        dx, dy, p = phase_correlation(small[i - 1], small[i])
        shifts.append((dx * factor, dy * factor))
        peaks.append(p)
    return np.array(shifts, dtype=np.float64).reshape(-1, 2), np.array(peaks, dtype=np.float64)


def radial_profile(power: np.ndarray, nbins: int = 64) -> tuple[np.ndarray, np.ndarray]:
    """Mean of a centred 2-D spectrum in rings of normalised frequency (0 .. 0.5 cycles/px)."""
    h, w = power.shape
    fy = np.fft.fftshift(np.fft.fftfreq(h))[:, None]
    fx = np.fft.fftshift(np.fft.fftfreq(w))[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2)
    edges = np.linspace(0, 0.5, nbins + 1)
    idx = np.clip(np.digitize(f.ravel(), edges) - 1, 0, nbins)
    sums = np.bincount(idx, weights=power.ravel(), minlength=nbins + 1)[:nbins]
    counts = np.bincount(idx, minlength=nbins + 1)[:nbins]
    centers = (edges[:-1] + edges[1:]) / 2
    return centers, sums / np.maximum(counts, 1)


# --------------------------------------------------------------------------------------------- colour


def srgb_to_linear(c) -> np.ndarray:
    c = np.asarray(c, dtype=np.float32) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def linear_to_srgb(c) -> np.ndarray:
    c = np.clip(np.asarray(c, dtype=np.float32), 0, 1)
    return (np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(c, 1 / 2.4) - 0.055) * 255.0).astype(np.float32)


_M_RGB2XYZ = np.array([[0.4124564, 0.3575761, 0.1804375],
                       [0.2126729, 0.7151522, 0.0721750],
                       [0.0193339, 0.1191920, 0.9503041]], dtype=np.float32)
_WHITE_D65 = np.array([0.95047, 1.0, 1.08883], dtype=np.float32)


def linear_to_xyz(lin) -> np.ndarray:
    return np.asarray(lin, dtype=np.float32) @ _M_RGB2XYZ.T


def xyz_to_lab(xyz) -> np.ndarray:
    t = np.asarray(xyz, dtype=np.float32) / _WHITE_D65
    d = 6 / 29
    f = np.where(t > d ** 3, np.cbrt(t), t / (3 * d * d) + 4 / 29)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], axis=-1).astype(np.float32)


def rgb_to_lab(rgb) -> np.ndarray:
    """sRGB (0-255) to CIELAB (D65)."""
    return xyz_to_lab(linear_to_xyz(srgb_to_linear(rgb)))


def lab_to_rgb(lab) -> np.ndarray:
    lab = np.asarray(lab, dtype=np.float32)
    fy = (lab[..., 0] + 16) / 116
    fx = fy + lab[..., 1] / 500
    fz = fy - lab[..., 2] / 200
    d = 6 / 29

    def inv(f):
        return np.where(f > d, f ** 3, 3 * d * d * (f - 4 / 29))

    xyz = np.stack([inv(fx), inv(fy), inv(fz)], axis=-1) * _WHITE_D65
    lin = xyz @ np.linalg.inv(_M_RGB2XYZ).T.astype(np.float32)
    return linear_to_srgb(lin)


def rgb_to_hsv(rgb) -> np.ndarray:
    """(...,3) 0-255 RGB to HSV with H in degrees [0,360), S and V in [0,1]."""
    a = np.asarray(rgb, dtype=np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(axis=-1)
    mn = a.min(axis=-1)
    d = mx - mn
    h = np.zeros_like(mx)
    nz = d > 1e-6
    rm = nz & (mx == r)
    gm = nz & (mx == g) & ~rm
    bm = nz & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = (b - r)[gm] / d[gm] + 2
    h[bm] = (r - g)[bm] / d[bm] + 4
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0)
    return np.stack([h * 60.0, s, mx], axis=-1).astype(np.float32)


def hex_color(rgb) -> str:
    c = np.clip(np.round(np.asarray(rgb, dtype=np.float64)), 0, 255).astype(int)
    return "#{:02X}{:02X}{:02X}".format(*c[:3])


def hex_to_rgb(text: str) -> np.ndarray:
    t = text.lstrip("#")
    return np.array([int(t[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def delta_e(lab1, lab2) -> np.ndarray:
    """CIE76 colour difference."""
    return np.linalg.norm(np.asarray(lab1, np.float32) - np.asarray(lab2, np.float32), axis=-1)


def kmeans(x, k: int, iters: int = 25, seed: int = 0, weights=None) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic k-means (k-means++ seeding). x: (n, d). Returns (centers (k', d), labels (n,))."""
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    k = max(1, min(k, n))
    rng = np.random.default_rng(seed)
    w = np.ones(n) if weights is None else np.asarray(weights, dtype=np.float64)
    centers = [x[int(rng.choice(n, p=w / w.sum()))]]
    for _ in range(1, k):
        d2 = np.min(((x[:, None, :] - np.array(centers)[None]) ** 2).sum(-1), axis=1) * w
        if d2.sum() <= 0:
            break
        centers.append(x[int(rng.choice(n, p=d2 / d2.sum()))])
    c = np.array(centers)
    labels = np.zeros(n, dtype=int)
    for _ in range(iters):
        d2 = ((x[:, None, :] - c[None]) ** 2).sum(-1)
        new = d2.argmin(1)
        if np.array_equal(new, labels) and _ > 0:
            break
        labels = new
        for j in range(len(c)):
            m = labels == j
            if m.any():
                c[j] = (x[m] * w[m, None]).sum(0) / w[m].sum()
    return c, labels


# --------------------------------------------------------------------------------------------- regions


def label_components(mask, connectivity: int = 8) -> tuple[np.ndarray, int]:
    """Connected-component labelling (run-based union-find). Returns (labels int32, count); 0 = background."""
    m = np.asarray(mask, dtype=bool)
    h, w = m.shape
    labels = np.zeros((h, w), dtype=np.int32)
    parent = [0]

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    ext = 1 if connectivity == 8 else 0
    prev: list[tuple[int, int, int]] = []
    for y in range(h):
        row = m[y].astype(np.int8)
        d = np.diff(np.concatenate(([0], row, [0])))
        starts = np.flatnonzero(d == 1)
        ends = np.flatnonzero(d == -1)
        cur = []
        j = 0
        for s, e in zip(starts.tolist(), ends.tolist()):
            while j < len(prev) and prev[j][1] + ext <= s:
                j += 1
            lab = 0
            k = j
            while k < len(prev) and prev[k][0] < e + ext:
                r = find(prev[k][2])
                if lab == 0:
                    lab = r
                elif r != lab:
                    parent[max(r, lab)] = min(r, lab)
                    lab = min(r, lab)
                k += 1
            if lab == 0:
                parent.append(len(parent))
                lab = len(parent) - 1
            labels[y, s:e] = lab
            cur.append((s, e, lab))
        prev = cur
    roots = np.array([find(i) for i in range(len(parent))], dtype=np.int32)
    uniq = np.unique(roots[1:]) if len(roots) > 1 else np.array([], dtype=np.int32)
    remap = np.zeros(len(parent), dtype=np.int32)
    lut = {int(r): i + 1 for i, r in enumerate(uniq.tolist())}
    for i in range(1, len(parent)):
        remap[i] = lut[int(roots[i])]
    return remap[labels], len(uniq)


def component_boxes(mask, min_area: int = 1, connectivity: int = 8) -> list[dict]:
    """Bounding boxes of connected components: [{bbox:[x,y,w,h], area, fill, centroid:[x,y]}], largest first."""
    labels, n = label_components(mask, connectivity)
    out = []
    if n == 0:
        return out
    ys, xs = np.nonzero(labels)
    ls = labels[ys, xs]
    for i in range(1, n + 1):
        sel = ls == i
        area = int(sel.sum())
        if area < min_area:
            continue
        x0, x1 = int(xs[sel].min()), int(xs[sel].max())
        y0, y1 = int(ys[sel].min()), int(ys[sel].max())
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        out.append({"bbox": [x0, y0, bw, bh], "area": area, "fill": area / float(bw * bh),
                    "centroid": [float(xs[sel].mean()), float(ys[sel].mean())]})
    out.sort(key=lambda d: -d["area"])
    return out


def persistent_edges(gray_frames, rel_thr: float = 3.0, abs_thr: float = 4.0) -> tuple[np.ndarray, np.ndarray]:
    """Fraction of frames in which each pixel holds a strong vertical edge (Ev, from |gx|) or horizontal edge
    (Eh, from |gy|). Strong = above max(abs_thr, rel_thr x that frame's median gradient)."""
    g = np.asarray(gray_frames, dtype=np.float32)
    gx, gy = gradients(g)
    ax, ay = np.abs(gx), np.abs(gy)
    med = np.median(np.hypot(gx, gy).reshape(len(g), -1), axis=1)
    thr = np.maximum(abs_thr, rel_thr * med)[:, None, None]
    return (ax > thr).mean(0), (ay > thr).mean(0)


def edge_segments(E, axis: str, min_len: int, thr: float = 0.7, max_gap: int = 2) -> list[tuple[int, int, int]]:
    """Straight runs in a persistence map. axis 'v': vertical runs -> (x, y0, y1); 'h': horizontal -> (y, x0, x1).
    Runs separated by up to max_gap weak pixels are joined. Adjacent duplicate lines are thinned to the strongest."""
    E = np.asarray(E)
    M = (E >= thr)
    if axis == "h":
        M = M.T
        E = E.T
    h, w = M.shape
    segs = []
    for x in range(w):
        col = M[:, x]
        if not col.any():
            continue
        idx = np.flatnonzero(col)
        groups = np.split(idx, np.flatnonzero(np.diff(idx) > max_gap + 1) + 1)
        for g in groups:
            if len(g) and g[-1] - g[0] + 1 >= min_len:
                segs.append((x, int(g[0]), int(g[-1]), float(E[g[0]:g[-1] + 1, x].mean())))
    # thin: among segments in neighbouring positions with overlapping extents keep the strongest
    segs.sort(key=lambda s: -s[3] * (s[2] - s[1]))
    kept: list[tuple[int, int, int, float]] = []
    for s in segs:
        if any(abs(s[0] - k[0]) <= 1 and min(s[2], k[2]) - max(s[1], k[1]) > 0.5 * (s[2] - s[1]) for k in kept):
            continue
        kept.append(s)
    return [(s[0], s[1], s[2]) for s in sorted(kept)]


def find_rectangles(Ev, Eh, min_w: int, min_h: int, tol: int = 3, corner_gap: int = 0,
                    thr: float = 0.7) -> list[dict]:
    """Axis-aligned rectangles whose four sides are persistent edges.

    corner_gap allows sides that stop short of the corners (rounded corners). Each rectangle:
    {bbox:[x,y,w,h], support} where support = mean coverage of the four sides (0-1)."""
    vs = edge_segments(Ev, "v", max(4, min_h // 2), thr)
    hs = edge_segments(Eh, "h", max(4, min_w // 2), thr)
    rects = []
    for i, (xa, ya0, ya1) in enumerate(vs):
        for xb, yb0, yb1 in vs[i + 1:]:
            if xb - xa < min_w:
                continue
            y0 = min(ya0, yb0)
            y1 = max(ya1, yb1)
            if min(ya1, yb1) - max(ya0, yb0) < 0.6 * max(ya1 - ya0, yb1 - yb0):
                continue
            top = [s for s in hs if abs(s[0] - (y0 - corner_gap - 1)) <= tol + corner_gap and s[1] <= xa + tol + corner_gap and s[2] >= xb - tol - corner_gap]
            bot = [s for s in hs if abs(s[0] - (y1 + corner_gap + 1)) <= tol + corner_gap and s[1] <= xa + tol + corner_gap and s[2] >= xb - tol - corner_gap]
            if not top or not bot:
                continue
            ty = min(top, key=lambda s: abs(s[0] - (y0 - corner_gap - 1)))[0]
            by = min(bot, key=lambda s: abs(s[0] - (y1 + corner_gap + 1)))[0]
            if by - ty < min_h:
                continue
            x0, x1, yy0, yy1 = xa, xb, ty, by
            sides = [Ev[yy0:yy1 + 1, x0].mean(), Ev[yy0:yy1 + 1, x1].mean(),
                     Eh[yy0, x0:x1 + 1].mean(), Eh[yy1, x0:x1 + 1].mean()]
            rects.append({"bbox": [int(x0), int(yy0), int(x1 - x0), int(yy1 - yy0)], "support": float(np.mean(sides))})
    # remove near-duplicates (keep best support)
    rects.sort(key=lambda r: -r["support"])
    out: list[dict] = []
    for r in rects:
        if any(iou(r["bbox"], o["bbox"]) > 0.85 for o in out):
            continue
        out.append(r)
    return out


def iou(a, b) -> float:
    ax0, ay0, aw, ah = a
    bx0, by0, bw, bh = b
    ix = max(0.0, min(ax0 + aw, bx0 + bw) - max(ax0, bx0))
    iy = max(0.0, min(ay0 + ah, by0 + bh) - max(ay0, by0))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def rounded_rect_mask(h: int, w: int, x0: int, y0: int, rw: int, rh: int, r: float) -> np.ndarray:
    """Boolean mask of an axis-aligned rectangle with corner radius r (pixel centres tested)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    m = (xx >= x0) & (xx < x0 + rw) & (yy >= y0) & (yy < y0 + rh)
    if r > 0:
        for cx, cy, sx, sy in ((x0 + r, y0 + r, -1, -1), (x0 + rw - r, y0 + r, 1, -1),
                               (x0 + r, y0 + rh - r, -1, 1), (x0 + rw - r, y0 + rh - r, 1, 1)):
            zone = ((xx - cx) * sx > 0) & ((yy - cy) * sy > 0)
            m &= ~(zone & ((xx - cx) ** 2 + (yy - cy) ** 2 > r * r))
    return m


def corner_radius_fit(insets, max_r: float | None = None) -> tuple[float, float]:
    """Fit a circular corner to an inset profile.

    insets[i] = how many pixels, counted inwards from the straight side, are *outside* the shape in the i-th
    pixel row away from the corner. A radius-r corner gives r - sqrt(r^2 - (r - (i + 0.5))^2) for i + 0.5 < r and
    0 after. Grid search in 0.25 px steps; returns (radius_px, rmse_px)."""
    ins = np.asarray(insets, dtype=np.float64)
    n = len(ins)
    if n == 0:
        return 0.0, 0.0
    max_r = float(max_r or n)
    i = np.arange(n) + 0.5
    best_r, best_e = 0.0, float(np.sqrt(np.mean(ins ** 2)))
    for r in np.arange(0.25, max_r + 0.01, 0.25):
        model = np.where(i < r, r - np.sqrt(np.maximum(0.0, r * r - (r - i) ** 2)), 0.0)
        e = float(np.sqrt(np.mean((model - ins) ** 2)))
        if e < best_e - 1e-9:
            best_r, best_e = float(r), e
    return best_r, best_e


# --------------------------------------------------------------------------------------------- bars


def scan_edge_bars(frames, tol: float = 12.0, pixel_frac: float = 0.97, frame_quorum: float = 0.9,
                   blur_ratio: float = 0.2, max_frac: float = 0.45, overlay_frac: float = 0.5,
                   overlay_tstd: float = 3.0) -> dict:
    """Uniform bars along each frame edge (letterbox/pillarbox) and blurred-fill bars.

    Solid bars: a line (row or column) is a strict bar line in a frame when at least ``pixel_frac`` of its
    pixels lie within ``tol`` (0-255, max over channels) of the bar colour (median colour of the outermost
    line). A relaxed line (static text or a logo inside the bar) needs only ``overlay_frac`` within tol and a
    mean temporal standard deviation <= ``overlay_tstd``; a bar may cross relaxed lines but must end on a
    strict line. Thickness per frame is the run of qualifying lines from the edge; the reported thickness is
    the (1 - frame_quorum) percentile across frames, so content that is briefly as dark as the bar does not
    widen it.
    Blurred-fill bars (tested when no solid bar is found): lines from the edge whose mean gradient is below
    ``blur_ratio`` x the frame centre's mean gradient. They are 'blurred-fill' when they change over time
    (or when fewer than 3 frames are available) and 'static-texture' otherwise.
    Returns {side: {px, color, style, consistency, overlay_lines}} for top/bottom/left/right.
    """
    f = np.asarray(frames, dtype=np.float32)
    if f.ndim == 3:
        f = f[None]
    n, h, w, _ = f.shape
    g = luma(f)
    gm = grad_mag(g)
    cy0, cy1, cx0, cx1 = int(h * 0.3), int(h * 0.7), int(w * 0.3), int(w * 0.7)
    centre_grad = float(np.mean(gm[:, cy0:cy1, cx0:cx1])) + 1e-6
    out = {}
    for side in ("top", "bottom", "left", "right"):
        if side in ("top", "bottom"):
            lines = f if side == "top" else f[:, ::-1]
            glines = gm if side == "top" else gm[:, ::-1]
            limit = int(h * max_frac)
        else:
            lines = f.transpose(0, 2, 1, 3) if side == "left" else f.transpose(0, 2, 1, 3)[:, ::-1]
            glines = gm.transpose(0, 2, 1) if side == "left" else gm.transpose(0, 2, 1)[:, ::-1]
            limit = int(w * max_frac)
        seg = lines[:, :limit]  # (n, limit, L, 3)
        color = np.median(seg[:, 0].reshape(-1, 3), axis=0)
        within = (np.abs(seg - color).max(axis=-1) <= tol).mean(axis=-1)  # (n, limit)
        strict = within >= pixel_frac
        if n >= 3:
            tstd = seg.std(axis=0).mean(axis=(-1, -2))  # (limit,)
            relaxed = strict | ((within >= overlay_frac) & (tstd <= overlay_tstd)[None, :])
        else:
            relaxed = strict
        thick = np.zeros(n, dtype=int)
        for i in range(n):
            bad = np.flatnonzero(~relaxed[i])
            run = int(bad[0]) if len(bad) else limit
            ok_end = np.flatnonzero(strict[i, :run])
            thick[i] = int(ok_end[-1]) + 1 if len(ok_end) else 0
        px = int(np.percentile(thick, (1 - frame_quorum) * 100, method="lower"))
        overlay_lines = int((~strict[:, :px]).all(axis=0).sum()) if px else 0
        style = "solid"
        if px == 0:
            gl = glines[:, :limit].mean(axis=-1)  # (n, limit)
            low = gl < blur_ratio * centre_grad
            run = np.where(low.all(axis=1), limit, np.argmin(low, axis=1))
            bpx = int(np.percentile(run, (1 - frame_quorum) * 100, method="lower"))
            if bpx >= 4:
                changing = (seg[:, :bpx].std(axis=0).mean() > 2.0) if n >= 3 else True
                px = bpx
                style = "blurred-fill" if changing else "static-texture"
                color = seg[:, :bpx].reshape(-1, 3).mean(axis=0)
                thick = run
        consistency = float(np.mean(np.abs(thick - px) <= 2)) if px else 0.0
        out[side] = {"px": px, "color": hex_color(color), "style": style if px else "none",
                     "consistency": round(consistency, 3), "overlay_lines": overlay_lines}
    return out


def content_rect_from_bars(bars: dict, h: int, w: int) -> list[int]:
    x0 = bars["left"]["px"]
    x1 = w - bars["right"]["px"]
    y0 = bars["top"]["px"]
    y1 = h - bars["bottom"]["px"]
    return [int(x0), int(y0), int(max(0, x1 - x0)), int(max(0, y1 - y0))]


# --------------------------------------------------------------------------------------------- shots


def detect_cuts(frames, times, hist_thr: float = 0.35, diff_thr: float = 18.0) -> list[dict]:
    """Fallback hard-cut detector on sampled frames: a cut is declared between two samples when both the
    colour-histogram distance (L1/2 on 3x16 bins, 0-1) exceeds hist_thr and the mean absolute luma
    difference of 64-px thumbnails exceeds diff_thr. Misses dissolves; can fire on very fast motion.
    Prefer shot lists from the video_re_detect_shots module (--shots)."""
    f = np.asarray(frames)
    t = np.asarray(times, dtype=np.float64)
    n = len(f)
    if n == 0:
        return []
    step = max(1, f.shape[2] // 64)
    thumbs = luma(f[:, ::step, ::step])
    hists = []
    for fr in f[:, ::step, ::step]:
        hh = [np.histogram(fr[..., c], bins=16, range=(0, 256))[0] for c in range(3)]
        hh = np.concatenate(hh).astype(np.float64)
        hists.append(hh / hh.sum())
    starts = [0]
    for i in range(1, n):
        hd = 0.5 * float(np.abs(hists[i] - hists[i - 1]).sum())
        dd = float(np.mean(np.abs(thumbs[i] - thumbs[i - 1])))
        if hd > hist_thr and dd > diff_thr:
            starts.append(i)
    shots = []
    dt = float(np.median(np.diff(t))) if n > 1 else 0.0
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else n
        shots.append({"start_s": float(t[s]), "end_s": float(t[e - 1] + dt), "first": s, "last": e - 1})
    return shots


def load_shots(path: str | None) -> list[tuple[float, float]] | None:
    """Read shots from JSON: a list of {start_s, end_s}, or an object with 'shots' (evidence.json from
    video_re_evidence_bundle) or 'payload': {'shots': [...]} (a detection envelope)."""
    if not path:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("shots") or (data.get("payload") or {}).get("shots") or []
    out = []
    for s in data:
        if isinstance(s, dict) and "start_s" in s and "end_s" in s:
            out.append((float(s["start_s"]), float(s["end_s"])))
    return out or None


def shots_for(frames, times, shots: list[tuple[float, float]] | None) -> list[dict]:
    """Group sampled frames into shots: given shots (start_s, end_s) or the fallback cut detector."""
    t = np.asarray(times, dtype=np.float64)
    if not shots:
        return detect_cuts(frames, t)
    out = []
    for s, e in shots:
        idx = np.flatnonzero((t >= s - 1e-6) & (t < e - 1e-6))
        if len(idx):
            out.append({"start_s": float(s), "end_s": float(e), "first": int(idx[0]), "last": int(idx[-1])})
    return out


# --------------------------------------------------------------------------------------------- envelope


def round_floats(obj: Any, nd: int = 4) -> Any:
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return round(obj, nd)
    if isinstance(obj, (np.floating,)):
        return round_floats(float(obj), nd)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return round_floats(obj.tolist(), nd)
    if isinstance(obj, dict):
        return {str(k): round_floats(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [round_floats(v, nd) for v in obj]
    return obj


def make_envelope(detector: str, version: str, source: dict, status: str, results: list, payload: dict | None,
                  params: dict | None = None, tools: dict | None = None, errors: list | None = None) -> dict:
    env = {
        "spec": ENVELOPE_SPEC,
        "detector": detector,
        "version": version,
        "source": {k: v for k, v in source.items() if v is not None},
        "status": status,
        "results": results,
        "payload": payload,
        "params": params or {},
        "tools": {k: str(v) for k, v in (tools or {}).items()},
        "errors": [str(e) for e in (errors or [])],
    }
    for r in env["results"]:
        if "evidence" in r and isinstance(r["evidence"], str):
            r["evidence"] = r["evidence"][:400]
        if "confidence" in r:
            r["confidence"] = float(min(1.0, max(0.0, r["confidence"])))
    return round_floats(env)


def source_from(info: dict | None, reference: str) -> dict:
    info = info or {}
    src = {"reference": reference}
    for k in ("duration_s", "width", "height", "fps"):
        if info.get(k) is not None:
            src[k] = info[k]
    return src


def validate_against(instance, schema_path) -> list[str]:
    """Validate with jsonschema when installed; returns a list of error messages (empty = valid)."""
    try:
        import jsonschema  # noqa: PLC0415  (optional dependency)
    except ImportError:
        return ["jsonschema not installed"]
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    v = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in v.iter_errors(instance)]


def _parse_value(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def run_cli(identity: str, version: str, analyse: Callable, defaults: dict, doc: str,
            argv: list[str] | None = None, decode: dict | None = None) -> int:
    """Shared command line: decode a video with ffmpeg, run ``analyse(frames, times, info, params)`` and print
    the envelope. ``analyse`` returns {status, results, payload, errors?, params?}.

    Exit status: 0 ok/partial, 2 unavailable (ffmpeg missing), 1 error."""
    decode = dict(decode or {})
    ap = argparse.ArgumentParser(prog=identity, description=doc.strip().splitlines()[0] if doc else identity)
    ap.add_argument("video", help="video file (local path or anything ffmpeg can open)")
    ap.add_argument("--reference", help="reference string to record in the envelope (default: file name)")
    ap.add_argument("--width", type=int, default=decode.get("width"), help="analysis width in px (0 = native)")
    ap.add_argument("--fps", type=float, default=decode.get("fps"), help="sampling rate (0 = every frame)")
    ap.add_argument("--max-frames", type=int, default=decode.get("max_frames"))
    ap.add_argument("--start", type=float, default=0.0, help="start time in seconds")
    ap.add_argument("--duration", type=float, default=decode.get("duration_s"), help="seconds to analyse")
    ap.add_argument("--shots", help="JSON shot list (video_re_detect_shots output or evidence.json)")
    ap.add_argument("--param", action="append", default=[], metavar="KEY=VALUE",
                    help="override a detector parameter (JSON value)")
    ap.add_argument("--out", help="write the envelope here as well as printing it")
    ap.add_argument("--compact", action="store_true")
    a = ap.parse_args(argv)
    params = dict(defaults)
    for kv in a.param:
        k, _, v = kv.partition("=")
        params[k.strip()] = _parse_value(v)
    reference = a.reference or Path(a.video).name
    decode_params = {"analysis_width": a.width or None, "sample_fps": a.fps or None, "max_frames": a.max_frames,
                     "start_s": a.start, "duration_s": a.duration, "crop": decode.get("crop"),
                     "mode": decode.get("mode", "rgb24")}
    tools = tool_versions()
    info = None
    try:
        info = probe(a.video)
        frames, times, info = decode_video(
            a.video, info, width=a.width or None, fps=a.fps or None, max_frames=a.max_frames,
            start_s=a.start, duration_s=a.duration, crop=decode.get("crop"), crop_align=decode.get("crop_align", 2),
            mode=decode.get("mode", "rgb24"))
        if len(frames) == 0:
            raise RuntimeError("no frames decoded")
        params["_shots"] = load_shots(a.shots)
        params["_video_path"] = a.video
        res = analyse(frames, times, info, params)
        params.pop("_shots", None)
        params.pop("_video_path", None)
        all_params = {**{k: v for k, v in params.items() if not k.startswith("_")}, **res.get("params", {}),
                      "decode": decode_params}
        env = make_envelope(identity, version, source_from(info, reference), res["status"], res["results"],
                            res["payload"], all_params, {**tools, **res.get("tools", {})}, res.get("errors"))
        code = 0
    except Unavailable as exc:
        env = make_envelope(identity, version, source_from(info, reference), "unavailable", [], None,
                            {"decode": decode_params}, tools, [str(exc)])
        code = 2
    except Exception as exc:  # noqa: BLE001
        env = make_envelope(identity, version, source_from(info, reference), "error", [], None,
                            {"decode": decode_params}, tools, [f"{type(exc).__name__}: {exc}"])
        code = 1
    text = json.dumps(env, indent=None if a.compact else 2)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return code


def analyse_to_envelope(identity: str, version: str, analyse: Callable, frames, times, info=None,
                        params: dict | None = None, defaults: dict | None = None, reference: str = "synthetic") -> dict:
    """Run a detector's analyse() on in-memory frames and wrap the result (used by tests and notebooks)."""
    p = dict(defaults or {})
    p.update(params or {})
    res = analyse(frames, times, info or {}, p)
    p = {k: v for k, v in p.items() if not k.startswith("_")}
    return make_envelope(identity, version, source_from(info, reference), res["status"], res["results"],
                         res["payload"], {**p, **res.get("params", {})}, res.get("tools", {}), res.get("errors"))


def scale_of(info: dict | None) -> float:
    """Source px per analysed px: set by decode_video (1.0 for native or cropped decoding and for tests)."""
    return float((info or {}).get("analysis_scale") or 1.0)


# --------------------------------------------------------------------------------------------- test helpers


def check_envelope(env: dict, folder) -> list[str]:
    """Validate an envelope against envelope.schema.json and its payload against payload.schema.json in
    ``folder`` (the package directory). Returns error messages; ['jsonschema not installed'] when it is not."""
    folder = Path(folder)
    errs = validate_against(env, folder / "envelope.schema.json")
    if errs == ["jsonschema not installed"]:
        return errs
    if env.get("payload") is not None and (folder / "payload.schema.json").exists():
        errs += [f"payload: {e}" for e in validate_against(env["payload"], folder / "payload.schema.json")]
    return errs


def write_clip(path, frames, fps: float = 10.0) -> str:
    """Encode (N,H,W,3) uint8 frames losslessly (FFV1 in Matroska, RGB) for command-line tests."""
    exe = shutil.which("ffmpeg")
    if not exe:
        raise Unavailable("ffmpeg is not installed")
    f = np.ascontiguousarray(np.asarray(frames, dtype=np.uint8))
    n, h, w, _ = f.shape
    cmd = [exe, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", f"{fps:g}",
           "-i", "-", "-c:v", "ffv1", "-pix_fmt", "bgr0", str(path)]
    subprocess.run(cmd, input=f.tobytes(), check=True, capture_output=True, timeout=120)
    return str(path)
