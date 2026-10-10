"""Detect static overlay regions: areas that stay put while the picture moves (frames, logos, watermarks, UI).

Method (per analysis window, default 4 s at 4 fps, hop 2 s):

1. Skip the window unless the picture moves: the share of pixels whose temporal grey-level std
   exceeds ``2 * stable_std`` must be at least ``min_moving_share``.
2. Static structure: per pixel, the temporal mean of the Sobel gradient *vector* is compared with
   the temporal mean of its magnitude. A drawn-on edge keeps the same direction in every frame, so
   ``|mean(g)| >= edge_thr`` and ``|mean(g)| / mean(|g|) >= coherence_thr``; moving content averages
   out. This finds opaque overlays and alpha-blended watermarks alike.
3. The mask is closed (radius ``close_r``), split into connected regions, and regions smaller than
   ``min_area_ratio`` or larger than ``max_area_ratio`` of the frame are dropped.
4. Each region's opacity class comes from the ratio of a low quantile (``overlay_quantile``) of
   its temporal std to the window's median std over moving pixels: below ``opaque_ratio`` it is
   ``opaque``; otherwise ``translucent`` with ``opacity_estimate = 1 - ratio`` (alpha model
   C = aO + (1-a)B; the estimate is low when the overlay covers under ~20% of its box).
5. Regions in consecutive windows with IoU >= ``merge_iou`` are joined into one time span.

Limits: a locked-off camera's static background is indistinguishable from an overlay (it is
reported as static too); overlays that animate (pulsing logos, moving lower thirds) are missed;
time spans are accurate to one window hop. Detection only: this module never removes, masks
or inpaints a logo or watermark, and stores no pixels.
"""

from __future__ import annotations

import numpy as np

import vre_detect_kit as kit

DETECTOR = "video_re_detect_static_overlay_regions"
VERSION = "1.0.0"
DEFAULTS = {
    "window_s": 4.0,
    "hop_s": 2.0,
    "stable_std": 3.0,
    "min_moving_share": 0.3,
    "edge_thr": 12.0,
    "coherence_thr": 0.6,
    "close_r": 2,
    "min_area_ratio": 0.0015,
    "max_area_ratio": 0.25,
    "opaque_ratio": 0.15,
    "overlay_quantile": 0.2,
    "merge_iou": 0.5,
}
PARAM_DOCS = {
    "window_s": "analysis window length in seconds",
    "hop_s": "step between windows in seconds (time spans are accurate to this)",
    "stable_std": "temporal std (grey levels) under which a pixel counts as unchanged",
    "min_moving_share": "share of pixels that must change for a window to be analysed",
    "edge_thr": "minimum magnitude of the time-averaged gradient vector (levels/pixel)",
    "coherence_thr": "|mean gradient| / mean |gradient|: 1 = edge never moves, ~0 = moving content",
    "close_r": "radius of the closing that joins logo pieces into one region (pixels)",
    "min_area_ratio": "smallest region kept, as a share of the frame",
    "max_area_ratio": "largest region kept, as a share of the frame",
    "opaque_ratio": "region std / moving-pixel std below which a region is opaque",
    "overlay_quantile": "quantile of temporal std inside a region taken as the overlay's own pixels",
    "merge_iou": "IoU that joins regions of consecutive windows",
}


def position_label(bbox, w: int, h: int) -> str:
    x, y, bw, bh = bbox
    cx, cy = (x + bw / 2) / w, (y + bh / 2) / h
    col = "left" if cx < 1 / 3 else ("right" if cx > 2 / 3 else "")
    row = "top" if cy < 1 / 3 else ("bottom" if cy > 2 / 3 else "")
    return "-".join(p for p in (row, col) if p) or "center"


