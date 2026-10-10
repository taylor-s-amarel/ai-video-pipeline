"""Picture-in-picture insets: rectangle, corner, border, shadow and on-screen time
(video_re_detect_picture_in_picture).

Method: frames are sampled (default 4 per second at 320 px wide) and grouped into windows of about one second.
Inside a window, an inset's outline is the only straight edge that stays put while the pictures inside and
outside it change. Two maps mark it: per-pixel edge persistence (share of frames with a strong gradient, for
bordered or contrasting insets) and the seam test shared with the split-screen detector (time-mean difference
across a boundary at least 2x that of its neighbours, for borderless insets between unrelated pictures).
Straight runs (gaps up to 8 px bridged) propose side positions; a rectangle is kept when each of its four
sides is marked along at least 60% of its length (corners excepted).
Rectangles covering 2-50% of the frame and not spanning it are kept. Rectangles nested within 12 px are one
inset: equal gaps on all sides are a border (width = gap, colour = median of the ring); gaps on two adjacent
sides only are a hard offset shadow (offset = the gaps). A soft drop shadow is reported when a 6 px band outside
two adjacent sides is consistently darker (>= 8/255) than the band on the opposite sides. Windows are linked
by overlap (IoU >= 0.6) into on-screen intervals; one missed window does not end an interval.

Limits: an inset over a static background whose own edges are also static can be confused with background
structure (support is lower); insets that move or scale are tracked only while they stay within the IoU link;
rounded insets need the corner gap allowance (see video_re_detect_rounded_corners for the radius); timing
resolution is one window.
"""

from __future__ import annotations

import sys

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_picture_in_picture"
VERSION = "1.0.0"
DEFAULTS = {"window_s": 1.0, "persist_thr": 0.7, "min_area": 0.02, "max_area": 0.5, "max_span": 0.9,
            "nest_px": 12, "link_iou": 0.6, "max_gap": 8, "min_cover": 0.6, "max_missed_windows": 1, "shadow_band": 6, "shadow_min_diff": 8.0, "corner_gap": 6}
DECODE = {"width": 320, "fps": 4.0, "max_frames": 480}


def rects_in_window(gray, p) -> list[dict]:
    n, h, w = gray.shape
    Ev, Eh = core.persistent_edges(gray)
    sx, sy, _, _ = core.seam_maps(gray)  # seams between two unrelated moving pictures (no border needed)
    Ev = np.maximum(Ev, np.pad(sx.astype(np.float32), [(0, 0), (0, 1)]))
    Eh = np.maximum(Eh, np.pad(sy.astype(np.float32), [(0, 1), (0, 0)]))
    rects = core.find_rectangles(Ev, Eh, int(0.1 * w), int(0.1 * h), tol=1, corner_gap=int(p["corner_gap"]),
                                 thr=p["persist_thr"], dedup_iou=0.97, max_gap=int(p["max_gap"]),
                                 min_cover=p["min_cover"])
    keep = []
    for r in rects:
        x, y, rw, rh = r["bbox"]
        a = rw * rh / float(w * h)
        if not (p["min_area"] <= a <= p["max_area"]) or rw > p["max_span"] * w or rh > p["max_span"] * h:
            continue
        keep.append(r)
    # merge nested rectangles (outer + inner = bordered inset)
    keep.sort(key=lambda r: -r["bbox"][2] * r["bbox"][3])
    out = []
    for r in keep:
        x, y, rw, rh = r["bbox"]
        parent = None
        for o in out:
            ox, oy, ow, oh = o["bbox"]
            gaps = [x - ox, y - oy, ox + ow - (x + rw), oy + oh - (y + rh)]
            if all(-1 <= gp <= p["nest_px"] for gp in gaps):
                parent = o
                if float(np.median(gaps)) >= 1.5:  # otherwise a 1 px duplicate of the same outline
                    o.setdefault("inner", []).append(r["bbox"])
                break
        if parent is None:
            out.append(dict(r))
    return out


