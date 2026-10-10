"""Detect freeze frames, frame-duplication slow motion and speed changes (ramps) inside shots.

Method (grey frames at the SOURCE frame rate, long side 160; frame-exact timing matters here):

1. Freeze: a run of consecutive-frame differences below ``freeze_diff`` grey levels lasting at
   least ``min_freeze_s`` while the surrounding second moves (median difference >=
   ``moving_diff``). Rate 0.
2. Duplicate-frame slow motion: at least ``min_cycles`` consecutive cycles of "one new frame then
   r repeats" with the same r >= 1. Rate 1 / (r + 1) (r = 1 is half speed).
3. Speed changes: per-frame global displacement by phase correlation (frames whose peak is below
   ``min_peak`` are skipped), median-filtered over 5 frames, then split into constant-speed
   segments by binary segmentation on log speed (segments >= ``min_seg_s``; a split needs a speed
   ratio >= ``min_ratio``). The longest segment is the shot's normal speed; every other segment
   whose speed differs by ``min_ratio`` or more is a ``speed_change`` with rate = its speed / normal.

Limits: a subject that genuinely slows down looks like slow motion; optical-flow (interpolated)
slow motion has no duplicates and is only seen as a speed change; non-rigid content without a
dominant global motion gives no speed estimate (reported as skipped frames); freezes shorter
than ``min_freeze_s`` are ignored.
"""

from __future__ import annotations

import math

import numpy as np

import vre_detect_kit as kit

DETECTOR = "video_re_detect_speed_ramp_freeze"
VERSION = "1.0.0"
DEFAULTS = {
    "freeze_diff": 0.5,
    "moving_diff": 1.5,
    "min_freeze_s": 0.2,
    "min_cycles": 3,
    "min_peak": 0.2,
    "min_seg_s": 0.4,
    "min_ratio": 1.6,
    "min_speed": 0.3,
    "cut_threshold": 0.3,
}
PARAM_DOCS = {
    "freeze_diff": "mean grey difference under which two consecutive frames are identical",
    "moving_diff": "median difference around a freeze that shows the video was moving",
    "min_freeze_s": "shortest freeze reported",
    "min_cycles": "repeat cycles needed to call duplicate-frame slow motion",
    "min_peak": "phase-correlation peak for a usable per-frame displacement",
    "min_seg_s": "shortest constant-speed segment",
    "min_ratio": "speed ratio between segments that counts as a change",
    "min_speed": "px/frame below which a segment counts as still (not used as normal speed)",
    "cut_threshold": "cut score for the built-in shot splitter",
}


def segments_by_speed(logv: np.ndarray, min_len: int, min_ratio: float) -> list[tuple[int, int]]:
    """Binary segmentation of a 1-D log-speed series into constant pieces."""
    out: list[tuple[int, int]] = []

    def split(a: int, b: int) -> None:
        x = logv[a:b]
        n = len(x)
        best, at = 0.0, None
        if n >= 2 * min_len:
            cs = np.cumsum(x)
            for k in range(min_len, n - min_len + 1):
                m1 = cs[k - 1] / k
                m2 = (cs[-1] - cs[k - 1]) / (n - k)
                score = abs(m1 - m2) * math.sqrt(k * (n - k) / n)
                if score > best and abs(m1 - m2) >= math.log(min_ratio):
                    best, at = score, k
        if at is None:
            out.append((a, b))
        else:
            split(a, a + at)
            split(a + at, b)

    split(0, len(logv))
    return sorted(out)


