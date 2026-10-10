"""Split-screen and grid layouts (1x2, 2x1, 2x2, 3-up ...) with panel rectangles
(video_re_detect_split_screen_layout).

Method: a seam between two panels is a line where neighbouring pixels belong to different pictures. Over sampled
frames the time-mean absolute difference across each column boundary (and row boundary) is compared with the
same quantity two to four pixels away on both sides; a seam pixel is at least 2x its neighbourhood and at least
3/255. A seam must cover at least 80% of the region it splits. The frame is split recursively (guillotine
cuts, at most 3 levels): the strongest seam splits a region, a second seam within 4% of the size is read as
the other side of a gutter, and both halves are searched again. Regions narrower than 12% of the frame are not
split further. More than 3 seams of similar strength on one axis at the top level means a striped texture,
not a layout, and the frame is left whole. Panels are classified as a grid (rows x columns) when the cuts line
up, otherwise as 3-up arrangements or custom-N.

Layout names are rows x columns: 1x2 = two panels side by side, 2x1 = two panels stacked.
Limits: panels whose content is identical across the seam (mirrored or duplicated video) leave no seam; a static
scene with a straight full-height edge (a door frame, a horizon) can be read as a seam when the camera never
moves; picture-in-picture insets are left to video_re_detect_picture_in_picture.
"""

from __future__ import annotations

import sys

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_split_screen_layout"
VERSION = "1.0.0"
DEFAULTS = {"ratio_thr": 2.0, "abs_min": 3.0, "span_thr": 0.8, "max_gutter_frac": 0.04, "min_panel_frac": 0.12,
            "max_depth": 3, "texture_guard": 3, "edge_margin_frac": 0.06}
DECODE = {"width": 320, "fps": 2.0, "max_frames": 60}


seam_maps = core.seam_maps


def split_region(sx, sy, region, depth, p, frame_w, frame_h, top=False):
    x0, y0, w, h = region
    if depth > p["max_depth"]:
        return [region], []
    cands = []
    min_w = p["min_panel_frac"] * frame_w
    min_h = p["min_panel_frac"] * frame_h
    if w >= 2 * min_w:
        span = sx[y0:y0 + h, x0:x0 + w - 1].mean(axis=0)  # per boundary column
        m = max(1, int(p["edge_margin_frac"] * w))
        for i in range(m, w - 1 - m):
            if span[i] >= p["span_thr"]:
                cands.append(("v", x0 + i, float(span[i])))
    if h >= 2 * min_h:
        span = sy[y0:y0 + h - 1, x0:x0 + w].mean(axis=1)
        m = max(1, int(p["edge_margin_frac"] * h))
        for i in range(m, h - 1 - m):
            if span[i] >= p["span_thr"]:
                cands.append(("h", y0 + i, float(span[i])))
    if not cands:
        return [region], []
    if top:
        for axis in ("v", "h"):
            pos = sorted(c[1] for c in cands if c[0] == axis)
            groups = np.split(np.array(pos), np.flatnonzero(np.diff(pos) > max(3, int(p["max_gutter_frac"] * (frame_w if axis == "v" else frame_h)))) + 1) if pos else []
            if len(groups) > p["texture_guard"]:
                cands = [c for c in cands if c[0] != axis]
        if not cands:
            return [region], []
    best = max(cands, key=lambda c: c[2])
    axis, pos, score = best
    gut = p["max_gutter_frac"] * (frame_w if axis == "v" else frame_h)
    partners = [c for c in cands if c[0] == axis and 0 < abs(c[1] - pos) <= gut and c[2] >= 0.8 * score]
    a, b = pos, pos
    if partners:
        far = max(partners, key=lambda c: abs(c[1] - pos))[1]
        a, b = min(pos, far), max(pos, far)
    seam = {"orientation": "vertical" if axis == "v" else "horizontal", "a": a, "b": b, "span": score}
    if axis == "v":
        left = (x0, y0, a + 1 - x0, h)
        right = (b + 1, y0, x0 + w - (b + 1), h)
        if left[2] < min_w or right[2] < min_w:
            return [region], []
        parts = [left, right]
    else:
        upper = (x0, y0, w, a + 1 - y0)
        lower = (x0, b + 1, w, y0 + h - (b + 1))
        if upper[3] < min_h or lower[3] < min_h:
            return [region], []
        parts = [upper, lower]
    panels, seams = [], [seam]
    for part in parts:
        pp, ss = split_region(sx, sy, part, depth + 1, p, frame_w, frame_h)
        panels += pp
        seams += ss
    return panels, seams


