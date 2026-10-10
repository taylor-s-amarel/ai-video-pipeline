"""Detect shots in a video: hard cuts and gradual transitions (dissolves, fades).

Usage:
    python video_re_detect_shots.py video.mp4 [--method frames|scdet] [--min-shot 0.2] [--out shots.json]

Method 'frames' (default) decodes every frame at a small size (96 px wide) and scores each frame
against the previous one:

    score = 0.5 * colour-histogram distance (soft 16-bin Y, Cb, Cr histograms, mean L1/2, 0..1)
          + 0.5 * min(1, 2 * mean absolute grey difference / 255)

A frame starts a new shot (hard cut) when its score is a local maximum, is at least ``min_score``
and is at least ``adaptive_ratio`` times the median score of the surrounding ``window_s`` seconds,
and the previous shot is at least ``min_shot_s`` long. Cut times are frame-exact: the new shot
starts at frame_index / fps.

Gradual transitions are found with a long-range difference: frame t against frame t-k
(k = ``gradual_window_s``). A bump in that curve that is not explained by a hard cut, builds up over
several frames and lasts less than ``max_gradual_s`` + k is a dissolve or fade; its centre is the
boundary. Continuous camera motion produces a long plateau instead and is rejected.

Method 'scdet' runs ffmpeg's scdet filter instead (hard cuts only); useful as a cross-check.

Known limits: whip pans, strobe/flash frames and very fast motion can create false cuts; cuts between
two near-identical framings can be missed; gradual-transition boundaries are approximate (a few
frames) and marked ``type: gradual``.
"""

from __future__ import annotations

import argparse
import re

import numpy as np

from video_re_common import (ToolMissing, clean, dump_json, iter_frames, media_info, run as run_cmd,
                             tool_versions, unavailable)

IDENTITY = "video_re_detect_shots"
VERSION = "1.0.0"

DEFAULTS = {"width": 96, "min_score": 0.12, "adaptive_ratio": 3.0, "window_s": 0.5, "min_shot_s": 0.2,
            "gradual": True, "gradual_window_s": 0.5, "gradual_min": 0.3, "max_gradual_s": 2.0, "merge_s": 0.6}