def gaps_of(outer, inner) -> list[int]:
    x, y, rw, rh = outer
    ix, iy, iw, ih = inner
    return [ix - x, iy - y, x + rw - (ix + iw), y + rh - (iy + ih)]  # left, top, right, bottom


def describe(frames, bbox, inner, p) -> dict:
    f = np.asarray(frames, dtype=np.float32)
    n, h, w = f.shape[:3]
    border = None
    hard_shadow = None
    lum = core.luma(f).mean(axis=0)
    x, y, rw, rh = bbox
    ringed = [b for b in (inner or []) if min(gaps_of(bbox, b)) >= 1 and np.ptp(gaps_of(bbox, b)) <= 3]
    if ringed:
        ix, iy, iw, ih = max(ringed, key=lambda b: sum(gaps_of(bbox, b)))
        gaps = gaps_of(bbox, [ix, iy, iw, ih])
        ring = np.zeros((h, w), bool)
        ring[y:y + rh, x:x + rw] = True
        ring[iy + 1:iy + ih, ix + 1:ix + iw] = False
        px = f[:, ring].reshape(-1, 3)
        spread = float(np.percentile(np.abs(px - np.median(px, 0)).max(1), 80))
        border = {"px": round(float(np.median(gaps)), 1), "color": core.hex_color(np.median(px, 0)),
                  "uniform": spread <= 24.0}
    else:
        for ib in sorted(inner or [], key=lambda b: -sum(gaps_of(bbox, b))):
            gl, gt, gr, gb = gaps_of(bbox, ib)
            pairs = {"bottom-right": (gl, gt, gr, gb), "bottom-left": (gr, gt, gl, gb),
                     "top-right": (gl, gb, gr, gt), "top-left": (gr, gb, gl, gt)}
            for direction, (z1, z2, o1, o2) in pairs.items():
                if not (z1 <= 1 and z2 <= 1 and o1 >= 2 and o2 >= 2):
                    continue
                band = np.zeros((h, w), bool)
                band[y:y + rh, x:x + rw] = True
                band[ib[1]:ib[1] + ib[3], ib[0]:ib[0] + ib[2]] = False
                around = core.dilate(band, 4) & ~band
                around[ib[1]:ib[1] + ib[3], ib[0]:ib[0] + ib[2]] = False
                if band.any() and around.any() and lum[band].mean() < 0.85 * lum[around].mean():
                    hard_shadow = {"direction": direction,
                                   "offset_px": [o1 if "right" in direction else -o1, o2 if "bottom" in direction else -o2]}
                    bbox = list(ib)
                    break
            if hard_shadow:
                break
    x, y, rw, rh = bbox
    b = int(p["shadow_band"])
    g = core.luma(f).mean(axis=0)

    def band(side):
        if side == "right":
            return g[y + b:y + rh, min(w, x + rw + 1):min(w, x + rw + 1 + b)]
        if side == "left":
            return g[y + b:y + rh, max(0, x - 1 - b):max(0, x - 1)]
        if side == "bottom":
            return g[min(h, y + rh + 1):min(h, y + rh + 1 + b), x + b:x + rw]
        return g[max(0, y - 1 - b):max(0, y - 1), x + b:x + rw]

    means = {s: (float(band(s).mean()) if band(s).size else None) for s in ("left", "right", "top", "bottom")}
    shadow = None
    if None not in means.values():
        dx = means["left"] - means["right"]  # positive: right side darker
        dy = means["top"] - means["bottom"]
        parts = []
        if abs(dy) >= p["shadow_min_diff"]:
            parts.append("bottom" if dy > 0 else "top")
        if abs(dx) >= p["shadow_min_diff"]:
            parts.append("right" if dx > 0 else "left")
        if parts:
            shadow = {"direction": "-".join(parts), "darkening": round(max(abs(dx), abs(dy)) / 255.0, 3),
                      "offset_px": None}
    if hard_shadow:
        shadow = {"direction": hard_shadow["direction"],
                  "darkening": shadow["darkening"] if shadow else None, "offset_px": hard_shadow["offset_px"]}
    cx, cy = x + rw / 2, y + rh / 2
    horiz = "left" if cx < w / 3 else ("right" if cx > 2 * w / 3 else "center")
    vert = "top" if cy < h / 3 else ("bottom" if cy > 2 * h / 3 else "middle")
    corner = "center" if (horiz, vert) == ("center", "middle") else (f"{vert}-{horiz}" if horiz != "center" else vert)
    if vert == "middle" and horiz != "center":
        corner = f"middle-{horiz}"
    return {"bbox": bbox, "border": border, "shadow": shadow, "corner": corner,
            "margin": {"left": x, "top": y, "right": w - (x + rw), "bottom": h - (y + rh)}}


