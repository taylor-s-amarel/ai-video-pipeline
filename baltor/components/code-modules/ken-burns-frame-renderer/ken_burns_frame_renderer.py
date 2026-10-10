"""Render Ken Burns frames from a still with sub-pixel accurate crops (Pillow).

``render_frames`` takes crop rectangles ``(x, y, w, h)`` in source pixels
(for example from the ken_burns_path module) and resamples each one straight
to the output size with ``Image.transform(..., Image.EXTENT)``. Because the
crop is not rounded to whole pixels first, slow zooms do not jitter.

Frames can be yielded as Pillow images or raw RGB bytes for piping into
``ffmpeg -f rawvideo -pix_fmt rgb24 -s WxH -r FPS -i -``.

Usage::

    from PIL import Image
    from ken_burns_frame_renderer import render_frames, ffmpeg_pipe_argv
    img = Image.open("photo.jpg")
    for frame in render_frames(img, rects, (1080, 1920)):
        proc.stdin.write(frame.tobytes())
"""

from __future__ import annotations

from typing import Iterable, Iterator

from PIL import Image

RESAMPLE = {"bicubic": Image.Resampling.BICUBIC, "bilinear": Image.Resampling.BILINEAR,
            "lanczos": Image.Resampling.LANCZOS}


def render_frame(img: Image.Image, rect, out_size, resample: str = "bicubic") -> Image.Image:
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        raise ValueError("crop width and height must be > 0")
    src = img if img.mode in ("RGB", "RGBA") else img.convert("RGB")
    # LANCZOS is not supported by transform; fall back to bicubic for it
    rs = RESAMPLE.get(resample, Image.Resampling.BICUBIC)
    if rs == Image.Resampling.LANCZOS:
        rs = Image.Resampling.BICUBIC
    return src.transform(tuple(out_size), Image.Transform.EXTENT, (x, y, x + w, y + h), resample=rs)


def render_frames(img: Image.Image, rects: Iterable, out_size, resample: str = "bicubic",
                  supersample: int = 1) -> Iterator[Image.Image]:
    """Yield one frame per rect. ``supersample`` > 1 renders larger then downsizes (sharper on big zooms)."""
    if supersample < 1:
        raise ValueError("supersample must be >= 1")
    big = (out_size[0] * supersample, out_size[1] * supersample)
    for rect in rects:
        f = render_frame(img, rect, big, resample)
        if supersample > 1:
            f = f.resize(tuple(out_size), Image.Resampling.LANCZOS)
        yield f


def ffmpeg_pipe_argv(out_path: str, size, fps: float = 30, crf: int = 18, pix_fmt_in: str = "rgb24") -> list[str]:
    w, h = size
    return ["ffmpeg", "-nostdin", "-y", "-f", "rawvideo", "-pix_fmt", pix_fmt_in, "-s", f"{w}x{h}", "-r", f"{fps:g}",
            "-i", "-", "-c:v", "libx264", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            out_path]
