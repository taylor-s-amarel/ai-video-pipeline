"""How much the picture changes, in the centre (subject) and in the border (background), per shot.

Usage:
    python video_re_motion_energy.py video.mp4 [--shots shots.json] [--out motion.json]

Frames are decoded as grey, 160 px wide, at the source frame rate (capped at 30 fps with ffmpeg's fps
filter for faster sources). For each pair of consecutive frames:

    center = mean |frame_t - frame_t-1| inside the central box (60% x 60% of the frame)
    border = the same over the rest of the frame

in grey levels (0-255). Pairs that straddle a shot boundary are left out of the per-shot means.

Outputs per shot {center, border, whole}, a 0.5 s series, and a summary with
``background_moving_ratio``: the share of 2-second windows whose mean border difference is at least
``moving_threshold`` (default 0.6 grey levels), a direct check of "the background keeps moving";
``still_ratio``: share of frame pairs with whole-frame difference under 0.3 (frozen picture).
Values depend on resolution and frame rate, so compare videos measured with the same settings.
"""

from __future__ import annotations

import argparse

import numpy as np

from video_re_common import (ToolMissing, clean, dump_json, import_sibling, iter_frames, load_json, media_info,
                             shots_from_json, unavailable, whole_clip_shot)

IDENTITY = "video_re_motion_energy"
VERSION = "1.0.0"
CENTER_FRACTION = 0.6


def center_mask(h: int, w: int, fraction: float = CENTER_FRACTION) -> np.ndarray:
    m = np.zeros((h, w), dtype=bool)
    y0, y1 = int(round(h * (1 - fraction) / 2)), int(round(h * (1 + fraction) / 2))
    x0, x1 = int(round(w * (1 - fraction) / 2)), int(round(w * (1 + fraction) / 2))
    m[y0:y1, x0:x1] = True
    return m


def pair_series(frames, times) -> dict:
    """Per consecutive-pair center/border/whole differences from an iterable of grey frames."""
    prev, mask = None, None
    t_out, c_out, b_out, w_out = [], [], [], []
    for t, f in zip(times, frames):
        g = f.astype(np.int16)
        if prev is not None:
            if mask is None:
                mask = center_mask(*g.shape)
            d = np.abs(g - prev)
            c_out.append(float(d[mask].mean()))
            b_out.append(float(d[~mask].mean()))
            w_out.append(float(d.mean()))
            t_out.append(t)
        prev = g
    return {"t": np.asarray(t_out), "center": np.asarray(c_out), "border": np.asarray(b_out),
            "whole": np.asarray(w_out)}


def summarise(series: dict, shots: list[dict], fps: float, moving_threshold: float = 0.6) -> dict:
    t = series["t"]
    per_shot = []
    for s in shots:
        a, b = float(s["start_s"]), float(s["end_s"])
        # the pair ending at time t compares t-1/fps and t; keep pairs fully inside the shot
        sel = (t - 1.0 / fps >= a - 1e-6) & (t < b - 1e-6)
        if sel.any():
            per_shot.append({"index": s["index"], "center": float(series["center"][sel].mean()),
                             "border": float(series["border"][sel].mean()),
                             "whole": float(series["whole"][sel].mean()), "pairs": int(sel.sum())})
        else:
            per_shot.append({"index": s["index"], "center": None, "border": None, "whole": None, "pairs": 0})
    out_series = []
    if len(t):
        for k in range(int(np.ceil((t.max() + 1e-9) / 0.5))):
            sel = (t >= k * 0.5) & (t < (k + 1) * 0.5)
            if sel.any():
                out_series.append({"t_s": k * 0.5, "center": float(series["center"][sel].mean()),
                                   "border": float(series["border"][sel].mean())})
    windows = []
    if len(t):
        for k in range(max(1, int(np.floor(t.max() / 2.0)))):
            sel = (t >= k * 2.0) & (t < (k + 1) * 2.0)
            if sel.any():
                windows.append(float(series["border"][sel].mean()))
    summary = {
        "center_mean": float(series["center"].mean()) if len(t) else None,
        "border_mean": float(series["border"].mean()) if len(t) else None,
        "background_moving_ratio": float(np.mean(np.asarray(windows) >= moving_threshold)) if windows else None,
        "still_ratio": float(np.mean(series["whole"] < 0.3)) if len(t) else None,
        "moving_threshold": moving_threshold,
    }
    return {"shots": per_shot, "series": out_series, "summary": summary}


def analyse(video: str, shots: list[dict], width: int = 160, max_fps: float = 30.0,
            moving_threshold: float = 0.6, info: dict | None = None) -> dict:
    info = info or media_info(video)
    src_fps = info.get("fps") or 25.0
    fps = min(src_fps, max_fps)
    times, frames = [], []
    for t, f in iter_frames(video, width=width, pix_fmt="gray", fps=fps if src_fps > max_fps else None, info=info):
        times.append(t)
        frames.append(f)
    series = pair_series(frames, times)
    res = summarise(series, shots, fps, moving_threshold)
    res["params"] = {"width": width, "fps": fps, "center_fraction": CENTER_FRACTION}
    return res


def run(video: str, shots: list[dict] | None = None, **kw) -> dict:
    try:
        info = media_info(video)
        shots = shots or whole_clip_shot(info.get("duration_s") or 0.0)
        res = analyse(video, shots, info=info, **kw)
    except ToolMissing as exc:
        return unavailable(str(exc))
    except RuntimeError as exc:
        return {"status": "error", "reason": str(exc)}
    return clean({"status": "ok", "module": IDENTITY, "version": VERSION, **res})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--shots", help="detect_shots JSON; default: run video_re_detect_shots")
    ap.add_argument("--threshold", type=float, default=0.6, help="border difference counted as moving")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if a.shots:
        shots = shots_from_json(load_json(a.shots))
    else:
        det = import_sibling("video_re_detect_shots").run(a.video)
        shots = det.get("shots") if det.get("status") == "ok" else None
    res = run(a.video, shots, moving_threshold=a.threshold)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
