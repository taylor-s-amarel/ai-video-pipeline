"""Render crisp title and caption text to transparent RGBA images (Pillow).

* fits text into a box: wraps words and picks the largest font size whose
  lines fit width and height;
* draws with optional stroke (outline) and supersampling (render at 2-4x,
  then downscale) for sharp edges at video resolution;
* supports per-line alignment and line spacing; returns the image and the
  tight bounding box of the ink.

The result is ready to overlay with ffmpeg (``overlay``) or Pillow.

Usage::

    from text_render_rgba import render_text
    img, info = render_text("SHE LIVED UNDERWATER FOR 14 DAYS", "/fonts/Inter-Black.ttf", box=(900, 300),
                            color="#FFD21F", stroke=6, stroke_color="#000000", align="center")
    img.save("title.png")
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont


def _rgba(color, alpha: float = 1.0):
    if isinstance(color, str):
        h = color.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (int(round(255 * alpha)),)
    return tuple(color[:3]) + (int(round(255 * alpha)),)


def wrap(text: str, font, max_w: float, draw) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        cand = f"{cur} {w}".strip()
        if draw.textlength(cand, font=font) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit(text: str, font_path: str, box, max_size: int = 220, min_size: int = 12, line_spacing: float = 1.1,
        stroke: int = 0):
    scratch = ImageDraw.Draw(Image.new("L", (1, 1)))
    bw, bh = box
    for size in range(max_size, min_size - 1, -1):
        f = ImageFont.truetype(font_path, size)
        lines = wrap(text, f, bw - 2 * stroke, scratch)
        widths = [scratch.textlength(l, font=f) + 2 * stroke for l in lines]
        if max(widths) <= bw and len(lines) * size * line_spacing + 2 * stroke <= bh:
            return size, lines
    raise ValueError("text does not fit the box even at the minimum size")


def render_text(text: str, font_path: str, box, color="#FFFFFF", stroke: int = 0, stroke_color="#000000",
                align: str = "center", line_spacing: float = 1.1, supersample: int = 3, opacity: float = 0.98,
                max_size: int = 220):
    if align not in ("left", "center", "right"):
        raise ValueError("align must be left, center or right")
    if not 0 < opacity <= 1:
        raise ValueError("opacity must be within (0, 1]")
    size, lines = fit(text, font_path, box, max_size=max_size, line_spacing=line_spacing, stroke=stroke)
    s = max(1, int(supersample))
    W, H = box[0] * s, box[1] * s
    font = ImageFont.truetype(font_path, size * s)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lh = size * s * line_spacing
    total_h = lh * (len(lines) - 1) + size * s
    y = (H - total_h) / 2
    for line in lines:
        lw = d.textlength(line, font=font)
        x = {"left": stroke * s, "center": (W - lw) / 2, "right": W - lw - stroke * s}[align]
        d.text((x, y), line, font=font, fill=_rgba(color), stroke_width=stroke * s,
               stroke_fill=_rgba(stroke_color))
        y += lh
    if s > 1:
        img = img.resize(tuple(box), Image.Resampling.LANCZOS)
    # apply opacity after resampling so filter overshoot can never exceed the cap
    img.putalpha(img.getchannel("A").point(lambda v: int(round(v * opacity))))
    return img, {"font_size": size, "lines": lines, "ink_bbox": img.getbbox()}