def frame_features(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(48-value soft histogram: 16 bins each of Y, Cb, Cr, each summing to 1; grey image float32).

    Soft binning (each value split linearly between its two nearest bins) keeps the histogram
    distance continuous, so a dissolve changes it a little every frame instead of in jumps.
    """
    f = rgb.astype(np.float32)
    y = 0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2]
    cb = 128.0 - 0.168736 * f[..., 0] - 0.331264 * f[..., 1] + 0.5 * f[..., 2]
    cr = 128.0 + 0.5 * f[..., 0] - 0.418688 * f[..., 1] - 0.081312 * f[..., 2]
    hs = []
    for c in (y, cb, cr):
        pos = np.clip(c, 0, 255).ravel() * (15.0 / 255.0)
        lo = np.floor(pos).astype(np.int64)
        fr = pos - lo
        hi = np.minimum(lo + 1, 15)
        h = np.bincount(lo, weights=1.0 - fr, minlength=16) + np.bincount(hi, weights=fr, minlength=16)
        hs.append(h / max(1e-9, h.sum()))
    return np.concatenate(hs), y


def pair_score(h1: np.ndarray, g1: np.ndarray, h2: np.ndarray, g2: np.ndarray) -> float:
    hist_d = float(np.abs(h1 - h2).sum()) / 6.0
    pix_d = float(np.abs(g1 - g2).mean()) / 255.0
    return 0.5 * hist_d + 0.5 * min(1.0, 2.0 * pix_d)


def compute_features(video: str, width: int = 96, info: dict | None = None):
    info = info or media_info(video)
    hists, greys = [], []
    for _, f in iter_frames(video, width=width, pix_fmt="rgb24", info=info):
        h, g = frame_features(f)
        hists.append(h)
        greys.append(g)
    if not hists:
        raise RuntimeError("no frames decoded")
    return np.stack(hists), np.stack(greys), info


def score_series(hists: np.ndarray, greys: np.ndarray, lag: int = 1) -> np.ndarray:
    """score[t] = pair_score(frame t-lag, frame t); score[:lag] = 0."""
    n = len(hists)
    out = np.zeros(n)
    if n <= lag:
        return out
    hist_d = np.abs(hists[lag:] - hists[:-lag]).sum(axis=1) / 6.0  # mean over 3 channels of L1/2
    pix_d = np.abs(greys[lag:] - greys[:-lag]).mean(axis=(1, 2)) / 255.0
    out[lag:] = 0.5 * hist_d + 0.5 * np.minimum(1.0, 2.0 * pix_d)
    return out


def find_cuts(scores: np.ndarray, fps: float, min_score: float = 0.12, adaptive_ratio: float = 3.0,
              window_s: float = 0.5, min_shot_s: float = 0.2) -> list[tuple[int, float]]:
    """Frame indices that start a new shot after a hard cut, with their scores."""
    n = len(scores)
    w = max(2, int(round(window_s * fps)))
    min_gap = max(1, int(round(min_shot_s * fps)))
    cand = []
    for t in range(1, n):
        s = scores[t]
        if s < min_score:
            continue
        lo, hi = max(1, t - w), min(n, t + w + 1)
        neigh = np.concatenate([scores[lo:max(lo, t - 1)], scores[min(hi, t + 2):hi]])
        local = float(np.median(neigh)) if len(neigh) else 0.0
        if s < adaptive_ratio * local + 1e-9:
            continue
        if s < scores[max(1, t - 2):t + 3].max():
            continue  # not the local maximum
        cand.append((t, float(s)))
    cuts: list[tuple[int, float]] = []
    for t, s in sorted(cand, key=lambda c: -c[1]):  # strongest first, then enforce minimum shot length
        if t < min_gap:
            continue  # the first shot would be shorter than min_shot_s
        if all(abs(t - c) >= min_gap for c, _ in cuts):
            cuts.append((t, s))
    return sorted(cuts)


def find_gradual(hists: np.ndarray, greys: np.ndarray, scores: np.ndarray, cuts: list[int], fps: float,
                 gradual_window_s: float = 0.5, gradual_min: float = 0.3, max_gradual_s: float = 2.0,
                 cut_threshold: float = 0.12, min_shot_s: float = 0.2) -> list[tuple[int, float, int, int]]:
    """(centre frame, long-range score, start frame, end frame) of gradual transitions."""
    n = len(hists)
    k = max(3, int(round(gradual_window_s * fps)))
    if n <= 2 * k:
        return []
    d = score_series(hists, greys, lag=k)
    cut_arr = np.asarray(cuts, dtype=int)
    above = d >= gradual_min
    out = []
    t = k
    max_len = k + int(round(max_gradual_s * fps))
    while t < n:
        if not above[t]:
            t += 1
            continue
        s = t
        while t < n and above[t]:
            t += 1
        e = t  # region [s, e)
        if e - s > max_len:
            continue  # sustained change: camera motion, not a transition
        peak = s + int(np.argmax(d[s:e]))
        start, end = peak - k, peak
        if len(cut_arr) and np.any((cut_arr > start - 2) & (cut_arr <= end + 2)):
            continue  # explained by a hard cut
        window = scores[start + 1:end + 1]
        if window.max() >= max(cut_threshold, 0.6 * d[peak]):
            continue  # change happened in one frame
        if window.sum() < 0.5 * d[peak]:
            continue  # change did not accumulate frame by frame
        # the region where frame t differs from frame t-k is about (transition + k) long and centred
        # k/2 after the transition's centre
        centre = int(round((s + e - 1) / 2.0 - k / 2.0))
        out.append((centre, float(d[peak]), max(0, s - k), e - 1))
    min_gap = max(1, int(round(min_shot_s * fps)))
    kept: list[tuple[int, float, int, int]] = []
    for g in out:
        if all(abs(g[0] - c) >= min_gap for c in cuts) and all(abs(g[0] - x[0]) >= min_gap for x in kept):
            kept.append(g)
    return kept


def merge_transitional(bounds: list[dict], scores: np.ndarray, greys: np.ndarray, fps: float,
                       merge_s: float = 0.6) -> list[dict]:
    """Merge boundaries less than ``merge_s`` apart when every frame between them is transitional
    (still changing, or flat such as a black frame in a fade). A fade through black then reads as one
    gradual transition instead of two cuts around a 'shot' of black frames."""
    if not bounds:
        return []
    flat = greys.reshape(len(greys), -1).std(axis=1) < 4.0
    base = float(np.median(scores[1:])) if len(scores) > 1 else 0.0
    elevated = scores > max(0.03, 3.0 * base)
    out: list[dict] = []
    for b in sorted(bounds, key=lambda x: x["frame"]):
        if out and b["frame"] - out[-1]["frame"] <= merge_s * fps:
            a = out[-1]
            between = range(a["frame"] + 1, b["frame"])
            if all(elevated[i] or flat[i] for i in between):
                lo = min(a.get("span", [a["frame"]])[0], a["frame"] - 1)
                hi = max(b.get("span", [b["frame"], b["frame"]])[-1], b["frame"])
                out[-1] = {"frame": int(round((lo + hi) / 2.0)), "type": "gradual",
                           "score": max(a["score"] or 0, b["score"] or 0), "span": [lo, hi]}
                continue
        out.append(b)
    return out


def shots_from_boundaries(boundaries: list[dict], n_frames: int, fps: float) -> list[dict]:
    starts = [{"frame": 0, "type": "start", "score": None}] + sorted(boundaries, key=lambda b: b["frame"])
    shots = []
    for i, b in enumerate(starts):
        end_frame = starts[i + 1]["frame"] if i + 1 < len(starts) else n_frames
        shot = {"index": i, "start_s": b["frame"] / fps, "end_s": end_frame / fps,
                "duration_s": (end_frame - b["frame"]) / fps, "start_frame": b["frame"], "end_frame": end_frame,
                "transition_in": {"type": b["type"], "score": b.get("score")}}
        if b.get("span"):
            shot["transition_in"]["span_s"] = [b["span"][0] / fps, b["span"][1] / fps]
        shots.append(shot)
    return shots


def detect_frames(video: str, **params) -> dict:
    p = {**DEFAULTS, **{k: v for k, v in params.items() if v is not None}}
    hists, greys, info = compute_features(video, width=int(p["width"]))
    fps = info.get("fps") or 25.0
    scores = score_series(hists, greys)
    cuts = find_cuts(scores, fps, p["min_score"], p["adaptive_ratio"], p["window_s"], p["min_shot_s"])
    bounds = [{"frame": t, "type": "cut", "score": s} for t, s in cuts]
    if p["gradual"]:
        for centre, s, a, b in find_gradual(hists, greys, scores, [t for t, _ in cuts], fps, p["gradual_window_s"],
                                            p["gradual_min"], p["max_gradual_s"], p["min_score"], p["min_shot_s"]):
            bounds.append({"frame": centre, "type": "gradual", "score": s, "span": [a, b]})
    bounds = merge_transitional(bounds, scores, greys, fps, p["merge_s"])
    n = len(hists)
    shots = shots_from_boundaries(bounds, n, fps)
    return {"fps": fps, "frame_count": n, "duration_s": n / fps, "shots": shots,
            "transitions": [{"t_s": b["frame"] / fps, "frame": b["frame"], "type": b["type"], "score": b["score"]}
                            for b in sorted(bounds, key=lambda x: x["frame"])],
            "score_summary": {"median": float(np.median(scores[1:])) if n > 1 else None,
                              "p95": float(np.percentile(scores[1:], 95)) if n > 1 else None,
                              "max": float(scores.max()) if n else None},
            "params": p}


SCDET_TIME = re.compile(r"lavfi\.scd\.time=([0-9.]+)")
SCDET_SCORE = re.compile(r"lavfi\.scd\.score=([0-9.]+)")


def detect_scdet(video: str, threshold: float = 10.0, min_shot_s: float = 0.2) -> dict:
    info = media_info(video)
    fps = info.get("fps") or 25.0
    proc = run_cmd(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", video, "-map", "0:v:0",
                    "-vf", f"scdet=threshold={threshold}:sc_pass=1,metadata=print:file=-", "-f", "null", "-"],
                   timeout=1800)
    text = proc.stdout.decode("utf-8", "replace")
    times = [float(x) for x in SCDET_TIME.findall(text)]
    scores = [float(x) for x in SCDET_SCORE.findall(text)]
    duration = info.get("duration_s") or 0.0
    n = int(round(duration * fps))
    bounds, last = [], -1e9
    for t, s in zip(times, scores):
        frame = int(round(t * fps))
        if frame - last >= max(1, round(min_shot_s * fps)) and frame > 0:
            bounds.append({"frame": frame, "type": "cut", "score": s / 100.0})
            last = frame
    return {"fps": fps, "frame_count": n, "duration_s": duration, "shots": shots_from_boundaries(bounds, n, fps),
            "transitions": [{"t_s": b["frame"] / fps, "frame": b["frame"], "type": "cut", "score": b["score"]}
                            for b in bounds],
            "params": {"threshold": threshold, "min_shot_s": min_shot_s}}


def run(video: str, method: str = "frames", **params) -> dict:
    try:
        if method == "scdet":
            res = detect_scdet(video, params.get("threshold", 10.0), params.get("min_shot_s", 0.2))
        else:
            res = detect_frames(video, **params)
    except ToolMissing as exc:
        return unavailable(str(exc))
    except RuntimeError as exc:
        return {"status": "error", "reason": str(exc)}
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, "method": method, **res,
                  "tools": tool_versions(("ffmpeg",), ("numpy",))})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--method", choices=["frames", "scdet"], default="frames")
    ap.add_argument("--min-shot", type=float, default=DEFAULTS["min_shot_s"], help="minimum shot length, s")
    ap.add_argument("--min-score", type=float, default=DEFAULTS["min_score"])
    ap.add_argument("--ratio", type=float, default=DEFAULTS["adaptive_ratio"], help="adaptive threshold ratio")
    ap.add_argument("--no-gradual", action="store_true")
    ap.add_argument("--threshold", type=float, default=10.0, help="scdet threshold (percent)")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if a.method == "scdet":
        res = run(a.video, "scdet", threshold=a.threshold, min_shot_s=a.min_shot)
    else:
        res = run(a.video, "frames", min_shot_s=a.min_shot, min_score=a.min_score, adaptive_ratio=a.ratio,
                  gradual=not a.no_gradual)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
