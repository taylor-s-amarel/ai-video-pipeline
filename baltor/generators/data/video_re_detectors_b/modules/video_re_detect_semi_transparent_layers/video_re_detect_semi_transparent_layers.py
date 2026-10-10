"""Detect semi-transparent overlay panels and estimate their opacity.

Model: inside a static panel of colour O and opacity a over moving content B(t), every pixel is
C(t) = a*O + (1 - a)*B(t), so its temporal standard deviation shrinks by (1 - a) and its mean moves
toward O.

Method (per window, default 6 s at 5 fps, hop 3 s):

1. Temporal grey-level std per pixel, smoothed with a (2*smooth_r+1)^2 box. Skip the window if
   fewer than ``min_moving_share`` of pixels change by more than ``move_std`` levels.
2. Candidates: pixels whose smoothed std is below ``dim_ratio`` x the median std of moving pixels.
   Connected regions are kept when they fill at least ``min_rectangularity`` of their bounding box
   (panels have straight edges; natural low-motion areas usually do not) and cover
   ``min_area_ratio``-``max_area_ratio`` of the frame.
3. Opacity: a = 1 - median(std inside) / median(std in a ``ring_px`` ring outside the box).
   a >= ``opaque_at`` is reported as opaque. Tint: O = (mean_in - (1 - a) * mean_ring) / a per channel.
4. Frosting cue: gradient energy inside vs the ring. Pure alpha scales it by (1 - a); a ratio below
   ``blur_factor`` x (1 - a) means the content behind was also blurred (frosted glass).

Limits: assumes the content under the panel moves like the content around it (a ring that is
static, or a panel over a different scene, biases the estimate); blurred backing makes the
opacity an upper bound; panels that move are missed; non-rectangular soft vignettes are left to
other detectors.
"""

from __future__ import annotations

import numpy as np

import vre_detect_kit as kit

DETECTOR = "video_re_detect_semi_transparent_layers"
VERSION = "1.0.0"
DEFAULTS = {
    "window_s": 6.0,
    "hop_s": 3.0,
    "move_std": 4.0,
    "min_moving_share": 0.3,
    "smooth_r": 3,
    "dim_ratio": 0.8,
    "min_rectangularity": 0.75,
    "min_area_ratio": 0.004,
    "max_area_ratio": 0.6,
    "ring_px": 6,
    "opaque_at": 0.98,
    "blur_factor": 0.5,
    "merge_iou": 0.5,
}
PARAM_DOCS = {
    "window_s": "analysis window in seconds",
    "hop_s": "step between windows in seconds",
    "move_std": "temporal std (grey levels) above which a pixel counts as moving",
    "min_moving_share": "share of moving pixels needed to analyse a window",
    "smooth_r": "box radius used to smooth the std map",
    "dim_ratio": "std / reference std under which a pixel is a panel candidate",
    "min_rectangularity": "region area / bounding-box area needed for a panel",
    "min_area_ratio": "smallest panel as a share of the frame",
    "max_area_ratio": "largest panel as a share of the frame",
    "ring_px": "width of the reference ring outside the panel box",
    "opaque_at": "opacity at or above which the panel is reported as opaque",
    "blur_factor": "gradient ratio below blur_factor*(1-a) flags blurred (frosted) backing",
    "merge_iou": "IoU that joins panels of consecutive windows",
}


def ring_mask(H: int, W: int, bbox, r: int) -> np.ndarray:
    x, y, w, h = bbox
    m = np.zeros((H, W), dtype=bool)
    m[max(0, y - r):min(H, y + h + r), max(0, x - r):min(W, x + w + r)] = True
    m[y:y + h, x:x + w] = False
    return m


