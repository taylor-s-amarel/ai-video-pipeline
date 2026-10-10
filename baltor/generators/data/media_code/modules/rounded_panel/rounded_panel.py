"""Rounded backing panels (RGBA) with optional gradient, border and soft edge.

Draws the panel behind a title, number or caption: rounded rectangle at
``opacity`` (default 0.6, never above 0.98), optional vertical gradient,
thin border, and a feathered edge made by blurring the alpha mask so there
is no hard cutout. Supersampled for clean corners.

Usage::

    from rounded_panel import panel
    p = panel((920, 260), radius=40, color="#0E1116", opacity=0.6, feather=10, border="#FFD21F", border_px=3)
    frame.alpha_composite(p, (80, 280))
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def panel(size, radius: int = 32, color: str = "#000000", opacity: float = 0.6, gradient_to: str | None = None,
          border: str | None = None, border_px: int = 0, feather: float = 0.0, supersample: int = 3) -> Image.Image:
    if not 0 < opacity <= 0.98:
        raise ValueError("opacity must be within (0, 0.98]")
    w, h = size
    if w <= 0 or h <= 0:
        raise ValueError("size must be positive")
    s = max(1, supersample)
    pad = int(feather * 2) + 2
    W, H = (w + 2 * pad) * s, (h + 2 * pad) * s
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([pad * s, pad * s, (pad + w) * s - 1, (pad + h) * s - 1],
                                           radius=radius * s, fill=int(255 * opacity))
    if feather > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(feather * s / 2))
    top = _rgb(color)
    bottom = _rgb(gradient_to) if gradient_to else top
    fill = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / max(1, H - 1)
        fill.putpixel((0, y), tuple(int(round(a + (b - a) * t)) for a, b in zip(top, bottom)))
    out = fill.resize((W, H)).convert("RGBA")
    out.putalpha(mask)
    if border and border_px > 0:
        d = ImageDraw.Draw(out)
        d.rounded_rectangle([pad * s, pad * s, (pad + w) * s - 1, (pad + h) * s - 1], radius=radius * s,
                            outline=_rgb(border) + (int(255 * 0.98),), width=border_px * s)
    if s > 1:
        out = out.resize((w + 2 * pad, h + 2 * pad), Image.Resampling.LANCZOS)
    return out


def paste_offset(pos, feather: float = 0.0) -> tuple[int, int]:
    """Where to alpha_composite a panel so its body lands at ``pos`` (the feather margin is outside)."""
    pad = int(feather * 2) + 2
    return pos[0] - pad, pos[1] - pad
