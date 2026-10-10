"""Detect looping footage: repeat period, whether the loop point is seamless, and whether the video's
end flows back into its start (autoplay loops).

Method (grey frames at 12 fps, long side 160):

1. Each frame becomes a 32 x 18 grey thumbnail (``region`` = ``border`` blanks the central
   ``center_frac`` box so subjects and captions do not mask a looping background).
2. Period: for every lag L >= ``min_period_s`` the median thumbnail distance between frames i and
   i + L is divided by the typical distance between frames that far apart; the smallest lag whose
   score is <= ``max_score`` (and within 25% of the best) is the period. The sequence must hold
   at least 1.5 periods. Searched over the whole input and, when there are cuts, per shot.
3. Seam: consecutive-frame distances are folded by phase (frame index mod period). A loop point
   that jumps shows up as one phase with a much larger distance than the median; its ratio to
   the median is ``seam_ratio`` and the loop is seamless when it is <= ``seam_tol``.
4. End to start: distance between the last and first frame divided by the median consecutive
   distance (<= ``seam_tol`` means the clip can autoplay-loop without a visible jump).

Limits: loops that differ slightly on every pass (re-encoded, with overlays changing) score
worse; periods shorter than ``min_period_s`` or longer than two thirds of the input are not
searched; a static picture repeats trivially and is reported as static, not as a loop.
"""

from __future__ import annotations

import numpy as np

import vre_detect_kit as kit

DETECTOR = "video_re_detect_loop_seam"
VERSION = "1.0.0"
DEFAULTS = {
    "region": "full",
    "center_frac": 0.6,
    "min_period_s": 0.5,
    "max_score": 0.15,
    "seam_tol": 2.0,
    "static_diff": 0.5,
    "cut_threshold": 0.3,
}
PARAM_DOCS = {
    "region": "full = whole frame; border = ignore the central box (subjects, captions)",
    "center_frac": "width/height share of the central box ignored with region=border",
    "min_period_s": "shortest loop period searched",
    "max_score": "repeat score (0 = identical) at or below which the input loops",
    "seam_tol": "jump at the loop point / median frame-to-frame change that still counts as seamless",
    "static_diff": "median thumbnail change (grey levels) under which the input is static",
    "cut_threshold": "cut score for the built-in shot splitter",
}


def thumbs(gray: np.ndarray, p: dict) -> np.ndarray:
    s = kit.frame_signatures(gray, 32, 18).reshape(len(gray), 18, 32)
    if p["region"] == "border":
        cy, cx = int(18 * p["center_frac"] / 2), int(32 * p["center_frac"] / 2)
        s[:, 9 - cy:9 + cy, 16 - cx:16 + cx] = 0.0
    return s.reshape(len(gray), -1)


def loop_in(sig: np.ndarray, fps: float, p: dict) -> dict | None:
    cd = np.abs(np.diff(sig, axis=0)).mean(axis=1)
    if len(cd) == 0 or float(np.median(cd)) < p["static_diff"]:
        return None
    per = kit.find_period(sig, fps, p["min_period_s"], p["max_score"])
    if per is None:
        return None
    P = per["period_frames"]
    phase = np.array([cd[k::P].mean() for k in range(P)])
    med = float(np.median(cd)) + 1e-6
    k = int(np.argmax(phase))
    ratio = float(phase[k] / med)
    seamless = ratio <= p["seam_tol"]
    seams = [] if seamless else [(k + 1 + j * P) / fps for j in range(len(sig)) if k + 1 + j * P < len(sig)]
    return {"period_s": P / fps, "repetitions": len(sig) / P, "similarity_score": per["score"],
            "seamless": bool(seamless), "seam_ratio": ratio, "seam_times_s": seams}


def analyse(frames, fps, p, ctx):
    gray = kit.as_gray(np.asarray(frames))
    N = len(gray)
    t0 = ctx["t0"]
    if p["region"] not in {"full", "border"}:
        return {"status": "error", "results": [], "payload": None, "errors": ["region must be full or border"]}
    sig = thumbs(gray, p)
    loops = []
    whole = loop_in(sig, fps, p)
    if whole:
        loops.append({"scope": "whole", "shot_index": None, "t_start_s": t0, "t_end_s": t0 + N / fps, **whole})
    cuts = None if ctx.get("shots") else kit.detect_cuts(gray, fps, abs_thr=p["cut_threshold"])
    ranges = kit.shot_ranges(N, fps, t0, cuts, ctx.get("shots"))
    if len(ranges) > 1:
        for k, (a, b) in enumerate(ranges):
            lp = loop_in(sig[a:b], fps, p) if b - a >= 4 else None
            if lp:
                loops.append({"scope": "shot", "shot_index": k, "t_start_s": t0 + a / fps, "t_end_s": t0 + b / fps,
                              **lp, "seam_times_s": [t0 + a / fps + s for s in lp["seam_times_s"]]})
    for lp in loops:
        if lp["scope"] == "whole":
            lp["seam_times_s"] = [t0 + s for s in lp["seam_times_s"]]
    cd = np.abs(np.diff(sig, axis=0)).mean(axis=1)
    end_ratio = float(np.abs(sig[-1] - sig[0]).mean() / (float(np.median(cd)) + 1e-6)) if N > 2 else None
    static = bool(N > 1 and float(np.median(cd)) < p["static_diff"])
    payload = {"region": p["region"], "static": static, "loops": loops,
               "end_to_start": {"ratio": end_ratio,
                                "seamless": bool(end_ratio is not None and not static and end_ratio <= p["seam_tol"])}}
    results = [kit.result("loop" if lp["seamless"] else "loop_with_seam", max(0.3, 1 - lp["similarity_score"] * 3),
                          t_start_s=lp["t_start_s"], t_end_s=lp["t_end_s"], value=round(lp["period_s"], 3),
                          evidence=f"repeats every {lp['period_s']:.2f} s ({lp['repetitions']:.1f}x), "
                                   f"loop-point jump {lp['seam_ratio']:.1f}x the usual frame change")
               for lp in loops]
    if payload["end_to_start"]["seamless"]:
        results.append(kit.result("end_loops_to_start", 0.7, t_start_s=t0, t_end_s=t0 + N / fps,
                                  evidence=f"last-to-first frame change {end_ratio:.1f}x the usual frame change"))
    return {"status": "ok", "results": results, "payload": payload, "errors": []}


DET = kit.Detector(DETECTOR, VERSION, DEFAULTS, analyse, long_side=160, fps=12.0, pix_fmt="gray",
                   description="Detect looping footage, its period, seam quality and end-to-start continuity.")


def detect(frames, fps, **kw):
    """Envelope for frames (N, H, W[, 3]) uint8 at ``fps``."""
    return DET.detect(frames, fps, **kw)


def detect_file(path, **kw):
    return DET.detect_file(path, **kw)


def main(argv=None):
    return DET.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
