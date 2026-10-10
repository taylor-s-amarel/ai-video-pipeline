"""Detect Ken Burns moves (slow pan/zoom over a still): direction, zoom rate, start and end crops.

Method (per shot, grey frames at 10 fps):

1. Similarity motion between frames i and i + ``stride`` (a chain of non-overlapping steps, so slow
   moves accumulate measurable displacement): block phase correlation, then a least-squares
   pan + zoom fit about the frame centre. Each step's residual after warping by the fit is measured.
2. The steps are composed into a cumulative transform from the shot's first frame:
   scale S = product of step scales; translation T <- s * T + t.
3. A shot is a Ken Burns move when the picture is rigid (median rigid-block share >= ``min_rigid``
   and residual <= ``max_residual`` grey levels), it actually moves (|ln S| >= ``min_zoom`` or
   |T| >= ``min_pan`` frame widths) and it moves slowly (zoom rate <= ``max_zoom_rate`` per second,
   pan <= ``max_pan_rate`` frame widths per second).
4. Reported: relative zoom (zoom_from 1.0 at the first frame, zoom_to S), zoom rate (ln/s), content
   motion and the camera direction (the opposite), the end view as a crop of the start frame
   ([x, y, w, h] as ratios of the start frame; values outside 0-1 mean the end view shows more than
   the start frame did, as in a zoom out), and how linear the zoom/pan progress is (R^2).

Limits: absolute crop of the original still is unknown (only the start-relative move is measurable);
a camera pan over a flat or distant real scene also qualifies; rotation is fitted but not reported.
"""

from __future__ import annotations

import math

import numpy as np

import vre_detect_kit as kit

DETECTOR = "video_re_detect_ken_burns"
VERSION = "1.0.0"
DEFAULTS = {
    "stride": 3,
    "block": 32,
    "step": 16,
    "min_rigid": 0.7,
    "max_residual": 4.0,
    "min_zoom": 0.02,
    "min_pan": 0.03,
    "max_zoom_rate": 0.3,
    "max_pan_rate": 0.35,
    "cut_threshold": 0.3,
}
PARAM_DOCS = {
    "stride": "frames between the two images of each motion step",
    "block": "block size for phase correlation (analysed px)",
    "step": "block grid step",
    "min_rigid": "median share of textured blocks that must follow the fit",
    "max_residual": "largest median grey-level residual after compensation",
    "min_zoom": "smallest |ln total zoom| that counts as a zoom",
    "min_pan": "smallest total pan (frame widths) that counts as a pan",
    "max_zoom_rate": "largest |ln zoom| per second for a slow (Ken Burns) move",
    "max_pan_rate": "largest pan speed in frame widths per second",
    "cut_threshold": "cut score for the built-in shot splitter",
}


def r2_linear(t: np.ndarray, y: np.ndarray) -> float | None:
    if len(t) < 3 or float(np.ptp(y)) < 1e-9:
        return None
    coef = np.polyfit(t, y, 1)
    res = y - np.polyval(coef, t)
    return float(1 - (res ** 2).sum() / ((y - y.mean()) ** 2).sum())


def shot_move(gray: np.ndarray, fps: float, p: dict) -> dict | None:
    n, H, W = gray.shape
    st = max(1, int(p["stride"]))
    if n <= st:
        return None
    c = ((W - 1) / 2.0, (H - 1) / 2.0)
    S, T = 1.0, np.zeros(2)
    ts, logs, txs, tys, shares, resids = [0.0], [0.0], [0.0], [0.0], [], []
    for i in range(0, n - st, st):
        a, b = gray[i], gray[i + st]
        bm = kit.block_motion(a, b, p["block"], p["step"])
        textured = bm["texture"] >= 4.0
        ok = kit.reliable_blocks(bm) & textured
        fit = kit.fit_similarity(bm["centres"][ok], bm["vectors"][ok], center=c) if ok.sum() >= 4 else None
        if fit is None:
            return {"rigid": False, "reason": "no reliable motion fit"}
        err = np.hypot(*(kit._sim_predict(fit, bm["centres"], c) - bm["vectors"]).T)
        shares.append(float(((err <= 0.5 * st) & ok).sum() / max(1, textured.sum())))
        resids.append(kit.compensated_residual(a, b, fit))
        S *= fit["scale"]
        T = fit["scale"] * T + np.array([fit["tx"], fit["ty"]])
        ts.append((i + st) / fps)
        logs.append(math.log(S))
        txs.append(T[0])
        tys.append(T[1])
    dur = ts[-1]
    rigid = float(np.median(shares)) >= p["min_rigid"] and float(np.median(resids)) <= p["max_residual"]
    lnS = math.log(S)
    pan_fw = [T[0] / W, T[1] / H]
    out = {"rigid": rigid, "rigid_share": float(np.median(shares)), "residual": float(np.median(resids)),
           "duration_s": dur, "zoom_to": S, "zoom_rate_per_s": lnS / dur if dur else 0.0,
           "pan_fw": pan_fw, "pan_fw_per_s": [v / dur for v in pan_fw] if dur else [0.0, 0.0]}
    t = np.asarray(ts)
    q = np.asarray(logs) if abs(lnS) >= p["min_zoom"] else np.hypot(np.asarray(txs) / W, np.asarray(tys) / H)
    out["progress_r2"] = r2_linear(t, q)
    # end view expressed in start-frame coordinates (inverse of the cumulative transform)
    x0 = c[0] + (0 - c[0] - T[0]) / S
    y0 = c[1] + (0 - c[1] - T[1]) / S
    out["end_crop"] = [x0 / W, y0 / H, 1.0 / S, 1.0 / S]
    return out


