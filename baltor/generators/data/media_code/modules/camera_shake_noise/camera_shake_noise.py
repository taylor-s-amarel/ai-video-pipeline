"""Deterministic, smooth camera shake from 1D value noise.

``shake_offsets`` returns per-frame (dx, dy, rotation_deg) from layered
smooth noise. Intensity follows the common "trauma" model: shake amount is
trauma squared, and trauma decays linearly, so a hit starts strong and fades.
``ffmpeg_crop_filter`` gives a sum-of-sines shake that ffmpeg can evaluate
itself (crop + scale back), for when frames are not rendered in Python.

Usage::

    from camera_shake_noise import shake_offsets, ffmpeg_crop_filter
    offs = shake_offsets(frames=45, fps=30, amplitude_px=18, frequency_hz=9, seed=3, decay_s=1.2)
    vf = ffmpeg_crop_filter(1080, 1920, amplitude_px=12, frequency_hz=6)
"""

from __future__ import annotations

import math


def _hash01(i: int, seed: int) -> float:
    # integer hash (xorshift-multiply) -> [0, 1); deterministic across platforms
    x = (i * 374761393 + seed * 668265263) & 0xFFFFFFFF
    x = ((x ^ (x >> 13)) * 1274126177) & 0xFFFFFFFF
    x ^= x >> 16
    return (x & 0xFFFFFF) / float(1 << 24)


def value_noise_1d(t: float, seed: int = 0) -> float:
    """Smooth noise in [-1, 1] with unit lattice spacing (smoothstep interpolation)."""
    i = math.floor(t)
    f = t - i
    u = f * f * (3 - 2 * f)
    a, b = _hash01(i, seed), _hash01(i + 1, seed)
    return (a + (b - a) * u) * 2 - 1


def fbm_1d(t: float, seed: int = 0, octaves: int = 3) -> float:
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * value_noise_1d(t * (2 ** o), seed + 101 * o)
        norm += amp
        amp *= 0.5
    return total / norm


def shake_offsets(frames: int, fps: float = 30, amplitude_px: float = 12, rotation_deg: float = 1.0,
                  frequency_hz: float = 8, seed: int = 0, decay_s: float | None = None,
                  octaves: int = 3) -> list[tuple[float, float, float]]:
    out = []
    for n in range(frames):
        t = n / fps
        trauma = 1.0 if decay_s is None else max(0.0, 1.0 - t / decay_s)
        k = trauma * trauma
        x = fbm_1d(t * frequency_hz, seed, octaves)
        y = fbm_1d(t * frequency_hz, seed + 7919, octaves)
        r = fbm_1d(t * frequency_hz, seed + 15485, octaves)
        out.append((k * amplitude_px * x, k * amplitude_px * y, k * rotation_deg * r))
    return out


def overscan_scale(width: int, height: int, amplitude_px: float, rotation_deg: float = 0.0) -> float:
    """Scale factor needed so shaken frames never reveal an edge."""
    rot = math.radians(abs(rotation_deg))
    need_w = width * math.cos(rot) + height * math.sin(rot) + 2 * amplitude_px
    need_h = width * math.sin(rot) + height * math.cos(rot) + 2 * amplitude_px
    return max(need_w / width, need_h / height)


def ffmpeg_crop_filter(width: int, height: int, amplitude_px: float = 10, frequency_hz: float = 6) -> str:
    """Crop a moving window (sum of incommensurate sines) and scale back to the frame size."""
    a = float(amplitude_px)
    f = 2 * math.pi * frequency_hz
    xs = f"{a:g}+{a * 0.6:g}*sin({f:.4f}*t)+{a * 0.4:g}*sin({f * 2.31:.4f}*t+1.3)"
    ys = f"{a:g}+{a * 0.6:g}*sin({f * 1.13:.4f}*t+0.7)+{a * 0.4:g}*sin({f * 2.71:.4f}*t+2.1)"
    cw, ch = int(width - 2 * a), int(height - 2 * a)
    cw -= cw % 2
    ch -= ch % 2
    return f"crop={cw}:{ch}:x='{xs}':y='{ys}',scale={width}:{height}"
