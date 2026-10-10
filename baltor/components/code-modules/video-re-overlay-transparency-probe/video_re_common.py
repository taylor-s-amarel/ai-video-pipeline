"""Shared helpers for the video_re_* measurement modules.

This file is vendored: every video_re_* package ships an identical copy, so each
package works on its own. It needs only the standard library, numpy and the
ffmpeg/ffprobe command-line tools.

Main helpers
------------
probe(path)                       ffprobe JSON for a file
media_info(path)                  width/height (rotation applied), fps, duration, has_audio, ...
analysis_size(w, h, target_w)     even-sized analysis resolution keeping the aspect ratio
iter_frames(path, width, ...)     stream decoded frames as numpy arrays (grey or RGB)
read_frames(path, width, ...)     the same, stacked into one array, plus timestamps
read_frame_at(path, t, width)     one frame at a time position
read_audio(path, sr)              mono float32 samples in [-1, 1]
import_sibling(identity)          import another video_re_* module placed next to this package
tool_versions(...)                versions of ffmpeg/ffprobe/numpy/... for evidence records
"""

from __future__ import annotations

import importlib
import importlib.metadata
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterator

import numpy as np

COMMON_VERSION = "1.0.0"


class ToolMissing(RuntimeError):
    """An external command (ffmpeg, ffprobe, tesseract, ...) is not installed."""


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def require(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise ToolMissing(f"{tool} is not installed or not on PATH")
    return path


def run(argv: list[str], timeout: float = 600, input_bytes: bytes | None = None,
        check: bool = True) -> subprocess.CompletedProcess:
    """Run a command, capturing stdout/stderr as bytes. Never reads from the terminal."""
    require(argv[0])
    proc = subprocess.run(argv, input=input_bytes, capture_output=True, timeout=timeout,
                          stdin=None if input_bytes is not None else subprocess.DEVNULL)
    if check and proc.returncode != 0:
        tail = proc.stderr.decode("utf-8", "replace").strip()[-800:]
        raise RuntimeError(f"{argv[0]} exited with {proc.returncode}: {tail}")
    return proc


# ---------------------------------------------------------------- versions

def tool_version(tool: str) -> str | None:
    """Version string of a command-line tool, or None if it is missing."""
    if not have(tool):
        return None
    flag = "-version" if tool in {"ffmpeg", "ffprobe"} else "--version"
    try:
        proc = subprocess.run([tool, flag], capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL)
    except Exception:  # noqa: BLE001
        return None
    text = (proc.stdout or proc.stderr or "").strip().splitlines()
    if not text:
        return None
    first = text[0]
    m = re.search(r"version\s+(\S+)", first)
    if m:
        return m.group(1)
    m = re.search(r"(\d+\.\d+(?:\.\d+)?\S*)", first)
    return m.group(1) if m else first[:60]


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def tool_versions(tools: tuple[str, ...] = ("ffmpeg", "ffprobe"),
                  packages: tuple[str, ...] = ("numpy",)) -> dict[str, str]:
    out: dict[str, str] = {}
    for t in tools:
        v = tool_version(t)
        if v:
            out[t] = v
    for p in packages:
        v = package_version(p)
        if v:
            out[p] = v
    out["python"] = sys.version.split()[0]
    return out


# ---------------------------------------------------------------- probing

def probe(path: str | os.PathLike) -> dict:
    proc = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
               timeout=120)
    return json.loads(proc.stdout.decode("utf-8", "replace") or "{}")


def _ratio(text: str | None) -> float | None:
    if not text or text in {"0/0", "N/A"}:
        return None
    if "/" in text:
        a, b = text.split("/", 1)
        try:
            a_f, b_f = float(a), float(b)
        except ValueError:
            return None
        return a_f / b_f if b_f else None
    try:
        return float(text)
    except ValueError:
        return None


