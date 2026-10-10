"""Compose video thumbnails with Pillow: photo, scrim, big title, contrast check.

Layout: the photo fills the canvas (cover crop with a focus point), an
optional gradient scrim darkens the text side, and the title is fitted to a
box (largest size whose wrapped lines fit) with a stroke for legibility.
Text colour is checked for WCAG contrast against the pixels under it; the
result reports the ratio so a weak thumbnail is caught before upload.

Usage::

    from thumbnail_composer import compose
    img, report = compose("photo.jpg", "SHE LIVED UNDERWATER 14 DAYS", size=(1280, 720),
                          font_path="/fonts/Inter-Black.ttf", text_color="#FFD21F", text_box=(60, 60, 700, 600))
    img.save("thumb.jpg", quality=92)
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lum(rgb) -> float:
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(lin @ np.array([0.2126, 0.7152, 0.0722]))


def cover(img: Image.Image, size, focus=(0.5, 0.5)) -> Image.Image:
    W, H = size
    s = max(W / img.width, H / img.height)
    r = img.resize((max(W, round(img.width * s)), max(H, round(img.height * s))), Image.Resampling.LANCZOS)
    x = int((r.width - W) * focus[0])
    y = int((r.height - H) * focus[1])
    return r.crop((x, y, x + W, y + H))


def _font(path, size):
    if path:
        return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if draw.textlength(cand, font=font) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_text(draw, text, font_path, box, max_size=200, min_size=16, line_gap=0.1):
    x, y, w, h = box
    for size in range(max_size, min_size - 1, -2):
        f = _font(font_path, size)
        lines = _wrap(draw, text, f, w)
        lh = size * (1 + line_gap)
        if len(lines) * lh <= h and all(draw.textlength(l, font=f) <= w for l in lines):
            return f, lines, size
    f = _font(font_path, min_size)
    return f, _wrap(draw, text, f, w), min_size


def compose(photo, title: str, size=(1280, 720), font_path: str | None = None, text_color: str = "#FFD21F",
            stroke_color: str = "#000000", text_box=None, focus=(0.5, 0.5), scrim: float = 0.55,
            scrim_side: str = "left"):
    src = photo if isinstance(photo, Image.Image) else Image.open(photo)
    W, H = size
    canvas = cover(src.convert("RGB"), size, focus)
    if scrim > 0:
        ramp = np.linspace(scrim, 0.0, W) if scrim_side == "left" else np.linspace(0.0, scrim, W)
        mask = np.tile(ramp, (H, 1))
        arr = np.asarray(canvas, dtype=np.float64) * (1 - mask[..., None])
        canvas = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    box = text_box or (int(W * 0.05), int(H * 0.08), int(W * 0.55), int(H * 0.84))
    draw = ImageDraw.Draw(canvas)
    font, lines, fsize = fit_text(draw, title, font_path, box)
    stroke = max(2, fsize // 14)
    y = box[1]
    for line in lines:
        draw.text((box[0], y), line, font=font, fill=_rgb(text_color), stroke_width=stroke, stroke_fill=_rgb(stroke_color))
        y += int(fsize * 1.1)
    region = np.asarray(canvas)[box[1]:box[1] + box[3], box[0]:box[0] + box[2]].reshape(-1, 3)
    bg_lum = float(np.median([_lum(p) for p in region[:: max(1, len(region) // 2000)]]))
    tl = _lum(_rgb(text_color))
    ratio = (max(tl, bg_lum) + 0.05) / (min(tl, bg_lum) + 0.05)
    return canvas, {"font_size": fsize, "lines": lines, "contrast_vs_median_bg": round(ratio, 2),
                    "readable": ratio >= 3.0}
