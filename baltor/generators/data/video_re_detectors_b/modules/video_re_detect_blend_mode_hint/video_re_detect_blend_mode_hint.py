"""Find evidence of how a static overlay is blended over moving content: normal, screen, multiply or add.

Per pixel and colour channel (values 0-1), a static overlay O composited over moving content B(t)
gives an affine map C = g * B + c:

    normal (alpha a)   g = 1 - a (same in every channel and pixel)   c = a * O, so 0 <= c <= 1 - g
    screen             g = 1 - O                                      c = O,     so g + c = 1
    multiply           g = O                                          c = 0
    add (linear dodge) g = 1                                          c = O      (until clipping)

Method (one window over the clip, default 5 fps):

1. Per channel, temporal mean and std of every pixel, pooled into ``cell`` x ``cell`` cells.
   The content's own statistics (mu_B, sigma_B) are the medians over all cells, which assumes
   the overlay covers under half the frame and the content is statistically uniform.
2. g = sigma_C / sigma_B and c = mu_C - g * mu_B per cell and channel. Cells where any channel has
   |g - 1| > ``g_tol`` or |c| > ``c_tol`` form the overlay; the largest connected region is kept and
   its border cells are dropped.
3. Each model's constraint residual is computed over the region's (g, c) pairs and divided by
   their distance from "no overlay" (g = 1, c = 0). The lowest score wins; modes scoring within
   ``ambiguity`` x the best are reported together as ``ambiguous``. Some overlays are genuinely
   ambiguous: white in normal mode equals screen with grey, and black in normal mode equals
   multiply with grey, pixel for pixel; colour or spatial variation in the overlay separates them.

Limits: needs moving content under the overlay; clipping (bright content under add/screen) biases
g downward; content whose statistics differ under the overlay from elsewhere (a sky band behind a
lower-third) breaks the reference assumption; soft-light/overlay modes are not modelled (they are
non-linear in B) and show up as poor fits of every mode.
"""

from __future__ import annotations

import numpy as np

import vre_detect_kit as kit

DETECTOR = "video_re_detect_blend_mode_hint"
VERSION = "1.0.0"
DEFAULTS = {
    "cell": 8,
    "g_tol": 0.08,
    "c_tol": 0.04,
    "min_region_cells": 6,
    "min_moving_std": 0.03,
    "ambiguity": 1.6,
    "max_good_score": 0.25,
}
PARAM_DOCS = {
    "cell": "pooling cell size in analysed pixels",
    "g_tol": "|gain - 1| above which a cell is affected by an overlay",
    "c_tol": "|offset| (0-1 units) above which a cell is affected",
    "min_region_cells": "fewest cells in an overlay region",
    "min_moving_std": "content temporal std (0-1) needed to measure anything",
    "ambiguity": "modes scoring within this factor of the best are reported together",
    "max_good_score": "best normalised residual above which no mode fits (reported as unknown)",
}

MODES = ("normal", "screen", "multiply", "add")


def model_scores(g: np.ndarray, c: np.ndarray) -> dict:
    """Normalised constraint residuals (lower = better) for (g, c) arrays of shape (cells, 3)."""
    scale = float(np.sqrt(np.mean((g - 1) ** 2 + c ** 2))) + 1e-6
    gm = float(np.median(g))
    normal = np.sqrt(np.mean((g - gm) ** 2 + np.maximum(0, c - (1 - gm)) ** 2 + np.maximum(0, -c) ** 2))
    screen = np.sqrt(np.mean((g + c - 1) ** 2 + np.maximum(0, -c) ** 2))
    multiply = np.sqrt(np.mean(c ** 2 + np.maximum(0, g - 1) ** 2))
    add = np.sqrt(np.mean((g - 1) ** 2 + np.maximum(0, -c) ** 2))
    return {k: float(v) / scale for k, v in zip(MODES, (normal, screen, multiply, add))}


