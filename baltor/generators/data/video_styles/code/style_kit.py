"""Style preset kit for vertical shorts.

Turns Baltor video style presets (caption, title, palette, camera move, transition, 2x2 grid,
layer stack, text animation, aspect format) into numbers and ffmpeg filter graphs:

* WCAG 2.x relative luminance and contrast, including the worst-case contrast of text over a
  semi-transparent (frosted) panel when the video underneath is unknown.
* Easing curves, cubic-bezier timing and a damped-spring solver for springy text pops.
* Camera-move state over time, an ffmpeg ``zoompan`` builder and a sub-pixel Pillow renderer.
* ``xfade`` chains with correct offsets, a feathered 2x2 grid and a layer-stack
  ``filter_complex`` builder that refuses any layer above 98% opacity.
* Safe-area layout for caption and title boxes.
* Optional Pillow renderers (imported lazily): frosted-glass panel and caption preview.

Only the standard library is needed, except Pillow for the ``render_*``/``frosted_panel``/
``camera_frames`` functions.
"""

from __future__ import annotations

import math
import re
from typing import Callable, Iterable, Iterator, Sequence

__all__ = [
    "MAX_LAYER_OPACITY", "XFADE_TRANSITIONS", "BLEND_MODES",
    "hex_to_rgb", "rgb_to_hex", "relative_luminance", "contrast_ratio", "composite", "panel_contrast",
    "is_large_text", "required_ratio", "wcag_level",
    "ease", "ease_expr", "cubic_bezier", "spring", "spring_metrics", "keyframe_value", "text_anim_state",
    "camera_state", "zoompan_filter", "camera_frames",
    "xfade_chain", "grid_2x2_rects", "grid_2x2_filter",
    "layer_stack_problems", "layer_stack_filter",
    "safe_rect", "place_box",
    "frosted_panel", "render_caption_preview",
]

MAX_LAYER_OPACITY = 0.98
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

# --------------------------------------------------------------------------- colour and contrast


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    """'#FFD21F' -> (255, 210, 31)."""
    if not isinstance(color, str) or not _HEX.match(color):
        raise ValueError(f"expected a #RRGGBB colour, got {color!r}")
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def rgb_to_hex(rgb: Iterable[float]) -> str:
    return "#" + "".join(f"{max(0, min(255, int(round(c)))):02X}" for c in rgb)


def _rgb(color) -> tuple[float, float, float]:
    if isinstance(color, str):
        return tuple(float(c) for c in hex_to_rgb(color))  # type: ignore[return-value]
    r, g, b = color
    return float(r), float(g), float(b)


def _linear(c8: float) -> float:
    c = c8 / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(color) -> float:
    """WCAG 2.x relative luminance of an sRGB colour (hex string or 0-255 triple)."""
    r, g, b = _rgb(color)
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def _ratio_from_luminance(la: float, lb: float) -> float:
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def contrast_ratio(a, b) -> float:
    """WCAG contrast ratio (L1 + 0.05) / (L2 + 0.05), from 1.0 to 21.0."""
    return _ratio_from_luminance(relative_luminance(a), relative_luminance(b))


def composite(top, bottom, alpha: float) -> tuple[float, float, float]:
    """Straight-alpha 'normal' blend of ``top`` over ``bottom`` in 8-bit sRGB values.

    This is what ffmpeg ``overlay`` and most editors do for a flat tint layer.
    """
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be within 0..1")
    t, b = _rgb(top), _rgb(bottom)
    return tuple(alpha * x + (1.0 - alpha) * y for x, y in zip(t, b))  # type: ignore[return-value]


def panel_contrast(text, tint, opacity: float) -> dict:
    """Worst-case contrast of ``text`` over a ``tint`` panel at ``opacity`` drawn over unknown video.

    The panel's colour is ``opacity * tint + (1 - opacity) * video``. Each channel rises with the
    video's channel and luminance rises with every channel, so the panel's luminance lies between
    the tint composited over black and over white. If the text's luminance falls inside that
    range some frame could match it exactly, and the worst case is 1.0. Blurring the video
    (frosted glass) moves pixels around but cannot leave this range, so the bound still holds.
    """
    dark = composite(tint, (0, 0, 0), opacity)
    light = composite(tint, (255, 255, 255), opacity)
    l_text, l_dark, l_light = relative_luminance(text), relative_luminance(dark), relative_luminance(light)
    over_black = _ratio_from_luminance(l_text, l_dark)
    over_white = _ratio_from_luminance(l_text, l_light)
    worst = 1.0 if l_dark <= l_text <= l_light else min(over_black, over_white)
    return {
        "over_black": round(over_black, 2),
        "over_white": round(over_white, 2),
        "worst": round(worst, 2),
        "panel_dark": rgb_to_hex(dark),
        "panel_light": rgb_to_hex(light),
    }


