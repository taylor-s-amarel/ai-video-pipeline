"""Dominant colours and tone statistics per shot.

Usage:
    python video_re_palette_per_shot.py video.mp4 [--shots shots.json] [--k 5] [--out palette.json]

Frames are decoded at ``sample_fps`` (default 4) and 64 px wide; every shot gets the frames inside
it (or its middle frame when it is shorter than one sample interval). Pixels are clustered with
k-means in CIE L*a*b* (D65, deterministic k-means++ seeding), clusters closer than ``merge_delta_e``
(default 8) are merged, and each colour is reported as the mean sRGB of its pixels with its share of
the shot's area.

Per shot: palette (hex, largest share first), shares, mean_luma (0-255), luma_std (contrast proxy),
saturation (mean HSV saturation, 0-1), warmth ((mean R - mean B) / 255, -1..1). Plus the same for the
whole video. Colours are measured after the video's own encoding and compression, so they shift a
little from the colours the editor picked.
"""

from __future__ import annotations

import argparse

import numpy as np

from video_re_common import (ToolMissing, clean, dump_json, import_sibling, iter_frames, load_json, media_info,
                             read_frame_at, shots_from_json, unavailable, whole_clip_shot)

IDENTITY = "video_re_palette_per_shot"
VERSION = "1.0.0"


def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    c = rgb.astype(np.float64) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def kmeans(x: np.ndarray, k: int, iters: int = 15, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Plain k-means with k-means++ seeding. Returns (centres, labels)."""
    rng = np.random.default_rng(seed)
    n = len(x)
    k = max(1, min(k, n))
    centres = [x[rng.integers(n)]]
    for _ in range(1, k):
        d2 = np.min(((x[:, None, :] - np.asarray(centres)[None]) ** 2).sum(-1), axis=1)
        if d2.sum() <= 0:
            break
        centres.append(x[rng.choice(n, p=d2 / d2.sum())])
    c = np.asarray(centres, dtype=np.float64)
    labels = np.zeros(n, dtype=int)
    for _ in range(iters):
        labels = np.argmin(((x[:, None, :] - c[None]) ** 2).sum(-1), axis=1)
        new = np.array([x[labels == j].mean(axis=0) if np.any(labels == j) else c[j] for j in range(len(c))])
        if np.allclose(new, c):
            break
        c = new
    return c, labels


def palette(pixels_rgb: np.ndarray, k: int = 5, merge_delta_e: float = 8.0, max_pixels: int = 6000,
            seed: int = 0) -> list[dict]:
    """[{hex, share, rgb}] for an (N, 3) uint8 pixel array, largest share first."""
    px = pixels_rgb.reshape(-1, 3)
    if len(px) > max_pixels:
        px = px[np.random.default_rng(seed).choice(len(px), max_pixels, replace=False)]
    lab = srgb_to_lab(px)
    centres, labels = kmeans(lab, k, seed=seed)
    groups = [[j] for j in range(len(centres))]
    merged = True
    while merged:  # merge perceptually identical clusters
        merged = False
        for a in range(len(groups)):
            for b in range(a + 1, len(groups)):
                ca = lab[np.isin(labels, groups[a])].mean(axis=0)
                cb = lab[np.isin(labels, groups[b])].mean(axis=0)
                if np.linalg.norm(ca - cb) < merge_delta_e:
                    groups[a] += groups.pop(b)
                    merged = True
                    break
            if merged:
                break
    out = []
    for g in groups:
        mask = np.isin(labels, g)
        if not mask.any():
            continue
        rgb = px[mask].astype(np.float64).mean(axis=0)
        r, gg, b = (int(round(v)) for v in rgb)
        out.append({"hex": f"#{r:02X}{gg:02X}{b:02X}", "share": float(mask.mean()), "rgb": [r, gg, b]})
    return sorted(out, key=lambda c: -c["share"])


def tone_stats(pixels_rgb: np.ndarray) -> dict:
    px = pixels_rgb.reshape(-1, 3).astype(np.float64)
    luma = px @ np.array([0.299, 0.587, 0.114])
    mx, mn = px.max(axis=1), px.min(axis=1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0.0)
    return {"mean_luma": float(luma.mean()), "luma_std": float(luma.std()), "saturation": float(sat.mean()),
            "warmth": float((px[:, 0].mean() - px[:, 2].mean()) / 255.0)}


def analyse(video: str, shots: list[dict], k: int = 5, sample_fps: float = 4.0, width: int = 64,
            info: dict | None = None) -> dict:
    info = info or media_info(video)
    times, frames = [], []
    for t, f in iter_frames(video, width=width, pix_fmt="rgb24", fps=sample_fps, info=info):
        times.append(t)
        frames.append(f)
    times_a = np.asarray(times)
    per_shot, all_px = [], []
    for shot in shots:
        a, b = float(shot["start_s"]), float(shot["end_s"])
        idx = np.where((times_a >= a) & (times_a < b))[0] if len(times_a) else []
        if len(idx):
            px = np.concatenate([frames[i].reshape(-1, 3) for i in idx])
        else:
            px = read_frame_at(video, (a + b) / 2.0, width=width, info=info).reshape(-1, 3)
        pal = palette(px, k)
        per_shot.append({"index": shot["index"], "palette": [c["hex"] for c in pal],
                         "shares": [c["share"] for c in pal], "frames_sampled": int(len(idx)) or 1, **tone_stats(px)})
        all_px.append(px)
    overall_px = np.concatenate(all_px) if all_px else np.zeros((0, 3), np.uint8)
    overall = {}
    if len(overall_px):
        pal = palette(overall_px, k + 1)
        overall = {"palette": [c["hex"] for c in pal], "shares": [c["share"] for c in pal], **tone_stats(overall_px)}
    return {"shots": per_shot, "overall": overall, "params": {"k": k, "sample_fps": sample_fps, "width": width}}


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
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--sample-fps", type=float, default=4.0)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if a.shots:
        shots = shots_from_json(load_json(a.shots))
    else:
        det = import_sibling("video_re_detect_shots").run(a.video)
        shots = det.get("shots") if det.get("status") == "ok" else None
    res = run(a.video, shots, k=a.k, sample_fps=a.sample_fps)
    dump_json(res, a.out)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
