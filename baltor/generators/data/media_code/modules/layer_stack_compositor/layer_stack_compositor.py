"""Compose a stack of video/image layers into one ffmpeg ``filter_complex``.

Each layer: input index, opacity (<= 0.98, the house cap: no layer fully
opaque), blend mode, placement and optional time window. The base is a solid
canvas of the output size and duration.

* ``normal`` layers use ``overlay`` with alpha scaled by opacity, so they can
  be positioned and sized;
* other modes (screen, multiply, overlay, softlight, addition, lighten,
  darken, difference, ...) use ffmpeg ``blend`` on planar RGB (``gbrp``) at
  full canvas size, so the blend maths happen in RGB, not YUV.

Usage::

    from layer_stack_compositor import Layer, compose
    graph, out = compose([
        Layer(0, opacity=0.92),                                  # moving background video
        Layer(1, opacity=0.35, blend="screen"),                  # light leak
        Layer(2, opacity=0.98, x=54, y=420, w=972, h=1296),      # main photo
    ], size=(1080, 1920), fps=30, duration=64)
"""

from __future__ import annotations

from dataclasses import dataclass

BLEND_MODES = {"addition", "average", "burn", "darken", "difference", "divide", "dodge", "exclusion", "glow",
               "hardlight", "hardmix", "lighten", "linearlight", "multiply", "negation", "overlay", "phoenix",
               "pinlight", "reflect", "screen", "softlight", "subtract", "vividlight"}
MAX_OPACITY = 0.98


@dataclass
class Layer:
    input: int
    opacity: float = MAX_OPACITY
    blend: str = "normal"
    x: int = 0
    y: int = 0
    w: int | None = None
    h: int | None = None
    start: float | None = None
    end: float | None = None
    loop: bool = False


def validate(layers: list[Layer], clamp: bool = False) -> list[str]:
    problems = []
    for i, l in enumerate(layers):
        if l.opacity > MAX_OPACITY:
            if clamp:
                l.opacity = MAX_OPACITY
            else:
                problems.append(f"layer {i}: opacity {l.opacity} > {MAX_OPACITY}")
        if l.opacity < 0:
            problems.append(f"layer {i}: negative opacity")
        if l.blend != "normal" and l.blend not in BLEND_MODES:
            problems.append(f"layer {i}: unknown blend mode {l.blend!r}")
        if (l.start is None) != (l.end is None):
            problems.append(f"layer {i}: give both start and end or neither")
        elif l.start is not None and l.end <= l.start:
            problems.append(f"layer {i}: end must be after start")
    return problems


def compose(layers: list[Layer], size=(1080, 1920), fps: float = 30, duration: float = 10.0,
            canvas_color: str = "black", clamp: bool = False) -> tuple[str, str]:
    probs = validate(layers, clamp)
    if probs:
        raise ValueError("; ".join(probs))
    W, H = size
    parts = [f"color=c={canvas_color}:s={W}x{H}:r={fps:g}:d={duration:g},format=gbrp[acc0]"]
    acc = "acc0"
    for i, l in enumerate(layers):
        src = f"[{l.input}:v]"
        prep = []
        if l.loop:
            prep.append("loop=loop=-1:size=32767:start=0")
        prep.append(f"fps={fps:g}")
        enable = f":enable='between(t,{l.start:g},{l.end:g})'" if l.start is not None else ""
        if l.blend == "normal":
            w, h = (l.w or W), (l.h or H)
            prep += [f"scale={w}:{h}", "format=rgba", f"colorchannelmixer=aa={l.opacity:g}"]
            parts.append(f"{src}{','.join(prep)}[L{i}]")
            parts.append(f"[{acc}][L{i}]overlay={l.x}:{l.y}:format=gbrp:shortest=0{enable}[acc{i + 1}]")
        else:
            prep += [f"scale={W}:{H}", "format=gbrp"]
            parts.append(f"{src}{','.join(prep)}[L{i}]")
            parts.append(f"[{acc}][L{i}]blend=all_mode={l.blend}:all_opacity={l.opacity:g}:shortest=0{enable}[acc{i + 1}]")
        acc = f"acc{i + 1}"
    parts.append(f"[{acc}]trim=duration={duration:g},format=yuv420p[stack]")
    return ";".join(parts), "[stack]"