def analyse(frames, fps, p, ctx):
    rgb = kit.as_rgb(np.asarray(frames)).astype(np.float32) / 255.0
    N, H, W = rgb.shape[:3]
    t0 = ctx["t0"]
    empty = {"mode": "none", "candidates": [], "confidence": 0.0, "region": None, "scores": None,
             "fit": None, "frames_used": N}
    if N < 4:
        return {"status": "partial", "results": [], "payload": empty, "errors": ["need at least 4 frames"]}
    k = int(p["cell"])
    Hc, Wc = H // k, W // k
    a = rgb[:, :Hc * k, :Wc * k]
    mu = a.mean(axis=0).reshape(Hc, k, Wc, k, 3).mean(axis=(1, 3))
    var = a.var(axis=0).reshape(Hc, k, Wc, k, 3).mean(axis=(1, 3))
    sd = np.sqrt(var)
    sd_ref = np.median(sd.reshape(-1, 3), axis=0)
    mu_ref = np.median(mu.reshape(-1, 3), axis=0)
    if float(sd_ref.min()) < p["min_moving_std"]:
        return {"status": "partial", "results": [], "payload": empty,
                "errors": ["content barely moves; blend mode cannot be measured"]}
    g = sd / sd_ref
    c = mu - g * mu_ref
    affected = ((np.abs(g - 1) > p["g_tol"]) | (np.abs(c) > p["c_tol"])).any(axis=-1)
    labels, comps = kit.components(affected)
    comps = [cc for cc in comps if cc["area"] >= p["min_region_cells"]]
    if not comps:
        return {"status": "ok", "results": [], "payload": empty, "errors": []}
    best = comps[0]
    region = labels == best["label"]
    core = kit.erode(region, 1) & region
    use = core if core.sum() >= 3 else region
    gs, cs = g[use], c[use]
    scores = model_scores(gs, cs)
    order = sorted(MODES, key=lambda m: scores[m])
    top = scores[order[0]]
    cands = [m for m in order if scores[m] <= max(top * p["ambiguity"], top + 0.02)]
    if top > p["max_good_score"]:
        mode, conf = "unknown", 0.2
    elif len(cands) > 1:
        mode, conf = "ambiguous", 0.4
    else:
        second = scores[order[1]]
        mode, conf = order[0], float(np.clip(1 - top / max(second, 1e-6), 0.3, 0.95))
    x, y, w, h = best["bbox"]
    bbox = [x * k, y * k, w * k, h * k]
    payload = {
        "mode": mode, "candidates": cands if mode in {"ambiguous"} else ([mode] if mode in MODES else []),
        "confidence": conf,
        "region": {"bbox": bbox, "bbox_ratio": kit.bbox_ratio(bbox, W, H), "cells": int(use.sum())},
        "scores": scores,
        "fit": {"gain_median": np.median(gs, axis=0).tolist(), "offset_median": np.median(cs, axis=0).tolist(),
                "gain_spread": float(np.std(gs)), "offset_spread": float(np.std(cs))},
        "frames_used": N,
    }
    ev = ", ".join(f"{m} {scores[m]:.2f}" for m in order)
    results = [kit.result(f"blend_{mode}", conf, t_start_s=t0, t_end_s=t0 + N / fps, bbox=bbox,
                          value=cands, evidence=f"constraint residuals (lower fits better): {ev}")]
    return {"status": "ok", "results": results, "payload": payload, "errors": []}


DET = kit.Detector(DETECTOR, VERSION, DEFAULTS, analyse, long_side=320, fps=5.0, pix_fmt="rgb24", max_seconds=20.0,
                   description="Infer the blend mode (normal/screen/multiply/add) of a static overlay over moving content.")


def detect(frames, fps, **kw):
    """Envelope for frames (N, H, W, 3) uint8 at ``fps``; analyse one overlay segment at a time."""
    return DET.detect(frames, fps, **kw)


def detect_file(path, **kw):
    return DET.detect_file(path, **kw)


def main(argv=None):
    return DET.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