def window_panels(rgb: np.ndarray, p: dict) -> tuple[list[dict], bool]:
    gray = kit.as_gray(rgb)
    n, H, W = gray.shape
    std = gray.std(axis=0)
    moving = std > p["move_std"]
    if moving.mean() < p["min_moving_share"]:
        return [], False
    ref = float(np.median(std[moving]))
    sm = kit.box_mean(std, int(p["smooth_r"]))
    cand = sm < p["dim_ratio"] * ref
    _, comps = kit.components(cand)
    mean_rgb = rgb.astype(np.float32).mean(axis=0)
    grad_in = np.zeros((H, W), np.float32)
    for g in gray[:: max(1, n // 8)]:
        grad_in += kit.grad_mag(g)
    out = []
    for c in comps:
        x, y, w, h = c["bbox"]
        area = w * h / float(H * W)
        if area < p["min_area_ratio"] or area > p["max_area_ratio"]:
            continue
        if c["area"] / float(w * h) < p["min_rectangularity"]:
            continue
        ring = ring_mask(H, W, c["bbox"], int(p["ring_px"])) & ~cand
        if ring.sum() < 20:
            continue
        inner = np.zeros((H, W), dtype=bool)
        r = int(p["smooth_r"])
        inner[y + r:y + h - r, x + r:x + w - r] = True
        if inner.sum() < 10:
            inner[y:y + h, x:x + w] = True
        s_ring = float(np.median(std[ring]))
        if s_ring < p["move_std"]:
            continue
        a = float(np.clip(1.0 - np.median(std[inner]) / s_ring, 0.0, 1.0))
        m_in = mean_rgb[inner].mean(axis=0)
        m_ring = mean_rgb[ring].mean(axis=0)
        tint = (m_in - (1 - a) * m_ring) / a if a >= 0.2 else None
        g_ratio = float(np.median(grad_in[inner]) / max(np.median(grad_in[ring]), 1e-6))
        blurred = bool(a < p["opaque_at"] and (1 - a) > 0.05 and g_ratio < p["blur_factor"] * (1 - a))
        out.append({"bbox": [x, y, w, h], "opacity": a, "tint": tint, "gradient_ratio": g_ratio,
                    "blurred_behind": blurred, "rectangularity": c["area"] / float(w * h)})
    return out, True


def analyse(frames, fps, p, ctx):
    rgb = kit.as_rgb(np.asarray(frames))
    N, H, W = rgb.shape[:3]
    t0 = ctx["t0"]
    win = max(2, int(round(p["window_s"] * fps)))
    hop = max(1, int(round(p["hop_s"] * fps)))
    starts = list(range(0, max(1, N - win + 1), hop)) if N >= win else [0]
    tracks: list[dict] = []
    analysed = 0
    for s in starts:
        e = min(N, s + win)
        if e - s < 3:
            continue
        panels, ok = window_panels(rgb[s:e], p)
        if not ok:
            continue
        analysed += 1
        for pn in panels:
            tr = next((t for t in tracks if t["last"] >= s - hop and kit.iou(t["bbox"], pn["bbox"]) >= p["merge_iou"]), None)
            if tr is None:
                tracks.append({**pn, "f0": s, "f1": e, "last": s, "ops": [pn["opacity"]]})
            else:
                tr.update(f1=e, last=s)
                tr["ops"].append(pn["opacity"])
                tr["blurred_behind"] = tr["blurred_behind"] or pn["blurred_behind"]
    regions, results = [], []
    for tr in sorted(tracks, key=lambda d: (d["f0"], d["bbox"][1])):
        a = float(np.median(tr["ops"]))
        kind = "opaque" if a >= p["opaque_at"] else "semi_transparent"
        reg = {"bbox": tr["bbox"], "bbox_ratio": kit.bbox_ratio(tr["bbox"], W, H),
               "t_start_s": t0 + tr["f0"] / fps, "t_end_s": t0 + tr["f1"] / fps,
               "kind": kind, "opacity": a,
               "tint_color": kit.hexcolor(tr["tint"]) if tr["tint"] is not None else None,
               "blurred_behind": tr["blurred_behind"], "gradient_ratio": tr["gradient_ratio"],
               "rectangularity": tr["rectangularity"]}
        regions.append(reg)
        conf = min(1.0, 0.4 + 0.6 * tr["rectangularity"]) * (0.9 if tr["blurred_behind"] else 1.0)
        results.append(kit.result(kind, conf, t_start_s=reg["t_start_s"], t_end_s=reg["t_end_s"], value=round(a, 3),
                                  bbox=tr["bbox"], evidence=f"temporal std inside is {1 - a:.2f} of the ring around it"
                                  + ("; content behind is blurred (frosted)" if tr["blurred_behind"] else "")))
    semi = [r for r in regions if r["kind"] == "semi_transparent"]
    payload = {"regions": regions, "windows_analysed": analysed,
               "max_opacity": max((r["opacity"] for r in regions), default=None),
               "semi_transparent_count": len(semi)}
    errors = [] if analysed else ["no window had enough moving content under a panel to measure opacity"]
    return {"status": "ok" if analysed else "partial", "results": results, "payload": payload, "errors": errors}


DET = kit.Detector(DETECTOR, VERSION, DEFAULTS, analyse, long_side=320, fps=5.0, pix_fmt="rgb24",
                   description="Find panels that moving content shows through and estimate their opacity.")


def detect(frames, fps, **kw):
    """Envelope for frames (N, H, W, 3) uint8 at ``fps``."""
    return DET.detect(frames, fps, **kw)


def detect_file(path, **kw):
    return DET.detect_file(path, **kw)


def main(argv=None):
    return DET.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
