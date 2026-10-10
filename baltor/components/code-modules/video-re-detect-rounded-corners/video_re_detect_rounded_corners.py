"""Corner radius of photos, cards and panels, estimated from the curvature of their outline
(video_re_detect_rounded_corners).

Method: elements are found in two ways. (1) Static elements over a moving background (cards, captions panels,
framed photos): pixels whose temporal standard deviation stays below 3/255 while the frame's median is above
6/255 form a mask; connected components covering 1-60% of the frame, not touching the frame edge, are the
elements and the mask gives their outline exactly. (2) Elements given by the caller (``--param rects=[[x,y,w,h]]``
in analysis pixels, e.g. from the picture-in-picture or frosted-panel detectors) or found as rectangles in edge
maps: their outline is the first marked pixel (edge persistence or seam) met when walking inwards from the
bounding box. For each corner the inset of the outline over the rows (and, symmetrically, columns) next to the
corner is fitted with a circle, r - sqrt(r^2 - (r - i - 0.5)^2), by grid search in 0.25 px steps. The element
radius is the median of the four corners; ``shape`` is rect (r < 1.5 px), rounded, or pill (r >= 0.45 x the short
side). Radii are in source pixels.

Limits: non-circular corners (squircles, chamfers) are reported with the best circle and a larger fit error;
antialiasing and analysis downscaling limit precision to about one analysis pixel; elements that move or
whose content blends into the background need given rectangles and clear edges.
"""

from __future__ import annotations

import sys

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_rounded_corners"
VERSION = "1.0.0"
DEFAULTS = {"static_tstd": 3.0, "moving_min_tstd": 6.0, "min_area": 0.01, "max_area": 0.6, "min_fill": 0.6,
            "edge_thr": 0.6, "pill_ratio": 0.45, "rect_corner_gap": 24, "rects": None}
DECODE = {"width": 480, "fps": 2.0, "max_frames": 60}


def corner_profiles(inside: np.ndarray, bbox, depth: int) -> list[list[int]]:
    """Insets for the four corners (tl, tr, br, bl), averaging the row-wise and column-wise walk.
    ``inside`` is a boolean map where True marks the element (mask) or its outline (edges)."""
    x, y, w, h = bbox
    H, W = inside.shape
    sub = np.zeros((h + 2, w + 2), bool)
    ys0, xs0 = max(0, y - 1), max(0, x - 1)
    ys1, xs1 = min(H, y + h + 1), min(W, x + w + 1)
    sub[ys0 - (y - 1):ys0 - (y - 1) + (ys1 - ys0), xs0 - (x - 1):xs0 - (x - 1) + (xs1 - xs0)] = inside[ys0:ys1, xs0:xs1]
    profiles = []
    for fy, fx in ((False, False), (False, True), (True, True), (True, False)):
        s = sub[::-1] if fy else sub
        s = s[:, ::-1] if fx else s
        s = s[1:, 1:]  # drop the 1 px margin on the corner side
        rows = []
        for i in range(min(depth, s.shape[0])):
            hit = np.flatnonzero(s[i, :depth])
            rows.append(int(hit[0]) if len(hit) else depth)
        cols = []
        for i in range(min(depth, s.shape[1])):
            hit = np.flatnonzero(s[:depth, i])
            cols.append(int(hit[0]) if len(hit) else depth)
        n = min(len(rows), len(cols))
        profiles.append([(rows[k] + cols[k]) / 2.0 for k in range(n)])
    return profiles