def rotation_of(stream: dict) -> int:
    """Rotation in degrees (0, 90, 180, 270) from stream tags or display-matrix side data."""
    rot = 0.0
    tags = stream.get("tags") or {}
    if "rotate" in tags:
        try:
            rot = float(tags["rotate"])
        except ValueError:
            rot = 0.0
    for sd in stream.get("side_data_list") or []:
        if "rotation" in sd:
            try:
                rot = float(sd["rotation"])
            except (TypeError, ValueError):
                pass
    return int(round(rot)) % 360


def media_info_from_probe(info: dict, reference: str = "") -> dict:
    streams = info.get("streams") or []
    fmt = info.get("format") or {}
    video = next((s for s in streams if s.get("codec_type") == "video"
                  and not (s.get("disposition") or {}).get("attached_pic")), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    subs = [s for s in streams if s.get("codec_type") == "subtitle"]
    duration = _ratio(str(fmt.get("duration"))) if fmt.get("duration") is not None else None
    if duration is None and video is not None and video.get("duration"):
        duration = _ratio(str(video.get("duration")))
    out: dict[str, Any] = {
        "reference": reference,
        "duration_s": round(duration, 4) if duration is not None else None,
        "width": None, "height": None, "fps": None, "has_audio": audio is not None,
        "coded_width": None, "coded_height": None, "rotation": 0, "sample_aspect_ratio": None,
        "video_codec": None, "pix_fmt": None, "nb_frames": None, "bit_rate": None,
        "audio_codec": audio.get("codec_name") if audio else None,
        "sample_rate": int(audio["sample_rate"]) if audio and audio.get("sample_rate") else None,
        "channels": audio.get("channels") if audio else None,
        "subtitle_streams": [{"index": s.get("index"), "codec": s.get("codec_name"),
                              "language": (s.get("tags") or {}).get("language")} for s in subs],
        "container": fmt.get("format_name"),
        "start_time_s": _ratio(str(fmt.get("start_time"))) if fmt.get("start_time") else None,
    }
    if fmt.get("bit_rate"):
        try:
            out["bit_rate"] = int(fmt["bit_rate"])
        except ValueError:
            pass
    if video is not None:
        w, h = int(video.get("width") or 0), int(video.get("height") or 0)
        out["coded_width"], out["coded_height"] = w, h
        sar = _ratio((video.get("sample_aspect_ratio") or "1:1").replace(":", "/")) or 1.0
        out["sample_aspect_ratio"] = round(sar, 6)
        disp_w = int(round(w * sar)) if sar and abs(sar - 1.0) > 1e-6 else w
        rot = rotation_of(video)
        out["rotation"] = rot
        if rot in (90, 270):
            disp_w, h = h, disp_w
        out["width"], out["height"] = disp_w, h
        fps = _ratio(video.get("avg_frame_rate")) or _ratio(video.get("r_frame_rate"))
        out["fps"] = round(fps, 6) if fps else None
        out["video_codec"] = video.get("codec_name")
        out["pix_fmt"] = video.get("pix_fmt")
        if video.get("nb_frames"):
            try:
                out["nb_frames"] = int(video["nb_frames"])
            except ValueError:
                pass
    return out


def media_info(path: str | os.PathLike) -> dict:
    return media_info_from_probe(probe(path), reference=Path(path).name)


# ---------------------------------------------------------------- frames

def analysis_size(width: int, height: int, target_width: int) -> tuple[int, int]:
    """Even (w, h) close to target_width that keeps the display aspect ratio."""
    if not width or not height:
        raise ValueError("unknown frame size")
    w = max(2, int(target_width) // 2 * 2)
    h = max(2, int(round(w * height / width / 2.0)) * 2)
    return w, h


def _frame_argv(path: str, size: tuple[int, int], pix_fmt: str, fps: float | None,
                start_s: float | None, duration_s: float | None, max_frames: int | None) -> list[str]:
    argv = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error"]
    if start_s:
        argv += ["-ss", f"{start_s:.6f}"]
    argv += ["-i", str(path), "-map", "0:v:0", "-an", "-sn"]
    if duration_s:
        argv += ["-t", f"{duration_s:.6f}"]
    filters = []
    if fps:
        filters.append(f"fps={fps:.6f}")
    filters.append(f"scale={size[0]}:{size[1]}:flags=area")
    argv += ["-vf", ",".join(filters)]
    if max_frames:
        argv += ["-frames:v", str(int(max_frames))]
    argv += ["-f", "rawvideo", "-pix_fmt", pix_fmt, "-"]
    return argv


def iter_frames(path: str | os.PathLike, width: int = 160, pix_fmt: str = "gray", fps: float | None = None,
                start_s: float | None = None, duration_s: float | None = None, max_frames: int | None = None,
                info: dict | None = None) -> Iterator[tuple[float, np.ndarray]]:
    """Yield (time_s, frame) pairs. Frames are uint8, shape (h, w) for gray or (h, w, 3) for rgb24.

    Time stamps are index / rate (+ start_s): ffmpeg outputs a constant-rate stream at the source's
    average rate (or at ``fps`` when given), so variable-frame-rate sources get frames duplicated or
    dropped to that rate.
    """
    if pix_fmt not in {"gray", "rgb24"}:
        raise ValueError("pix_fmt must be 'gray' or 'rgb24'")
    info = info or media_info(path)
    size = analysis_size(info["width"], info["height"], width)
    rate = fps or info.get("fps") or 25.0
    channels = 1 if pix_fmt == "gray" else 3
    frame_bytes = size[0] * size[1] * channels
    argv = _frame_argv(str(path), size, pix_fmt, fps, start_s, duration_s, max_frames)
    require("ffmpeg")
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
    i = 0
    try:
        assert proc.stdout is not None
        while True:
            buf = proc.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            arr = np.frombuffer(buf, dtype=np.uint8)
            arr = arr.reshape(size[1], size[0]) if channels == 1 else arr.reshape(size[1], size[0], 3)
            yield (start_s or 0.0) + i / rate, arr
            i += 1
    finally:
        if proc.stdout:
            proc.stdout.close()
        err = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
        if proc.stderr:
            proc.stderr.close()
        code = proc.wait()
        if code not in (0, None) and i == 0:
            raise RuntimeError(f"ffmpeg could not decode {path}: {err.strip()[-400:]}")


def read_frames(path: str | os.PathLike, width: int = 160, pix_fmt: str = "gray", fps: float | None = None,
                start_s: float | None = None, duration_s: float | None = None, max_frames: int | None = None,
                info: dict | None = None) -> tuple[np.ndarray, np.ndarray]:
    """All frames stacked: (frames, times). Use iter_frames for long videos at large sizes."""
    times, frames = [], []
    for t, f in iter_frames(path, width, pix_fmt, fps, start_s, duration_s, max_frames, info):
        times.append(t)
        frames.append(f)
    if not frames:
        raise RuntimeError(f"no frames decoded from {path}")
    return np.stack(frames), np.asarray(times, dtype=np.float64)


def read_frame_at(path: str | os.PathLike, t_s: float, width: int = 320, pix_fmt: str = "rgb24",
                  info: dict | None = None) -> np.ndarray:
    """One frame at (or just after) t_s, accurate seek."""
    info = info or media_info(path)
    size = analysis_size(info["width"], info["height"], width)
    argv = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0.0, t_s):.6f}",
            "-i", str(path), "-map", "0:v:0", "-frames:v", "1", "-vf", f"scale={size[0]}:{size[1]}:flags=area",
            "-f", "rawvideo", "-pix_fmt", pix_fmt, "-"]
    data = run(argv, timeout=120).stdout
    ch = 1 if pix_fmt == "gray" else 3
    need = size[0] * size[1] * ch
    if len(data) < need:
        raise RuntimeError(f"no frame at {t_s:.3f}s")
    arr = np.frombuffer(data[:need], dtype=np.uint8)
    return arr.reshape(size[1], size[0]) if ch == 1 else arr.reshape(size[1], size[0], 3)


