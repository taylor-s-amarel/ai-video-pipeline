"""Nominal versus effective frame rate: duplicate frames, animation on twos/threes, pulldown-like hold patterns
and variable frame rate (video_re_detect_frame_rate_cadence).

Method: every frame of the first 20 seconds (default, up to 600 frames) is decoded at 160 px wide with its
presentation timestamp (ffmpeg showinfo). The mean absolute luma difference d between consecutive frames is
compared with a local reference (median of the upper half of d over 12 transitions): in active stretches
(reference >= 1.0/255) a transition with d below 0.2 x the reference is a repeat of the previous image. Hold lengths (how many frames each image
stays) give the cadence: "on ones/twos/threes/fours" when at least 90% of holds share one length; otherwise the
shortest repeating hold pattern that matches at least 85% of holds (e.g. 1-1-1-2 = 24 fps material in 30 fps,
2-3 = 12 fps material in 30 fps); otherwise "on N" when 70% share one length; otherwise irregular. Effective fps = nominal fps x images / frames.
Variable frame rate: the frame intervals from timestamps vary by more than 10% of their median for at least
1% of frames.

Limits: frame-blended conversions (no exact repeats) read as on ones; still stretches carry no cadence
information and are excluded (active_share); heavy encoder noise on repeated frames can hide repeats below the
0.2 ratio; only the decoded window is analysed.
"""

from __future__ import annotations

import sys

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_frame_rate_cadence"
VERSION = "1.0.0"
DEFAULTS = {"dup_rel": 0.2, "active_thr": 1.0, "local_window": 12, "on_n_share": 0.7, "pattern_match": 0.85,
            "max_period": 8, "vfr_dev": 0.1, "vfr_share": 0.01}
DECODE = {"width": 160, "fps": 0, "max_frames": 600, "duration_s": 20.0}


def frame_diffs(gray) -> np.ndarray:
    g = np.asarray(gray, dtype=np.float32)
    return np.abs(np.diff(g, axis=0)).mean(axis=(1, 2))


def repeats(d: np.ndarray, p) -> tuple[np.ndarray, np.ndarray]:
    """Boolean arrays over transitions: (is_repeat, is_active).

    The reference level at each transition is the median of the upper half of the differences in a window of
    ``local_window`` transitions (on twos, half the differences are repeats, so a plain median would sit between
    the two populations)."""
    n = len(d)
    half = int(p["local_window"]) // 2
    ref = np.empty(n, dtype=np.float64)
    for i in range(n):
        win = np.sort(d[max(0, i - half):min(n, i + half + 1)])
        ref[i] = np.median(win[len(win) // 2:])
    active = ref >= p["active_thr"]
    rep = active & (d < p["dup_rel"] * ref)
    return rep, active


def hold_lengths(rep: np.ndarray, active: np.ndarray) -> list[int]:
    """Frames per image inside active stretches; holds cut by a still stretch or the window edge are dropped."""
    holds: list[int] = []
    cur = None  # None = not inside a measurable hold yet
    for r, a in zip(rep, active):
        if not a:
            cur = None
            continue
        if r:
            if cur is not None:
                cur += 1
        else:
            if cur is not None:
                holds.append(cur)
            cur = 1
    return holds


def find_pattern(holds: list[int], p) -> tuple[str, list[int] | None]:
    if not holds:
        return "static", None
    vals, counts = np.unique(holds, return_counts=True)
    top = int(vals[np.argmax(counts)])
    share = counts.max() / len(holds)
    names = {1: "on-ones", 2: "on-twos", 3: "on-threes", 4: "on-fours"}
    if share >= 0.9:
        return names.get(top, f"on-{top}s"), [top]
    h = np.array(holds)
    for period in range(2, int(p["max_period"]) + 1):
        if len(h) < 2 * period + 2:
            break
        if np.mean(h[period:] == h[:-period]) >= p["pattern_match"]:
            seg = [int(v) for v in h[:period]]
            if len(set(seg)) > 1:
                return "pattern", min(seg[i:] + seg[:i] for i in range(period))
    if share >= p["on_n_share"]:
        return names.get(top, f"on-{top}s"), [top]
    return "irregular", None


def analyse(frames, times, info, params) -> dict:
    p = {**DEFAULTS, **params}
    g = core.gray_frames(frames)
    t = np.asarray(times, dtype=np.float64)
    n = len(g)
    nominal = info.get("r_frame_rate") or info.get("fps")
    dt = np.diff(t) if n > 1 else np.array([])
    if not nominal and len(dt):
        nominal = 1.0 / float(np.median(dt))
    errors = []
    if n < 8:
        return {"status": "partial", "results": [], "errors": ["need at least 8 consecutive frames"],
                "payload": None}
    med = float(np.median(dt))
    dev = np.abs(dt - med) / med if med > 0 else np.zeros_like(dt)
    vfr = bool(np.mean(dev > p["vfr_dev"]) >= p["vfr_share"])
    d = frame_diffs(g)
    rep, active = repeats(d, p)
    holds = hold_lengths(rep, active)
    cadence, pattern = find_pattern(holds, p)
    active_share = float(active.mean())
    dup_ratio = float(rep[active].mean()) if active.any() else None
    if cadence == "pattern":
        eff = nominal * len(pattern) / sum(pattern)
    elif cadence.startswith("on-") and pattern:
        eff = nominal / pattern[0]
    elif dup_ratio is not None:
        eff = nominal * (1.0 - dup_ratio)
    else:
        eff = None
        errors.append("no motion in the analysed window: cadence cannot be measured")
    payload = {
        "nominal_fps": round(float(nominal), 4) if nominal else None,
        "avg_fps": round(float(info["avg_frame_rate"]), 4) if info.get("avg_frame_rate") else (round(1.0 / med, 4) if med > 0 else None),
        "effective_fps": None if eff is None else round(float(eff), 3),
        "duplicate_ratio": None if dup_ratio is None else round(dup_ratio, 4),
        "cadence": cadence,
        "hold_pattern": pattern,
        "vfr": vfr,
        "interval_ms": {"median": round(med * 1000, 3), "min": round(float(dt.min()) * 1000, 3),
                        "max": round(float(dt.max()) * 1000, 3), "cv": round(float(dt.std() / med) if med > 0 else 0.0, 4)},
        "active_share": round(active_share, 3),
        "frames_analysed": int(n),
    }
    results = [{"t_start_s": float(t[0]), "t_end_s": float(t[-1]), "label": cadence,
                "value": payload["effective_fps"], "confidence": 0.85 if active_share > 0.5 else 0.5,
                "evidence": f"{int(rep.sum())} repeated frame(s) of {int(active.sum())} active transitions; holds "
                            f"{holds[:12]}; nominal {payload['nominal_fps']} fps"}]
    if vfr:
        results.append({"t_start_s": float(t[0]), "t_end_s": float(t[-1]), "label": "variable_frame_rate",
                        "value": payload["interval_ms"], "confidence": 0.9,
                        "evidence": f"{int((dev > p['vfr_dev']).sum())} interval(s) deviate > {p['vfr_dev']:.0%} from the median"})
    return {"status": "ok" if eff is not None else "partial", "results": results, "payload": payload, "errors": errors}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