def direction_words(zoom_to: float, pan_fw: list[float], p: dict) -> tuple[str, str]:
    zoom = "in" if math.log(zoom_to) >= p["min_zoom"] else ("out" if math.log(zoom_to) <= -p["min_zoom"] else "none")
    vx, vy = pan_fw
    if math.hypot(vx, vy) < p["min_pan"]:
        return zoom, "none"
    # content moving left means the virtual camera moves right
    if abs(vx) >= abs(vy):
        cam = "right" if vx < 0 else "left"
    else:
        cam = "down" if vy < 0 else "up"
    return zoom, cam


def analyse(frames, fps, p, ctx):
    gray = kit.as_gray(np.asarray(frames))
    N = len(gray)
    t0 = ctx["t0"]
    cuts = None if ctx.get("shots") else kit.detect_cuts(gray, fps, abs_thr=p["cut_threshold"])
    ranges = kit.shot_ranges(N, fps, t0, cuts, ctx.get("shots"))
    moves, results, checked = [], [], 0
    for k, (a, b) in enumerate(ranges):
        if b - a <= p["stride"] + 1:
            continue
        mv = shot_move(gray[a:b], fps, p)
        checked += 1
        if not mv or not mv["rigid"]:
            continue
        zoom, cam = direction_words(mv["zoom_to"], mv["pan_fw"], p)
        if zoom == "none" and cam == "none":
            continue
        pan_rate = math.hypot(*mv["pan_fw_per_s"])
        if abs(mv["zoom_rate_per_s"]) > p["max_zoom_rate"] or pan_rate > p["max_pan_rate"]:
            continue
        rec = {"shot_index": k, "t_start_s": t0 + a / fps, "t_end_s": t0 + b / fps,
               "zoom_from": 1.0, "zoom_to": mv["zoom_to"], "zoom_direction": zoom,
               "zoom_rate_per_s": mv["zoom_rate_per_s"], "camera_pan": cam,
               "content_motion_fw_per_s": mv["pan_fw_per_s"], "start_crop": [0.0, 0.0, 1.0, 1.0],
               "end_crop": mv["end_crop"], "progress_r2": mv["progress_r2"], "rigid_share": mv["rigid_share"],
               "residual": mv["residual"]}
        moves.append(rec)
        results.append(kit.result("ken_burns", min(0.95, mv["rigid_share"]), t_start_s=rec["t_start_s"],
                                  t_end_s=rec["t_end_s"], value={"zoom": zoom, "pan": cam},
                                  evidence=f"rigid pan/zoom to {mv['zoom_to']:.3f}x, camera {cam}; "
                                           f"residual {mv['residual']:.2f} grey levels"))
    payload = {"moves": moves, "shots_checked": checked,
               "share_of_shots": len(moves) / checked if checked else None}
    return {"status": "ok" if checked else "partial", "results": results, "payload": payload,
            "errors": [] if checked else ["no shot long enough to measure"]}


DET = kit.Detector(DETECTOR, VERSION, DEFAULTS, analyse, long_side=320, fps=10.0, pix_fmt="gray",
                   description="Detect slow pan/zoom moves on stills (Ken Burns): zoom rate, direction, crops.")


def detect(frames, fps, **kw):
    """Envelope for frames (N, H, W[, 3]) uint8 at ``fps``."""
    return DET.detect(frames, fps, **kw)


def detect_file(path, **kw):
    return DET.detect_file(path, **kw)


def main(argv=None):
    return DET.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
