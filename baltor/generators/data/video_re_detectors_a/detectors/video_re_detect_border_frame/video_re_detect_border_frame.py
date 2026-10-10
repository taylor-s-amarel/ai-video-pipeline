"""Decorative border / padding frame around moving content: width per side, colour or gradient, inner radius
(video_re_detect_border_frame).

Method: the border of a framed video is static while the content inside moves. Per pixel temporal standard
deviation over the sampled frames separates static pixels (std <= 3/255 by default). Each side is scanned
inwards: a line belongs to the border while at least 95% of its pixels are static. Border pixels are then
described: solid when their colour spread is within 8/255, gradient when a linear colour ramp over (x, y)
explains at least 80% of the variance, otherwise textured. The inner corner radius is fitted to the inset of
static pixels along the first rows inside each corner of the content rectangle (circle model, grid search),
and the median of the four corners is reported. Sizes are in source pixels.

Limits: needs moving content (a still image has no static/moving contrast and returns status partial); a static
title or logo touching the frame edge across a whole side can be read as border; borders thinner than one
analysis pixel are not resolved; outer rounding of the whole frame is not measured.
"""

from __future__ import annotations

import sys

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_border_frame"
VERSION = "1.0.0"
DEFAULTS = {"static_tstd": 3.0, "line_static_frac": 0.95, "solid_tol": 8.0, "gradient_r2": 0.8,
            "min_px": 2, "max_frac": 0.25, "min_sides": 3, "moving_min_tstd": 4.0}
DECODE = {"width": 480, "fps": 2.0, "max_frames": 60}


def static_mask(frames, static_tstd: float) -> tuple[np.ndarray, np.ndarray]:
    f = np.asarray(frames, dtype=np.float32)
    tstd = f.std(axis=0).max(axis=-1)
    return tstd <= static_tstd, tstd


def side_widths(static: np.ndarray, line_frac: float, max_frac: float) -> dict:
    h, w = static.shape
    out = {}
    for side in ("top", "right", "bottom", "left"):
        if side == "top":
            lines, lim = static, int(h * max_frac)
        elif side == "bottom":
            lines, lim = static[::-1], int(h * max_frac)
        elif side == "left":
            lines, lim = static.T, int(w * max_frac)
        else:
            lines, lim = static.T[::-1], int(w * max_frac)
        frac = lines[: lim + 1].mean(axis=1)
        bad = np.flatnonzero(frac < line_frac)
        out[side] = int(bad[0]) if len(bad) else lim + 1
    return out


def corner_insets(static: np.ndarray, rect: list[int], depth: int) -> list[list[int]]:
    """Static-pixel insets inside the four corners of rect, one list per corner (tl, tr, br, bl)."""
    x0, y0, rw, rh = rect
    sub = static[y0:y0 + rh, x0:x0 + rw]
    out = []
    for flip in ((False, False), (False, True), (True, True), (True, False)):
        s = sub[::-1] if flip[0] else sub
        s = s[:, ::-1] if flip[1] else s
        rows = []
        for i in range(min(depth, s.shape[0])):
            row = s[i, :depth]
            rows.append(int(np.argmin(row)) if not row.all() else depth)
        out.append(rows)
    return out


def describe_colour(frames, border_mask, solid_tol: float, gradient_r2: float) -> dict:
    f = np.asarray(frames, dtype=np.float32).mean(axis=0)
    ys, xs = np.nonzero(border_mask)
    px = f[ys, xs]
    color = core.hex_color(np.median(px, axis=0))
    spread = float(np.percentile(np.abs(px - np.median(px, axis=0)).max(axis=1), 95))
    if spread <= solid_tol:
        return {"style": "solid", "color": color, "gradient": None}
    A = np.stack([np.ones_like(xs), xs, ys], axis=1).astype(np.float64)
    coef, *_ = np.linalg.lstsq(A, px.astype(np.float64), rcond=None)
    pred = A @ coef
    r2 = 1 - ((px - pred) ** 2).sum() / max(1e-9, ((px - px.mean(0)) ** 2).sum())
    if r2 >= gradient_r2:
        g = coef[1:].T  # (3, 2): d colour / d(x, y)
        evals, evecs = np.linalg.eigh(g.T @ g)
        v = evecs[:, int(np.argmax(evals))]
        ang = float(np.degrees(np.arctan2(v[1], v[0]))) % 180.0
        u = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
        proj = xs * u[0] + ys * u[1]
        lo, hi = np.argmin(proj), np.argmax(proj)
        return {"style": "gradient", "color": color,
                "gradient": {"from": core.hex_color(pred[lo]), "to": core.hex_color(pred[hi]), "angle_deg": round(ang, 1),
                             "r2": round(float(r2), 3)}}
    return {"style": "textured", "color": color, "gradient": None}


