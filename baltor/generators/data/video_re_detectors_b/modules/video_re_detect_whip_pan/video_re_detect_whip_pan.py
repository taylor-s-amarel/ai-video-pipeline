"""Detect whip pans: very fast pans whose motion blur smears the picture, often used as transitions.

Method (grey frames at the source frame rate, long side 192):

1. Per frame, Sobel gradient energies Ex = mean(gx^2) and Ey = mean(gy^2), and their medians over
   the surrounding ``window_s`` seconds as the shot's own baseline (so a scene that is naturally
   full of horizontal lines does not look blurred).
2. A frame is part of a whip when its total gradient energy is at most ``sharp_drop`` x the
   baseline and the loss is directional: (Ey/Ey_base) / (Ex/Ex_base) >= ``min_aniso`` (horizontal
   motion blur removes horizontal gradients) or <= 1/``min_aniso`` (vertical whip). Runs of such
   frames (one-frame gaps allowed) at least ``min_frames`` long are events.
3. Direction: phase correlation between consecutive frames of the event (half size); content
   moving left means the camera whipped right. Low correlation peaks give ``unknown``.
4. ``at_cut``: the colour histograms just before and just after the event differ by at least
   ``cut_hist`` (the whip hides a cut between two differently coloured shots).

Limits: a defocus or rack-focus blur is isotropic and is ignored on purpose; fast pans that
stay sharp (high shutter speed) are not whips by this definition; diagonal whips are labelled
by their dominant axis.
"""

from __future__ import annotations

import math

import numpy as np

import vre_detect_kit as kit

DETECTOR = "video_re_detect_whip_pan"
VERSION = "1.0.0"
DEFAULTS = {
    "window_s": 1.0,
    "sharp_drop": 0.45,
    "min_aniso": 2.5,
    "min_frames": 2,
    "min_peak": 0.15,
    "cut_hist": 0.3,
}
PARAM_DOCS = {
    "window_s": "half-width of the window whose median sharpness is the baseline",
    "sharp_drop": "frame sharpness / baseline at or below which a frame is blurred",
    "min_aniso": "ratio of the per-axis energy losses that makes the blur directional",
    "min_frames": "fewest blurred frames in a whip",
    "min_peak": "phase-correlation peak needed to report a direction",
    "cut_hist": "histogram distance before vs after the whip that marks it as hiding a cut",
}


def frame_energies(gray: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ex, ey = [], []
    for g in gray:
        gx, gy = kit.gradients(g)
        ex.append(float((gx ** 2).mean()) + 1e-3)
        ey.append(float((gy ** 2).mean()) + 1e-3)
    return np.asarray(ex), np.asarray(ey)


def analyse(frames, fps, p, ctx):
    arr = np.asarray(frames)
    gray = kit.as_gray(arr)
    N = len(gray)
    t0 = ctx["t0"]
    ex, ey = frame_energies(gray)
    w = max(2, int(round(p["window_s"] * fps)))
    blurred = np.zeros(N, dtype=bool)
    aniso = np.ones(N)
    drop = np.ones(N)
    for i in range(N):
        lo, hi = max(0, i - w), min(N, i + w + 1)
        bx, by = float(np.median(ex[lo:hi])), float(np.median(ey[lo:hi]))
        drop[i] = (ex[i] + ey[i]) / (bx + by)
        aniso[i] = (ey[i] / by) / (ex[i] / bx)
        blurred[i] = drop[i] <= p["sharp_drop"] and max(aniso[i], 1 / aniso[i]) >= p["min_aniso"]
    aniso = np.log(aniso)
    runs, i = [], 0
    while i < N:
        if not blurred[i]:
            i += 1
            continue
        j = i
        while j + 1 < N and (blurred[j + 1] or (j + 2 < N and blurred[j + 2] and np.sign(aniso[j + 2]) == np.sign(aniso[i]))):
            j += 1
        while not blurred[j]:
            j -= 1
        runs.append((i, j))
        i = j + 1
    events, results = [], []
    rgb = kit.as_rgb(arr)
    for a, b in runs:
        if b - a + 1 < p["min_frames"]:
            continue
        ax = float(np.median(aniso[a:b + 1]))
        axis = "horizontal" if ax > 0 else "vertical"
        shifts = []
        for k in range(a, b):
            dx, dy, pk = kit.phase_correlation(kit.downsample(gray[k], 2), kit.downsample(gray[k + 1], 2))
            if float(pk) >= p["min_peak"]:
                shifts.append((float(dx) * 2, float(dy) * 2))
        direction = "unknown"
        if shifts:
            sx, sy = np.median(np.array(shifts), axis=0)
            if axis == "horizontal" and abs(sx) > 1:
                direction = "right" if sx < 0 else "left"
            elif axis == "vertical" and abs(sy) > 1:
                direction = "down" if sy < 0 else "up"
        at_cut = None
        if a > 0 and b + 1 < N:
            at_cut = bool(kit.hist_distances(np.stack([rgb[a - 1], rgb[b + 1]]))[0] >= p["cut_hist"])
        ev = {"t_start_s": t0 + a / fps, "t_end_s": t0 + (b + 1) / fps, "frames": b - a + 1, "axis": axis,
              "camera_direction": direction, "blur_anisotropy": float(math.exp(abs(ax))),
              "sharpness_ratio": float(np.min(drop[a:b + 1])), "at_cut": at_cut}
        events.append(ev)
        conf = min(0.95, 0.5 + 0.1 * ev["frames"] + 0.1 * (ev["blur_anisotropy"] > 4))
        results.append(kit.result("whip_pan", conf, t_start_s=ev["t_start_s"], t_end_s=ev["t_end_s"],
                                  value={"axis": axis, "direction": direction},
                                  evidence=f"{ev['frames']} frames at {ev['sharpness_ratio']:.2f}x baseline sharpness, "
                                           f"gradient anisotropy {ev['blur_anisotropy']:.1f}"
                                           + ("; hides a cut" if at_cut else "")))
    dur = N / fps
    payload = {"events": events, "count": len(events), "per_minute": len(events) / dur * 60 if dur else None,
               "as_transition": sum(1 for e in events if e["at_cut"])}
    return {"status": "ok", "results": results, "payload": payload, "errors": []}


DET = kit.Detector(DETECTOR, VERSION, DEFAULTS, analyse, long_side=192, fps=None, pix_fmt="rgb24",
                   description="Detect whip pans from directional motion blur, with direction and whether they hide a cut.")


def detect(frames, fps, **kw):
    """Envelope for frames (N, H, W[, 3]) uint8 at ``fps`` (use the source frame rate)."""
    return DET.detect(frames, fps, **kw)


def detect_file(path, **kw):
    return DET.detect_file(path, **kw)


def main(argv=None):
    return DET.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
