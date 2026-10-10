"""Detect parallax: layers that move the same way at different speeds, implying depth.

Method (per shot):

1. Coherent motion layers exactly as in ``video_re_detect_layer_count_estimate``: block phase
   correlation over the shot, rigid blocks grouped by sequential similarity fits (``tol`` px/frame).
2. Keep translating layers whose speed is at least ``min_speed`` px/frame.
3. Take the fastest layer's direction; every layer within ``angle_tol`` degrees of it joins the
   parallax set. Parallax is reported when the set has at least two layers and the fastest is at
   least ``min_ratio`` times the slowest. Layers are ranked by speed: in a camera translation the
   faster layer is nearer (``depth_rank`` 0 = nearest).

Directions are image angles of the content's motion: 0 = right, 90 = down, 180 = left, 270 = up.
Speeds are px/s of the analysed frame and frame widths per second.

Limits: an orbiting camera moves foreground and background in opposite directions, which this
reports as two layers without parallax; zooms with depth (dolly) are not separated by speed;
independently moving objects that happen to share a direction look like parallax.
"""

from __future__ import annotations

import math

import numpy as np

import vre_detect_kit as kit

DETECTOR = "video_re_detect_parallax_depth_layers"
VERSION = "1.0.0"
DEFAULTS = {
    "block": 32,
    "step": 16,
    "max_pairs": 30,
    "min_peak": 0.35,
    "min_reliable": 0.6,
    "max_spread": 0.75,
    "tol": 0.5,
    "min_blocks": 3,
    "min_texture": 4.0,
    "min_speed": 0.2,
    "angle_tol": 30.0,
    "min_ratio": 1.25,
    "cut_threshold": 0.3,
}
PARAM_DOCS = {
    "block": "block size in analysed pixels",
    "step": "grid step between blocks",
    "max_pairs": "frame pairs sampled per shot",
    "min_peak": "phase-correlation peak for a reliable block vector",
    "min_reliable": "share of pairs a block must be reliable in",
    "max_spread": "largest median deviation of a rigid block's vectors (px/frame)",
    "tol": "how close (px/frame) a block must follow a layer's motion",
    "min_blocks": "fewest blocks that make a layer",
    "min_texture": "block grey-level std below which it is ignored",
    "min_speed": "slowest layer speed (px/frame) that counts as moving",
    "angle_tol": "largest direction difference (degrees) inside one parallax set",
    "min_ratio": "fastest/slowest speed ratio needed to call parallax",
    "cut_threshold": "cut score for the built-in shot splitter",
}


def angle_of(vx: float, vy: float) -> float:
    return math.degrees(math.atan2(vy, vx)) % 360.0


def angle_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def shot_parallax(gray: np.ndarray, fps: float, p: dict) -> dict:
    H, W = gray.shape[1:]
    tr = kit.block_tracks(gray, p["block"], p["step"], p["max_pairs"], 1, p["min_peak"], 3.0)
    ml = kit.motion_layers(tr, (H, W), p["tol"], p["min_blocks"], p["min_reliable"], p["max_spread"],
                           p["min_texture"], 1e9)
    half = p["block"] / 2.0
    moving = []
    for ly in ml["layers"]:
        f = ly["fit"]
        speed = math.hypot(f["tx"], f["ty"])
        if speed < p["min_speed"]:
            continue
        cen = tr["centres"][ly["blocks"]]
        x0, y0 = max(0.0, cen[:, 0].min() - half), max(0.0, cen[:, 1].min() - half)
        x1, y1 = min(W, cen[:, 0].max() + half), min(H, cen[:, 1].max() + half)
        bbox = [x0, y0, x1 - x0, y1 - y0]
        moving.append({"speed": speed, "dir": angle_of(f["tx"], f["ty"]), "bbox": bbox,
                       "share": len(ly["blocks"]) / max(1, int((~ml["flat"]).sum()))})
    if not moving:
        return {"parallax": False, "direction_deg": None, "layers": [], "max_speed_ratio": None}
    moving.sort(key=lambda d: -d["speed"])
    lead = moving[0]
    group = [m for m in moving if angle_diff(m["dir"], lead["dir"]) <= p["angle_tol"]]
    slowest = min(m["speed"] for m in group)
    ratio = lead["speed"] / max(slowest, 1e-6)
    parallax = len(group) >= 2 and ratio >= p["min_ratio"]
    layers = []
    for rank, m in enumerate(sorted(group, key=lambda d: -d["speed"])):
        x, y, w, h = m["bbox"]
        layers.append({
            "speed_px_s": m["speed"] * fps,
            "speed_fw_per_s": m["speed"] / W * fps,
            "speed_ratio": m["speed"] / max(slowest, 1e-6),
            "direction_deg": m["dir"],
            "depth_rank": rank,
            "block_share": m["share"],
            "region": {"bbox": m["bbox"], "bbox_ratio": kit.bbox_ratio(m["bbox"], W, H),
                       "y_center_ratio": (y + h / 2) / H},
        })
    return {"parallax": bool(parallax), "direction_deg": lead["dir"], "layers": layers,
            "max_speed_ratio": ratio, "other_moving_layers": len(moving) - len(group)}


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
            rec.update(parallax=None, direction_deg=None, layers=[], max_speed_ratio=None, other_moving_layers=0)
            errors.append(f"shot {k}: fewer than 3 frames, not measured")
            shots.append(rec)
            continue
        info = shot_parallax(gray[a:b], fps, p)
        info.setdefault("other_moving_layers", 0)
        rec.update(info)
        shots.append(rec)
        if info["parallax"]:
            ratios = ", ".join(f"{ly['speed_ratio']:.2f}" for ly in info["layers"])
            conf = min(1.0, 0.5 + 0.25 * (len(info["layers"]) - 1) + 0.1 * (info["max_speed_ratio"] - 1))
            results.append(kit.result("parallax", conf, t_start_s=rec["t_start_s"], t_end_s=rec["t_end_s"],
                                      value=len(info["layers"]),
                                      evidence=f"{len(info['layers'])} layers moving at {info['direction_deg']:.0f} deg "
                                               f"with speed ratios {ratios}"))
    measured = [s for s in shots if s["parallax"] is not None]
    payload = {"shots": shots, "shots_with_parallax": sum(1 for s in measured if s["parallax"]),
               "max_layers_in_parallax": max((len(s["layers"]) for s in measured if s["parallax"]), default=0)}
    return {"status": "ok" if measured else "partial", "results": results, "payload": payload, "errors": errors}


DET = kit.Detector(DETECTOR, VERSION, DEFAULTS, analyse, long_side=320, fps=10.0, pix_fmt="gray",
                   description="Find layers moving the same way at different speeds (parallax) per shot.")


def detect(frames, fps, **kw):
    """Envelope for frames (N, H, W[, 3]) uint8 at ``fps``."""
    return DET.detect(frames, fps, **kw)


def detect_file(path, **kw):
    return DET.detect_file(path, **kw)


def main(argv=None):
    return DET.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