def analyse(frames, times, info, params) -> dict:
    p = {**DEFAULTS, **params}
    f = np.asarray(frames)
    n, h, w = f.shape[:3]
    scale = core.scale_of(info)
    errors = []
    if n < 3:
        return {"status": "partial", "results": [], "errors": ["need at least 3 frames to separate static border from moving content"],
                "payload": {"detected": False, "border": None, "content_rect": None, "static_content": True,
                            "frames_analysed": int(n)}}
    static, tstd = static_mask(f, p["static_tstd"])
    widths = side_widths(static, p["line_static_frac"], p["max_frac"])
    capped = [s for s, v in widths.items() if v > (h if s in ("top", "bottom") else w) * p["max_frac"]]
    inner = tstd[int(h * 0.3):int(h * 0.7), int(w * 0.3):int(w * 0.7)]
    static_content = bool(np.median(inner) < p["moving_min_tstd"]) or len(capped) >= 2
    sides = {s: (v if s not in capped else 0) for s, v in widths.items()}
    n_sides = sum(1 for v in sides.values() if v >= p["min_px"])
    detected = n_sides >= p["min_sides"] and not static_content
    rect = [sides["left"], sides["top"], w - sides["left"] - sides["right"], h - sides["top"] - sides["bottom"]]
    payload = {"detected": bool(detected), "border": None,
               "content_rect": {"x": int(round(rect[0] * scale)), "y": int(round(rect[1] * scale)),
                                "w": int(round(rect[2] * scale)), "h": int(round(rect[3] * scale))},
               "static_content": static_content, "frames_analysed": int(n)}
    results = []
    if static_content:
        errors.append("content barely moves: static border cannot be separated from static content")
    if detected:
        bmask = np.zeros((h, w), bool)
        bmask[: sides["top"]] = True
        bmask[h - sides["bottom"]:] = True
        bmask[:, : sides["left"]] = True
        bmask[:, w - sides["right"]:] = True
        col = describe_colour(f, bmask & static, p["solid_tol"], p["gradient_r2"])
        depth = int(min(rect[2], rect[3]) * 0.5)
        radii, rmses = [], []
        for ins in corner_insets(static, rect, depth):
            r, e = core.corner_radius_fit(ins, depth)
            radii.append(r)
            rmses.append(e)
        radius = float(np.median(radii))
        payload["border"] = {
            "top": int(round(sides["top"] * scale)), "right": int(round(sides["right"] * scale)),
            "bottom": int(round(sides["bottom"] * scale)), "left": int(round(sides["left"] * scale)),
            "style": col["style"], "color": col["color"], "gradient": col["gradient"],
            "inner_radius_px": round(radius * scale, 2) if radius >= 1 else 0.0,
            "corner_radii_px": [round(r * scale, 2) for r in radii],
        }
        conf = 0.6 + 0.1 * n_sides
        results.append({"t_start_s": float(times[0]), "t_end_s": float(times[-1]), "label": "border_frame",
                        "value": payload["border"]["style"], "confidence": min(0.95, conf),
                        "bbox": [0, 0, w, h],
                        "evidence": f"static {col['style']} frame {sides} analysis px around moving content; "
                                    f"inner radius fit rmse {np.median(rmses):.2f} px"})
    else:
        results.append({"label": "no_border", "confidence": 0.5 if static_content else 0.8,
                        "evidence": f"static edge widths {sides} on {n} frames; {n_sides} side(s) above {p['min_px']} px"})
    return {"status": "partial" if static_content else "ok", "results": results, "payload": payload, "errors": errors}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
