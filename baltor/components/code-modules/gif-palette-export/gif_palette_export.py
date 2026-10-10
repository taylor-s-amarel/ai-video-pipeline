"""High-quality GIF previews with ffmpeg's palettegen/paletteuse in one pass.

A single ``filter_complex`` splits the stream: one branch computes an
optimised palette (``palettegen``), the other maps frames onto it
(``paletteuse``). Options: fps, width, max colours, dither (bayer with a
scale, sierra2_4a, floyd_steinberg, none) and ``stats_mode=diff`` to spend
colours on moving parts.

Usage::

    from gif_palette_export import gif_argv
    cmd = gif_argv("render.mp4", "preview.gif", start=2.0, duration=4.0, fps=12, width=360)
"""

from __future__ import annotations

DITHERS = {"bayer", "heckbert", "floyd_steinberg", "sierra2", "sierra2_4a", "sierra3", "burkes", "atkinson", "none"}


def gif_filter(fps: float = 12, width: int = 480, max_colors: int = 128, dither: str = "bayer",
               bayer_scale: int = 3, stats_mode: str = "diff") -> str:
    if not 2 <= max_colors <= 256:
        raise ValueError("max_colors must be within [2, 256]")
    if dither not in DITHERS:
        raise ValueError(f"dither must be one of {sorted(DITHERS)}")
    if stats_mode not in ("full", "diff", "single"):
        raise ValueError("stats_mode must be full, diff or single")
    if not 0 <= bayer_scale <= 5:
        raise ValueError("bayer_scale must be within [0, 5]")
    use = f"paletteuse=dither={dither}" + (f":bayer_scale={bayer_scale}" if dither == "bayer" else "")
    if stats_mode == "diff":
        use += ":diff_mode=rectangle"
    return (f"fps={fps:g},scale={int(width)}:-2:flags=lanczos,split[gp_a][gp_b];"
            f"[gp_a]palettegen=max_colors={max_colors}:stats_mode={stats_mode}[gp_p];[gp_b][gp_p]{use}")


def gif_argv(src: str, dst: str, start: float | None = None, duration: float | None = None, loop: int = 0,
             **kw) -> list[str]:
    if not dst.lower().endswith(".gif"):
        raise ValueError("output must be a .gif file")
    a = ["ffmpeg", "-nostdin", "-y"]
    if start is not None:
        a += ["-ss", f"{start:g}"]
    if duration is not None:
        a += ["-t", f"{duration:g}"]
    return a + ["-i", src, "-filter_complex", gif_filter(**kw), "-loop", str(loop), dst]