def name_layout(panels, w, h, tol) -> tuple[str, int | None, int | None]:
    n = len(panels)
    if n == 1:
        return "single", 1, 1

    def merge(vals):
        out = []
        for v in sorted(vals):
            if not out or v - out[-1] > tol:
                out.append(v)
        return out

    xs = merge([p[0] for p in panels])
    ys = merge([p[1] for p in panels])
    if len(xs) * len(ys) == n:
        return f"{len(ys)}x{len(xs)}", len(ys), len(xs)
    if n == 3:
        return "3-up", None, None
    return f"custom-{n}", None, None


def analyse(frames, times, info, params) -> dict:
    p = {**DEFAULTS, **params}
    f = np.asarray(frames)
    n, h, w = f.shape[:3]
    scale = core.scale_of(info)
    g = core.gray_frames(f)
    sx, sy, _, _ = seam_maps(g, p["ratio_thr"], p["abs_min"])
    panels, seams = split_region(sx, sy, (0, 0, w, h), 1, p, w, h, top=True)
    panels.sort(key=lambda r: (round(r[1] / max(1, h * 0.05)), r[0]))
    layout, rows, cols = name_layout(panels, w, h, tol=max(3, int(0.05 * max(w, h))))
    gutters = [s["b"] - s["a"] for s in seams if s["b"] > s["a"]]
    gutter_px = float(np.median(gutters)) * scale if gutters else None
    gutter_color = None
    if gutters:
        s0 = next(s for s in seams if s["b"] > s["a"])
        band = f[:, :, s0["a"] + 1:s0["b"] + 1] if s0["orientation"] == "vertical" else f[:, s0["a"] + 1:s0["b"] + 1]
        if band.size:
            gutter_color = core.hex_color(np.median(band.reshape(-1, 3), axis=0))
    payload = {
        "layout": layout, "rows": rows, "cols": cols,
        "panels": [{"x": int(round(r[0] * scale)), "y": int(round(r[1] * scale)), "w": int(round(r[2] * scale)),
                    "h": int(round(r[3] * scale))} for r in panels],
        "gutter_px": None if gutter_px is None else round(gutter_px, 1),
        "gutter_color": gutter_color,
        "seams": [{"orientation": s["orientation"], "position_px": round((s["a"] + s["b"]) / 2 * scale + 0.5 * scale, 1),
                   "span": round(s["span"], 3)} for s in seams],
        "frames_analysed": int(n),
    }
    results = [{"t_start_s": float(times[0]), "t_end_s": float(times[-1]), "label": layout, "value": len(panels),
                "confidence": 0.85 if layout != "single" else 0.7,
                "evidence": f"{len(seams)} seam(s) with span >= {p['span_thr']} over {n} frames"}]
    for i, r in enumerate(panels if len(panels) > 1 else []):
        results.append({"t_start_s": float(times[0]), "t_end_s": float(times[-1]), "label": f"panel_{i}",
                        "confidence": 0.8, "bbox": [int(v) for v in r]})
    status = "ok" if n >= 2 else "partial"
    errors = [] if n >= 2 else ["one frame: seams from static content cannot be excluded"]
    return {"status": status, "results": results, "payload": payload, "errors": errors}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
