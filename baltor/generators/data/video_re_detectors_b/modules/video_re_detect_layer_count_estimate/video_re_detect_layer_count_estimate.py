"""Estimate how many independently moving layers each shot has.

Method (per shot; shots come from ``--evidence`` or from the kit's histogram cut detector):

1. Block motion: grey frames are split into ``block`` px blocks on a ``step`` px grid and each block's
   translation between consecutive analysed frames is measured by low-pass-weighted phase
   correlation (up to ``max_pairs`` frame pairs per shot). A block is *rigid* when it is reliable
   (correlation peak >= ``min_peak``) in at least ``min_reliable`` of the pairs and its vectors
   spread no more than ``max_spread`` px/frame around their median.
2. Sequential similarity fits: seed with the densest velocity cluster (tolerance ``tol`` px/frame),
   fit pan + zoom + rotation to it, absorb every rigid block that the model predicts within
   ``tol``, refit, and repeat on the rest. Each fit is one motion layer (a zooming background is
   one layer, not many).
3. Textured blocks that change by at least ``nonrigid_change`` grey levels but are rarely
   reliable are non-rigid motion (water, particles, crowds); if they cover at least
   ``min_nonrigid_share`` of the textured blocks they count as one more layer.

The count is a lower bound on the composited layers: layers that move together, fully covered
layers and flat (untextured) layers cannot be told apart. Velocities are in frame widths/heights
per second, zoom as natural-log scale change per second (positive = growing).
"""

from __future__ import annotations

import math

import numpy as np

import vre_detect_kit as kit

DETECTOR = "video_re_detect_layer_count_estimate"
VERSION = "1.0.0"
DEFAULTS = {
    "block": 32,
    "step": 16,
    "max_pairs": 30,
    "min_peak": 0.35,
    "min_reliable": 0.6,
    "max_spread": 0.75,
    "tol": 0.6,
    "min_blocks": 3,
    "min_texture": 4.0,
    "nonrigid_change": 6.0,
    "min_nonrigid_share": 0.08,
    "static_speed": 0.15,
    "zoom_per_frame": 0.002,
    "cut_threshold": 0.3,
}
PARAM_DOCS = {
    "block": "block size in analysed pixels",
    "step": "grid step between blocks in analysed pixels",
    "max_pairs": "frame pairs sampled per shot",
    "min_peak": "phase-correlation peak for a reliable block vector",
    "min_reliable": "share of pairs a block must be reliable in to count as rigid",
    "max_spread": "largest median deviation of a rigid block's vectors (px/frame)",
    "tol": "how close (px/frame) a block must follow a layer's motion model",
    "min_blocks": "fewest blocks that make a layer",
    "min_texture": "block grey-level std below which it is flat and ignored",
    "nonrigid_change": "mean abs grey change for an unreliable block to count as non-rigid motion",
    "min_nonrigid_share": "share of textured blocks that makes non-rigid motion a layer",
    "static_speed": "speed (px/frame) under which a layer is static",
    "zoom_per_frame": "|ln scale| per frame above which a layer is zooming",
    "cut_threshold": "histogram/pixel cut score for the built-in shot splitter",
}


def classify_layer(fit: dict, p: dict) -> str:
    if abs(math.log(max(fit["scale"], 1e-6))) >= p["zoom_per_frame"]:
        return "zooming"
    if math.hypot(fit["tx"], fit["ty"]) < p["static_speed"]:
        return "static"
    return "moving"


