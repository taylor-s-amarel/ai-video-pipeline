"""Check a render's first frame for the bold yellow hook title (numpy).

Finds pixels close to the house title colour (default #FFD21F) in the first
frame, then checks that:

* enough of them exist to be a title (``min_pixels_fraction``);
* their bounding box centre is in the upper part (centre y <= 40% height);
* the box is reasonably wide (a title, not a stray yellow object).

Colour matching uses distance in RGB with a tolerance, so antialiased and
slightly compressed text still counts. ``first_frame`` extracts frame 0
through ffmpeg; ``check_frame`` works on any RGB array.

Usage::

    from first_frame_title_check import check_video
    check_video("render.mp4")   # {'passed': True, 'bbox': (x, y, w, h), 'centre_y_fraction': 0.21, ...}
"""

from __future__ import annotations

import subprocess

import numpy as np


def _hex(c: str) -> np.ndarray:
    h = c.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def check_frame(rgb: np.ndarray, color: str = "#FFD21F", tolerance: float = 60.0, max_center_y: float = 0.40,
                min_pixels_fraction: float = 0.002, min_width_fraction: float = 0.25) -> dict:
    if rgb.ndim != 3 or rgb.shape[2] < 3:
        raise ValueError("expected an RGB frame (H, W, 3)")
    H, W = rgb.shape[:2]
    dist = np.linalg.norm(rgb[..., :3].astype(np.float32) - _hex(color), axis=2)
    mask = dist <= tolerance
    count = int(mask.sum())
    result = {"pixels": count, "pixels_fraction": round(count / (H * W), 5), "bbox": None,
              "centre_y_fraction": None, "problems": []}
    if count < min_pixels_fraction * H * W:
        result["problems"].append("no title in the house colour found on the first frame")
        result["passed"] = False
        return result
    ys, xs = np.nonzero(mask)
    # robust box: ignore the outer 1% of matching pixels (stray specks)
    x0, x1 = np.percentile(xs, [1, 99])
    y0, y1 = np.percentile(ys, [1, 99])
    bbox = (int(x0), int(y0), int(x1 - x0 + 1), int(y1 - y0 + 1))
    cy = (y0 + y1) / 2 / H
    result["bbox"], result["centre_y_fraction"] = bbox, round(float(cy), 4)
    if cy > max_center_y:
        result["problems"].append(f"title centre at {cy:.0%} of height (must be <= {max_center_y:.0%})")
    if bbox[2] < min_width_fraction * W:
        result["problems"].append(f"title is only {bbox[2] / W:.0%} of the width")
    result["passed"] = not result["problems"]
    return result


def first_frame(path: str, width: int = 540) -> np.ndarray:
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout.strip()
    w, h = (int(x) for x in probe.split(",")[:2])
    oh = int(round(h * width / w / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-frames:v", "1", "-vf",
                          f"scale={width}:{oh}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(oh, width, 3)


def check_video(path: str, width: int = 540, **kw) -> dict:
    return check_frame(first_frame(path, width), **kw)
