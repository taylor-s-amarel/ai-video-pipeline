"""Check that a video's background actually moves (no slideshow look).

Reads downscaled grayscale frames from ffmpeg through a pipe (no temporary
files), takes the mean absolute difference between consecutive frames inside
a background region (default: the whole frame minus a central photo box),
and requires every ``window_s`` window to average above ``min_mean_diff``
(0-255 scale; the house default is 0.6).

Usage::

    from background_motion_checker import check_video, check_frames
    report = check_video("render.mp4", exclude=(0.05, 0.12, 0.90, 0.68))   # exclude (x, y, w, h) fractions
    report["passed"], report["windows"]
"""

from __future__ import annotations

import json
import shutil
import subprocess

import numpy as np


def region_mask(h: int, w: int, exclude=None) -> np.ndarray:
    m = np.ones((h, w), bool)
    if exclude:
        x, y, ew, eh = exclude
        m[int(y * h):int((y + eh) * h), int(x * w):int((x + ew) * w)] = False
    if not m.any():
        raise ValueError("the exclusion box covers the whole frame")
    return m


def frame_diffs(frames: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    f = frames.astype(np.float32)
    d = np.abs(f[1:] - f[:-1])
    if mask is not None:
        return d[:, mask].mean(axis=1)
    return d.reshape(len(d), -1).mean(axis=1)


def check_frames(frames: np.ndarray, fps: float, exclude=None, window_s: float = 2.0,
                 min_mean_diff: float = 0.6) -> dict:
    if len(frames) < 2:
        raise ValueError("need at least two frames")
    mask = region_mask(frames.shape[1], frames.shape[2], exclude)
    diffs = frame_diffs(frames, mask)
    per = max(1, int(round(window_s * fps)))
    windows = []
    for i in range(0, len(diffs), per):
        seg = diffs[i:i + per]
        windows.append({"start_s": round(i / fps, 3), "mean_diff": round(float(seg.mean()), 4),
                        "passed": bool(seg.mean() > min_mean_diff)})
    return {"passed": all(w["passed"] for w in windows), "threshold": min_mean_diff,
            "min_window": min(w["mean_diff"] for w in windows), "windows": windows}


def read_gray_frames(path: str, width: int = 160, fps: float | None = None, max_seconds: float | None = None):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe are required")
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                      "stream=width,height,avg_frame_rate", "-of", "json", path],
                                     capture_output=True, text=True, check=True).stdout)["streams"][0]
    num, den = info["avg_frame_rate"].split("/")
    src_fps = float(num) / float(den) if float(den) else 30.0
    use_fps = fps or src_fps
    h = int(round(info["height"] * width / info["width"] / 2) * 2)
    vf = f"fps={use_fps:g},scale={width}:{h},format=gray"
    argv = ["ffmpeg", "-nostdin", "-v", "error", "-i", path]
    if max_seconds:
        argv += ["-t", f"{max_seconds:g}"]
    argv += ["-vf", vf, "-f", "rawvideo", "-"]
    raw = subprocess.run(argv, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, width), use_fps


def check_video(path: str, exclude=None, window_s: float = 2.0, min_mean_diff: float = 0.6,
                width: int = 160, fps: float | None = None) -> dict:
    frames, used_fps = read_gray_frames(path, width, fps)
    return check_frames(frames, used_fps, exclude, window_s, min_mean_diff)
