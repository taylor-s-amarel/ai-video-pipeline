"""Estimate global camera motion per shot: pan, tilt and zoom (including Ken Burns moves on stills).

Usage:
    python video_re_camera_motion.py video.mp4 [--shots shots.json] [--stride 0.2] [--out camera.json]

Method: frames are decoded grey at 192 px wide and sampled every ``stride_s``/2 (default 0.1 s).
Inside each shot, frames ``stride_s`` apart (default 0.2 s; half that when the longer pair fails)
are compared block by block: every textured 64x64 block (step 32) is phase-correlated (Hann
window, normalised cross-power spectrum, parabolic sub-pixel peak). The block displacements are
fitted with a RANSAC-seeded least-squares model d = t + k x p (translation t, zoom k about the
frame centre): the motion most blocks agree with most closely (MSAC, 0.75 px) wins, and blocks that disagree - static titles, captions, logos, panel edges, moving subjects - are
dropped as outliers, so overlays do not pin the estimate to zero. Frames with too few textured
blocks fall back to a whole-frame estimate (phase correlation plus a scale search). Off-centre zooms
show up as zoom plus a small pan.

Conventions (per second, robust median over the shot's pairs):

* pan_x: frame widths per second, positive = camera moves right (content travels left)
* pan_y: frame heights per second, positive = camera moves down (content travels up)
* zoom: natural log of the scale change per second, positive = zoom in (content grows);
  0.0953 per second means 10% bigger every second
* jitter: mean absolute deviation of per-pair translation rate from the shot median (frame widths
  per second); high values mean handheld shake or noisy estimates
* label: static / pan-left / pan-right / tilt-up / tilt-down / zoom-in / zoom-out (joined with '+'),
  using |rate| >= 0.02 as the threshold

Pairs on flat frames (grey std < 2), with fewer than 40% inlier blocks or a correlation peak under
``min_peak`` (default 0.08) are skipped; a shot with no reliable pair gets nulls. ``mean_inliers``
is the share of textured blocks that agreed with the fitted motion. Block matching covers shifts up
to a quarter block (16 px at 192 px wide) per pair: about 0.4 frame widths per second at the
default stride, 0.8 with the short pair; faster whip pans read as unknown or wrong. Rotation, parallax and independently moving
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


def phase_correlate_batch(a: np.ndarray, b: np.ndarray, win: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """phase_correlate for stacks of equally sized patches (n, h, w), in one FFT call per stack."""
    n, h, w = a.shape
    fa = np.fft.rfft2((a - a.mean(axis=(1, 2), keepdims=True)) * win, axes=(1, 2))
    fb = np.fft.rfft2((b - b.mean(axis=(1, 2), keepdims=True)) * win, axes=(1, 2))
    r = np.conj(fa) * fb
    r /= np.abs(r) + 1e-9
    corr = np.fft.irfft2(r, s=(h, w), axes=(1, 2))
    flat = corr.reshape(n, -1).argmax(axis=1)
    py, px = np.unravel_index(flat, (h, w))
    idx = np.arange(n)
    c0 = corr[idx, py, px]

    def refine(cm, cp):
        den = cm - 2 * c0 + cp
        return np.where(np.abs(den) < 1e-12, 0.0, 0.5 * (cm - cp) / np.where(np.abs(den) < 1e-12, 1.0, den))

    sx = refine(corr[idx, py, (px - 1) % w], corr[idx, py, (px + 1) % w])
    sy = refine(corr[idx, (py - 1) % h, px], corr[idx, (py + 1) % h, px])
    dx = px + sx
    dy = py + sy
    dx = np.where(dx > w / 2, dx - w, dx)
    dy = np.where(dy > h / 2, dy - h, dy)
    return dx, dy, c0


def block_vectors(a: np.ndarray, b: np.ndarray, block: int = 64, step: int = 32, min_std: float = 4.0,
                  min_peak: float = 0.1) -> np.ndarray:
    """Phase-correlation displacement of every textured block: rows (x_off, y_off, dx, dy, peak) with
    x_off/y_off the block centre relative to the frame centre."""
    h, w = a.shape
    block = min(block, h, w) // 2 * 2
    win = np.outer(np.hanning(block), np.hanning(block))
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    pos, pa, pb = [], [], []
    for y in list(range(0, h - block + 1, step)) or [0]:
        for x in list(range(0, w - block + 1, step)) or [0]:
            ba = a[y:y + block, x:x + block]
            bb = b[y:y + block, x:x + block]
            if ba.std() < min_std or bb.std() < min_std:
                continue
            pos.append((x + block / 2 - cx, y + block / 2 - cy))
            pa.append(ba)
            pb.append(bb)
    if not pos:
        return np.zeros((0, 5))
    dx, dy, peak = phase_correlate_batch(np.asarray(pa, dtype=np.float64), np.asarray(pb, dtype=np.float64), win)
    pos_a = np.asarray(pos)
    ok = (peak >= min_peak) & (np.abs(dx) <= block / 4) & (np.abs(dy) <= block / 4)
    return np.column_stack([pos_a[ok, 0], pos_a[ok, 1], dx[ok], dy[ok], peak[ok]])


def _solve(px, py, dx, dy, w):
    n = len(px)
    A = np.zeros((2 * n, 3))
    A[:n, 0], A[:n, 2] = 1.0, px
    A[n:, 1], A[n:, 2] = 1.0, py
    ww = np.r_[w, w]
    sol, *_ = np.linalg.lstsq(A * ww[:, None], np.r_[dx, dy] * ww, rcond=None)
    return sol


def fit_motion(vecs: np.ndarray, tol: float = 0.75, max_hypotheses: int = 1500, seed: int = 0) -> dict | None:
    """Robust fit of d = t + k * p (translation t, zoom k = scale - 1 about the centre) to block vectors.

    RANSAC over pairs of blocks (each pair fixes t and k exactly), scored MSAC-style (each block
    within ``tol`` px adds peak x (1 - (residual/tol)^2)); the best hypothesis seeds a weighted
    least-squares fit, refined twice on its inliers. Blocks that disagree - static titles, captions, logos, panel edges, moving subjects -
    end up as outliers."""
    if len(vecs) < 4:
        return None
    px, py, dx, dy, wgt = vecs.T
    n = len(vecs)
    ii, jj = np.triu_indices(n, 1)
    if len(ii) > max_hypotheses:
        pick = np.random.default_rng(seed).choice(len(ii), max_hypotheses, replace=False)
        ii, jj = ii[pick], jj[pick]
    # minimal solution from two blocks: k from their relative displacement, t from their mean
    qx, qy = px[ii] - px[jj], py[ii] - py[jj]
    den = qx * qx + qy * qy
    ok = den > 1e-9
    ii, jj, qx, qy, den = ii[ok], jj[ok], qx[ok], qy[ok], den[ok]
    k = ((dx[ii] - dx[jj]) * qx + (dy[ii] - dy[jj]) * qy) / den
    tx = 0.5 * (dx[ii] + dx[jj] - k * (px[ii] + px[jj]))
    ty = 0.5 * (dy[ii] + dy[jj] - k * (py[ii] + py[jj]))
    res = np.hypot(dx[None, :] - (tx[:, None] + k[:, None] * px[None, :]),
                   dy[None, :] - (ty[:, None] + k[:, None] * py[None, :]))
    # MSAC score: closer agreement counts more, so a compromise between two motions loses
    support = (np.clip(1.0 - (res / tol) ** 2, 0.0, None) * wgt[None, :]).sum(axis=1)
    best_keep = res[int(np.argmax(support))] <= tol if len(support) else None
    keep = best_keep
    sol = None
    for _ in range(3):
        if keep is None or keep.sum() < 3:
            return None
        sol = _solve(px[keep], py[keep], dx[keep], dy[keep], wgt[keep])
        res = np.hypot(dx - (sol[0] + sol[2] * px), dy - (sol[1] + sol[2] * py))
        keep = res <= tol
    if keep.sum() < 3:
        return None
    return {"dx": float(sol[0]), "dy": float(sol[1]), "log_s": float(np.log1p(sol[2])),
            "inliers": float(keep.mean()), "blocks": int(n), "rms": float(np.sqrt(np.mean(res[keep] ** 2))),
            "peak": float(np.mean(wgt[keep]))}


def estimate_pair(a: np.ndarray, b: np.ndarray, global_est: "PairEstimator", min_inliers: float = 0.4) -> dict | None:
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    fit = fit_motion(block_vectors(a, b))
    if fit is not None and fit["inliers"] >= min_inliers:
        fit["method"] = "blocks"
        return fit
    if fit is None:  # too few textured blocks (small or plain frames): whole-frame estimate
        r = global_est.estimate(a, b)
        r["method"] = "global"
        return r
    return None


def analyse(video: str, shots: list[dict], width: int = 192, stride_s: float = 0.2, max_fps: float = 30.0,
            min_peak: float = 0.08, info: dict | None = None) -> dict:
    info = info or media_info(video)
    src_fps = info.get("fps") or 25.0
    fps = min(src_fps, max_fps)
    half = max(1, int(round(stride_s * fps / 2)))
    bounds = sorted((float(s["start_s"]), float(s["end_s"]), s["index"]) for s in shots)

    def shot_of(t):
        for a, b, i in bounds:
            if a - 1e-6 <= t < b - 1e-6:
                return i
        return None

    est, recent, pairs = None, [], []
    sample = -1
    for i, (t, f) in enumerate(iter_frames(video, width=width, pix_fmt="gray",
                                          fps=fps if src_fps > max_fps else None, info=info)):
        if i % half:
            continue
        sample += 1
        if est is None:
            est = PairEstimator(*f.shape)
        recent = (recent + [(t, f, shot_of(t))])[-3:]
        if len(recent) < 2 or (len(recent) == 3 and sample % 2 and recent[0][2] == recent[2][2]):
            continue  # one long pair per stride; odd samples only matter when a cut broke the long pair
        cands = [recent[0], recent[1]] if len(recent) == 3 else [recent[0]]
        t1, f1, s1 = recent[-1]
        for t0, f0, s0 in cands:  # long pair first (better zoom precision), short pair if it fails
            if s0 is None or s0 != s1 or f0.std() < 2 or f1.std() < 2:
                continue
            r = estimate_pair(f0, f1, est)
            if r is not None and r.get("peak", 0) >= min_peak:
                r.update({"t0": t0, "t1": t1, "shot": s1})
                pairs.append(r)
                break
    h, w = (est.h, est.w) if est else (1, 1)
    per_shot = []
    for s in shots:
        sel = [p for p in pairs if p["shot"] == s["index"]]
        if not sel:
            per_shot.append({"index": s["index"], "pan_x": None, "pan_y": None, "zoom": None, "jitter": None,
                             "label": "unknown", "pairs": 0})
            continue
        dt = np.array([p["t1"] - p["t0"] for p in sel])
        dxs = np.array([p["dx"] for p in sel]) / dt
        dys = np.array([p["dy"] for p in sel]) / dt
        pan_x = float(np.median(-dxs / w))
        pan_y = float(np.median(-dys / h))
        zoom = float(np.median(np.array([p["log_s"] for p in sel]) / dt))
        jitter = float(np.mean(np.hypot(dxs - np.median(dxs), dys - np.median(dys))) / w)
        inl = [p["inliers"] for p in sel if "inliers" in p]
        per_shot.append({"index": s["index"], "pan_x": pan_x, "pan_y": pan_y, "zoom": zoom, "jitter": jitter,
                         "label": label_for(pan_x, pan_y, zoom), "pairs": len(sel),
                         "mean_inliers": float(np.mean(inl)) if inl else None,
                         "mean_peak": float(np.mean([p["peak"] for p in sel]))})
    path = [{"t_s": p["t0"], "pan_x": -p["dx"] / w / (p["t1"] - p["t0"]), "pan_y": -p["dy"] / h / (p["t1"] - p["t0"]),
             "zoom": p["log_s"] / (p["t1"] - p["t0"]), "peak": p["peak"], "method": p["method"]} for p in pairs]
    return {"shots": per_shot, "path": path,
            "params": {"width": width, "stride_s": 2 * half / fps, "fps": fps, "min_peak": min_peak}}


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