def analyse(frames, times, info, params) -> dict:
    p = {**DEFAULTS, **params}
    f = np.asarray(frames)
    t = np.asarray(times, dtype=np.float64)
    n, h, w = f.shape[:3]
    scale = core.scale_of(info)
    dt = float(np.median(np.diff(t))) if n > 1 else 1.0
    k = max(3, int(round(p["window_s"] / max(dt, 1e-6))))
    gray = core.gray_frames(f)
    tracks: list[dict] = []
    for start in range(0, max(1, n - k + 1), k):
        sl = slice(start, min(n, start + k))
        if sl.stop - sl.start < 3:
            break
        found = rects_in_window(gray[sl], p)
        t0, t1 = float(t[sl.start]), float(t[sl.stop - 1] + dt)
        for r in found:
            match = None
            for tr in tracks:
                if tr["open"] and core.iou(tr["bbox"], r["bbox"]) >= p["link_iou"]:
                    match = tr
                    break
            if match:
                match["t_end_s"] = t1
                match["supports"].append(r["support"])
                match["seen"] = True
                match["inner"] = match["inner"] or r.get("inner")
            else:
                tracks.append({"bbox": r["bbox"], "inner": r.get("inner"), "t_start_s": t0, "t_end_s": t1,
                               "supports": [r["support"]], "frames": sl, "seen": True, "open": True})
        for tr in tracks:
            if tr["open"]:
                tr["missed"] = 0 if tr.get("seen") else tr.get("missed", 0) + 1
                if tr["missed"] > p["max_missed_windows"]:
                    tr["open"] = False
            tr["seen"] = False
    insets, results = [], []
    for tr in tracks:
        d = describe(f[tr["frames"]], tr["bbox"], tr["inner"], p)
        bb = [int(round(v * scale)) for v in d["bbox"]]
        inset = {"bbox": bb, "corner": d["corner"],
                 "margin_px": {k2: int(round(v * scale)) for k2, v in d["margin"].items()},
                 "border": None if d["border"] is None else {**d["border"], "px": round(d["border"]["px"] * scale, 1)},
                 "shadow": None if d["shadow"] is None else {**d["shadow"], "offset_px": None if d["shadow"]["offset_px"] is None else [int(round(v * scale)) for v in d["shadow"]["offset_px"]]},
                 "t_start_s": round(tr["t_start_s"], 3), "t_end_s": round(tr["t_end_s"], 3),
                 "support": round(float(np.mean(tr["supports"])), 3)}
        insets.append(inset)
        results.append({"t_start_s": inset["t_start_s"], "t_end_s": inset["t_end_s"], "label": "inset",
                        "value": d["corner"], "confidence": min(0.95, 0.5 + 0.5 * inset["support"]),
                        "bbox": [int(v) for v in d["bbox"]],
                        "evidence": f"persistent rectangular outline in {len(tr['supports'])} window(s); "
                                    f"border {inset['border']}; shadow {inset['shadow']}"})
    payload = {"insets": insets, "frames_analysed": int(n), "window_s": round(k * dt, 3)}
    if not insets:
        results.append({"label": "no_inset", "confidence": 0.7, "evidence": f"no persistent rectangle in {n} frames"})
    return {"status": "ok" if n >= 3 else "partial", "results": results, "payload": payload,
            "errors": [] if n >= 3 else ["fewer than 3 frames"]}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
