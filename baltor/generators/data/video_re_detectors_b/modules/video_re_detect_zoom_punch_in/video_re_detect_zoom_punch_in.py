"""Detect zoom punch-ins: sudden scale jumps (instant or within a few frames) used for emphasis.

Method (grey frames at the source frame rate, long side 192):

1. Instant jumps: consecutive-frame differences that spike (>= ``jump_diff`` grey levels and
   >= ``spike_k`` x the local median) are checked with a scale search: frame i is zoomed by each
   candidate scale about the centre (coarse grid on half-size frames, then refined in 0.5% steps),
   translation-corrected by
   phase correlation, and compared with frame i+1 by normalised cross-correlation over the
   central 70%. A best NCC >= ``min_ncc`` with |ln s| >= ln(``min_jump``) is a punch (in when s > 1,
   out when s < 1); otherwise the spike is a cut and is ignored.
2. Fast ramps: similarity fits between consecutive frames give a per-frame scale; runs where the
   zoom rate exceeds ``ramp_rate`` (ln per second) for at most ``max_ramp_s`` and accumulate
   |ln s| >= ln(``min_jump``) are ramp punches (slower zooms are Ken Burns, not punches).
3. With ``--evidence`` (audio onsets from video_re_evidence), each punch is marked on-beat when an
   onset lies within ``beat_tol_s``.

Limits: a cut between two framings of the same still is reported as an instant punch (which is
how editors build them); punches combined with large pans may fall below ``min_ncc``; scale
outside ``max_scale`` is not searched.
"""

from __future__ import annotations

import math

import numpy as np

import vre_detect_kit as kit

DETECTOR = "video_re_detect_zoom_punch_in"
VERSION = "1.0.0"
DEFAULTS = {
    "jump_diff": 6.0,
    "spike_k": 3.0,
    "min_ncc": 0.75,
    "min_jump": 1.04,
    "max_scale": 1.6,
    "ramp_rate": 0.6,
    "max_ramp_s": 0.4,
    "beat_tol_s": 0.07,
    "block": 32,
}
PARAM_DOCS = {
    "jump_diff": "consecutive-frame grey difference that makes a frame pair a jump candidate",
    "spike_k": "candidate difference must also exceed this multiple of the local median",
    "min_ncc": "normalised cross-correlation after the best zoom needed to call a punch (not a cut)",
    "min_jump": "smallest scale ratio reported",
    "max_scale": "largest scale ratio searched (and its inverse)",
    "ramp_rate": "|ln scale| per second above which a gradual zoom is a ramp punch",
    "max_ramp_s": "longest ramp still counted as a punch",
    "beat_tol_s": "largest distance to an audio onset for on_beat",
    "block": "block size for the per-frame similarity fits",
}


def best_scale(a: np.ndarray, b: np.ndarray, max_scale: float) -> tuple[float, float]:
    """Coarse search on half-size images (21 scales), then +-3% in 0.5% steps at full size."""
    coarse = np.exp(np.linspace(-math.log(max_scale), math.log(max_scale), 21))
    s0, _ = kit.scale_search(kit.downsample(a, 2), kit.downsample(b, 2), coarse)
    fine = s0 * np.exp(np.linspace(-0.03, 0.03, 13))
    return kit.scale_search(a, b, fine)


def analyse(frames, fps, p, ctx):
    gray = kit.as_gray(np.asarray(frames))
    N, H, W = gray.shape
    t0 = ctx["t0"]
    onsets = ctx.get("onsets") or []
    events = []
    d = kit.frame_diffs(gray)
    win = max(2, int(round(fps)))
    instant_frames = set()
    for i, v in enumerate(d):
        lo, hi = max(0, i - win), min(len(d), i + win + 1)
        base = float(np.median(np.delete(d[lo:hi], i - lo))) if hi - lo > 1 else 0.0
        if v < p["jump_diff"] or v < p["spike_k"] * base:
            continue
        s, c = best_scale(gray[i], gray[i + 1], p["max_scale"])
        if c >= p["min_ncc"] and abs(math.log(s)) >= math.log(p["min_jump"]):
            events.append({"t_s": t0 + (i + 1) / fps, "kind": "instant", "direction": "in" if s > 1 else "out",
                           "scale_jump": s, "duration_s": 0.0, "ncc": c})
            instant_frames.update({i, i + 1})
    # fast ramps from consecutive similarity fits
    fits = kit.global_motion(gray, 1, p["block"])
    rate = np.array([math.log(f["scale"]) * fps if f else 0.0 for f in fits])
    fast = np.abs(rate) >= p["ramp_rate"]
    i = 0
    max_len = max(1, int(round(p["max_ramp_s"] * fps)))
    while i < len(fast):
        if not fast[i] or i in instant_frames:
            i += 1
            continue
        j = i
        sign = np.sign(rate[i])
        while j + 1 < len(fast) and fast[j + 1] and np.sign(rate[j + 1]) == sign:
            j += 1
        total = float(np.sum(rate[i:j + 1]) / fps)
        if j - i + 1 <= max_len and abs(total) >= math.log(p["min_jump"]):
            events.append({"t_s": t0 + i / fps, "kind": "ramp", "direction": "in" if total > 0 else "out",
                           "scale_jump": math.exp(total), "duration_s": (j - i + 1) / fps, "ncc": None})
        i = j + 1
    events.sort(key=lambda e: e["t_s"])
    for e in events:
        if onsets:
            off = min((o - e["t_s"] for o in onsets), key=abs)
            e["on_beat"] = abs(off) <= p["beat_tol_s"]
            e["beat_offset_s"] = off
        else:
            e["on_beat"] = None
            e["beat_offset_s"] = None
    dur = N / fps
    results = [kit.result(f"zoom_punch_{e['direction']}", min(0.95, e["ncc"]) if e["ncc"] else 0.7,
                          t_start_s=e["t_s"], t_end_s=e["t_s"] + e["duration_s"], value=round(e["scale_jump"], 4),
                          evidence=f"{e['kind']} scale x{e['scale_jump']:.3f}"
                          + (f", NCC {e['ncc']:.2f} after zoom" if e["ncc"] else ""))
               for e in events]
    ins = [e for e in events if e["direction"] == "in"]
    payload = {"events": events, "count": len(events), "per_minute": len(events) / dur * 60 if dur else None,
               "median_scale_in": float(np.median([e["scale_jump"] for e in ins])) if ins else None,
               "beats_available": bool(onsets)}
    return {"status": "ok", "results": results, "payload": payload, "errors": []}


DET = kit.Detector(DETECTOR, VERSION, DEFAULTS, analyse, long_side=192, fps=None, pix_fmt="gray",
                   description="Detect sudden zoom punch-ins/outs (instant or fast ramps), optionally against beats.")


def detect(frames, fps, **kw):
    """Envelope for frames (N, H, W[, 3]) uint8 at ``fps``. Pass onsets=[...] seconds to mark on-beat punches."""
    return DET.detect(frames, fps, **kw)


def detect_file(path, **kw):
    return DET.detect_file(path, **kw)


def main(argv=None):
    return DET.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
