"""Scale curves for a key-word "pop" (default 1.0 -> 1.12 -> 1.0 over 180 ms).

Two shapes:

* ``ease``   rise with ease-out-cubic for ``rise_fraction`` of the duration,
             then settle with ease-in-out-sine. No overshoot below 1.0.
* ``spring`` an underdamped spring kick that peaks near ``peak`` and rings
             down to exactly 1.0 at the end (enveloped so it always lands).

Outputs per-frame scale factors, an ffmpeg expression in ``t`` (seconds) for a
pop starting at ``start_s`` (for drawtext ``fontsize`` or overlay sizes/positions), and
ASS ``\\t`` transform tags.

Usage::

    from text_pop_scale_curve import pop_scale, pop_frames, ffmpeg_expr, ass_tags
    pop_scale(0.072)                       # 1.12 at the top of the rise
    pop_frames(fps=60)                     # 12 values
    ffmpeg_expr(start_s=3.2, base=64)      # fontsize expression
    ass_tags()                             # {\\fscx100\\fscy100\\t(0,72,...)...}
"""

from __future__ import annotations

import math


def _out_cubic(x: float) -> float:
    return 1 - (1 - x) ** 3


def _in_out_sine(x: float) -> float:
    return -(math.cos(math.pi * x) - 1) / 2


def pop_scale(t: float, peak: float = 1.12, duration: float = 0.18, rise_fraction: float = 0.4,
              shape: str = "ease") -> float:
    """Scale factor at time ``t`` seconds after the pop starts."""
    if duration <= 0 or not 0 < rise_fraction < 1:
        raise ValueError("duration must be > 0 and 0 < rise_fraction < 1")
    if t <= 0 or t >= duration:
        return 1.0
    amp = peak - 1.0
    if shape == "ease":
        rise = duration * rise_fraction
        if t < rise:
            return 1.0 + amp * _out_cubic(t / rise)
        return 1.0 + amp * (1 - _in_out_sine((t - rise) / (duration - rise)))
    if shape == "spring":
        p = t / duration
        # half-sine kick with a decaying second lobe; envelope forces landing at 1.0
        wave = math.sin(math.pi * p / rise_fraction) if p < rise_fraction else \
            -0.35 * math.sin(math.pi * (p - rise_fraction) / (1 - rise_fraction))
        return 1.0 + amp * wave
    raise ValueError("shape must be 'ease' or 'spring'")


def pop_frames(fps: float = 30, **kw) -> list[float]:
    duration = kw.get("duration", 0.18)
    n = max(2, int(math.ceil(duration * fps)) + 1)
    return [pop_scale(i / fps, **kw) for i in range(n)]


def ffmpeg_expr(start_s: float, base: float = 1.0, peak: float = 1.12, duration: float = 0.18,
                rise_fraction: float = 0.4) -> str:
    """ffmpeg expression (variable ``t``) for the 'ease' shape, multiplied by ``base``.

    Commas are inside a single-quoted filter argument when used, e.g.
    ``drawtext=fontsize='<expr>'``.
    """
    rise = duration * rise_fraction
    amp = peak - 1.0
    u = f"(t-{start_s:.4f})"
    rise_part = f"(1+{amp:.4f}*(1-pow(1-{u}/{rise:.4f},3)))"
    fall_x = f"(({u}-{rise:.4f})/{duration - rise:.4f})"
    fall_part = f"(1+{amp:.4f}*(1-(1-cos(PI*{fall_x}))/2))"
    return (f"{base:g}*if(lt({u},0),1,if(lt({u},{rise:.4f}),{rise_part},"
            f"if(lt({u},{duration:.4f}),{fall_part},1)))")


def ass_tags(peak: float = 1.12, duration_ms: int = 180, rise_fraction: float = 0.4, offset_ms: int = 0) -> str:
    """ASS override block that pops a word starting ``offset_ms`` into its event."""
    rise = int(round(duration_ms * rise_fraction))
    p = int(round(peak * 100))
    a, b, c = offset_ms, offset_ms + rise, offset_ms + duration_ms
    return (f"{{\\fscx100\\fscy100\\t({a},{b},0.5,\\fscx{p}\\fscy{p})"
            f"\\t({b},{c},2,\\fscx100\\fscy100)}}")
