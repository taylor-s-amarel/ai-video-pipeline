"""How close text, logos and other overlays get to the frame edges, where platform UI sits
(video_re_detect_safe_margin_usage).

Method: overlays (captions, titles, stickers, logos) are detailed but hold still while the picture under them
changes. Frames are sampled (default 2 per second at 360 px wide) and grouped into 2-second windows. In each
window a pixel is overlay detail when its time-mean gradient magnitude is at least 8/255 and 2.5x the frame's
median, and its temporal standard deviation is at most 8/255; pixels are kept only inside 8x8 blocks where at
least 10% of pixels qualify (removes speckle). The extreme overlay pixels give that window's distance to each
frame edge. The payload reports the closest approach per side over the whole video (and when it happened),
the 10th-percentile margin, and margins as a share of the frame size. Caller-supplied text boxes
(``--param regions=evidence.json`` with ``text_regions``, or a JSON list of [x, y, w, h] in source pixels) are
used instead when given. Platform UI zones differ by app and change over time, so none are assumed here;
compare these margins with a zone map (video_re_safe_area_probe) to judge violations.

Limits: overlays that move (scrolling tickers, bouncing stickers) are missed unless regions are given; a static
detailed background (screen recording, still photo) reads as overlay everywhere and is flagged with
``static_background``; hairline graphics under 8/255 contrast are ignored.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_safe_margin_usage"
VERSION = "1.0.0"
DEFAULTS = {"window_s": 2.0, "grad_abs": 8.0, "grad_rel": 2.5, "static_tstd": 8.0, "block": 8, "block_frac": 0.1,
            "static_bg_share": 0.5, "regions": None}
DECODE = {"width": 360, "fps": 2.0, "max_frames": 240}
SIDES = ("top", "bottom", "left", "right")


def overlay_mask(frames, p) -> np.ndarray:
    g = core.luma(np.asarray(frames, dtype=np.float32))
    gm = core.grad_mag(g).mean(axis=0)
    tstd = g.std(axis=0) if len(g) > 1 else np.zeros_like(gm)
    med = float(np.median(gm))
    m = (gm >= max(p["grad_abs"], p["grad_rel"] * med)) & (tstd <= p["static_tstd"])
    b = int(p["block"])
    h, w = m.shape
    hb, wb = h // b, w // b
    frac = m[:hb * b, :wb * b].reshape(hb, b, wb, b).mean(axis=(1, 3))
    keep = np.kron(frac >= p["block_frac"], np.ones((b, b), bool))
    out = np.zeros_like(m)
    out[:hb * b, :wb * b] = m[:hb * b, :wb * b] & keep
    return out


def margins_of(mask: np.ndarray) -> dict | None:
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return None
    h, w = mask.shape
    return {"top": int(ys.min()), "bottom": int(h - 1 - ys.max()), "left": int(xs.min()), "right": int(w - 1 - xs.max())}


def load_regions(spec, info) -> list[tuple[float | None, list[float]]] | None:
    if spec is None:
        return None
    data = spec
    if isinstance(spec, str):
        data = json.loads(Path(spec).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("text_regions") or (data.get("payload") or {}).get("regions") or []
    out = []
    for r in data:
        if isinstance(r, dict) and "bbox" in r:
            out.append((r.get("t_s"), [float(v) for v in r["bbox"]]))
        elif isinstance(r, (list, tuple)) and len(r) == 4:
            out.append((None, [float(v) for v in r]))
    return out


def analyse(frames, times, info, params) -> dict:
    p = {**DEFAULTS, **params}
    f = np.asarray(frames)
    t = np.asarray(times, dtype=np.float64)
    n, h, w = f.shape[:3]
    scale = core.scale_of(info)
    W, H = w * scale, h * scale
    per_window = []  # (t, {side: px in source px})
    source = "static-detail"
    static_bg = False
    regions = load_regions(p.get("regions"), info)
    if regions:
        source = "regions"
        W = float(info.get("width") or W)
        H = float(info.get("height") or H)
        for ts, (x, y, bw, bh) in regions:
            per_window.append((ts, {"top": y, "bottom": H - (y + bh), "left": x, "right": W - (x + bw)}))
    else:
        dt = float(np.median(np.diff(t))) if n > 1 else 1.0
        k = max(2, int(round(p["window_s"] / max(dt, 1e-6))))
        for s in range(0, n, k):
            sl = f[s:s + k]
            if len(sl) < 2:
                continue
            m = overlay_mask(sl, p)
            if m.mean() > p["static_bg_share"]:
                static_bg = True
                continue
            mg = margins_of(m)
            if mg:
                per_window.append((float(t[s]), {k2: v * scale for k2, v in mg.items()}))
    payload = {"min_margin_px": None, "min_margin_ratio": None, "p10_margin_px": None, "closest_t_s": None,
               "source": source, "windows_with_overlay": len(per_window), "static_background": static_bg,
               "frames_analysed": int(n)}
    results = []
    if per_window:
        mins, ratios, p10, when = {}, {}, {}, {}
        for side in SIDES:
            vals = np.array([mg[side] for _, mg in per_window], dtype=np.float64)
            i = int(np.argmin(vals))
            mins[side] = int(round(max(0.0, vals[i])))
            ratios[side] = round(max(0.0, vals[i]) / (H if side in ("top", "bottom") else W), 4)
            p10[side] = int(round(max(0.0, float(np.percentile(vals, 10)))))
            when[side] = per_window[i][0]
            results.append({"t_start_s": when[side] or 0.0, "label": f"min_margin_{side}", "value": mins[side],
                            "confidence": 0.75 if source == "static-detail" else 0.85,
                            "evidence": f"closest {source} pixel to the {side} edge: {mins[side]} px "
                                        f"({ratios[side]:.1%} of the frame)"})
        payload.update({"min_margin_px": mins, "min_margin_ratio": ratios, "p10_margin_px": p10,
                        "closest_t_s": when})
    else:
        results.append({"label": "no_overlay_detail", "confidence": 0.6,
                        "evidence": "no static detailed overlay found" + (" (static background)" if static_bg else "")})
    errors = ["background is static: overlays cannot be separated from it"] if static_bg and not per_window else []
    return {"status": "partial" if errors else "ok", "results": results, "payload": payload, "errors": errors}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
