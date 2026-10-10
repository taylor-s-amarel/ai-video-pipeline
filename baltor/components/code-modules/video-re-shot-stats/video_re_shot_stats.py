"""Shot-length statistics: the cut rhythm of a video as numbers.

Usage:
    python video_re_shot_stats.py shots.json [--duration 61.2] [--out stats.json]
    python video_re_shot_stats.py video.mp4            # runs video_re_detect_shots first (sibling package)

Input is the output of video_re_detect_shots (or an evidence.json, or a bare list of shots with
start_s/end_s). Output:

* count, mean_s, median_s, std_s, min_s, max_s, p10_s, p90_s of shot durations
* cut_rate_per_min = (count - 1) transitions per minute of video
* cv = std/mean (0 = perfectly regular cutting)
* trend_s_per_min: least-squares slope of shot length against shot start time (negative = cutting
  speeds up as the video goes on)
* hook_cuts_first_3s: transitions inside the first 3 seconds
* thirds: cut rate and median shot length in each third of the running time
* histogram: shot counts in duration bins (s): <0.5, 0.5-1, 1-2, 2-4, 4-8, >=8
* dominant_s and share_near_dominant: the most common shot length (0.1 s resolution) and the share of
  shots within +-10% of it; a high share suggests a fixed beat or template timing
* transitions: counts by type (cut, gradual)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from video_re_common import clean, dump_json, import_sibling, load_json, shots_from_json

IDENTITY = "video_re_shot_stats"
VERSION = "1.0.0"
BINS = [0.0, 0.5, 1.0, 2.0, 4.0, 8.0, float("inf")]
BIN_LABELS = ["<0.5", "0.5-1", "1-2", "2-4", "4-8", ">=8"]


def stats(shots: list[dict], duration_s: float | None = None) -> dict:
    if not shots:
        return {"count": 0, "median_s": None, "mean_s": None, "cut_rate_per_min": None}
    starts = np.array([float(s["start_s"]) for s in shots])
    ends = np.array([float(s["end_s"]) for s in shots])
    d = ends - starts
    if np.any(d < 0):
        raise ValueError("a shot ends before it starts")
    total = float(duration_s) if duration_s else float(ends.max() - starts.min())
    n = len(d)
    cuts = starts[1:]
    out = {
        "count": n,
        "mean_s": float(d.mean()),
        "median_s": float(np.median(d)),
        "std_s": float(d.std()),
        "min_s": float(d.min()),
        "max_s": float(d.max()),
        "p10_s": float(np.percentile(d, 10)),
        "p90_s": float(np.percentile(d, 90)),
        "cut_rate_per_min": (n - 1) * 60.0 / total if total > 0 else None,
        "duration_s": total,
        "cv": float(d.std() / d.mean()) if d.mean() > 0 else None,
        "trend_s_per_min": None,
        "hook_cuts_first_3s": int(np.sum(cuts < 3.0)),
    }
    if n >= 3 and np.ptp(starts) > 0:
        slope = np.polyfit(starts, d, 1)[0]
        out["trend_s_per_min"] = float(slope * 60.0)
    thirds = []
    if total > 0:
        for k in range(3):
            a, b = total * k / 3.0, total * (k + 1) / 3.0
            in_third = d[(starts >= a) & (starts < b)]
            thirds.append({"start_s": a, "end_s": b,
                           "cut_rate_per_min": float(np.sum((cuts >= a) & (cuts < b)) * 60.0 / (b - a)),
                           "median_shot_s": float(np.median(in_third)) if len(in_third) else None})
    out["thirds"] = thirds
    hist, _ = np.histogram(d, bins=BINS)
    out["histogram"] = dict(zip(BIN_LABELS, (int(x) for x in hist)))
    rounded = np.round(d, 1)
    vals, counts = np.unique(rounded, return_counts=True)
    dom = float(vals[np.argmax(counts)])
    out["dominant_s"] = dom
    out["share_near_dominant"] = float(np.mean(np.abs(d - dom) <= 0.1 * max(dom, 1e-6))) if dom > 0 else None
    types: dict[str, int] = {}
    for s in shots[1:]:
        t = (s.get("transition_in") or {}).get("type", "cut")
        types[t] = types.get(t, 0) + 1
    out["transitions"] = types
    return out


def run(shots: list[dict], duration_s: float | None = None) -> dict:
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, **stats(shots, duration_s)})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="shots JSON (detect_shots output / evidence.json) or a video file")
    ap.add_argument("--duration", type=float, help="video duration in seconds (default: span of the shots)")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    duration = a.duration
    if Path(a.input).suffix.lower() == ".json":
        data = load_json(a.input)
        shots = shots_from_json(data)
        if duration is None and isinstance(data, dict):
            duration = data.get("duration_s") or (data.get("source") or {}).get("duration_s")
    else:
        det = import_sibling("video_re_detect_shots").run(a.input)
        if det.get("status") != "ok":
            dump_json(det, a.out)
            return 1
        shots, duration = det["shots"], duration or det.get("duration_s")
    res = run(shots, duration)
    dump_json(res, a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
