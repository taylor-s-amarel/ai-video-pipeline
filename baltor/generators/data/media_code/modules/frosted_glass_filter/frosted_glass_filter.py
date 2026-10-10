"""ffmpeg filtergraph for a frosted-glass panel behind titles and captions.

Builds a ``filter_complex`` that, for one rectangle of the frame:

1. crops the region from the live background (so the glass moves with it);
2. blurs it (``gblur`` sigma, or ``boxblur`` radius for speed);
3. tints it with a colour at 55-75% opacity (house range, enforced unless
   ``allow_any_tint``) using ``drawbox`` fill blending;
4. applies a feathered rounded-rectangle alpha (``geq`` signed-distance
   expression, or a pre-rendered mask input via ``alphamerge``);
5. overlays it back at ``x, y``. Panel opacity is capped at 0.98.

Usage::

    from frosted_glass_filter import frosted_glass
    graph, out = frosted_glass(in_label="[0:v]", box=(90, 260, 900, 220), sigma=18,
                               tint="#101418", tint_opacity=0.6, radius=36, feather=28)
    argv = ["ffmpeg", "-i", "bg.mp4", "-filter_complex", graph, "-map", out, "out.mp4"]
"""

from __future__ import annotations

import re


def _hex(c: str) -> str:
    h = c.lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", h):
        raise ValueError(f"colour must be #RRGGBB, got {c!r}")
    return "0x" + h.upper()


def rounded_alpha_expr(radius: float, feather: float, max_alpha: float = 0.98) -> str:
    """geq alpha expression for a feathered rounded rectangle filling the frame (W, H)."""
    r, f = float(radius), max(float(feather), 0.001)
    qx = f"(abs(X-(W-1)/2)-(W/2-{f / 2:g}-{r:g}))"
    qy = f"(abs(Y-(H-1)/2)-(H/2-{f / 2:g}-{r:g}))"
    sd = f"(hypot(max({qx},0),max({qy},0))+min(max({qx},{qy}),0)-{r:g})"
    return f"255*{max_alpha:g}*clip(0.5-{sd}/{f:g},0,1)"


def frosted_glass(in_label: str = "[0:v]", box=(0, 0, 100, 100), sigma: float = 16.0, blur: str = "gblur",
                  tint: str = "#0E1116", tint_opacity: float = 0.6, radius: float = 32, feather: float = 24,
                  panel_opacity: float = 0.98, mask_label: str | None = None, out_label: str = "[glassed]",
                  allow_any_tint: bool = False) -> tuple[str, str]:
    x, y, w, h = (int(round(v)) for v in box)
    if w < 4 or h < 4:
        raise ValueError("box is too small")
    if not allow_any_tint and not 0.55 <= tint_opacity <= 0.75:
        raise ValueError("house rule: tint opacity must be 0.55-0.75 (pass allow_any_tint=True to override)")
    if not 0 < panel_opacity <= 0.98:
        raise ValueError("panel opacity must be within (0, 0.98]")
    w -= w % 2
    h -= h % 2
    if blur == "gblur":
        blur_f = f"gblur=sigma={sigma:g}"
    elif blur == "boxblur":
        blur_f = f"boxblur=luma_radius={max(1, int(sigma)):d}:luma_power=2"
    else:
        raise ValueError("blur must be gblur or boxblur")
    tint_f = f"drawbox=x=0:y=0:w=iw:h=ih:color={_hex(tint)}@{tint_opacity:g}:t=fill"
    parts = [f"{in_label}split=2[fg_base][fg_src]",
             f"[fg_src]crop={w}:{h}:{x}:{y},{blur_f},{tint_f},format=rgba[fg_tinted]"]
    if mask_label:
        parts.append(f"{mask_label}scale={w}:{h},format=gray[fg_mask]")
        parts.append(f"[fg_tinted][fg_mask]alphamerge,colorchannelmixer=aa={panel_opacity:g}[fg_panel]")
    else:
        alpha = rounded_alpha_expr(radius, feather, panel_opacity)
        parts.append(f"[fg_tinted]geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='{alpha}'[fg_panel]")
    parts.append(f"[fg_base][fg_panel]overlay={x}:{y}:format=auto{out_label}")
    return ";".join(parts), out_label
