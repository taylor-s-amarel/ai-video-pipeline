"""Letterbox / pillarbox bars: sizes in px, colour, and blurred-fill vs solid (video_re_detect_letterbox_pillarbox).

Method: frames are sampled (default 1 per second at 480 px wide). For every frame edge, lines (rows for
top/bottom, columns for left/right) are scanned inwards. A solid bar line has at least 97% of its pixels within
12/255 of the bar colour (the median colour of the outermost line); static text or a logo inside the bar is
allowed if the bar resumes after it. Thickness is the 10th percentile of the per-frame runs so dark content
touching the bar in a few frames does not widen it. When no solid bar exists, a blurred-fill bar is a run of
lines whose mean gradient is below 0.2 x the centre's while still changing over time (the usual
"blurred copy of the video behind it" fill). Sizes are reported in source pixels (analysis px x scale).

Limits: a bar colour that also fills the content edge on every sampled frame (black background graphics
touching a black bar) is counted as bar; gradient or patterned fills are reported as static-texture when they do
not move; precision is about one analysis pixel times the scale (reported as px_precision).
"""

from __future__ import annotations

import sys

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_letterbox_pillarbox"
VERSION = "1.0.0"
DEFAULTS = {"tol": 12.0, "pixel_frac": 0.97, "frame_quorum": 0.9, "blur_ratio": 0.2, "min_bar_px": 2,
            "overlay_frac": 0.5, "overlay_tstd": 3.0}
DECODE = {"width": 480, "fps": 1.0, "max_frames": 90}


def detect_bars(frames, **params) -> dict:
    """Return bars per side in analysis pixels: {side: {px, color, style, consistency, overlay_lines}}."""
    p = {**DEFAULTS, **params}
    return core.scan_edge_bars(frames, tol=p["tol"], pixel_frac=p["pixel_frac"], frame_quorum=p["frame_quorum"],
                               blur_ratio=p["blur_ratio"], overlay_frac=p["overlay_frac"],
                               overlay_tstd=p["overlay_tstd"])


def classify(bars: dict, min_px: int) -> str:
    tb = bars["top"]["px"] >= min_px and bars["bottom"]["px"] >= min_px
    lr = bars["left"]["px"] >= min_px and bars["right"]["px"] >= min_px
    if tb and lr:
        return "windowbox"
    if tb:
        return "letterbox"
    if lr:
        return "pillarbox"
    if any(bars[s]["px"] >= min_px for s in bars):
        return "single-side"
    return "none"


def analyse(frames, times, info, params) -> dict:
    f = np.asarray(frames)
    n, h, w = f.shape[:3]
    scale = core.scale_of(info)
    bars = detect_bars(f, **{k: v for k, v in params.items() if k in DEFAULTS})
    min_px = int(params.get("min_bar_px", 2))
    kind = classify(bars, min_px)
    out_bars, results = [], []
    t0 = float(times[0]) if len(times) else 0.0
    t1 = float(times[-1]) if len(times) else 0.0
    for side in ("top", "bottom", "left", "right"):
        b = bars[side]
        if b["px"] < min_px:
            continue
        px_src = int(round(b["px"] * scale))
        out_bars.append({"side": side, "px": px_src, "color": b["color"], "style": b["style"],
                         "consistency": b["consistency"], "overlay_in_bar": b["overlay_lines"] > 0})
        if side == "top":
            bbox = [0, 0, w, b["px"]]
        elif side == "bottom":
            bbox = [0, h - b["px"], w, b["px"]]
        elif side == "left":
            bbox = [0, 0, b["px"], h]
        else:
            bbox = [w - b["px"], 0, b["px"], h]
        conf = 0.5 + 0.5 * b["consistency"] if b["style"] == "solid" else 0.6
        results.append({"t_start_s": t0, "t_end_s": t1, "label": f"bar_{side}", "value": px_src,
                        "confidence": conf, "bbox": bbox,
                        "evidence": f"{b['style']} {b['color']} bar of {b['px']} analysis px on {n} frame(s); "
                                    f"{int(b['consistency'] * 100)}% of frames within 2 px"})
    rect = core.content_rect_from_bars({s: {"px": bars[s]["px"] if bars[s]["px"] >= min_px else 0} for s in bars}, h, w)
    rect_src = [int(round(v * scale)) for v in rect]
    payload = {
        "kind": kind,
        "bars": out_bars,
        "content_rect": {"x": rect_src[0], "y": rect_src[1], "w": rect_src[2], "h": rect_src[3]},
        "content_aspect": round(rect[2] / rect[3], 4) if rect[3] else None,
        "frames_analysed": int(n),
        "px_precision": round(max(1.0, scale), 3),
    }
    results.insert(0, {"t_start_s": t0, "t_end_s": t1, "label": kind, "value": len(out_bars),
                       "confidence": float(np.mean([r["confidence"] for r in results])) if results else 0.8,
                       "evidence": f"{len(out_bars)} bar(s) found on {n} sampled frame(s)"})
    status = "ok" if n >= 3 else "partial"
    errors = [] if n >= 3 else ["fewer than 3 frames: bar thickness may include dark content"]
    return {"status": status, "results": results, "payload": payload, "errors": errors}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