def is_large_text(size_px: float, weight: int = 400) -> bool:
    """WCAG large-scale text: at least 18pt (24 CSS px), or at least 14pt (about 18.67 px) and bold."""
    return size_px >= 24 or (size_px >= 18.66 and weight >= 700)


def required_ratio(size_px: float, weight: int = 400) -> float:
    """This library's minimum: 3.0 only for text that is both >= 24 px and bold (>= 700), else 4.5.

    Stricter than WCAG AA, which also accepts 3.0 for 24 px regular or 18.67 px bold text.
    """
    return 3.0 if size_px >= 24 and weight >= 700 else 4.5


def wcag_level(ratio: float, size_px: float, weight: int = 400) -> str:
    """'AAA', 'AA' or 'fail' for text of the given size and weight (WCAG 1.4.3 / 1.4.6)."""
    large = is_large_text(size_px, weight)
    if ratio >= (4.5 if large else 7.0):
        return "AAA"
    if ratio >= (3.0 if large else 4.5):
        return "AA"
    return "fail"


# --------------------------------------------------------------------------- easing and springs

_C1 = 1.70158
_C3 = _C1 + 1.0


def _clamp01(t: float) -> float:
    return 0.0 if t < 0 else 1.0 if t > 1 else t


def ease(name: str, t: float) -> float:
    """Evaluate a named easing curve at t in [0, 1]."""
    t = _clamp01(t)
    if name == "linear":
        return t
    if name == "ease-in":
        return t ** 3
    if name == "ease-out":
        return 1 - (1 - t) ** 3
    if name == "ease-in-out":
        return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2
    if name == "sine-in-out":
        return -(math.cos(math.pi * t) - 1) / 2
    if name == "ease-out-back":
        return 1 + _C3 * (t - 1) ** 3 + _C1 * (t - 1) ** 2
    if name == "ease-out-elastic":
        if t in (0.0, 1.0):
            return t
        return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1
    if name == "step":
        return 1.0 if t >= 1 else 0.0
    raise ValueError(f"unknown easing {name!r}")


def ease_expr(name: str, s: str) -> str:
    """The same curves as ffmpeg expression text, where ``s`` is an expression in [0, 1]."""
    if name == "linear":
        return f"({s})"
    if name == "ease-in":
        return f"pow({s},3)"
    if name == "ease-out":
        return f"(1-pow(1-({s}),3))"
    if name == "ease-in-out":
        return f"if(lt({s},0.5),4*pow({s},3),1-pow(-2*({s})+2,3)/2)"
    if name == "sine-in-out":
        return f"(0.5-0.5*cos(PI*({s})))"
    if name == "ease-out-back":
        return f"(1+{_C3}*pow(({s})-1,3)+{_C1}*pow(({s})-1,2))"
    if name == "step":
        return f"gte({s},1)"
    raise ValueError(f"easing {name!r} has no ffmpeg expression form")


def cubic_bezier(x1: float, y1: float, x2: float, y2: float) -> Callable[[float], float]:
    """CSS-style cubic-bezier(x1, y1, x2, y2) timing function."""
    if not (0 <= x1 <= 1 and 0 <= x2 <= 1):
        raise ValueError("x1 and x2 must be within 0..1")

    def bez(a: float, b: float, s: float) -> float:
        return 3 * a * (1 - s) ** 2 * s + 3 * b * (1 - s) * s ** 2 + s ** 3

    def dbez(a: float, b: float, s: float) -> float:
        return 3 * a * (1 - s) ** 2 + 6 * (b - a) * (1 - s) * s + 3 * (1 - b) * s ** 2

    def f(t: float) -> float:
        t = _clamp01(t)
        s = t
        for _ in range(8):
            err = bez(x1, x2, s) - t
            if abs(err) < 1e-7:
                break
            d = dbez(x1, x2, s)
            if abs(d) < 1e-6:
                break
            s = _clamp01(s - err / d)
        else:
            lo, hi = 0.0, 1.0
            for _ in range(60):
                s = (lo + hi) / 2
                if bez(x1, x2, s) < t:
                    lo = s
                else:
                    hi = s
        return bez(y1, y2, s)

    return f