# ---------------------------------------------------------------- audio

def read_audio(path: str | os.PathLike, sr: int = 16000, start_s: float | None = None,
               duration_s: float | None = None) -> np.ndarray:
    """Decode the first audio stream to mono float32 at ``sr`` Hz. Raises RuntimeError if there is none."""
    argv = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error"]
    if start_s:
        argv += ["-ss", f"{start_s:.6f}"]
    argv += ["-i", str(path), "-map", "0:a:0", "-vn", "-sn"]
    if duration_s:
        argv += ["-t", f"{duration_s:.6f}"]
    argv += ["-ac", "1", "-ar", str(int(sr)), "-f", "f32le", "-"]
    proc = run(argv, timeout=600, check=False)
    if proc.returncode != 0:
        raise RuntimeError("no decodable audio stream: " + proc.stderr.decode("utf-8", "replace").strip()[-300:])
    return np.frombuffer(proc.stdout, dtype="<f4").astype(np.float32, copy=True)


def frame_signal(x: np.ndarray, frame: int, hop: int) -> np.ndarray:
    """Split a 1-D signal into overlapping frames (n_frames, frame), zero-padding the tail."""
    if len(x) < frame:
        x = np.pad(x, (0, frame - len(x)))
    n = 1 + (len(x) - frame) // hop
    idx = np.arange(frame)[None, :] + hop * np.arange(n)[:, None]
    return x[idx]


