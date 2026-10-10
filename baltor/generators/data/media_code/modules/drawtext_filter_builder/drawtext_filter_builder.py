"""ffmpeg ``drawtext`` filters with safe text, boxes, fades and time windows.

Literal text is drawn with ``expansion=none`` (so ``%{...}`` and backslashes
are not interpreted) and escaped for the option and filtergraph levels, so
any string, including ``'``, ``:``, ``,``, ``;`` and ``[``, renders as typed.
For long or multi-line text, ``textfile`` mode writes nothing itself: pass a
path to a UTF-8 file you created.

Options cover position expressions, font colour and opacity, border, shadow,
a backing box with padding, an ``enable='between(t,a,b)'`` window and alpha
fades in and out.

Usage::

    from drawtext_filter_builder import drawtext
    vf = drawtext("SHE LIVED UNDERWATER: 14 DAYS", fontfile="/fonts/Inter-Bold.ttf", size=72,
                  color="#FFD21F", x="(w-text_w)/2", y="h*0.18", start=0, end=3.0, fade=0.25,
                  box=True, box_color="#000000", box_opacity=0.45)
"""

from __future__ import annotations

import re


def _esc(value) -> str:
    s = str(value)
    if any(c in s for c in "\x00\r"):
        raise ValueError("text may not contain NUL or CR")
    s = re.sub(r"([\\':])", r"\\\1", s)
    return re.sub(r"([\\'\[\],;])", r"\\\1", s)


def _expr(e) -> str:
    # expressions are quoted so commas inside functions survive the graph parser
    s = str(e)
    if "'" in s:
        raise ValueError("expressions may not contain single quotes")
    return f"'{s}'"


def _color(hex_rgb: str, opacity: float = 1.0) -> str:
    h = hex_rgb.lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", h):
        raise ValueError(f"colour must be #RRGGBB, got {hex_rgb!r}")
    if not 0 <= opacity <= 1:
        raise ValueError("opacity must be within [0, 1]")
    return f"0x{h.upper()}@{opacity:.3g}"


def drawtext(text: str | None = None, fontfile: str | None = None, size: float = 64, color: str = "#FFFFFF",
             opacity: float = 0.98, x="(w-text_w)/2", y="(h-text_h)/2", textfile: str | None = None,
             border: float = 0, border_color: str = "#000000", shadow: tuple | None = None,
             box: bool = False, box_color: str = "#000000", box_opacity: float = 0.5, box_pad: int = 24,
             start: float | None = None, end: float | None = None, fade: float = 0.0,
             line_spacing: int = 0) -> str:
    if (text is None) == (textfile is None):
        raise ValueError("give exactly one of text or textfile")
    opts = []
    if fontfile:
        opts.append(f"fontfile={_esc(fontfile)}")
    if text is not None:
        if "\n" in text:
            raise ValueError("use textfile for multi-line text")
        opts.append(f"text={_esc(text)}")
    else:
        opts.append(f"textfile={_esc(textfile)}")
    opts.append("expansion=none")
    opts += [f"fontsize={size:g}", f"x={_expr(x)}", f"y={_expr(y)}"]
    if fade > 0 and start is not None and end is not None:
        a = f"if(lt(t,{start + fade:g}),(t-{start:g})/{fade:g},if(gt(t,{end - fade:g}),({end:g}-t)/{fade:g},1))"
        opts.append(f"fontcolor={_color(color)}")
        opts.append(f"alpha={_expr(f'{opacity:g}*max(0,min(1,{a}))')}")
    else:
        opts.append(f"fontcolor={_color(color, opacity)}")
    if border:
        opts += [f"borderw={border:g}", f"bordercolor={_color(border_color)}"]
    if shadow:
        dx, dy, scol = shadow
        opts += [f"shadowx={dx:g}", f"shadowy={dy:g}", f"shadowcolor={_color(scol, 0.6)}"]
    if box:
        opts += ["box=1", f"boxcolor={_color(box_color, box_opacity)}", f"boxborderw={int(box_pad)}"]
    if line_spacing:
        opts.append(f"line_spacing={int(line_spacing)}")
    if start is not None and end is not None:
        if end <= start:
            raise ValueError("end must be after start")
        opts.append(f"enable={_expr(f'between(t,{start:g},{end:g})')}")
    return "drawtext=" + ":".join(opts)
