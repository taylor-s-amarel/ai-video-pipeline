"""Storyboard / contact-sheet grid: frames with timestamps and notes (Pillow).

Lays out frames (Pillow images, any size) in a grid of ``cols`` columns,
each scaled to fit a cell, with a caption strip under every frame showing
the timestamp and an optional note (scene label, shot move). Good for
review handoffs and for checking first-frame and per-scene composition at a
glance. ``timestamps_for`` picks evenly spaced or scene-midpoint times;
``extract_argv`` gives the ffmpeg command to pull one frame.

Usage::

    from storyboard_grid_exporter import contact_sheet, timestamps_for
    sheet = contact_sheet(frames, times=[0, 5, 10], notes=["HOOK", "FACT 1", "FACT 2"], cols=3)
    sheet.save("storyboard.png")
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFont


def _font(size: int, path: str | None):
    if path:
        return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def fmt_time(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:05.2f}"


def timestamps_for(duration: float, count: int, include_first: bool = True) -> list[float]:
    if count < 1 or duration <= 0:
        raise ValueError("count must be >= 1 and duration > 0")
    if include_first:
        return [round(duration * i / count, 3) for i in range(count)]
    return [round(duration * (i + 0.5) / count, 3) for i in range(count)]


def extract_argv(video: str, t: float, out_png: str, width: int = 360) -> list[str]:
    return ["ffmpeg", "-nostdin", "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-vf", f"scale={width}:-2",
            out_png]


def contact_sheet(frames: list[Image.Image], times: list[float] | None = None, notes: list[str] | None = None,
                  cols: int = 4, cell_w: int = 270, gap: int = 12, caption_h: int = 34, bg=(18, 18, 22),
                  fg=(235, 235, 235), font_path: str | None = None, title: str | None = None) -> Image.Image:
    if not frames:
        raise ValueError("no frames")
    if times is not None and len(times) != len(frames):
        raise ValueError("times must match frames")
    if notes is not None and len(notes) != len(frames):
        raise ValueError("notes must match frames")
    aspect = frames[0].height / frames[0].width
    cell_h = int(round(cell_w * aspect))
    rows = math.ceil(len(frames) / cols)
    title_h = 48 if title else 0
    W = cols * cell_w + (cols + 1) * gap
    H = title_h + rows * (cell_h + caption_h) + (rows + 1) * gap
    sheet = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(sheet)
    font = _font(max(12, caption_h - 16), font_path)
    if title:
        d.text((gap, gap), title, fill=fg, font=_font(26, font_path))
    for i, fr in enumerate(frames):
        r, c = divmod(i, cols)
        x = gap + c * (cell_w + gap)
        y = title_h + gap + r * (cell_h + caption_h + gap)
        thumb = fr.convert("RGB")
        thumb.thumbnail((cell_w, cell_h))
        sheet.paste(thumb, (x + (cell_w - thumb.width) // 2, y + (cell_h - thumb.height) // 2))
        label = " ".join(p for p in (fmt_time(times[i]) if times is not None else f"#{i + 1}",
                                     notes[i] if notes else "") if p)
        d.text((x + 4, y + cell_h + 6), label, fill=fg, font=font)
    return sheet
