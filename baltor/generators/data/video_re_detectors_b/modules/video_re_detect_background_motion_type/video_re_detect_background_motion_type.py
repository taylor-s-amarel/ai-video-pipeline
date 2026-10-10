"""Classify each shot's background motion: static, still with pan/zoom, procedural, video (or video loop).

Method (per shot, consecutive analysed frames, up to ``max_pairs`` pairs):

1. Raw change: median mean-absolute grey difference between consecutive frames. Below
   ``static_diff`` levels the shot is ``static``.
2. Rigid fit: block phase correlation (``block`` px, step ``step``) and a similarity fit (pan +
   zoom + rotation). ``rigid_share`` = share of textured blocks whose vector the fit predicts
   within ``tol`` px/frame. After warping frame i by the fit, the residual difference to frame
   i+1 is measured. If the fit holds for most pairs (rigid share >= ``min_rigid_share``) and the
   residual is at most max(``resid_abs``, ``resid_rel`` x raw change), the whole picture moves as one
   flat image: ``still_pan_zoom`` (Ken Burns on a still, or a pure pan/zoom of a flat scene).
3. Otherwise the content changes non-rigidly. The shot's grey thumbnails are searched for a
   repeat period (lag >= ``min_loop_s``; see ``find_period`` in the kit). A middle frame's share of
   spatial power above 0.03 cycles/px and its palette concentration (share of pixels in the 8 most
   common 4-bit colours) separate rendered motion graphics (``procedural``: power share <
   ``hf_thr`` = smooth gradients, or concentration >= ``palette_thr`` = flat shapes) from camera
   footage (``video``); footage that repeats is ``video_loop``.

Limits: a camera panning over a distant or flat real scene is indistinguishable from a pan over a
still; the procedural/video split is a heuristic hint (confidence capped at 0.7); a shot whose
foreground subject dominates the frame is classified by that subject, not the background.
"""

from __future__ import annotations

import math

import numpy as np

import vre_detect_kit as kit

DETECTOR = "video_re_detect_background_motion_type"
VERSION = "1.0.0"
DEFAULTS = {
    "block": 32,
    "step": 16,
    "max_pairs": 24,
    "static_diff": 0.8,
    "tol": 0.5,
    "min_rigid_share": 0.75,
    "resid_abs": 3.0,
    "resid_rel": 0.35,
    "min_loop_s": 0.8,
    "loop_score": 0.15,
    "hf_thr": 0.02,
    "palette_thr": 0.6,
    "cut_threshold": 0.3,
}
PARAM_DOCS = {
    "block": "block size for motion vectors (analysed px)",
    "step": "grid step between blocks",
    "max_pairs": "consecutive frame pairs sampled per shot",
    "static_diff": "median frame difference (grey levels) under which a shot is static",
    "tol": "px/frame a block may deviate from the similarity fit and still count as rigid",
    "min_rigid_share": "share of textured blocks that must follow the fit for still_pan_zoom",
    "resid_abs": "largest compensated residual (grey levels) for still_pan_zoom",
    "resid_rel": "or this fraction of the raw frame difference, whichever is larger",
    "min_loop_s": "shortest loop period searched",
    "loop_score": "repeat score (0 = identical) at or below which the shot loops",
    "hf_thr": "share of spatial power above 0.03 cycles/px under which content looks rendered (smooth)",
    "palette_thr": "8-colour palette concentration at or above which content looks rendered",
    "cut_threshold": "cut score for the built-in shot splitter",
}