def spring(t: float, stiffness: float = 300.0, damping: float = 18.0, mass: float = 1.0, v0: float = 0.0) -> float:
    """Position of a damped spring released at 0 and pulled toward 1, at time t seconds."""
    if t <= 0:
        return 0.0
    w0 = math.sqrt(stiffness / mass)
    zeta = damping / (2 * math.sqrt(stiffness * mass))
    if zeta < 1:
        wd = w0 * math.sqrt(1 - zeta * zeta)
        e = math.exp(-zeta * w0 * t)
        return 1 - e * (math.cos(wd * t) + (zeta * w0 - v0) / wd * math.sin(wd * t))
    if zeta == 1:
        return 1 + math.exp(-w0 * t) * (-1 + (v0 - w0) * t)
    r1 = -w0 * (zeta - math.sqrt(zeta * zeta - 1))
    r2 = -w0 * (zeta + math.sqrt(zeta * zeta - 1))
    c2 = (v0 + r1) / (r2 - r1)
    c1 = -1 - c2
    return 1 + c1 * math.exp(r1 * t) + c2 * math.exp(r2 * t)


def spring_metrics(stiffness: float, damping: float, mass: float = 1.0, tol: float = 0.02,
                   horizon_s: float = 5.0) -> dict:
    """Damping ratio, peak value, peak time and settle time (|x - 1| <= tol thereafter), sampled at 1 ms."""
    zeta = damping / (2 * math.sqrt(stiffness * mass))
    peak, peak_t, settle = 0.0, 0.0, 0.0
    steps = int(horizon_s * 1000)
    for k in range(1, steps + 1):
        t = k / 1000
        x = spring(t, stiffness, damping, mass)
        if x > peak:
            peak, peak_t = x, t
        if abs(x - 1) > tol:
            settle = t
    return {"damping_ratio": round(zeta, 3), "peak": round(peak, 3), "peak_time_s": round(peak_t, 3),
            "settle_time_s": round(settle, 3)}


def keyframe_value(keyframes: Sequence[dict], t: float, prop: str, default: float = 0.0) -> float:
    """Interpolate ``prop`` across keyframes [{"t": 0..1, prop: v, "ease": name}, ...] at normalised t.

    A keyframe's ``ease`` shapes the segment that ends at it. Keyframes without ``prop`` are skipped.
    """
    pts = sorted((k for k in keyframes if prop in k), key=lambda k: k["t"])
    if not pts:
        return default
    if t <= pts[0]["t"]:
        return float(pts[0][prop])
    for a, b in zip(pts, pts[1:]):
        if t <= b["t"]:
            span = b["t"] - a["t"]
            u = 1.0 if span <= 0 else (t - a["t"]) / span
            return float(a[prop]) + (float(b[prop]) - float(a[prop])) * ease(b.get("ease", "linear"), u)
    return float(pts[-1][prop])


_TEXT_PROPS = {"scale": 1.0, "opacity": 1.0, "dx_px": 0.0, "dy_px": 0.0, "rotation_deg": 0.0, "blur_px": 0.0,
               "reveal": 1.0}


def text_anim_state(anim: dict, t_ms: float, n_units: int) -> list[dict]:
    """Per-unit (text, line, word or character) state of a text animation preset at t_ms.

    Keyframed presets interpolate ``keyframes``; spring presets move each property from
    ``from`` to ``to`` along a damped spring, so values can overshoot the target.
    """
    out = []
    stagger = float(anim.get("stagger_ms", 0))
    dur = max(1.0, float(anim.get("duration_ms", 1)))
    for i in range(max(1, n_units)):
        local = t_ms - i * stagger
        state = dict(_TEXT_PROPS)
        if "spring" in anim:
            sp = anim["spring"]
            p = spring(max(0.0, local) / 1000.0, sp["stiffness"], sp["damping"], sp.get("mass", 1.0))
            for k, v0 in anim.get("from", {}).items():
                v1 = anim.get("to", {}).get(k, _TEXT_PROPS.get(k, 0.0))
                state[k] = v0 + (v1 - v0) * p if local > 0 else v0
            if "opacity" in anim.get("from", {}):
                state["opacity"] = max(0.0, min(1.0, state["opacity"]))
        else:
            u = _clamp01(local / dur)
            for k, dv in _TEXT_PROPS.items():
                state[k] = keyframe_value(anim.get("keyframes", []), u, k, dv)
        state["visible"] = local >= 0
        out.append(state)
    return out


# --------------------------------------------------------------------------- camera moves


def _move_progress(move: dict, t: float) -> float:
    dur = float(move["duration_s"])
    u = _clamp01(t / dur) if dur > 0 else 1.0
    curve = move.get("easing", "ease-in-out")
    if isinstance(curve, (list, tuple)):
        return cubic_bezier(*curve)(u)
    return ease(curve, u)


