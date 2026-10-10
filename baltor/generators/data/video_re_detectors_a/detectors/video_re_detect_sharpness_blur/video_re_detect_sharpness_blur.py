"""Per-shot sharpness (variance of the Laplacian and a no-reference blur metric) and deliberate defocus
(video_re_detect_sharpness_blur).

Method: frames are sampled (default 2 per second) at a fixed analysis width of 480 px, because both measures
depend on scale. For each frame: the variance of the 4-neighbour Laplacian of luma (VoL, Pech-Pacheco et al.
2000) and the perceptual blur metric of Crete-Roffet et al. (2007): the frame is re-blurred with a 9-tap
average, and the share of neighbour-difference energy that the re-blur does not remove is subtracted from 1;
0 = sharp, 1 = fully blurred. Labels: sharp < 0.35 <= soft < 0.55 <= blurred (calibrated on 1/f test images:
unblurred 0.15-0.25, Gaussian sigma 1.5 px about 0.45-0.58, sigma 3 px about 0.71-0.81). Deliberate defocus:
on a 3 x 3 grid, a frame is selective-focus when its sharpest cell is sharp (metric < 0.35) and the VoL of the
sharpest cell is at least 8x that of the softest. Shots come from --shots (video_re_detect_shots output or
evidence.json) or the fallback cut detector; inside a shot a blur-metric swing of at least 0.2 between the
first and last third is a focus change (rack focus, blur-in or blur-out). Frames with luma std below 4 are flat
and skipped.

Limits: VoL depends on content and contrast, so compare it within one video only; the blur metric is more
content-independent but grain and noise read as sharpness; motion blur and defocus are not told apart here
(see video_re_detect_motion_blur); a single-subject frame on a plain background can look selective-focus.
"""

from __future__ import annotations

import sys

import numpy as np

import vre_pixel_core as core

IDENTITY = "video_re_detect_sharpness_blur"
VERSION = "1.0.0"
DEFAULTS = {"sharp_max": 0.35, "soft_max": 0.55, "selective_vol_ratio": 8.0, "focus_change": 0.2, "flat_std": 4.0,
            "grid": 3}
DECODE = {"width": 480, "fps": 2.0, "max_frames": 240}


def blur_metric(gray) -> float:
    """Crete-Roffet no-reference blur metric of one grey image (0 sharp .. 1 blurred)."""
    g = np.asarray(gray, dtype=np.float32)
    k = np.ones(9, np.float32) / 9.0
    vals = []
    for ax in (0, 1):
        b = core.conv1d(g, k, ax)
        df = np.abs(np.diff(g, axis=ax))
        db = np.abs(np.diff(b, axis=ax))
        s_f = float(df.sum())
        if s_f <= 1e-6:
            vals.append(1.0)
            continue
        vals.append((s_f - float(np.maximum(0.0, df - db).sum())) / s_f)
    return float(max(vals))


def variance_of_laplacian(gray) -> float:
    return float(core.laplacian(gray).var())


def frame_measures(gray, p) -> dict:
    g = np.asarray(gray, dtype=np.float32)
    if g.std() < p["flat_std"]:
        return {"flat": True}
    h, w = g.shape
    k = int(p["grid"])
    cells = []
    for i in range(k):
        for j in range(k):
            c = g[i * h // k:(i + 1) * h // k, j * w // k:(j + 1) * w // k]
            cells.append((variance_of_laplacian(c), blur_metric(c), float(c.std())))
    textured = [c for c in cells if c[2] >= p["flat_std"]]
    selective = False
    if len(textured) >= 3:
        best = max(textured, key=lambda c: c[0])
        worst = min(textured, key=lambda c: c[0])
        selective = best[1] < p["sharp_max"] and best[0] >= p["selective_vol_ratio"] * max(worst[0], 1e-3)
    return {"flat": False, "vol": variance_of_laplacian(g), "blur": blur_metric(g), "selective": bool(selective)}


def label_for(b: float, p) -> str:
    return "sharp" if b < p["sharp_max"] else ("soft" if b < p["soft_max"] else "blurred")


def analyse(frames, times, info, params) -> dict:
    p = {**DEFAULTS, **params}
    g = core.gray_frames(frames)
    t = np.asarray(times, dtype=np.float64)
    meas = [frame_measures(x, p) for x in g]
    shots = core.shots_for(frames, t, p.get("_shots"))
    per_shot, results = [], []
    for k, s in enumerate(shots):
        ms = [meas[i] for i in range(s["first"], s["last"] + 1) if not meas[i]["flat"]]
        if not ms:
            per_shot.append({"index": k, "start_s": s["start_s"], "end_s": s["end_s"], "label": "flat",
                             "vol_median": None, "blur_median": None, "selective_focus_share": 0.0,
                             "focus_change": None})
            continue
        blurs = np.array([m["blur"] for m in ms])
        vols = np.array([m["vol"] for m in ms])
        change = None
        if len(blurs) >= 3:
            third = max(1, len(blurs) // 3)
            delta = float(blurs[-third:].mean() - blurs[:third].mean())
            if abs(delta) >= p["focus_change"]:
                change = "blur-out" if delta > 0 else "blur-in"
        lab = label_for(float(np.median(blurs)), p)
        sel = float(np.mean([m["selective"] for m in ms]))
        entry = {"index": k, "start_s": s["start_s"], "end_s": s["end_s"], "label": lab,
                 "vol_median": round(float(np.median(vols)), 2), "blur_median": round(float(np.median(blurs)), 4),
                 "selective_focus_share": round(sel, 3), "focus_change": change}
        per_shot.append(entry)
        results.append({"t_start_s": s["start_s"], "t_end_s": s["end_s"], "label": lab, "value": entry["blur_median"],
                        "confidence": 0.8, "evidence": f"blur metric median {entry['blur_median']}, VoL median "
                                                       f"{entry['vol_median']} over {len(ms)} frame(s)"})
        if sel >= 0.5:
            results.append({"t_start_s": s["start_s"], "t_end_s": s["end_s"], "label": "selective_focus",
                            "value": round(sel, 3), "confidence": 0.65,
                            "evidence": f"sharpest grid cell >= {p['selective_vol_ratio']}x the softest's VoL in {sel:.0%} of frames"})
        if change:
            results.append({"t_start_s": s["start_s"], "t_end_s": s["end_s"], "label": change, "confidence": 0.6,
                            "evidence": "blur metric changes by >= 0.2 between the first and last third of the shot"})
    valid = [m for m in meas if not m["flat"]]
    payload = {
        "analysis_width": int(g.shape[2]),
        "video": None if not valid else {
            "vol_median": round(float(np.median([m["vol"] for m in valid])), 2),
            "blur_median": round(float(np.median([m["blur"] for m in valid])), 4),
            "label": label_for(float(np.median([m["blur"] for m in valid])), p),
            "selective_focus_share": round(float(np.mean([m["selective"] for m in valid])), 3)},
        "shots": per_shot,
        "shots_source": "given" if p.get("_shots") else "fallback-cut-detector",
        "frames_analysed": int(len(g)),
    }
    return {"status": "ok" if valid else "partial", "results": results, "payload": payload,
            "errors": [] if valid else ["all sampled frames are flat"]}


def main(argv=None) -> int:
    return core.run_cli(IDENTITY, VERSION, analyse, DEFAULTS, __doc__, argv, DECODE)


if __name__ == "__main__":
    sys.exit(main())
