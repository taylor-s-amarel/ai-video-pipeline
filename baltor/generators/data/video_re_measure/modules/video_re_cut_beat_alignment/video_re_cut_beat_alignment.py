"""Do the cuts land on the music? Cut-to-beat alignment with a chance baseline.

Usage:
    python video_re_cut_beat_alignment.py --shots shots.json --beats beats.json [--tolerance 0.07] [--out align.json]

Inputs are cut times (starts of shots 2..n from video_re_detect_shots) and beat times (or, when no
beats were tracked, onset times) from video_re_onsets_beats.

* cuts_on_beat_ratio: share of cuts within ``tolerance_s`` (default 70 ms, about two frames at
  30 fps) of the nearest reference time. Only cuts inside the music (first to last reference time,
  plus the tolerance) count.
* chance_ratio: the share expected if the same cuts were placed at random: for beats,
  min(1, 2 x tolerance / median beat interval); for onsets, the share of the music span covered by
  +-tolerance windows around onsets. ``lift`` = ratio / chance; values well above 1 mean the editor
  cut to the music.
* median_offset_s: median signed (cut - nearest reference); negative = cuts come just before beats.
* beats_per_shot: median shot length in beats (for example 2.0 = a cut every second beat).
"""

from __future__ import annotations

import argparse

import numpy as np

from video_re_common import clean, dump_json, load_json, shots_from_json

IDENTITY = "video_re_cut_beat_alignment"
VERSION = "1.0.0"


def coverage(times: np.ndarray, tol: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    iv = sorted((max(lo, t - tol), min(hi, t + tol)) for t in times)
    total, cur_a, cur_b = 0.0, None, None
    for a, b in iv:
        if cur_b is None or a > cur_b:
            if cur_b is not None:
                total += cur_b - cur_a
            cur_a, cur_b = a, b
        else:
            cur_b = max(cur_b, b)
    if cur_b is not None:
        total += cur_b - cur_a
    return total / (hi - lo)


def align(cuts_s: list[float], beats_s: list[float] | None = None, onsets_s: list[float] | None = None,
          tolerance_s: float = 0.07) -> dict:
    ref_name = "beats" if beats_s and len(beats_s) >= 2 else "onsets" if onsets_s and len(onsets_s) >= 2 else None
    if ref_name is None:
        return {"cuts_on_beat_ratio": None, "reason": "no beat or onset times", "tolerance_s": tolerance_s}
    ref = np.sort(np.asarray(beats_s if ref_name == "beats" else onsets_s, dtype=float))
    lo, hi = ref[0] - tolerance_s, ref[-1] + tolerance_s
    cuts = np.sort(np.asarray([c for c in cuts_s if lo <= c <= hi], dtype=float))
    if len(cuts) == 0:
        return {"cuts_on_beat_ratio": None, "reason": "no cuts inside the music", "reference": ref_name,
                "tolerance_s": tolerance_s}
    idx = np.clip(np.searchsorted(ref, cuts), 1, len(ref) - 1)
    left, right = ref[idx - 1], ref[idx]
    nearest = np.where(np.abs(cuts - left) <= np.abs(cuts - right), left, right)
    offsets = cuts - nearest
    on = np.abs(offsets) <= tolerance_s + 1e-9
    interval = float(np.median(np.diff(ref)))
    chance = min(1.0, 2 * tolerance_s / interval) if ref_name == "beats" else coverage(ref, tolerance_s, lo, hi)
    ratio = float(on.mean())
    shot_lengths = np.diff(cuts)
    return {
        "reference": ref_name, "tolerance_s": tolerance_s, "cuts_considered": int(len(cuts)),
        "cuts_on_beat_ratio": ratio, "chance_ratio": chance, "lift": ratio / chance if chance > 0 else None,
        "median_offset_s": float(np.median(offsets)), "reference_interval_s": interval,
        "beats_per_shot": float(np.median(shot_lengths) / interval) if len(shot_lengths) and ref_name == "beats" else None,
        "per_cut": [{"t_s": float(c), "nearest_s": float(n), "offset_s": float(o), "on_beat": bool(b)}
                    for c, n, o, b in zip(cuts, nearest, offsets, on)],
    }


def run(cuts_s: list[float], beats_s: list[float] | None = None, onsets_s: list[float] | None = None,
        tolerance_s: float = 0.07) -> dict:
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION,
                  **align(cuts_s, beats_s, onsets_s, tolerance_s)})


def cuts_from_shots(shots: list[dict]) -> list[float]:
    return [float(s["start_s"]) for s in sorted(shots, key=lambda s: s["start_s"])[1:]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shots", required=True, help="video_re_detect_shots JSON or evidence.json")
    ap.add_argument("--beats", required=True, help="video_re_onsets_beats JSON")
    ap.add_argument("--tolerance", type=float, default=0.07)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    beats = load_json(a.beats)
    if "audio" in beats:  # evidence.json
        beats = {"onsets_s": beats["audio"].get("onsets_s")}
    res = run(cuts_from_shots(shots_from_json(load_json(a.shots))), beats.get("beats_s"), beats.get("onsets_s"),
              a.tolerance)
    dump_json(res, a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