def measure(inside: np.ndarray, bbox, scale: float, pill_ratio: float) -> dict:
    x, y, w, h = bbox
    depth = max(2, int(min(w, h) * 0.5))
    radii, errs = [], []
    for prof in corner_profiles(inside, bbox, depth):
        # the first row may sit on the bbox line itself; drop leading rows that are entirely outside
        r, e = core.corner_radius_fit(np.minimum(prof, depth), depth)
        radii.append(r)
        errs.append(e)
    r = float(np.median(radii))
    shape = "rect" if r < 1.5 else ("pill" if r >= pill_ratio * min(w, h) else "rounded")
    names = ("tl", "tr", "br", "bl")
    return {"bbox": [int(round(v * scale)) for v in bbox], "radius_px": round(r * scale, 2),
            "corners": {k: round(v * scale, 2) for k, v in zip(names, radii)},
            "fit_rmse_px": round(float(np.median(errs)) * scale, 3), "shape": shape}


def analyse(frames, times, info, params) -> dict:
    p = {**DEFAULTS, **params}
    f = np.asarray(frames, dtype=np.float32)
    n, h, w = f.shape[:3]
    scale = core.scale_of(info)
    errors, elements, method = [], [], None
    gray = core.luma(f)
    if p.get("rects"):
        Ev, Eh = core.persistent_edges(gray)
        sx, sy, _, _ = core.seam_maps(gray)
        E = np.maximum(np.maximum(Ev, Eh), np.maximum(np.pad(sx, [(0, 0), (0, 1)]), np.pad(sy, [(0, 1), (0, 0)])))
        for bb in p["rects"]:
            elements.append({**measure(E >= p["edge_thr"], [int(v) for v in bb], scale, p["pill_ratio"]), "source": "given"})
        method = "given-rects"
    elif n >= 3:
        tstd = f.std(axis=0).max(axis=-1)
        if np.median(tstd) >= p["moving_min_tstd"]:
            mask = tstd <= p["static_tstd"]
            for comp in core.component_boxes(mask, min_area=int(p["min_area"] * w * h)):
                x, y, bw, bh = comp["bbox"]
                if comp["area"] > p["max_area"] * w * h or comp["fill"] < p["min_fill"]:
                    continue
                if x == 0 or y == 0 or x + bw >= w or y + bh >= h:
                    continue
                elements.append({**measure(mask, comp["bbox"], scale, p["pill_ratio"]), "source": "static-mask"})
            method = "static-mask"
        if not elements:
            Ev, Eh = core.persistent_edges(gray)
            sx, sy, _, _ = core.seam_maps(gray)
            Ev = np.maximum(Ev, np.pad(sx.astype(np.float32), [(0, 0), (0, 1)]))
            Eh = np.maximum(Eh, np.pad(sy.astype(np.float32), [(0, 1), (0, 0)]))
            E = np.maximum(Ev, Eh) >= p["edge_thr"]
            g = int(p["rect_corner_gap"] / max(scale, 1e-6)) if scale > 1 else int(p["rect_corner_gap"])
            for r in core.find_rectangles(Ev, Eh, int(0.1 * w), int(0.1 * h), corner_gap=g, thr=p["edge_thr"],
                                          max_gap=6, min_cover=0.6)[:6]:
                x, y, bw, bh = r["bbox"]
                if bw * bh > p["max_area"] * w * h:
                    continue
                elements.append({**measure(E, r["bbox"], scale, p["pill_ratio"]), "source": "edge-rect"})
            method = "edge-rect" if elements else method
    else:
        errors.append("need 3+ frames (or given rects) to separate elements from the background")
    results = [{"t_start_s": float(times[0]), "t_end_s": float(times[-1]), "label": e["shape"],
                "value": e["radius_px"], "confidence": max(0.3, min(0.9, 0.9 - 0.1 * e["fit_rmse_px"])),
                "bbox": [int(round(v / scale)) for v in e["bbox"]],
                "evidence": f"{e['source']} outline; corner radii {e['corners']} px, fit rmse {e['fit_rmse_px']} px"}
               for e in elements]
    if not elements:
        results.append({"label": "no_element", "confidence": 0.5, "evidence": f"no element outline found in {n} frames"})
    payload = {"elements": elements, "method": method, "frames_analysed": int(n)}
    return {"status": "ok" if not errors else "partial", "results": results, "payload": payload, "errors": errors}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
