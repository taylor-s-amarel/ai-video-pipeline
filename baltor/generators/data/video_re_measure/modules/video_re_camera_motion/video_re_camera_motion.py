"""Estimate global camera motion per shot: pan, tilt and zoom (including Ken Burns moves on stills).

Usage:
    python video_re_camera_motion.py video.mp4 [--shots shots.json] [--stride 0.2] [--out camera.json]

Method: frames are decoded grey at 128 px wide. Inside each shot, frames ``stride_s`` apart (default
0.2 s) are compared. For each pair (A earlier, B later) a scale search runs over
s = exp(-0.08 .. +0.08) (coarse, then fine, then a parabola through the best three): B is resampled
about the frame centre by s and phase-correlated with A (Hann window, normalised cross-power
spectrum) over the central 80% of the frame. The scale with the highest correlation peak is the zoom,
and that peak's position is the translation. Off-centre zooms show up as zoom plus a small pan.

Conventions (per second, robust median over the shot's pairs):

* pan_x: frame widths per second, positive = camera moves right (content travels left)
* pan_y: frame heights per second, positive = camera moves down (content travels up)
* zoom: natural log of the scale change per second, positive = zoom in (content grows);
  0.0953 per second means 10% bigger every second
* jitter: mean absolute deviation of per-pair translation from the shot median (frame widths per
  pair); high values mean handheld shake or noisy estimates
* label: static / pan-left / pan-right / tilt-up / tilt-down / zoom-in / zoom-out (joined with '+'),
  using |rate| >= 0.02 as the threshold

Pairs on flat frames (grey std < 2) or with a correlation peak under ``min_peak`` (default 0.08) are
skipped; a shot with no reliable pair gets nulls. Rotation, parallax and independently moving
subjects are not modelled: a large moving subject can be reported as camera motion.
"""

from __future__ import annotations

import argparse

import numpy as np

from video_re_common import (ToolMissing, clean, dump_json, import_sibling, iter_frames, load_json, media_info,
                             shots_from_json, unavailable, whole_clip_shot)

IDENTITY = "video_re_camera_motion"
VERSION = "1.0.0"
LABEL_THRESHOLD = 0.02


def phase_correlate(a: np.ndarray, b: np.ndarray, win: np.ndarray | None = None,
                    fa: np.ndarray | None = None) -> tuple[float, float, float]:
    """Translation (dx, dy) of B's content relative to A's, in pixels, and the correlation peak (0..1).
    B(x) ~ A(x - d): positive dx means content moved right."""
    h, w = a.shape
    if win is None:
        win = np.outer(np.hanning(h), np.hanning(w))
    if fa is None:
        fa = np.fft.fft2((a - a.mean()) * win)
    fb = np.fft.fft2((b - b.mean()) * win)
    r = np.conj(fa) * fb
    r /= np.abs(r) + 1e-9
    corr = np.fft.ifft2(r).real
    py, px = np.unravel_index(int(np.argmax(corr)), corr.shape)
    peak = float(corr[py, px])

    def refine(c_m, c_0, c_p):
        den = c_m - 2 * c_0 + c_p
        return 0.0 if abs(den) < 1e-12 else 0.5 * (c_m - c_p) / den

    sx = refine(corr[py, (px - 1) % w], corr[py, px], corr[py, (px + 1) % w])
    sy = refine(corr[(py - 1) % h, px], corr[py, px], corr[(py + 1) % h, px])
    dx = px + sx
    dy = py + sy
    if dx > w / 2:
        dx -= w
    if dy > h / 2:
        dy -= h
    return float(dx), float(dy), peak


def sample_bilinear(img: np.ndarray, ys: np.ndarray, xs: np.ndarray) -> np.ndarray:
    h, w = img.shape
    xs = np.clip(xs, 0, w - 1.000001)
    ys = np.clip(ys, 0, h - 1.000001)
    x0, y0 = np.floor(xs).astype(int), np.floor(ys).astype(int)
    fx, fy = xs - x0, ys - y0
    a = img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx
    b = img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


class PairEstimator:
    """Scale + translation between two grey frames of a fixed size."""

    def __init__(self, h: int, w: int, crop: float = 0.8, max_log: float = 0.08):
        self.h, self.w = h, w
        self.cy, self.cx = (h - 1) / 2.0, (w - 1) / 2.0
        ch, cw = int(h * crop) // 2 * 2, int(w * crop) // 2 * 2
        self.y0, self.x0 = (h - ch) // 2, (w - cw) // 2
        self.ch, self.cw = ch, cw
        yy, xx = np.mgrid[self.y0:self.y0 + ch, self.x0:self.x0 + cw].astype(np.float64)
        self.dy, self.dx = yy - self.cy, xx - self.cx
        self.win = np.outer(np.hanning(ch), np.hanning(cw))
        self.max_log = max_log

    def crop(self, img: np.ndarray) -> np.ndarray:
        return img[self.y0:self.y0 + self.ch, self.x0:self.x0 + self.cw]

    def warp(self, img: np.ndarray, log_s: float) -> np.ndarray:
        s = np.exp(log_s)  # sample B at c + (x - c) * s: undoes a zoom-in of s
        return sample_bilinear(img, self.cy + self.dy * s, self.cx + self.dx * s)

    def estimate(self, a: np.ndarray, b: np.ndarray) -> dict:
        a = a.astype(np.float64)
        b = b.astype(np.float64)
        ac = self.crop(a)
        fa = np.fft.fft2((ac - ac.mean()) * self.win)

        def score(ls):
            return phase_correlate(ac, self.warp(b, ls), self.win, fa)

        coarse = np.linspace(-self.max_log, self.max_log, 13)
        results = {float(ls): score(ls) for ls in coarse}
        best = max(results, key=lambda k: results[k][2])
        step = coarse[1] - coarse[0]
        for ls in np.linspace(best - step, best + step, 9):
            results.setdefault(float(ls), score(ls))
        keys = sorted(results)
        i = max(range(len(keys)), key=lambda j: results[keys[j]][2])
        log_s = keys[i]
        if 0 < i < len(keys) - 1:
            x = np.array(keys[i - 1:i + 2])
            y = np.array([results[k][2] for k in keys[i - 1:i + 2]])
            coef = np.polyfit(x, y, 2)
            if coef[0] < 0:
                log_s = float(np.clip(-coef[1] / (2 * coef[0]), x[0], x[2]))
        dx, dy, peak = score(log_s)
        return {"dx": dx, "dy": dy, "log_s": log_s, "peak": peak}