def classify_shot(rgb: np.ndarray, gray: np.ndarray, fps: float, p: dict) -> dict:
    n, H, W = gray.shape
    idx = list(range(n - 1))
    if len(idx) > p["max_pairs"]:
        idx = [idx[int(round(k))] for k in np.linspace(0, len(idx) - 1, p["max_pairs"])]
    raws, comps, shares, txs, tys, zooms = [], [], [], [], [], []
    fitted = 0
    c = ((W - 1) / 2.0, (H - 1) / 2.0)
    for i in idx:
        a, b = gray[i], gray[i + 1]
        raw = float(np.abs(b - a).mean())
        raws.append(raw)
        bm = kit.block_motion(a, b, p["block"], p["step"])
        textured = bm["texture"] >= 4.0
        ok = kit.reliable_blocks(bm) & textured
        fit = kit.fit_similarity(bm["centres"][ok], bm["vectors"][ok], center=c) if ok.sum() >= 4 else None
        if fit is None:
            shares.append(0.0)
            comps.append(raw)
            continue
        fitted += 1
        pred = kit._sim_predict(fit, bm["centres"], c)
        err = np.hypot(*(pred - bm["vectors"]).T)
        shares.append(float(((err <= p["tol"]) & ok).sum() / max(1, textured.sum())))
        comps.append(kit.compensated_residual(a, b, fit))
        txs.append(fit["tx"])
        tys.append(fit["ty"])
        zooms.append(math.log(max(fit["scale"], 1e-6)))
    raw_med = float(np.median(raws)) if raws else 0.0
    comp_med = float(np.median(comps)) if comps else raw_med
    share_med = float(np.median(shares)) if shares else 0.0
    pan = [float(np.median(txs)) / W * fps, float(np.median(tys)) / H * fps] if txs else None
    zoom = float(np.median(zooms)) * fps if zooms else None
    mid = rgb[n // 2]
    hf = kit.hf_energy_fraction(gray[n // 2])
    pal = kit.palette_concentration(mid)
    per = kit.find_period(kit.frame_signatures(gray), fps, p["min_loop_s"], p["loop_score"]) if n >= 4 else None
    rec = {"raw_frame_diff": raw_med, "residual_after_compensation": comp_med, "rigid_share": share_med,
           "pan_fw_per_s": pan, "zoom_per_s": zoom, "hf_energy_fraction": hf, "palette_concentration": pal,
           "loops": per is not None, "loop_period_s": per["period_frames"] / fps if per else None,
           "pairs_used": len(idx)}
    if raw_med < p["static_diff"]:
        rec.update(type="static", confidence=0.9)
    elif fitted >= 0.6 * len(idx) and share_med >= p["min_rigid_share"] and \
            comp_med <= max(p["resid_abs"], p["resid_rel"] * raw_med):
        rec.update(type="still_pan_zoom", confidence=min(0.95, share_med))
    else:
        smooth, flat = hf < p["hf_thr"], pal >= p["palette_thr"]
        if smooth or flat:
            rec.update(type="procedural", confidence=0.7 if (smooth and flat) else 0.6)
        else:
            rec.update(type="video_loop" if per else "video", confidence=0.6)
    return rec


def analyse(frames, fps, p, ctx):
    rgb = kit.as_rgb(np.asarray(frames))
    gray = kit.as_gray(rgb)
    N = len(gray)
    t0 = ctx["t0"]
    cuts = None if ctx.get("shots") else kit.detect_cuts(rgb, fps, abs_thr=p["cut_threshold"])
    ranges = kit.shot_ranges(N, fps, t0, cuts, ctx.get("shots"))
    shots, results, errors = [], [], []
    for k, (a, b) in enumerate(ranges):
        rec = {"shot_index": k, "t_start_s": t0 + a / fps, "t_end_s": t0 + b / fps}
        if b - a < 3:
            errors.append(f"shot {k}: fewer than 3 frames, not classified")
            rec.update(type="unknown", confidence=0.0, raw_frame_diff=None, residual_after_compensation=None,
                       rigid_share=None, pan_fw_per_s=None, zoom_per_s=None, hf_energy_fraction=None,
                       palette_concentration=None, loops=False, loop_period_s=None, pairs_used=0)
            shots.append(rec)
            continue
        rec.update(classify_shot(rgb[a:b], gray[a:b], fps, p))
        shots.append(rec)
        ev = (f"frame diff {rec['raw_frame_diff']:.2f}, after pan/zoom compensation "
              f"{rec['residual_after_compensation']:.2f}; rigid share {rec['rigid_share']:.2f}")
        if rec["loops"]:
            ev += f"; repeats every {rec['loop_period_s']:.2f} s"
        results.append(kit.result(rec["type"], rec["confidence"], t_start_s=rec["t_start_s"], t_end_s=rec["t_end_s"],
                                  value=rec["type"], evidence=ev))
    counts: dict[str, int] = {}
    for s in shots:
        counts[s["type"]] = counts.get(s["type"], 0) + 1
    payload = {"shots": shots, "type_counts": counts}
    status = "ok" if any(s["type"] != "unknown" for s in shots) else "partial"
    return {"status": status, "results": results, "payload": payload, "errors": errors}


DET = kit.Detector(DETECTOR, VERSION, DEFAULTS, analyse, long_side=320, fps=10.0, pix_fmt="rgb24",
                   description="Classify each shot's background: static, still with pan/zoom, procedural, video or video loop.")


def detect(frames, fps, **kw):
    """Envelope for frames (N, H, W[, 3]) uint8 at ``fps``."""
    return DET.detect(frames, fps, **kw)


def detect_file(path, **kw):
    return DET.detect_file(path, **kw)


def main(argv=None):
    return DET.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