def camera_state(move: dict, t: float) -> dict:
    """zoom, centre (fractions of the source) and rotation of a camera-move preset at t seconds.

    ``move`` follows the camera-move contract: duration_s, zoom {from,to}, center {from,to},
    optional rotation_deg {from,to}, easing (name or cubic-bezier list), optional zoom keyframes
    (for punch-ins) and optional shake {amplitude, frequency_hz}.
    """
    dur = float(move["duration_s"])
    p = _move_progress(move, t)
    if move.get("zoom_keyframes"):
        z = keyframe_value(move["zoom_keyframes"], _clamp01(t / dur) if dur else 1.0, "zoom", 1.0)
    else:
        z = move["zoom"]["from"] + (move["zoom"]["to"] - move["zoom"]["from"]) * p
    c0, c1 = move["center"]["from"], move["center"]["to"]
    cx, cy = c0[0] + (c1[0] - c0[0]) * p, c0[1] + (c1[1] - c0[1]) * p
    rot = 0.0
    if "rotation_deg" in move:
        rot = move["rotation_deg"]["from"] + (move["rotation_deg"]["to"] - move["rotation_deg"]["from"]) * p
    shake = move.get("shake")
    if shake:
        a, f = shake["amplitude"], shake["frequency_hz"]
        cx += a * (math.sin(2 * math.pi * f * t) + 0.5 * math.sin(2 * math.pi * f * 2.3 * t + 1.1)) / 1.5
        cy += a * (math.cos(2 * math.pi * f * 1.7 * t + 0.4) + 0.5 * math.sin(2 * math.pi * f * 3.1 * t)) / 1.5
    return {"zoom": z, "cx": cx, "cy": cy, "rotation_deg": rot}


def _piecewise_expr(keyframes: Sequence[dict], prop: str, s: str) -> str:
    pts = sorted((k for k in keyframes if prop in k), key=lambda k: k["t"])
    expr = f"{float(pts[-1][prop]):g}"
    for a, b in reversed(list(zip(pts, pts[1:]))):
        span = max(b["t"] - a["t"], 1e-9)
        u = f"(({s})-{a['t']:g})/{span:g}"
        seg = f"({float(a[prop]):g}+({float(b[prop]) - float(a[prop]):g})*{ease_expr(b.get('ease', 'linear'), u)})"
        expr = f"if(lt({s},{b['t']:g}),{seg},{expr})"
    return f"if(lt({s},{pts[0]['t']:g}),{float(pts[0][prop]):g},{expr})"


