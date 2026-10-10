"""Compression blockiness (8x8 block-edge energy) and ringing as an encode-quality estimate
(video_re_detect_compression_blockiness).

Method: frames are decoded at native resolution (centre crop of at most 640 x 640 px with offsets on a 16 px
grid, so the codec's block grid keeps its phase; no scaling). For each axis the mean absolute luma difference
across block boundaries (every 8th column or row, at the phase 0-7 that maximises it) is divided by the mean
difference at all other positions. Unblocked pictures give about 1.0; DCT blocking raises it because each block
is smoothed internally and steps at its edges. The same ratio is computed on low-activity rows/columns only
(where blocking is most visible) and for 4- and 16-pixel periods. Labels from the larger axis ratio (heuristic
thresholds, not a standard): clean < 1.1 <= mild < 1.3 <= visible < 1.7 <= heavy; score = clip(ratio - 1, 0, 1).
Ringing (mosquito noise): the high-pass standard deviation in a 2-3 px band beside strong edges (gradient >= 40)
that are otherwise flat, divided by the same in flat areas at least 6 px from any edge.

Limits: H.264/HEVC/AV1 deblocking filters and variable block sizes weaken the fixed-grid signal, so a "clean"
label means no visible fixed grid, not a high bitrate; scaling after encoding moves the grid off the 8 px
period (the phase search does not recover a non-integer period); strongly periodic textures with an 8 px period
can raise the ratio; the ringing ratio is a heuristic and also rises with real fine texture next to edges.
"""

from __future__ import annotations

import sys

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_compression_blockiness"
VERSION = "1.0.0"
DEFAULTS = {"period": 8, "flat_activity": 4.0, "edge_thr": 40.0, "thresholds": [1.1, 1.3, 1.7]}
DECODE = {"width": 0, "fps": 1.0, "max_frames": 12, "crop": [640, 640], "crop_align": 16}


def boundary_ratio(gray, period: int = 8, axis: int = 1, mask_low_activity: float | None = None) -> tuple[float, int]:
    """(ratio, phase) of mean |difference| across period boundaries vs elsewhere, best phase."""
    g = np.asarray(gray, dtype=np.float32)
    if g.ndim == 2:
        g = g[None]
    d = np.abs(np.diff(g, axis=axis + 1))  # axis 1: columns -> diff along x
    prof = d.mean(axis=(0, 1)) if axis == 1 else d.mean(axis=(0, 2))
    if mask_low_activity is not None:
        act = d.mean(axis=2 if axis == 1 else 1)  # per row (axis=1) or per column (axis=0)
        keep = act <= mask_low_activity
        if keep.sum() >= 4:
            if axis == 1:
                prof = (d * keep[..., None]).sum(axis=(0, 1)) / keep.sum()
            else:
                prof = (d * keep[:, None, :]).sum(axis=(0, 2)) / keep.sum()
        else:
            return float("nan"), 0
    n = len(prof)
    idx = np.arange(n)
    best = (0.0, 0)
    for phase in range(period):
        on = ((idx + 1 - phase) % period) == 0
        if on.sum() == 0 or (~on).sum() == 0:
            continue
        r = float(prof[on].mean() / max(1e-6, prof[~on].mean()))
        if r > best[0]:
            best = (r, phase)
    return best


def ringing_ratio(gray, edge_thr: float) -> float | None:
    g = np.asarray(gray, dtype=np.float32)
    hp = g - core.blur(g, 1.0)
    gm = core.grad_mag(g)
    edges = gm >= edge_thr
    if edges.mean() < 0.002:
        return None
    near = core.dilate(edges, 3) & ~core.dilate(edges, 1)
    far = ~core.dilate(edges, 6) & (core.box_blur(gm, 3, axes=(0, 1)) < edge_thr / 8)
    if near.sum() < 50 or far.sum() < 50:
        return None
    return float(np.std(hp[near]) / max(0.05, np.std(hp[far])))


def analyse(frames, times, info, params) -> dict:
    p = {**DEFAULTS, **params}
    g = core.gray_frames(frames)
    per = int(p["period"])
    rh, ph = boundary_ratio(g, per, axis=1)
    rv, pv = boundary_ratio(g, per, axis=0)
    fh, _ = boundary_ratio(g, per, axis=1, mask_low_activity=p["flat_activity"])
    fv, _ = boundary_ratio(g, per, axis=0, mask_low_activity=p["flat_activity"])
    grid = {}
    for q in (4, 8, 16):
        a, _ = boundary_ratio(g, q, axis=1)
        b, _ = boundary_ratio(g, q, axis=0)
        grid[str(q)] = round(max(a, b), 4)
    ratio = max(rh, rv)
    t1, t2, t3 = p["thresholds"]
    label = "clean" if ratio < t1 else ("mild" if ratio < t2 else ("visible" if ratio < t3 else "heavy"))
    rings = [r for r in (ringing_ratio(x, p["edge_thr"]) for x in g[: min(len(g), 6)]) if r is not None]

    def fin(v):
        return None if v is None or not np.isfinite(v) else round(float(v), 4)

    payload = {
        "blockiness_score": round(float(np.clip(ratio - 1.0, 0.0, 1.0)), 4),
        "label": label,
        "ratio": {"x": round(rh, 4), "y": round(rv, 4)},
        "ratio_flat_areas": {"x": fin(fh), "y": fin(fv)},
        "grid_phase": {"x": int(ph), "y": int(pv)},
        "grid_ratios": grid,
        "ringing_ratio": None if not rings else round(float(np.median(rings)), 4),
        "native_pixels": core.scale_of(info) == 1.0,
        "frames_analysed": int(len(g)),
    }
    errors = [] if payload["native_pixels"] else ["frames were scaled before analysis: the block grid is not preserved"]
    t = np.asarray(times, dtype=np.float64)
    results = [{"t_start_s": float(t[0]), "t_end_s": float(t[-1]), "label": label, "value": payload["blockiness_score"],
                "confidence": 0.7 if payload["native_pixels"] else 0.3,
                "evidence": f"{per}px boundary/interior difference ratio x={rh:.3f} (phase {ph}) y={rv:.3f} (phase {pv}); "
                            f"ringing {payload['ringing_ratio']}"}]
    return {"status": "ok" if not errors else "partial", "results": results, "payload": payload, "errors": errors}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
