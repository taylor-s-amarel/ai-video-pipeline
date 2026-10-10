"""Build injection-safe ffmpeg filters that burn subtitles into video.

* ``ass_filter(path)`` for .ass scripts (styling comes from the script);
* ``subtitles_filter(path, force_style=..., fonts_dir=...)`` for .srt/.vtt
  with an ASS ``force_style`` override (``Fontname=Inter,Fontsize=18,...``).

Every user-controlled value (path, fonts directory, style string) is escaped
for both the filter-option and filtergraph levels, so a file named
``a',drawbox=...`` stays a file name. The returned string is meant to be one
argv element after ``-vf``/``-filter_complex``; ``command`` builds the argv.

Usage::

    from subtitle_burnin_filter import subtitles_filter, command
    vf = subtitles_filter("captions.srt", force_style={"Fontname": "Inter", "Fontsize": 18, "Outline": 2})
    argv = command("in.mp4", "out.mp4", vf)
"""

from __future__ import annotations

import re

_STYLE_KEY = re.compile(r"^[A-Za-z]+$")


def _esc(value: str) -> str:
    s = str(value)
    if any(c in s for c in "\x00\n\r"):
        raise ValueError("values may not contain NUL or newlines")
    s = re.sub(r"([\\':])", r"\\\1", s)          # option level
    return re.sub(r"([\\'\[\],;])", r"\\\1", s)   # filtergraph level


def force_style_string(style: dict) -> str:
    parts = []
    for k, v in style.items():
        if not _STYLE_KEY.match(k):
            raise ValueError(f"bad ASS style field {k!r}")
        sv = str(v)
        if "," in sv or "=" in sv:
            raise ValueError(f"style value for {k} may not contain ',' or '='")
        parts.append(f"{k}={sv}")
    return ",".join(parts)


def ass_filter(path: str, fonts_dir: str | None = None) -> str:
    out = f"ass=filename={_esc(path)}"
    if fonts_dir:
        out += f":fontsdir={_esc(fonts_dir)}"
    return out


def subtitles_filter(path: str, force_style: dict | None = None, fonts_dir: str | None = None,
                     charenc: str | None = None, original_size: str | None = None) -> str:
    out = f"subtitles=filename={_esc(path)}"
    if fonts_dir:
        out += f":fontsdir={_esc(fonts_dir)}"
    if charenc:
        out += f":charenc={_esc(charenc)}"
    if original_size:
        if not re.fullmatch(r"\d+x\d+", original_size):
            raise ValueError("original_size must look like 1080x1920")
        out += f":original_size={original_size}"
    if force_style:
        out += f":force_style={_esc(force_style_string(force_style))}"
    return out


def command(src: str, dst: str, vf: str, crf: int = 18, copy_audio: bool = True) -> list[str]:
    argv = ["ffmpeg", "-nostdin", "-y", "-i", src, "-vf", vf, "-c:v", "libx264", "-crf", str(crf),
            "-pix_fmt", "yuv420p"]
    argv += ["-c:a", "copy"] if copy_audio else ["-an"]
    return argv + ["-movflags", "+faststart", dst]
