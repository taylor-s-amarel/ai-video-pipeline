"""Typed media information from ffprobe (no shell, JSON output).

``probe(path)`` runs ``ffprobe -print_format json -show_format -show_streams``
and ``summarise`` turns the result into a flat, typed dict: duration, size,
container, video codec/size/fps/pix_fmt/rotation/SAR/bit depth hints, audio
codec/sample rate/channels, frame count when known, and whether the frame
rate is variable. ``summarise`` is pure, so tests run on stored JSON.

Usage::

    from ffprobe_media_info import probe, summarise
    info = summarise(probe("render.mp4"))
    info["video"]["fps"], info["audio"]["sample_rate"], info["vfr"]
"""

from __future__ import annotations

import json
import shutil
import subprocess
from fractions import Fraction


def probe(path: str, timeout: float = 60.0) -> dict:
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe is not installed")
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
                         capture_output=True, text=True, check=True, timeout=timeout).stdout
    return json.loads(out)


def _rate(s: str | None) -> float | None:
    if not s or s in ("0/0", "0"):
        return None
    try:
        return float(Fraction(s))
    except (ValueError, ZeroDivisionError):
        return None


def _rotation(stream: dict) -> int:
    tags = stream.get("tags", {})
    if "rotate" in tags:
        return int(tags["rotate"]) % 360
    for sd in stream.get("side_data_list", []):
        if "rotation" in sd:
            return int(-float(sd["rotation"])) % 360
    return 0


def summarise(info: dict) -> dict:
    fmt = info.get("format", {})
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    out = {
        "duration": float(fmt["duration"]) if fmt.get("duration") else None,
        "size_bytes": int(fmt["size"]) if fmt.get("size") else None,
        "bit_rate": int(fmt["bit_rate"]) if fmt.get("bit_rate") else None,
        "container": fmt.get("format_name"),
        "video": None, "audio": None, "vfr": False,
        "subtitle_streams": sum(1 for s in streams if s.get("codec_type") == "subtitle"),
    }
    if v:
        rot = _rotation(v)
        w, h = int(v.get("width", 0)), int(v.get("height", 0))
        if rot in (90, 270):
            w, h = h, w
        avg, real = _rate(v.get("avg_frame_rate")), _rate(v.get("r_frame_rate"))
        out["video"] = {"codec": v.get("codec_name"), "width": w, "height": h, "pix_fmt": v.get("pix_fmt"),
                        "fps": round(avg or real or 0, 4) or None, "rotation": rot,
                        "sar": v.get("sample_aspect_ratio", "1:1"), "profile": v.get("profile"),
                        "frames": int(v["nb_frames"]) if str(v.get("nb_frames", "")).isdigit() else None,
                        "color_space": v.get("color_space"), "bits_per_raw_sample": v.get("bits_per_raw_sample")}
        out["vfr"] = bool(avg and real and abs(avg - real) / real > 0.01)
    if a:
        out["audio"] = {"codec": a.get("codec_name"), "sample_rate": int(a.get("sample_rate", 0)) or None,
                        "channels": a.get("channels"), "layout": a.get("channel_layout")}
    return out