def zoompan_filter(move: dict, out_w: int, out_h: int, fps: int = 30, prescale: int = 4) -> str:
    """ffmpeg filter chain applying a camera-move preset to a still image input.

    Covers the output aspect first, upscales by ``prescale`` (reduces zoompan's integer-pixel
    jitter), then runs zoompan for duration_s * fps frames. Use with ``-i photo.jpg`` (no -loop).
    Rotation and shake are not expressible in zoompan; use :func:`camera_frames` for those.
    """
    n = max(2, int(round(float(move["duration_s"]) * fps)))
    s = f"(on/{n - 1})"
    curve = move.get("easing", "ease-in-out")
    if isinstance(curve, (list, tuple)):
        raise ValueError("cubic-bezier easing needs camera_frames(); zoompan supports named curves")
    p = ease_expr(curve, s)
    if move.get("zoom_keyframes"):
        z = _piecewise_expr(move["zoom_keyframes"], "zoom", s)
    else:
        z0, z1 = move["zoom"]["from"], move["zoom"]["to"]
        z = f"{z0:g}+({z1 - z0:g})*{p}"
    (cx0, cy0), (cx1, cy1) = move["center"]["from"], move["center"]["to"]
    cx = f"({cx0:g}+({cx1 - cx0:g})*{p})"
    cy = f"({cy0:g}+({cy1 - cy0:g})*{p})"
    x = f"max(0,min(iw-iw/zoom,{cx}*iw-iw/zoom/2))"
    y = f"max(0,min(ih-ih/zoom,{cy}*ih-ih/zoom/2))"
    bw, bh = out_w * prescale, out_h * prescale
    return (f"scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},"
            f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={out_w}x{out_h}:fps={fps},setsar=1")


def camera_frames(image, move: dict, out_size: tuple[int, int], fps: int = 30) -> Iterator:
    """Yield Pillow frames of a camera move with sub-pixel (bicubic) sampling, rotation and shake."""
    from PIL import Image  # lazy

    out_w, out_h = out_size
    src = image.convert("RGB")
    iw, ih = src.size
    base = max(out_w / iw, out_h / ih)
    n = max(2, int(round(float(move["duration_s"]) * fps)))
    for k in range(n):
        st = camera_state(move, k / fps)
        scale = base * max(st["zoom"], 1e-6)
        vw, vh = out_w / scale, out_h / scale
        cx = min(max(st["cx"] * iw, vw / 2), iw - vw / 2)
        cy = min(max(st["cy"] * ih, vh / 2), ih - vh / 2)
        th = math.radians(st["rotation_deg"])
        cos_t, sin_t = math.cos(th) / scale, math.sin(th) / scale
        # output pixel (u, v) -> input pixel (x, y), rotating about the output centre
        a, b = cos_t, sin_t
        d, e = -sin_t, cos_t
        c = cx - a * out_w / 2 - b * out_h / 2
        f = cy - d * out_w / 2 - e * out_h / 2
        yield src.transform((out_w, out_h), Image.AFFINE, (a, b, c, d, e, f), resample=Image.BICUBIC)


# --------------------------------------------------------------------------- transitions and grids

XFADE_TRANSITIONS = frozenset("""
fade wipeleft wiperight wipeup wipedown slideleft slideright slideup slidedown circlecrop rectcrop distance
fadeblack fadewhite radial smoothleft smoothright smoothup smoothdown circleopen circleclose vertopen vertclose
horzopen horzclose dissolve pixelize diagtl diagtr diagbl diagbr hlslice hrslice vuslice vdslice hblur fadegrays
wipetl wipetr wipebl wipebr squeezeh squeezev zoomin fadefast fadeslow hlwind hrwind vuwind vdwind coverleft
coverright coverup coverdown revealleft revealright revealup revealdown
""".split())


def xfade_chain(durations: Sequence[float], transitions: Sequence[dict], fps: int = 30,
                size: tuple[int, int] | None = None) -> tuple[str, float]:
    """filter_complex joining clips [0:v]..[n-1:v] with xfade transitions or hard cuts.

    ``transitions[k]`` joins clip k and k+1: {"xfade": "<name>", "duration_ms": 400} or {"cut": true}.
    Returns (graph ending in [v], total duration in seconds). Each xfade starts at
    (length of everything joined so far) - (its duration), which is the offset xfade expects.
    """
    if len(transitions) != len(durations) - 1:
        raise ValueError("need exactly one transition between each pair of clips")
    norm = f"settb=AVTB,fps={fps},format=yuv420p,setsar=1"
    if size:
        norm = f"scale={size[0]}:{size[1]},{norm}"
    parts = [f"[{i}:v]{norm}[c{i}]" for i in range(len(durations))]
    label, length = "c0", float(durations[0])
    for k, tr in enumerate(transitions, start=1):
        out = f"x{k}"
        if tr.get("cut") or not tr.get("xfade"):
            parts.append(f"[{label}][c{k}]concat=n=2:v=1:a=0[{out}]")
            length += float(durations[k])
        else:
            name = tr["xfade"]
            if name not in XFADE_TRANSITIONS:
                raise ValueError(f"unknown xfade transition {name!r}")
            d = float(tr["duration_ms"]) / 1000.0
            if d >= min(length, float(durations[k])):
                raise ValueError(f"transition {k} ({d}s) is longer than a clip it joins")
            parts.append(f"[{label}][c{k}]xfade=transition={name}:duration={d:g}:offset={length - d:.3f}[{out}]")
            length += float(durations[k]) - d
        label = out
    parts.append(f"[{label}]null[v]")
    return ";".join(parts), round(length, 3)


def _even(n: float) -> int:
    return max(2, int(n) // 2 * 2)


def grid_2x2_rects(width: int, height: int, gutter: int = 24, margin: int = 0) -> list[tuple[int, int, int, int]]:
    """Four (x, y, w, h) cells, row-major, with even sizes (yuv420p needs even dimensions)."""
    cw = _even((width - 2 * margin - gutter) / 2)
    ch = _even((height - 2 * margin - gutter) / 2)
    xs = (margin, margin + cw + gutter)
    ys = (margin, margin + ch + gutter)
    return [(xs[c], ys[r], cw, ch) for r in (0, 1) for c in (0, 1)]


def _feather_mask_expr(feather: float, radius: float, opacity: float) -> str:
    """geq luma expression: rounded-rectangle mask with a linear feather, scaled by opacity."""
    f = max(feather, 0.5)
    r = max(radius, 0.0)
    # distance inside the rounded rectangle (positive inside), computed per pixel
    dx = f"max({r}-X,X-(W-1-{r}))"
    dy = f"max({r}-Y,Y-(H-1-{r}))"
    corner = f"({r}-hypot(max({dx},0),max({dy},0)))"
    edge = f"min(min(X,W-1-X),min(Y,H-1-Y))"
    inside = f"if(gt({dx},0)*gt({dy},0),{corner},{edge})"
    return f"255*{opacity:g}*clip({inside}/{f:g},0,1)"


def grid_2x2_filter(grid: dict, width: int, height: int, fps: int = 30,
                    base_label: str = "base", inputs: Sequence[str] = ("1:v", "2:v", "3:v", "4:v"),
                    out_label: str = "grid") -> str:
    """Overlay four moving sources as a feathered 2x2 grid on ``[base_label]``.

    ``grid`` follows the grid-system contract (gutter_px, margin_px, feather_px, corner_radius_px,
    cells[].opacity, cells[].mirror, cells[].start_offset_s). Masks are rendered once and reused.
    """
    rects = grid_2x2_rects(width, height, grid.get("gutter_px", 24), grid.get("margin_px", 0))
    parts, label = [], base_label
    for i, ((x, y, w, h), cell) in enumerate(zip(rects, grid["cells"])):
        op = float(cell.get("opacity", grid.get("opacity", 0.35)))
        if op > MAX_LAYER_OPACITY:
            raise ValueError(f"cell {i} opacity {op} exceeds {MAX_LAYER_OPACITY}")
        mirror = {"h": ",hflip", "v": ",vflip", "hv": ",hflip,vflip"}.get(cell.get("mirror", ""), "")
        offset = float(cell.get("start_offset_s", 0))
        trim = f",trim=start={offset:g},setpts=PTS-STARTPTS" if offset else ""
        mask = _feather_mask_expr(grid.get("feather_px", 32), grid.get("corner_radius_px", 0), op)
        parts.append(f"[{inputs[i]}]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}{mirror}{trim},"
                     f"fps={fps},format=yuva420p[s{i}]")
        parts.append(f"color=c=black:s={w}x{h}:r={fps}:d=1,trim=end_frame=1,format=gray,geq=lum='{mask}',"
                     f"loop=loop=-1:size=1:start=0,setpts=N/({fps}*TB)[m{i}]")
        parts.append(f"[s{i}][m{i}]alphamerge[a{i}]")
        nxt = out_label if i == 3 else f"g{i}"
        parts.append(f"[{label}][a{i}]overlay=x={x}:y={y}:shortest=1[{nxt}]")
        label = nxt
    return ";".join(parts)


# --------------------------------------------------------------------------- layer stacks

BLEND_MODES = {
    "normal": "normal", "screen": "screen", "multiply": "multiply", "overlay": "overlay",
    "soft-light": "softlight", "hard-light": "hardlight", "add": "addition", "lighten": "lighten",
    "darken": "darken", "color-dodge": "dodge", "difference": "difference",
}
_BACKGROUND_ROLES = {"base", "background-video", "background-image", "grid-2x2", "texture", "light", "particles",
                     "haze", "grain", "vignette", "overlay"}


def layer_stack_problems(stack: dict, min_layers: int = 5, min_photo_width: float = 0.80) -> list[str]:
    """House-rule problems in a layer-stack preset (empty list when it passes)."""
    layers = stack.get("layers", [])
    out = []
    if len(layers) < min_layers:
        out.append(f"{len(layers)} layers; at least {min_layers} required")
    zs = [layer.get("z") for layer in layers]
    if len(set(zs)) != len(zs):
        out.append("duplicate z values")
    for layer in layers:
        op = layer.get("opacity", 1.0)
        if op > MAX_LAYER_OPACITY:
            out.append(f"layer {layer.get('id')} opacity {op} > {MAX_LAYER_OPACITY}")
        if layer.get("blend", "normal") not in BLEND_MODES:
            out.append(f"layer {layer.get('id')} uses unknown blend {layer.get('blend')}")
        if layer.get("role") == "photo":
            rect = layer.get("rect") or {}
            if rect and rect.get("w", 1.0) < min_photo_width:
                out.append(f"photo layer {layer.get('id')} is {rect.get('w')} of frame width (< {min_photo_width})")
    moving = [layer for layer in layers if layer.get("role") in _BACKGROUND_ROLES
              and (layer.get("motion") or {}).get("type", "static") != "static"]
    if not moving:
        out.append("no moving background layer")
    return out


def layer_stack_filter(layers: Sequence[dict], width: int, height: int, fps: int = 30,
                       out_label: str = "v") -> str:
    """filter_complex that composites layers bottom-to-top.

    Each layer needs ``input`` (an ffmpeg input index, so input order is yours to choose),
    ``opacity`` (<= 0.98) and ``blend``. Full-frame layers blend in planar RGB with
    ``blend=all_mode=...:all_opacity=...``; a layer with ``rect`` {x, y, w, h} (fractions of the frame)
    is scaled into that rectangle, feathered by ``feather_px`` and overlaid with its opacity as alpha.
    The first layer is the base and is drawn at its own opacity over black.
    """
    if not layers:
        raise ValueError("no layers")
    parts = []
    for i, layer in enumerate(layers):
        op = float(layer.get("opacity", MAX_LAYER_OPACITY))
        if op > MAX_LAYER_OPACITY:
            raise ValueError(f"layer {layer.get('id', i)} opacity {op} exceeds {MAX_LAYER_OPACITY}")
        if layer.get("blend", "normal") not in BLEND_MODES:
            raise ValueError(f"layer {layer.get('id', i)} has unknown blend {layer.get('blend')}")
        if "input" not in layer:
            raise ValueError(f"layer {layer.get('id', i)} needs an ffmpeg input index")
    first = layers[0]
    parts.append(f"color=c=black:s={width}x{height}:r={fps},format=gbrp[k]")
    parts.append(f"[{first['input']}:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
                 f"crop={width}:{height},fps={fps},format=gbrp,setsar=1[l0]")
    # blend 'normal' computes first*opacity + second*(1 - opacity); every other mode treats the
    # first input as the base and mixes the blended result in by opacity.
    parts.append(f"[l0][k]blend=all_mode=normal:all_opacity={float(first.get('opacity', 0.98)):g}:shortest=1[acc0]")
    acc = "acc0"
    for i, layer in enumerate(layers[1:], start=1):
        op = float(layer.get("opacity", 0.98))
        src = f"[{layer['input']}:v]"
        nxt = out_label if i == len(layers) - 1 else f"acc{i}"
        rect = layer.get("rect")
        if rect:
            w, h = _even(rect["w"] * width), _even(rect["h"] * height)
            x, y = int(round(rect["x"] * width)), int(round(rect["y"] * height))
            mask = _feather_mask_expr(layer.get("feather_px", 0), layer.get("corner_radius_px", 0), op)
            parts.append(f"{src}scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},"
                         f"format=yuva420p,setsar=1[p{i}]")
            parts.append(f"color=c=black:s={w}x{h}:r={fps}:d=1,trim=end_frame=1,format=gray,geq=lum='{mask}',"
                         f"loop=loop=-1:size=1:start=0,setpts=N/({fps}*TB)[pm{i}]")
            parts.append(f"[p{i}][pm{i}]alphamerge[pa{i}]")
            parts.append(f"[{acc}][pa{i}]overlay=x={x}:y={y}:format=gbrp:shortest=1[{nxt}]")
        else:
            mode = BLEND_MODES[layer.get("blend", "normal")]
            parts.append(f"{src}scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
                         f"fps={fps},format=gbrp,setsar=1[l{i}]")
            pair = f"[l{i}][{acc}]" if mode == "normal" else f"[{acc}][l{i}]"
            parts.append(f"{pair}blend=all_mode={mode}:all_opacity={op:g}:shortest=1[{nxt}]")
        acc = nxt
    if len(layers) == 1:
        parts.append(f"[{acc}]null[{out_label}]")
    return ";".join(parts)


# --------------------------------------------------------------------------- layout


def safe_rect(width: int, height: int, margins: dict) -> tuple[int, int, int, int]:
    """(x0, y0, x1, y1) inside the margins, given as fractions {top, bottom, left, right}."""
    x0 = int(round(margins.get("left", 0) * width))
    x1 = int(round(width - margins.get("right", 0) * width))
    y0 = int(round(margins.get("top", 0) * height))
    y1 = int(round(height - margins.get("bottom", 0) * height))
    if x1 <= x0 or y1 <= y0:
        raise ValueError("margins leave no safe area")
    return x0, y0, x1, y1


def place_box(box_w: int, box_h: int, center_y_fraction: float, width: int, height: int,
              margins: dict, align: str = "center") -> tuple[int, int]:
    """Top-left (x, y) for a box centred at center_y_fraction, pushed inside the safe area."""
    x0, y0, x1, y1 = safe_rect(width, height, margins)
    if box_w > x1 - x0 or box_h > y1 - y0:
        raise ValueError("box does not fit inside the safe area; reduce font size or words")
    if align == "left":
        x = x0
    elif align == "right":
        x = x1 - box_w
    else:
        x = int(round((x0 + x1) / 2 - box_w / 2))
    y = int(round(center_y_fraction * height - box_h / 2))
    return x, min(max(y, y0), y1 - box_h)


# --------------------------------------------------------------------------- Pillow renderers (optional)


def frosted_panel(frame, box: tuple[int, int, int, int], tint: str = "#0B1220", opacity: float = 0.62,
                  blur_px: float = 28, radius_px: int = 28, feather_px: int = 12):
    """Return a copy of ``frame`` with a frosted-glass panel in ``box`` (x0, y0, x1, y1).

    The region is blurred, tinted at ``opacity`` (capped at 0.98) and pasted back through a
    rounded, feathered mask so the panel has no hard rectangular edge.
    """
    from PIL import Image, ImageDraw, ImageFilter  # lazy

    if opacity > MAX_LAYER_OPACITY:
        raise ValueError(f"panel opacity {opacity} exceeds {MAX_LAYER_OPACITY}")
    img = frame.convert("RGB").copy()
    x0, y0, x1, y1 = box
    pad = int(blur_px * 2)
    ex = (max(0, x0 - pad), max(0, y0 - pad), min(img.width, x1 + pad), min(img.height, y1 + pad))
    region = img.crop(ex).filter(ImageFilter.GaussianBlur(blur_px))
    region = region.crop((x0 - ex[0], y0 - ex[1], x1 - ex[0], y1 - ex[1]))
    tinted = Image.blend(region, Image.new("RGB", region.size, tint), opacity)
    mask = Image.new("L", region.size, 0)
    inset = feather_px // 2
    ImageDraw.Draw(mask).rounded_rectangle((inset, inset, region.width - 1 - inset, region.height - 1 - inset),
                                           radius=radius_px, fill=255)
    if feather_px:
        mask = mask.filter(ImageFilter.GaussianBlur(feather_px / 2))
    img.paste(tinted, (x0, y0), mask)
    return img


def _font(path: str | None, size: int):
    from PIL import ImageFont  # lazy

    if path:
        return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def render_caption_preview(frame, words: Sequence[str], style: dict, keyword_index: int | None = None,
                           t_ms: float = 1000.0, font_path: str | None = None, margins: dict | None = None):
    """Draw one caption line on ``frame`` following a caption-style preset; returns a new image.

    Uses style.font.size_px (at the style's reference width, rescaled to the frame), fill, stroke,
    backing (frosted-glass/solid/pill/scrim/none), layout.center_y_fraction and emphasis
    (keyword colour and pop scale at ``t_ms`` after the keyword starts).
    """
    from PIL import ImageDraw  # lazy

    img = frame.convert("RGB")
    ref_w = style.get("reference_size", [1080, 1920])[0]
    k = img.width / ref_w
    size = max(8, int(round(style["font"]["size_px"] * k)))
    font = _font(font_path, size)
    draw = ImageDraw.Draw(img)
    stroke = style.get("stroke", {})
    sw = int(round(stroke.get("width_px", 0) * k))
    space = draw.textlength(" ", font=font)
    widths = [draw.textlength(w, font=font) for w in words]
    line_w = int(sum(widths) + space * (len(words) - 1)) + 2 * sw
    asc, desc = font.getmetrics() if hasattr(font, "getmetrics") else (size, size // 4)
    line_h = asc + desc + 2 * sw
    backing = style.get("backing", {})
    pad_y, pad_x = [int(round(p * k)) for p in backing.get("padding_px", [20, 32])]
    box_w, box_h = line_w + 2 * pad_x, line_h + 2 * pad_y
    x, y = place_box(box_w, box_h, style["layout"]["center_y_fraction"], img.width, img.height,
                     margins or {"top": 0.08, "bottom": 0.12, "left": 0.04, "right": 0.04})
    kind = backing.get("type", "none")
    if kind in ("frosted-glass", "solid", "pill", "scrim"):
        blur = backing.get("blur_px", 0) * k if kind == "frosted-glass" else 0
        radius = box_h // 2 if kind == "pill" else int(round(backing.get("radius_px", 0) * k))
        img = frosted_panel(img, (x, y, x + box_w, y + box_h), backing.get("tint", "#000000"),
                            backing.get("opacity", 0.6), blur_px=max(blur, 0.01), radius_px=radius,
                            feather_px=int(round(backing.get("feather_px", 0) * k)))
        draw = ImageDraw.Draw(img)
    cx = x + pad_x + sw
    emphasis = style.get("emphasis", {})
    for i, (word, w) in enumerate(zip(words, widths)):
        fill = style["fill"]
        wfont = font
        if i == keyword_index and emphasis.get("mode", "none") != "none":
            fill = emphasis.get("color", fill)
            peak = emphasis.get("scale_peak", 1.0)
            dur = max(1.0, emphasis.get("duration_ms", 180))
            u = _clamp01(t_ms / dur)
            scale = 1 + (peak - 1) * (math.sin(math.pi * u) if u < 1 else 0.0)
            if abs(scale - 1) > 1e-3:
                wfont = _font(font_path, max(8, int(round(size * scale))))
        draw.text((cx, y + pad_y + sw), word, font=wfont, fill=fill,
                  stroke_width=sw, stroke_fill=stroke.get("color", "#000000"))
        cx += w + space
    return img
