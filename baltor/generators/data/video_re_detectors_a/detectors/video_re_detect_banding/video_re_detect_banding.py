"""Gradient banding (posterised steps) in smooth regions (video_re_detect_banding).

Method: banding is measured on code values, so the command line reads the raw Y plane (no range conversion,
no scaling; centre crop of at most 960 x 960 px). Arrays given in Python may be Y codes (N,H,W) or RGB (the green
channel is used). Each frame is cut into 48 x 48 blocks. A block is a smooth ramp when a least-squares plane
over it rises by at least 4 code values (8-bit scale) and the residual around the plane is at most 3 codes
(a gentle gradient, not texture or an edge). In a smooth ramp the number of distinct code values L should be
about the range R + 1; the effective step q = R / (L - 1) is about 1 for clean 8-bit gradients (dithered
or not) and grows with posterisation. A ramp block is banded when q >= 1.8 codes. The score is the banded share of
ramp blocks; banded blocks are merged into regions. The median run of equal values along the gradient
direction (flat_run_px) tells how wide each visible band is.

Limits: 8-bit quantisation itself makes steps of 1 code that can be visible in very dark or very wide
gradients; they are not counted (q stays near 1) but flat_run_px shows them. Limited-range sources
converted to RGB give q near 1.16, still below the threshold. Noise or dither hides banding (by design).
Values are in the source's code values; 10-bit sources are scaled to 8-bit equivalents.
"""

from __future__ import annotations

import sys

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_banding"
VERSION = "1.0.0"
DEFAULTS = {"block": 48, "min_rise": 4.0, "max_resid": 3.0, "step_thr": 1.8, "min_count": 2}
DECODE = {"width": 0, "fps": 0.5, "max_frames": 8, "crop": [960, 960], "crop_align": 2, "mode": "y"}


def to_codes(frames, info) -> np.ndarray:
    a = np.asarray(frames)
    if a.ndim == 4:
        a = a[..., 1]
    a = a.astype(np.float32)
    if a.dtype != np.uint8 and int(info.get("bit_depth") or 8) > 8 and a.max() > 255:
        a = a / (2 ** (int(info["bit_depth"]) - 8))
    return a


def analyse_block(v: np.ndarray, p) -> dict | None:
    h, w = v.shape
    yy, xx = np.mgrid[0:h, 0:w]
    A = np.stack([np.ones(h * w), xx.ravel(), yy.ravel()], axis=1)
    coef, *_ = np.linalg.lstsq(A, v.ravel().astype(np.float64), rcond=None)
    plane = (A @ coef).reshape(h, w)
    rise = float(plane.max() - plane.min())
    resid = float((v - plane).std())
    if rise < p["min_rise"] or resid > p["max_resid"]:
        return None
    vals, counts = np.unique(np.round(v), return_counts=True)
    vals = vals[counts >= p["min_count"]]
    if len(vals) < 2:
        return None
    rng = float(np.percentile(v, 99) - np.percentile(v, 1))
    q = rng / max(1, len(vals) - 1)
    # flat runs along the dominant gradient axis
    axis = 1 if abs(coef[1]) >= abs(coef[2]) else 0
    lines = v if axis == 1 else v.T
    runs = []
    for line in lines[:: max(1, len(lines) // 8)]:
        change = np.flatnonzero(np.diff(np.round(line)) != 0)
        if len(change) >= 2:
            runs.extend(np.diff(change).tolist())
    return {"q": q, "rise": rise, "flat_run": float(np.median(runs)) if runs else float(len(lines[0]))}


def analyse(frames, times, info, params) -> dict:
    p = {**DEFAULTS, **params}
    codes = to_codes(frames, info)
    n, h, w = codes.shape
    b = int(p["block"])
    scale = core.scale_of(info)
    ramp = 0
    banded_map = np.zeros((n, h // b, w // b), bool)
    qs, runs = [], []
    for i in range(n):
        for by in range(h // b):
            for bx in range(w // b):
                r = analyse_block(codes[i, by * b:(by + 1) * b, bx * b:(bx + 1) * b], p)
                if r is None:
                    continue
                ramp += 1
                if r["q"] >= p["step_thr"]:
                    banded_map[i, by, bx] = True
                    qs.append(r["q"])
                    runs.append(r["flat_run"])
    regions = []
    if banded_map.any():
        union = banded_map.any(axis=0)
        for comp in core.component_boxes(union):
            x, y, bw, bh = comp["bbox"]
            regions.append({"bbox": [int(round(v * b * scale)) for v in (x, y, bw, bh)],
                            "blocks": int(comp["area"])})
    share = (banded_map.sum() / ramp) if ramp else None
    payload = {
        "score": None if share is None else round(float(share), 4),
        "banded": bool(share is not None and share >= 0.1),
        "step_code_values": None if not qs else round(float(np.median(qs)), 3),
        "flat_run_px": None if not runs else round(float(np.median(runs)) * scale, 2),
        "ramp_blocks": int(ramp),
        "banded_blocks": int(banded_map.sum()),
        "regions": regions[:20],
        "frames_analysed": int(n),
    }
    t = np.asarray(times, dtype=np.float64)
    results = [{"t_start_s": float(t[0]), "t_end_s": float(t[-1]),
                "label": "banded" if payload["banded"] else ("no_gradients" if not ramp else "clean_gradients"),
                "value": payload["score"], "confidence": 0.75 if ramp >= 10 else 0.4,
                "evidence": f"{payload['banded_blocks']} of {ramp} smooth-ramp blocks have steps >= {p['step_thr']} codes "
                            f"(median step {payload['step_code_values']})"}]
    for r in regions[:5]:
        results.append({"t_start_s": float(t[0]), "t_end_s": float(t[-1]), "label": "banded_region",
                        "confidence": 0.7, "bbox": [int(round(v / scale)) for v in r["bbox"]],
                        "evidence": f"{r['blocks']} banded {b}px block(s)"})
    errors = [] if ramp else ["no smooth gradients to test"]
    return {"status": "ok" if ramp else "partial", "results": results, "payload": payload, "errors": errors}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