def shot_layers(gray: np.ndarray, fps: float, p: dict) -> dict:
    H, W = gray.shape[1:]
    tr = kit.block_tracks(gray, p["block"], p["step"], p["max_pairs"], 1, p["min_peak"], 3.0)
    ml = kit.motion_layers(tr, (H, W), p["tol"], p["min_blocks"], p["min_reliable"], p["max_spread"],
                           p["min_texture"], p["nonrigid_change"])
    textured = int((~ml["flat"]).sum())
    out_layers = []
    half = p["block"] / 2.0
    for ly in ml["layers"]:
        b = ly["blocks"]
        cen = tr["centres"][b]
        x0, y0 = max(0.0, cen[:, 0].min() - half), max(0.0, cen[:, 1].min() - half)
        x1, y1 = min(W, cen[:, 0].max() + half), min(H, cen[:, 1].max() + half)
        f = ly["fit"]
        out_layers.append({
            "kind": classify_layer(f, p),
            "velocity_fw_per_s": [f["tx"] / W * fps, f["ty"] / H * fps],
            "zoom_per_s": math.log(max(f["scale"], 1e-6)) * fps,
            "block_share": len(b) / max(1, textured),
            "bbox": [x0, y0, x1 - x0, y1 - y0],
        })
    nonrigid_share = float(ml["nonrigid"].sum()) / max(1, textured)
    if nonrigid_share >= p["min_nonrigid_share"]:
        nb = np.flatnonzero(ml["nonrigid"])
        cen = tr["centres"][nb]
        x0, y0 = max(0.0, cen[:, 0].min() - half), max(0.0, cen[:, 1].min() - half)
        x1, y1 = min(W, cen[:, 0].max() + half), min(H, cen[:, 1].max() + half)
        out_layers.append({"kind": "nonrigid", "velocity_fw_per_s": None, "zoom_per_s": None,
                           "block_share": nonrigid_share, "bbox": [x0, y0, x1 - x0, y1 - y0]})
    assigned = sum(ly["block_share"] for ly in out_layers)
    return {"layers": sorted(out_layers, key=lambda d: -d["block_share"]), "pairs_used": tr["pairs"],
            "flat_share": float(ml["flat"].mean()) if ml["n_blocks"] else 1.0,
            "unassigned_share": max(0.0, 1.0 - assigned) if textured else 1.0}


def analyse(frames, fps, p, ctx):
    gray = kit.as_gray(np.asarray(frames))
    N = len(gray)
    t0 = ctx["t0"]
    cuts = None if ctx.get("shots") else kit.detect_cuts(gray, fps, abs_thr=p["cut_threshold"])
    ranges = kit.shot_ranges(N, fps, t0, cuts, ctx.get("shots"))
    shots, results, errors = [], [], []
    for k, (a, b) in enumerate(ranges):
        rec = {"shot_index": k, "t_start_s": t0 + a / fps, "t_end_s": t0 + b / fps}
        if b - a < 3:
            rec.update(layer_count=None, layers=[], pairs_used=0, flat_share=None, unassigned_share=None)
            errors.append(f"shot {k}: fewer than 3 frames, not measured")
            shots.append(rec)
            continue
        info = shot_layers(gray[a:b], fps, p)
        rec.update(layer_count=len(info["layers"]), **info)
        shots.append(rec)
        conf = max(0.1, min(1.0, 1.0 - info["unassigned_share"])) * min(1.0, info["pairs_used"] / 8)
        kinds = ", ".join(ly["kind"] for ly in info["layers"]) or "none"
        results.append(kit.result("layer_count", conf, t_start_s=rec["t_start_s"], t_end_s=rec["t_end_s"],
                                  value=rec["layer_count"],
                                  evidence=f"{len(info['layers'])} coherent motion layer(s): {kinds}; "
                                           f"{info['unassigned_share']:.0%} of textured blocks unassigned"))
    counts = [s["layer_count"] for s in shots if s["layer_count"] is not None]
    payload = {"method": "block-phase-correlation+sequential-similarity-fit", "shots": shots,
               "max_layer_count": max(counts) if counts else None,
               "median_layer_count": float(np.median(counts)) if counts else None}
    return {"status": "ok" if counts else "partial", "results": results, "payload": payload, "errors": errors}


DET = kit.Detector(DETECTOR, VERSION, DEFAULTS, analyse, long_side=320, fps=10.0, pix_fmt="gray",
                   description="Estimate the number of independently moving layers per shot from block motion.")


def detect(frames, fps, **kw):
    """Envelope for frames (N, H, W[, 3]) uint8 at ``fps``."""
    return DET.detect(frames, fps, **kw)


def detect_file(path, **kw):
    return DET.detect_file(path, **kw)


def main(argv=None):
    return DET.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