# ---------------------------------------------------------------- shots helpers

def shots_from_json(data: Any) -> list[dict]:
    """Accept a detect_shots result, an evidence.json or a bare list and return the shot list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("shots"), list):
            return data["shots"]
    raise ValueError("no 'shots' list found")


def whole_clip_shot(duration_s: float) -> list[dict]:
    return [{"index": 0, "start_s": 0.0, "end_s": float(duration_s), "duration_s": float(duration_s)}]


# ---------------------------------------------------------------- siblings and output

def kebab(identity: str) -> str:
    return identity.replace("_", "-")


def sibling_dirs(identity: str) -> list[Path]:
    """Directories where a sibling package may live: next to this package (catalogue or .baltor/lib
    layout, kebab or snake name) and in VIDEO_RE_LIB (os.pathsep-separated roots)."""
    here = Path(__file__).resolve().parent
    roots = [here.parent]
    for extra in os.environ.get("VIDEO_RE_LIB", "").split(os.pathsep):
        if extra:
            roots.append(Path(extra))
    out = []
    for root in roots:
        for name in (kebab(identity), identity):
            d = root / name
            if (d / f"{identity}.py").exists():
                out.append(d)
    return out


def import_sibling(identity: str):
    """Import a video_re_* module from sys.path or from a sibling package directory."""
    try:
        return importlib.import_module(identity)
    except ImportError:
        pass
    for d in sibling_dirs(identity):
        if str(d) not in sys.path:
            sys.path.append(str(d))
        try:
            return importlib.import_module(identity)
        except ImportError:
            continue
    raise ImportError(f"{identity} is not importable; place the package next to this one or set VIDEO_RE_LIB")


def unavailable(reason: str, **extra: Any) -> dict:
    return {"status": "unavailable", "reason": reason, **extra}


def clean(obj: Any, nd: int = 4) -> Any:
    """Round floats, turn numpy scalars into Python numbers and NaN/inf into None, recursively."""
    if isinstance(obj, dict):
        return {str(k): clean(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v, nd) for v in obj]
    if isinstance(obj, np.ndarray):
        return [clean(v, nd) for v in obj.tolist()]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        f = float(obj)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, nd)
    return obj


def dump_json(obj: Any, out: str | os.PathLike | None = None) -> str:
    text = json.dumps(clean(obj), indent=2, ensure_ascii=False) + "\n"
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return text


def load_json(path: str | os.PathLike) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
