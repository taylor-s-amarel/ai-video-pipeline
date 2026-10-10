"""2x2 motion grid: four moving panels over a layered background (ffmpeg).

Each of four inputs (clips or stills) is cover-cropped to its cell, given a
slow drift-zoom so every panel moves (alternating directions), masked with a
feathered rounded alpha (no hard rectangles), and the whole grid is laid
over the background at ``grid_opacity`` (default 0.35, capped at 0.98).

Returns a ``filter_complex`` fragment whose output label can be fed to the
rest of the layer stack.

Usage::

    from motion_grid_2x2 import motion_grid
    graph, out = motion_grid(bg="[0:v]", panels=["[1:v]", "[2:v]", "[3:v]", "[4:v]"],
                             size=(1080, 1920), gutter=28, margin=48, fps=30, duration=64)
"""

from __future__ import annotations

import math


def _even(v: float) -> int:
    v = int(v)
    return v - v % 2


def cells(size=(1080, 1920), gutter: int = 24, margin: int = 40):
    W, H = size
    cw = _even((W - 2 * margin - gutter) / 2)
    ch = _even((H - 2 * margin - gutter) / 2)
    return [(margin + c * (cw + gutter), margin + r * (ch + gutter), cw, ch) for r in (0, 1) for c in (0, 1)], (cw, ch)


def _alpha_expr(radius: float, feather: float, opacity: float) -> str:
    f = max(feather, 0.001)
    qx = f"(abs(X-(W-1)/2)-(W/2-{f / 2:g}-{radius:g}))"
    qy = f"(abs(Y-(H-1)/2)-(H/2-{f / 2:g}-{radius:g}))"
    sd = f"(hypot(max({qx},0),max({qy},0))+min(max({qx},{qy}),0)-{radius:g})"
    return f"255*{opacity:g}*clip(0.5-{sd}/{f:g},0,1)"


def motion_grid(bg: str, panels: list[str], size=(1080, 1920), gutter: int = 24, margin: int = 40,
                fps: float = 30, duration: float = 10.0, drift: float = 0.06, grid_opacity: float = 0.35,
                radius: float = 28, feather: float = 22, out_label: str = "[grid2x2]") -> tuple[str, str]:
    if len(panels) != 4:
        raise ValueError("a 2x2 grid needs exactly four panels")
    if not 0 < grid_opacity <= 0.98:
        raise ValueError("grid opacity must be within (0, 0.98]")
    W, H = size
    rects, (cw, ch) = cells(size, gutter, margin)
    parts = [f"{bg}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={fps:g},format=rgba[g_bg]"]
    over_w, over_h = _even(cw * (1 + drift)), _even(ch * (1 + drift))
    for i, p in enumerate(panels):
        # slow drift: the crop window moves across the overscanned panel; directions alternate per cell
        sx = 1 if i % 2 == 0 else -1
        sy = 1 if i < 2 else -1
        period = max(duration, 1.0)
        dx = f"({over_w - cw}/2)*(1+{sx}*sin(2*PI*t/{period * 2:g}))"
        dy = f"({over_h - ch}/2)*(1+{sy}*sin(2*PI*t/{period * 2:g}+{math.pi / 3:.4f}))"
        parts.append(
            f"{p}fps={fps:g},scale={over_w}:{over_h}:force_original_aspect_ratio=increase,crop={over_w}:{over_h},"
            f"crop={cw}:{ch}:x='{dx}':y='{dy}',format=rgba,"
            f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='{_alpha_expr(radius, feather, grid_opacity)}'[g_p{i}]")
    acc = "g_bg"
    for i, (x, y, _, _) in enumerate(rects):
        nxt = f"g_acc{i}"
        parts.append(f"[{acc}][g_p{i}]overlay={x}:{y}:format=auto:shortest=0[{nxt}]")
        acc = nxt
    parts.append(f"[{acc}]trim=duration={duration:g},format=yuv420p{out_label}")
    return ";".join(parts), out_label