def label_for(pan_x, pan_y, zoom, thr: float = LABEL_THRESHOLD) -> str:
    if pan_x is None:
        return "unknown"
    parts = []
    if pan_x >= thr:
        parts.append("pan-right")
    elif pan_x <= -thr:
        parts.append("pan-left")
    if pan_y >= thr:
        parts.append("tilt-down")
    elif pan_y <= -thr:
        parts.append("tilt-up")
    if zoom >= thr:
        parts.append("zoom-in")
    elif zoom <= -thr:
        parts.append("zoom-out")
    return "+".join(parts) or "static"


def analyse(video: str, shots: list[dict], width: int = 128, stride_s: float = 0.2, max_fps: float = 30.0,
            min_peak: float = 0.08, info: dict | None = None) -> dict:
    info = info or media_info(video)
    src_fps = info.get("fps") or 25.0
    fps = min(src_fps, max_fps)
    stride = max(1, int(round(stride_s * fps)))
    est = None
    pairs = []
    anchor = None
    for i, (t, f) in enumerate(iter_frames(video, width=width, pix_fmt="gray",
                                          fps=fps if src_fps > max_fps else None, info=info)):
        if est is None:
            est = PairEstimator(*f.shape)
        if i % stride:
            continue
        if anchor is not None:
            ta, fa = anchor
            if fa.std() >= 2 and f.std() >= 2:
                r = est.estimate(fa, f)
                r.update({"t0": ta, "t1": t})
                pairs.append(r)
            else:
                pairs.append({"t0": ta, "t1": t, "peak": 0.0, "flat": True})
        anchor = (t, f)
    h, w = (est.h, est.w) if est else (1, 1)
    per_shot = []
    for s in shots:
        a, b = float(s["start_s"]), float(s["end_s"])
        sel = [p for p in pairs if p["t0"] >= a - 1e-6 and p["t1"] < b - 1e-6 and p.get("peak", 0) >= min_peak
               and not p.get("flat")]
        if not sel:
            per_shot.append({"index": s["index"], "pan_x": None, "pan_y": None, "zoom": None, "jitter": None,
                             "label": "unknown", "pairs": 0})
            continue
        dt = np.array([p["t1"] - p["t0"] for p in sel])
        dxs = np.array([p["dx"] for p in sel])
        dys = np.array([p["dy"] for p in sel])
        pan_x = float(np.median(-dxs / w / dt))
        pan_y = float(np.median(-dys / h / dt))
        zoom = float(np.median(np.array([p["log_s"] for p in sel]) / dt))
        jitter = float(np.mean(np.hypot(dxs - np.median(dxs), dys - np.median(dys))) / w)
        per_shot.append({"index": s["index"], "pan_x": pan_x, "pan_y": pan_y, "zoom": zoom, "jitter": jitter,
                         "label": label_for(pan_x, pan_y, zoom), "pairs": len(sel),
                         "mean_peak": float(np.mean([p["peak"] for p in sel]))})
    path = [{"t_s": p["t0"], "pan_x": -p["dx"] / w / (p["t1"] - p["t0"]), "pan_y": -p["dy"] / h / (p["t1"] - p["t0"]),
             "zoom": p["log_s"] / (p["t1"] - p["t0"]), "peak": p["peak"]} for p in pairs if not p.get("flat")]
    return {"shots": per_shot, "path": path,
            "params": {"width": width, "stride_s": stride / fps, "fps": fps, "min_peak": min_peak}}


def run(video: str, shots: list[dict] | None = None, **kw) -> dict:
    try:
        info = media_info(video)
        shots = shots or whole_clip_shot(info.get("duration_s") or 0.0)
        res = analyse(video, shots, info=info, **kw)
    except ToolMissing as exc:
        return unavailable(str(exc))
    except RuntimeError as exc:
        return {"status": "error", "reason": str(exc)}
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, **res}, nd=5)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--shots", help="detect_shots JSON; default: run video_re_detect_shots")
    ap.add_argument("--stride", type=float, default=0.2, help="seconds between compared frames")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if a.shots:
        shots = shots_from_json(load_json(a.shots))
    else:
        det = import_sibling("video_re_detect_shots").run(a.video)
        shots = det.get("shots") if det.get("status") == "ok" else None
    res = run(a.video, shots, stride_s=a.stride)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