def window_regions(rgb: np.ndarray, p: dict) -> tuple[list[dict], bool]:
    gray = kit.as_gray(rgb)
    n, H, W = gray.shape
    std_t = gray.std(axis=0)
    moving = std_t > 2 * p["stable_std"]
    if moving.mean() < p["min_moving_share"]:
        return [], False
    gsum_x = np.zeros((H, W), np.float32)
    gsum_y = np.zeros((H, W), np.float32)
    msum = np.zeros((H, W), np.float32)
    for g in gray:
        gx, gy = kit.gradients(g)
        gsum_x += gx
        gsum_y += gy
        msum += np.hypot(gx, gy)
    mean_vec = np.hypot(gsum_x, gsum_y) / n
    mean_mag = msum / n
    coherence = mean_vec / np.maximum(mean_mag, 1e-6)
    structure = (mean_vec >= p["edge_thr"]) & (coherence >= p["coherence_thr"])
    r = int(p["close_r"])
    mask = kit.erode(kit.dilate(structure, r), r) if r > 0 else structure
    mask |= structure
    ref_std = float(np.median(std_t[moving])) if moving.any() else 0.0
    _, comps = kit.components(mask)
    frame_area = float(H * W)
    out = []
    for c in comps:
        x, y, w, h = c["bbox"]
        area = w * h / frame_area
        if area < p["min_area_ratio"] or area > p["max_area_ratio"]:
            continue
        inner = std_t[y:y + h, x:x + w]
        # overlay pixels are the least-changing ones inside the box (glyph gaps show plain content)
        ratio = float(np.quantile(inner, p["overlay_quantile"])) / max(ref_std, 1e-6)
        kind = "opaque" if ratio < p["opaque_ratio"] else "translucent"
        opacity = 1.0 if kind == "opaque" else float(np.clip(1.0 - ratio, 0.0, 1.0))
        med = np.median(rgb[:, y:y + h, x:x + w].reshape(-1, 3), axis=0)
        strength = float(np.clip(coherence[y:y + h, x:x + w][structure[y:y + h, x:x + w]].mean(), 0, 1)) \
            if structure[y:y + h, x:x + w].any() else 0.0
        out.append({"bbox": [x, y, w, h], "kind": kind, "opacity_estimate": opacity, "std_ratio": ratio,
                    "mean_color": kit.hexcolor(med), "coherence": strength})
    return out, True


def analyse(frames, fps, p, ctx):
    rgb = kit.as_rgb(np.asarray(frames))
    N, H, W = rgb.shape[:3]
    t0 = ctx["t0"]
    win = max(2, int(round(p["window_s"] * fps)))
    hop = max(1, int(round(p["hop_s"] * fps)))
    starts = list(range(0, max(1, N - win + 1), hop)) if N >= win else [0]
    tracks: list[dict] = []
    analysed = skipped = 0
    for s in starts:
        e = min(N, s + win)
        if e - s < 2:
            continue
        regs, ok = window_regions(rgb[s:e], p)
        if not ok:
            skipped += 1
            continue
        analysed += 1
        for rg in regs:
            match = None
            for tr in tracks:
                if tr["last_window"] >= s - hop and kit.iou(tr["bbox"], rg["bbox"]) >= p["merge_iou"]:
                    match = tr
                    break
            if match is None:
                tracks.append({**rg, "f0": s, "f1": e, "last_window": s, "n": 1})
            else:
                match["f1"] = e
                match["last_window"] = s
                match["n"] += 1
                match["opacity_estimate"] = (match["opacity_estimate"] * (match["n"] - 1) + rg["opacity_estimate"]) / match["n"]
                if rg["kind"] == "opaque":
                    match["kind"] = "opaque" if match["opacity_estimate"] > 0.9 else match["kind"]
    regions, results = [], []
    for tr in sorted(tracks, key=lambda d: (d["f0"], d["bbox"][1], d["bbox"][0])):
        x, y, w, h = tr["bbox"]
        reg = {
            "bbox": [x, y, w, h],
            "bbox_ratio": kit.bbox_ratio(tr["bbox"], W, H),
            "area_ratio": w * h / float(W * H),
            "t_start_s": t0 + tr["f0"] / fps,
            "t_end_s": t0 + tr["f1"] / fps,
            "kind": tr["kind"],
            "opacity_estimate": tr["opacity_estimate"],
            "position": position_label(tr["bbox"], W, H),
            "mean_color": tr["mean_color"],
            "edge_coherence": tr["coherence"],
        }
        regions.append(reg)
        conf = min(1.0, 0.5 + 0.5 * tr["coherence"]) * (1.0 if tr["n"] > 1 or analysed == 1 else 0.8)
        results.append(kit.result(f"static_{tr['kind']}_region", conf, t_start_s=reg["t_start_s"],
                                  t_end_s=reg["t_end_s"], bbox=reg["bbox"], value=reg["position"],
                                  evidence=f"edges kept direction in {tr['n']} window(s); std ratio "
                                           f"{tr['std_ratio']:.2f}; detection only, nothing removed"))
    errors = []
    if analysed == 0:
        errors.append("no window had enough moving picture to separate overlays from content")
    payload = {"handling": "detect-only", "regions": regions, "windows_analysed": analysed,
               "windows_skipped_static": skipped}
    return {"status": "ok" if analysed else "partial", "results": results, "payload": payload, "errors": errors}


DET = kit.Detector(DETECTOR, VERSION, DEFAULTS, analyse, long_side=320, fps=4.0, pix_fmt="rgb24",
                   description="Find regions that stay pixel-stable while the video moves (logos, frames, UI). Detection only.")


def detect(frames, fps, **kw):
    """Envelope for frames (N, H, W, 3) uint8 sampled at ``fps``."""
    return DET.detect(frames, fps, **kw)


def detect_file(path, **kw):
    return DET.detect_file(path, **kw)


def main(argv=None):
    return DET.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