def analyse(frames, fps, p, ctx):
    gray = kit.as_gray(np.asarray(frames))
    N = len(gray)
    t0 = ctx["t0"]
    d = kit.frame_diffs(gray)
    events = []
    still = d < p["freeze_diff"]
    used = np.zeros(len(d), dtype=bool)
    min_frz = max(2, int(round(p["min_freeze_s"] * fps)))
    w = max(2, int(round(fps)))
    # 1. freezes
    i = 0
    while i < len(d):
        if not still[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(d) and still[j + 1]:
            j += 1
        if j - i + 1 >= min_frz:
            ctx_d = np.concatenate([d[max(0, i - w):i], d[j + 1:j + 1 + w]])
            if ctx_d.size and float(np.median(ctx_d)) >= p["moving_diff"]:
                events.append({"type": "freeze", "t_start_s": t0 + (i + 1) / fps, "t_end_s": t0 + (j + 2) / fps,
                               "rate": 0.0, "frames": j - i + 1})
                used[i:j + 1] = True
        i = j + 1
    # 2. duplicate-frame cadence: one change followed by r repeats, repeated
    changes = np.flatnonzero(~still)
    if len(changes) >= p["min_cycles"] + 1:
        gaps = np.diff(changes) - 1
        k = 0
        while k < len(gaps):
            r = gaps[k]
            if r < 1 or used[changes[k]:changes[k + 1]].any():
                k += 1
                continue
            j = k
            while j + 1 < len(gaps) and gaps[j + 1] == r:
                j += 1
            cycles = j - k + 1
            if cycles >= p["min_cycles"]:
                a, b = changes[k], changes[j + 1]
                events.append({"type": "duplicate_slowmo", "t_start_s": t0 + a / fps, "t_end_s": t0 + (b + 1) / fps,
                               "rate": 1.0 / (r + 1), "frames": int(b - a + 1)})
                used[a:b + 1] = True
            k = j + 1
    # 3. speed changes per shot
    cuts = None if ctx.get("shots") else kit.detect_cuts(gray, fps, abs_thr=p["cut_threshold"])
    skipped = 0
    speed = np.full(len(d), np.nan)
    for i in range(len(d)):
        if used[i] or still[i]:
            continue
        dx, dy, pk = kit.phase_correlation(gray[i], gray[i + 1])
        if float(pk) >= p["min_peak"]:
            speed[i] = math.hypot(float(dx), float(dy))
        else:
            skipped += 1
    min_seg = max(3, int(round(p["min_seg_s"] * fps)))
    for (a, b) in kit.shot_ranges(N, fps, t0, cuts, ctx.get("shots")):
        idx = np.arange(a, min(b - 1, len(d)))
        idx = idx[np.isfinite(speed[idx])]
        if len(idx) < 2 * min_seg:
            continue
        v = speed[idx]
        vs = np.array([np.median(v[max(0, k - 2):k + 3]) for k in range(len(v))])
        segs = segments_by_speed(np.log(vs + 0.05), min_seg, p["min_ratio"])
        if len(segs) < 2:
            continue
        lens = [(e - s, s, e) for s, e in segs]
        moving = [x for x in lens if np.median(vs[x[1]:x[2]]) >= p["min_speed"]]
        ref_len, rs, re_ = max(moving or lens)
        ref = float(np.median(vs[rs:re_]))
        for s, e in segs:
            sp = float(np.median(vs[s:e]))
            rate = sp / max(ref, 1e-6)
            if (s, e) == (rs, re_) or abs(math.log(max(rate, 1e-6))) < math.log(p["min_ratio"]):
                continue
            events.append({"type": "speed_change", "t_start_s": t0 + idx[s] / fps, "t_end_s": t0 + (idx[e - 1] + 2) / fps,
                           "rate": rate, "frames": int(idx[e - 1] - idx[s] + 2)})
    events.sort(key=lambda e: e["t_start_s"])
    results = [kit.result(e["type"], 0.8 if e["type"] != "speed_change" else 0.6, t_start_s=e["t_start_s"],
                          t_end_s=e["t_end_s"], value=round(e["rate"], 4),
                          evidence={"freeze": "identical consecutive frames while the video moves",
                                    "duplicate_slowmo": "regular cadence of repeated frames",
                                    "speed_change": "global motion speed differs from the shot's normal speed"}[e["type"]])
               for e in events]
    counts = {t: sum(1 for e in events if e["type"] == t) for t in ("freeze", "duplicate_slowmo", "speed_change")}
    payload = {"events": events, "counts": counts, "frames_without_speed": skipped}
    return {"status": "ok", "results": results, "payload": payload, "errors": []}


DET = kit.Detector(DETECTOR, VERSION, DEFAULTS, analyse, long_side=160, fps=None, pix_fmt="gray",
                   description="Detect freeze frames, duplicate-frame slow motion and speed ramps (source frame rate).")


def detect(frames, fps, **kw):
    """Envelope for frames (N, H, W[, 3]) uint8 at the source ``fps`` (do not resample: it hides duplicates)."""
    return DET.detect(frames, fps, **kw)


def detect_file(path, **kw):
    return DET.detect_file(path, **kw)


def main(argv=None):
    return DET.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
