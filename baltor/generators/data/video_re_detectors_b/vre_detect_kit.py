"""vre_detect_kit: shared helpers for the video_re_detect_* detectors (layers, motion, transitions, text).

Vendored: every detector package ships an identical copy of this file, so each
package works on its own after ``baltor_catalog.py place``. It needs only the
standard library and numpy at import time; ffmpeg/ffprobe are run as
subprocesses only when a detector is pointed at a video file.

Conventions
-----------
* Frames are numpy arrays: RGB ``(H, W, 3)`` uint8 or grey ``(H, W)`` uint8, stacked as
  ``(N, H, W[, 3])``. Grey levels are 0-255; luma uses Rec. 601 weights on the
  gamma-encoded values (what ffmpeg's ``gray`` output gives).
* Bounding boxes are ``[x, y, w, h]`` in pixels of the analysed frame (origin top-left),
  as the detection envelope requires. ``bbox_ratio`` divides by the analysed frame size.
* Motion vectors are ``(dx, dy)`` in analysed pixels: content in the later frame sits at
  ``p + (dx, dy)`` when it was at ``p`` in the earlier one (positive dx = content moves right).
* A similarity "scale" > 1 means content grows from one frame to the next (zoom in).

Everything here is measurement. Nothing stores, reuses or republishes the analysed
footage: detectors return numbers, boxes and labels only.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

import numpy as np

KIT_VERSION = "1.0.0"
ENVELOPE_SPEC = "baltor.video-detection/v1"
LUMA_601 = np.array([0.299, 0.587, 0.114], dtype=np.float32)


class ToolMissing(RuntimeError):
    """ffmpeg / ffprobe / another external program is not on PATH."""


# =============================================================== processes and probing

def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def tool_version(tool: str) -> str | None:
    if not have(tool):
        return None
    flag = "-version" if tool in {"ffmpeg", "ffprobe"} else "--version"
    try:
        proc = subprocess.run([tool, flag], capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL)
    except Exception:  # noqa: BLE001
        return None
    lines = (proc.stdout or proc.stderr or "").strip().splitlines()
    if not lines:
        return None
    words = lines[0].split()
    for i, w in enumerate(words[:-1]):
        if w == "version":
            return words[i + 1]
    return lines[0][:60]


def tool_versions(extra_tools: Iterable[str] = (), file_mode: bool = True) -> dict[str, str]:
    out: dict[str, str] = {}
    if file_mode:
        for t in ("ffmpeg", "ffprobe", *extra_tools):
            v = tool_version(t)
            if v:
                out[t] = v
    out["numpy"] = np.__version__
    out["python"] = sys.version.split()[0]
    out["vre_detect_kit"] = KIT_VERSION
    return out


def _ratio(text: Any) -> float | None:
    if text in (None, "", "0/0", "N/A"):
        return None
    s = str(text)
    try:
        if "/" in s:
            a, b = s.split("/", 1)
            return float(a) / float(b) if float(b) else None
        return float(s)
    except ValueError:
        return None


def media_info(path: str | Path) -> dict:
    """Display width/height (rotation and sample aspect applied), fps, duration, has_audio via ffprobe."""
    if not have("ffprobe"):
        raise ToolMissing("ffprobe is not installed or not on PATH")
    proc = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams",
                           str(path)], capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {proc.stderr.strip()[-300:]}")
    info = json.loads(proc.stdout or "{}")
    streams = info.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"
                  and not (s.get("disposition") or {}).get("attached_pic")), None)
    if video is None:
        raise RuntimeError("no video stream")
    w, h = int(video.get("width") or 0), int(video.get("height") or 0)
    sar = _ratio(str(video.get("sample_aspect_ratio") or "1:1").replace(":", "/")) or 1.0
    if abs(sar - 1.0) > 1e-6:
        w = int(round(w * sar))
    rot = 0.0
    if "rotate" in (video.get("tags") or {}):
        rot = _ratio(video["tags"]["rotate"]) or 0.0
    for sd in video.get("side_data_list") or []:
        if "rotation" in sd:
            rot = _ratio(sd["rotation"]) or rot
    if int(round(rot)) % 180 == 90:
        w, h = h, w
    fmt = info.get("format") or {}
    duration = _ratio(fmt.get("duration")) or _ratio(video.get("duration"))
    return {
        "reference": Path(path).name,
        "width": w, "height": h,
        "fps": _ratio(video.get("avg_frame_rate")) or _ratio(video.get("r_frame_rate")),
        "duration_s": duration,
        "has_audio": any(s.get("codec_type") == "audio" for s in streams),
    }


def analysis_size(width: int, height: int, long_side: int) -> tuple[int, int]:
    """Even (w, h) whose longer side is ``long_side``, keeping the display aspect ratio."""
    if not width or not height:
        raise ValueError("unknown frame size")
    if width >= height:
        w = max(2, int(long_side) // 2 * 2)
        h = max(2, int(round(w * height / width / 2.0)) * 2)
    else:
        h = max(2, int(long_side) // 2 * 2)
        w = max(2, int(round(h * width / height / 2.0)) * 2)
    return w, h


def iter_frames(path: str | Path, long_side: int = 320, fps: float | None = None, pix_fmt: str = "rgb24",
                start_s: float | None = None, duration_s: float | None = None,
                info: dict | None = None) -> Iterator[np.ndarray]:
    """Decode frames with ffmpeg (rawvideo through a pipe), scaled with ``flags=area``.

    ``fps=None`` keeps the source's average rate (constant-rate output: variable-rate
    sources get frames duplicated or dropped to that rate).
    """
    if pix_fmt not in {"rgb24", "gray"}:
        raise ValueError("pix_fmt must be rgb24 or gray")
    if not have("ffmpeg"):
        raise ToolMissing("ffmpeg is not installed or not on PATH")
    info = info or media_info(path)
    w, h = analysis_size(info["width"], info["height"], long_side)
    argv = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error"]
    if start_s:
        argv += ["-ss", f"{start_s:.6f}"]
    argv += ["-i", str(path), "-map", "0:v:0", "-an", "-sn"]
    if duration_s:
        argv += ["-t", f"{duration_s:.6f}"]
    vf = ([f"fps={fps:.6f}"] if fps else []) + [f"scale={w}:{h}:flags=area"]
    argv += ["-vf", ",".join(vf), "-f", "rawvideo", "-pix_fmt", pix_fmt, "-"]
    ch = 3 if pix_fmt == "rgb24" else 1
    nbytes = w * h * ch
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
    n = 0
    try:
        assert proc.stdout is not None
        while True:
            buf = proc.stdout.read(nbytes)
            if len(buf) < nbytes:
                break
            arr = np.frombuffer(buf, dtype=np.uint8)
            yield arr.reshape(h, w, 3) if ch == 3 else arr.reshape(h, w)
            n += 1
    finally:
        if proc.stdout:
            proc.stdout.close()
        err = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
        if proc.stderr:
            proc.stderr.close()
        code = proc.wait()
        if code not in (0, None) and n == 0:
            raise RuntimeError(f"ffmpeg could not decode {path}: {err.strip()[-300:]}")


def read_frames(path: str | Path, long_side: int = 320, fps: float | None = None, pix_fmt: str = "rgb24",
                start_s: float | None = None, duration_s: float | None = None,
                info: dict | None = None) -> np.ndarray:
    frames = list(iter_frames(path, long_side, fps, pix_fmt, start_s, duration_s, info))
    if not frames:
        raise RuntimeError(f"no frames decoded from {path}")
    return np.stack(frames)


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def shots_from(data: Any) -> list[tuple[float, float]]:
    """(start_s, end_s) pairs from an evidence.json (video_re_evidence), a shots list or an envelope."""
    items: Any = data
    if isinstance(data, dict):
        if isinstance(data.get("shots"), list):
            items = data["shots"]
        elif isinstance(data.get("results"), list):
            items = [{"start_s": r.get("t_start_s"), "end_s": r.get("t_end_s")} for r in data["results"]]
        else:
            items = []
    out = []
    for it in items or []:
        if isinstance(it, dict) and it.get("start_s") is not None and it.get("end_s") is not None:
            out.append((float(it["start_s"]), float(it["end_s"])))
        elif isinstance(it, (list, tuple)) and len(it) >= 2:
            out.append((float(it[0]), float(it[1])))
    return sorted(out)


def onsets_from(data: Any) -> list[float]:
    """Onset/beat times from an evidence.json (audio.onsets_s) or a bare list of seconds."""
    if isinstance(data, list):
        return sorted(float(x) for x in data)
    if isinstance(data, dict):
        audio = data.get("audio") or {}
        if isinstance(audio.get("onsets_s"), list):
            return sorted(float(x) for x in audio["onsets_s"])
        if isinstance(data.get("onsets_s"), list):
            return sorted(float(x) for x in data["onsets_s"])
    return []


# =============================================================== envelope

def clean(obj: Any, nd: int = 4) -> Any:
    """numpy -> Python, floats rounded, NaN/inf -> None, recursively."""
    if isinstance(obj, dict):
        return {str(k): clean(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v, nd) for v in obj]
    if isinstance(obj, np.ndarray):
        return [clean(v, nd) for v in obj.tolist()]
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        f = float(obj)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, nd)
    return obj


def result(label: str, confidence: float, *, t_start_s: float | None = None, t_end_s: float | None = None,
           value: Any = None, bbox: Iterable[float] | None = None, evidence: str | None = None) -> dict:
    """One entry of the envelope's ``results`` list."""
    r: dict[str, Any] = {"label": str(label), "confidence": float(min(1.0, max(0.0, confidence)))}
    if t_start_s is not None:
        r["t_start_s"] = max(0.0, float(t_start_s))
    if t_end_s is not None:
        r["t_end_s"] = max(0.0, float(t_end_s))
    if value is not None:
        r["value"] = value
    if bbox is not None:
        r["bbox"] = [float(v) for v in bbox]
    if evidence:
        r["evidence"] = str(evidence)[:400]
    return r


def make_envelope(detector: str, version: str, *, source: dict, status: str, results: list, payload: Any,
                  params: dict, tools: dict | None = None, errors: list | None = None) -> dict:
    src = {"reference": str(source.get("reference") or "<array>")}
    for k in ("compare_to",):
        if source.get(k):
            src[k] = str(source[k])
    for k in ("duration_s", "fps"):
        v = source.get(k)
        if v is not None and np.isfinite(v) and v >= 0:
            src[k] = float(v)
    for k in ("width", "height"):
        v = source.get(k)
        if v:
            src[k] = int(v)
    env = {"spec": ENVELOPE_SPEC, "detector": detector, "version": version, "source": src, "status": status,
           "results": results, "payload": payload, "params": params, "tools": tools or {},
           "errors": [str(e) for e in (errors or [])]}
    return clean(env)


class Detector:
    """Wires a detector's ``analyse`` function to array input, video files and a CLI.

    ``analyse(frames, fps, params, ctx)`` gets frames (an array, or an iterator of frames when
    ``streaming`` is true), the frame rate and the merged parameters, and returns a dict with
    ``status``, ``results``, ``payload`` and optional ``errors``. ``ctx`` carries ``t0`` (time of
    the first frame), ``shots`` and ``onsets`` (from ``--evidence``), ``source`` (media info) and
    ``px_scale`` (source pixels per analysed pixel).
    """

    def __init__(self, identity: str, version: str, defaults: dict, analyse: Callable, *, long_side: int = 320,
                 fps: float | None = 10.0, pix_fmt: str = "rgb24", streaming: bool = False,
                 max_seconds: float = 90.0, extra_tools: tuple[str, ...] = (), description: str = ""):
        self.identity, self.version, self.defaults = identity, version, dict(defaults)
        self.analyse_fn = analyse
        self.long_side, self.fps, self.pix_fmt = long_side, fps, pix_fmt
        self.streaming, self.max_seconds, self.extra_tools = streaming, max_seconds, extra_tools
        self.description = description

    def params(self, overrides: dict) -> dict:
        unknown = sorted(set(overrides) - set(self.defaults))
        if unknown:
            raise TypeError(f"{self.identity}: unknown parameter(s) {unknown}")
        p = dict(self.defaults)
        p.update(overrides)
        return p

    def detect(self, frames: Any, fps: float, *, reference: str = "<array>", t0: float = 0.0,
               source: dict | None = None, shots: list | None = None, onsets: list | None = None,
               px_scale: float = 1.0, file_mode: bool = False, extra_params: dict | None = None,
               errors: list | None = None, **overrides: Any) -> dict:
        p = self.params(overrides)
        src = dict(source or {})
        src.setdefault("reference", reference)
        if not self.streaming:
            frames = np.asarray(frames)
            if frames.ndim < 3:
                raise ValueError("frames must be (N, H, W) or (N, H, W, 3)")
            src.setdefault("width", frames.shape[2])
            src.setdefault("height", frames.shape[1])
            src.setdefault("duration_s", frames.shape[0] / fps if fps else None)
            hw = frames.shape[1:3]
        else:
            hw = None
        src.setdefault("fps", fps)
        ctx = {"t0": float(t0), "shots": shots, "onsets": onsets, "source": src, "px_scale": float(px_scale)}
        errs = list(errors or [])
        try:
            out = self.analyse_fn(frames, float(fps), p, ctx)
        except Exception as exc:  # noqa: BLE001 - an envelope always comes back
            out = {"status": "error", "results": [], "payload": None, "errors": [f"{type(exc).__name__}: {exc}"]}
        errs += out.get("errors") or []
        params = {**p, **(extra_params or {}), "fps": float(fps), "px_scale": float(px_scale)}
        if hw is None:
            hw = ctx.get("frame_hw")
        if hw is not None:
            params["analysis_height"], params["analysis_width"] = int(hw[0]), int(hw[1])
        return make_envelope(self.identity, self.version, source=src, status=out.get("status", "ok"),
                             results=out.get("results") or [], payload=out.get("payload"), params=params,
                             tools=tool_versions(self.extra_tools, file_mode=file_mode), errors=errs)

    def detect_file(self, path: str | Path, *, long_side: int | None = None, fps: float | None = -1.0,
                    start_s: float | None = None, duration_s: float | None = None,
                    max_seconds: float | None = None, evidence: str | Path | None = None,
                    **overrides: Any) -> dict:
        long_side = long_side or self.long_side
        fps = self.fps if fps == -1.0 else fps
        max_seconds = self.max_seconds if max_seconds is None else max_seconds
        ref = Path(path).name
        errors: list[str] = []
        try:
            info = media_info(path)
        except ToolMissing as exc:
            return self._fail("unavailable", ref, str(exc), overrides)
        except Exception as exc:  # noqa: BLE001
            return self._fail("error", ref, f"probe failed: {exc}", overrides)
        rate = fps or info.get("fps") or 25.0
        dur = duration_s
        total = info.get("duration_s")
        if max_seconds and (dur is None or dur > max_seconds):
            remaining = (total - (start_s or 0.0)) if total else None
            if remaining is None or remaining > max_seconds:
                dur = max_seconds
                errors.append(f"analysed only {max_seconds:.0f} s from {start_s or 0.0:.2f} s "
                              f"(use --max-seconds 0 or --start/--duration for the rest)")
        aw, ah = analysis_size(info["width"], info["height"], long_side)
        px_scale = info["width"] / aw
        ctx_shots = ctx_onsets = None
        if evidence:
            try:
                data = load_json(evidence)
                ctx_shots = shots_from(data) or None
                ctx_onsets = onsets_from(data) or None
            except Exception as exc:  # noqa: BLE001
                errors.append(f"could not read evidence {evidence}: {exc}")
        source = {k: info[k] for k in ("reference", "width", "height", "fps", "duration_s")}
        try:
            it = iter_frames(path, long_side, fps, self.pix_fmt, start_s, dur, info)
            frames = it if self.streaming else np.stack(list(it))
        except ToolMissing as exc:
            return self._fail("unavailable", ref, str(exc), overrides)
        except Exception as exc:  # noqa: BLE001
            return self._fail("error", ref, f"decode failed: {exc}", overrides)
        env = self.detect(frames, rate, reference=ref, t0=start_s or 0.0, source=source, shots=ctx_shots,
                          onsets=ctx_onsets, px_scale=px_scale, file_mode=True, errors=errors,
                          extra_params={"long_side": long_side, "decode_fps": fps or "source",
                                        "start_s": start_s or 0.0, "duration_s": dur}, **overrides)
        if errors and env["status"] == "ok" and any(e.startswith("analysed only") for e in errors):
            env["status"] = "partial"
        return env

    def _fail(self, status: str, ref: str, message: str, overrides: dict) -> dict:
        return make_envelope(self.identity, self.version, source={"reference": ref}, status=status, results=[],
                             payload=None, params=self.params(overrides),
                             tools=tool_versions(self.extra_tools), errors=[message])

    def main(self, argv: list[str] | None = None) -> int:
        ap = argparse.ArgumentParser(prog=self.identity, description=self.description or self.identity)
        ap.add_argument("video", help="video file to analyse (decoded with ffmpeg; nothing is copied or kept)")
        ap.add_argument("--long-side", type=int, default=self.long_side,
                        help=f"analysis size: longer side in pixels (default {self.long_side})")
        ap.add_argument("--fps", type=float, default=self.fps if self.fps else 0.0,
                        help="analysis frame rate; 0 = source rate (default %(default)s)")
        ap.add_argument("--start", type=float, default=None, help="start time in seconds")
        ap.add_argument("--duration", type=float, default=None, help="seconds to analyse")
        ap.add_argument("--max-seconds", type=float, default=self.max_seconds,
                        help="cap on analysed seconds; 0 = no cap (default %(default)s)")
        ap.add_argument("--evidence", default=None,
                        help="optional evidence.json (video_re_evidence) or shots/onsets JSON to reuse")
        ap.add_argument("--param", action="append", default=[], metavar="NAME=JSON",
                        help="override a threshold, e.g. --param min_area_ratio=0.002")
        ap.add_argument("--out", default=None, help="write the envelope here instead of stdout")
        a = ap.parse_args(argv)
        overrides = {}
        for item in a.param:
            name, _, val = item.partition("=")
            try:
                overrides[name] = json.loads(val)
            except json.JSONDecodeError:
                overrides[name] = val
        env = self.detect_file(a.video, long_side=a.long_side, fps=a.fps or None, start_s=a.start,
                               duration_s=a.duration, max_seconds=a.max_seconds or 0, evidence=a.evidence,
                               **overrides)
        text = json.dumps(env, indent=2, ensure_ascii=False) + "\n"
        if a.out:
            Path(a.out).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0 if env["status"] in {"ok", "partial"} else 1


def validate_with_schema(instance: Any, schema_path: str | Path) -> list[str]:
    """Error messages from jsonschema (Draft 2020-12). Raises ImportError when jsonschema is absent."""
    import jsonschema  # noqa: PLC0415 - optional, used by tests

    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    v = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in v.iter_errors(instance)]


# =============================================================== pixels and colour

def as_gray(frames: np.ndarray) -> np.ndarray:
    """float32 grey 0-255 from RGB (..., 3) or grey input."""
    a = np.asarray(frames)
    if a.ndim >= 3 and a.shape[-1] == 3:
        return (a.astype(np.float32) @ LUMA_601).astype(np.float32)
    return a.astype(np.float32)


def as_rgb(frames: np.ndarray) -> np.ndarray:
    a = np.asarray(frames)
    if a.shape[-1] == 3 and a.ndim >= 3:
        return a
    return np.repeat(a[..., None], 3, axis=-1)


def hexcolor(rgb: Iterable[float]) -> str:
    r, g, b = (int(round(min(255.0, max(0.0, float(c))))) for c in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def srgb_to_linear(c: np.ndarray) -> np.ndarray:
    c = np.asarray(c, dtype=np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def relative_luminance(rgb: Iterable[float]) -> float:
    """WCAG 2.x relative luminance of an sRGB colour given as 0-255 values."""
    lin = srgb_to_linear(np.asarray(list(rgb), dtype=np.float64))
    return float(0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2])


def contrast_ratio(c1: Iterable[float], c2: Iterable[float]) -> float:
    """WCAG contrast ratio (1-21) between two sRGB colours."""
    l1, l2 = relative_luminance(c1), relative_luminance(c2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def color_name(rgb: Iterable[float]) -> str:
    """Coarse colour word (black, white, grey, red, orange, yellow, green, cyan, blue, purple, pink)."""
    r, g, b = (float(c) / 255.0 for c in rgb)
    mx, mn = max(r, g, b), min(r, g, b)
    if mx < 0.12:
        return "black"
    if mx - mn < 0.12:
        return "white" if mn > 0.85 else "grey"
    d = mx - mn
    if mx == r:
        hue = (60 * ((g - b) / d)) % 360
    elif mx == g:
        hue = 60 * ((b - r) / d) + 120
    else:
        hue = 60 * ((r - g) / d) + 240
    for limit, name in ((15, "red"), (40, "orange"), (70, "yellow"), (165, "green"), (195, "cyan"),
                        (255, "blue"), (290, "purple"), (335, "pink"), (360, "red")):
        if hue < limit:
            return name
    return "red"


def saturation_value(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """HSV saturation and value in 0-1 for RGB uint8 input."""
    a = np.asarray(rgb, dtype=np.float32) / 255.0
    mx = a.max(axis=-1)
    mn = a.min(axis=-1)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    return sat.astype(np.float32), mx.astype(np.float32)


# =============================================================== filters and morphology

def box_mean(img: np.ndarray, ry: int, rx: int | None = None) -> np.ndarray:
    """Mean over a (2ry+1) x (2rx+1) window on the last two axes, edges replicated (integral image)."""
    rx = ry if rx is None else rx
    a = np.asarray(img, dtype=np.float64)
    nd = a.ndim
    if ry > 0:
        pad = [(0, 0)] * (nd - 2) + [(ry + 1, ry), (0, 0)]
        c = np.cumsum(np.pad(a, pad, mode="edge"), axis=-2)
        a = (c[..., 2 * ry + 1:, :] - c[..., :-2 * ry - 1, :]) / (2 * ry + 1)
    if rx > 0:
        pad = [(0, 0)] * (nd - 1) + [(rx + 1, rx)]
        c = np.cumsum(np.pad(a, pad, mode="edge"), axis=-1)
        a = (c[..., 2 * rx + 1:] - c[..., :-2 * rx - 1]) / (2 * rx + 1)
    return a.astype(np.float32)


def local_mean_var(img: np.ndarray, r: int) -> tuple[np.ndarray, np.ndarray]:
    m = box_mean(img, r)
    m2 = box_mean(np.asarray(img, dtype=np.float64) ** 2, r)
    return m, np.maximum(m2 - m.astype(np.float64) ** 2, 0.0).astype(np.float32)


def dilate(mask: np.ndarray, ry: int, rx: int | None = None) -> np.ndarray:
    return box_mean(np.asarray(mask, dtype=np.float32), ry, rx) > 1e-6


def erode(mask: np.ndarray, ry: int, rx: int | None = None) -> np.ndarray:
    return box_mean(np.asarray(mask, dtype=np.float32), ry, rx) > 1 - 1e-6


def gradients(gray: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Sobel gradients (levels per pixel) of a 2-D grey image, edges replicated."""
    p = np.pad(np.asarray(gray, dtype=np.float32), 1, mode="edge")
    gx = ((p[:-2, 2:] + 2 * p[1:-1, 2:] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[1:-1, :-2] + p[2:, :-2])) / 8.0
    gy = ((p[2:, :-2] + 2 * p[2:, 1:-1] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[:-2, 1:-1] + p[:-2, 2:])) / 8.0
    return gx, gy


def grad_mag(gray: np.ndarray) -> np.ndarray:
    gx, gy = gradients(gray)
    return np.hypot(gx, gy)


def otsu(values: np.ndarray, lo: float = 0.0, hi: float = 255.0, bins: int = 256) -> float:
    v = np.asarray(values, dtype=np.float64).ravel()
    if v.size == 0:
        return (lo + hi) / 2
    hist, edges = np.histogram(v, bins=bins, range=(lo, hi))
    centers = (edges[:-1] + edges[1:]) / 2
    w0 = np.cumsum(hist)
    w1 = w0[-1] - w0
    s0 = np.cumsum(hist * centers)
    m0 = s0 / np.maximum(w0, 1)
    m1 = (s0[-1] - s0) / np.maximum(w1, 1)
    between = w0 * w1 * (m0 - m1) ** 2
    return float(centers[int(np.argmax(between))])


def components(mask: np.ndarray, min_area: int = 1) -> tuple[np.ndarray, list[dict]]:
    """8-connected components by run-length union-find. Returns (labels, [{label, bbox, area}])."""
    m = np.asarray(mask, dtype=bool)
    H, W = m.shape
    parent: list[int] = [0]

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    runs: list[tuple[int, int, int, int]] = []
    prev: list[tuple[int, int, int]] = []
    pad = np.zeros(W + 2, dtype=np.int8)
    for y in range(H):
        row = m[y]
        if not row.any():
            prev = []
            continue
        pad[1:-1] = row
        d = np.diff(pad)
        starts = np.flatnonzero(d == 1)
        ends = np.flatnonzero(d == -1)
        cur = []
        for s, e in zip(starts.tolist(), ends.tolist()):
            lab = 0
            for ps, pe, pl in prev:
                if ps <= e and pe >= s:
                    if lab == 0:
                        lab = find(pl)
                    else:
                        a, b = find(lab), find(pl)
                        if a != b:
                            parent[max(a, b)] = min(a, b)
                            lab = min(a, b)
            if lab == 0:
                lab = len(parent)
                parent.append(lab)
            cur.append((s, e, lab))
            runs.append((y, s, e, lab))
        prev = cur
    labels = np.zeros((H, W), dtype=np.int32)
    remap: dict[int, int] = {}
    stats: dict[int, list[int]] = {}
    for y, s, e, lab in runs:
        root = find(lab)
        if root not in remap:
            remap[root] = len(remap) + 1
            stats[remap[root]] = [s, y, e - 1, y, 0]
        k = remap[root]
        labels[y, s:e] = k
        st = stats[k]
        st[0] = min(st[0], s)
        st[2] = max(st[2], e - 1)
        st[3] = y
        st[4] += e - s
    comps = []
    for k, (x0, y0, x1, y1, area) in stats.items():
        if area >= min_area:
            comps.append({"label": k, "bbox": [x0, y0, x1 - x0 + 1, y1 - y0 + 1], "area": area})
    comps.sort(key=lambda c: -c["area"])
    return labels, comps


def bbox_of(mask: np.ndarray) -> list[int] | None:
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)]


def iou(a: Iterable[float], b: Iterable[float]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return float(inter / union) if union > 0 else 0.0


def bbox_ratio(bbox: Iterable[float], w: int, h: int) -> list[float]:
    x, y, bw, bh = bbox
    return [x / w, y / h, bw / w, bh / h]


def ncc(a: np.ndarray, b: np.ndarray, mask: np.ndarray | None = None) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if mask is not None:
        a, b = a[mask], b[mask]
    a = a - a.mean()
    b = b - b.mean()
    den = math.sqrt(float((a * a).sum() * (b * b).sum()))
    return float((a * b).sum() / den) if den > 1e-9 else 0.0


def kmeans(x: np.ndarray, k: int, iters: int = 25) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic k-means (farthest-point initialisation). Returns (centres, labels)."""
    x = np.asarray(x, dtype=np.float64)
    if len(x) == 0:
        return np.zeros((0, x.shape[1] if x.ndim > 1 else 1)), np.zeros(0, dtype=int)
    k = max(1, min(k, len(x)))
    centres = [x[np.argmin(x.sum(axis=1))]]
    for _ in range(1, k):
        d = np.min([((x - c) ** 2).sum(axis=1) for c in centres], axis=0)
        centres.append(x[int(np.argmax(d))])
    c = np.array(centres)
    lab = np.zeros(len(x), dtype=int)
    for _ in range(iters):
        d = ((x[:, None, :] - c[None, :, :]) ** 2).sum(axis=2)
        new = np.argmin(d, axis=1)
        for j in range(k):
            if np.any(new == j):
                c[j] = x[new == j].mean(axis=0)
        if np.array_equal(new, lab):
            break
        lab = new
    return c, lab


# =============================================================== resampling and warps

def bilinear_sample(img: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Sample img (H, W[, C]) at float coordinates (clamped to the border)."""
    a = np.asarray(img, dtype=np.float32)
    H, W = a.shape[:2]
    xs = np.clip(xs, 0, W - 1)
    ys = np.clip(ys, 0, H - 1)
    x0 = np.floor(xs).astype(np.int64)
    y0 = np.floor(ys).astype(np.int64)
    x1 = np.minimum(x0 + 1, W - 1)
    y1 = np.minimum(y0 + 1, H - 1)
    fx = (xs - x0).astype(np.float32)
    fy = (ys - y0).astype(np.float32)
    if a.ndim == 3:
        fx = fx[..., None]
        fy = fy[..., None]
    top = a[y0, x0] * (1 - fx) + a[y0, x1] * fx
    bot = a[y1, x0] * (1 - fx) + a[y1, x1] * fx
    return top * (1 - fy) + bot * fy


def resize(img: np.ndarray, out_h: int, out_w: int) -> np.ndarray:
    """Bilinear resize with pixel-centre alignment (float32 output)."""
    a = np.asarray(img)
    H, W = a.shape[:2]
    ys = (np.arange(out_h) + 0.5) * H / out_h - 0.5
    xs = (np.arange(out_w) + 0.5) * W / out_w - 0.5
    gx, gy = np.meshgrid(xs, ys)
    return bilinear_sample(a, gx, gy)


def downsample(img: np.ndarray, f: int) -> np.ndarray:
    """Block mean by an integer factor over the first two axes (crops the remainder)."""
    a = np.asarray(img, dtype=np.float32)
    if f <= 1:
        return a
    H, W = a.shape[0] // f * f, a.shape[1] // f * f
    a = a[:H, :W]
    return a.reshape(H // f, f, W // f, f, *a.shape[2:]).mean(axis=(1, 3))


def warp_similarity(img: np.ndarray, scale: float = 1.0, tx: float = 0.0, ty: float = 0.0,
                    rot_deg: float = 0.0, center: tuple[float, float] | None = None) -> np.ndarray:
    """Content scaled by ``scale`` and rotated about ``center`` then moved by (tx, ty); same output size."""
    a = np.asarray(img)
    H, W = a.shape[:2]
    cx, cy = center if center is not None else ((W - 1) / 2.0, (H - 1) / 2.0)
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    X, Y = gx - cx - tx, gy - cy - ty
    th = math.radians(rot_deg)
    c, s = math.cos(th), math.sin(th)
    xs = (c * X + s * Y) / scale + cx
    ys = (-s * X + c * Y) / scale + cy
    return bilinear_sample(a, xs, ys)


# =============================================================== motion

def hann2d(h: int, w: int) -> np.ndarray:
    return np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)


def phase_correlation(a: np.ndarray, b: np.ndarray, window: bool = True,
                      lowpass: float = 0.15) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Shift of b relative to a by phase correlation on the last two axes (batched).

    Returns (dx, dy, peak). ``b(p) ~ a(p - d)``: content moved by +d. ``peak`` is the height of the
    normalised correlation surface: about 1 for identical content, 0.8 for a shift of a tenth of
    the window, 0.2-0.3 for unrelated textures (so 0.35 is the default reliability cut).
    """
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    H, W = a.shape[-2:]
    a = a - a.mean(axis=(-2, -1), keepdims=True)
    b = b - b.mean(axis=(-2, -1), keepdims=True)
    if window:
        win = hann2d(H, W)
        a = a * win
        b = b * win
    fa = np.fft.rfft2(a)
    fb = np.fft.rfft2(b)
    r = fb * np.conj(fa)
    mag = np.abs(r)
    # whitened cross-power, weighted by a Gaussian low-pass (sigma = lowpass cycles/pixel) so that
    # noise-dominated high frequencies do not flatten the peak; normalised so a perfect match peaks at 1
    fy = np.fft.fftfreq(H)[:, None]
    fx = np.fft.rfftfreq(W)[None, :]
    g = np.exp(-(fx ** 2 + fy ** 2) / (2 * lowpass ** 2)).astype(np.float32)
    gfull = np.exp(-(np.fft.fftfreq(W)[None, :] ** 2 + fy ** 2) / (2 * lowpass ** 2))
    r = r / (mag + 1e-3 * (mag.mean(axis=(-2, -1), keepdims=True) + 1e-9)) * g * (H * W / float(gfull.sum()))
    surf = np.fft.irfft2(r, s=(H, W))
    flat = surf.reshape(*surf.shape[:-2], H * W)
    idx = np.argmax(flat, axis=-1)
    py, px = np.divmod(idx, W)
    peak = np.take_along_axis(flat, idx[..., None], axis=-1)[..., 0]

    def sub(c: np.ndarray, m: np.ndarray, p: np.ndarray) -> np.ndarray:
        den = m - 2 * c + p
        return np.where(np.abs(den) > 1e-9, 0.5 * (m - p) / np.where(np.abs(den) > 1e-9, den, 1.0), 0.0)

    flat_idx = lambda yy, xx: np.take_along_axis(flat, ((yy % H) * W + (xx % W))[..., None], axis=-1)[..., 0]  # noqa: E731
    cx_m, cx_p = flat_idx(py, px - 1), flat_idx(py, px + 1)
    cy_m, cy_p = flat_idx(py - 1, px), flat_idx(py + 1, px)
    dxs = np.clip(sub(peak, cx_m, cx_p), -0.5, 0.5)
    dys = np.clip(sub(peak, cy_m, cy_p), -0.5, 0.5)
    dx = np.where(px > W // 2, px - W, px) + dxs
    dy = np.where(py > H // 2, py - H, py) + dys
    return dx.astype(np.float32), dy.astype(np.float32), peak.astype(np.float32)


def block_grid(h: int, w: int, block: int, step: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    step = step or block
    ys = np.arange(0, max(1, h - block + 1), step)
    xs = np.arange(0, max(1, w - block + 1), step)
    return ys, xs


def block_motion(a: np.ndarray, b: np.ndarray, block: int = 32, step: int | None = None) -> dict:
    """Per-block translation from grey frame a to grey frame b by batched phase correlation.

    Returns centres (N, 2) as (x, y), vectors (N, 2) as (dx, dy), peak (N,), texture (N,)
    (std of the block in a, grey levels). Reliable range: |d| < block / 4.
    """
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    H, W = a.shape
    ys, xs = block_grid(H, W, block, step)
    ba = np.stack([a[y:y + block, x:x + block] for y in ys for x in xs])
    bb = np.stack([b[y:y + block, x:x + block] for y in ys for x in xs])
    dx, dy, peak = phase_correlation(ba, bb)
    centres = np.array([(x + block / 2.0, y + block / 2.0) for y in ys for x in xs], dtype=np.float32)
    texture = ba.reshape(len(ba), -1).std(axis=1)
    return {"centres": centres, "vectors": np.stack([dx, dy], axis=1), "peak": peak, "texture": texture,
            "grid": (len(ys), len(xs)), "block": block}


def fit_similarity(centres: np.ndarray, vectors: np.ndarray, weights: np.ndarray | None = None,
                   center: tuple[float, float] = (0.0, 0.0), trim: float = 0.2, iters: int = 3) -> dict | None:
    """Least-squares similarity motion v = (s R - I)(p - c) + t, with trimmed re-fits.

    Returns scale, rot_deg, tx, ty, rms (px), n (blocks used) or None with fewer than 3 blocks.
    """
    p = np.asarray(centres, dtype=np.float64) - np.asarray(center, dtype=np.float64)
    v = np.asarray(vectors, dtype=np.float64)
    n = len(p)
    if n < 3:
        return None
    w = np.ones(n) if weights is None else np.asarray(weights, dtype=np.float64)
    keep = w > 0
    sol = None
    for it in range(iters):
        if keep.sum() < 3:
            break
        X, Y = p[keep, 0], p[keep, 1]
        ww = np.sqrt(w[keep])
        A = np.zeros((2 * len(X), 4))
        A[0::2, 0], A[0::2, 1], A[0::2, 2] = X, -Y, 1
        A[1::2, 0], A[1::2, 1], A[1::2, 3] = Y, X, 1
        rhs = np.empty(2 * len(X))
        rhs[0::2], rhs[1::2] = v[keep, 0], v[keep, 1]
        Wt = np.repeat(ww, 2)
        sol, *_ = np.linalg.lstsq(A * Wt[:, None], rhs * Wt, rcond=None)
        a_, b_, tx, ty = sol
        pred = np.stack([a_ * p[:, 0] - b_ * p[:, 1] + tx, b_ * p[:, 0] + a_ * p[:, 1] + ty], axis=1)
        err = np.hypot(*(pred - v).T)
        if it < iters - 1 and trim > 0:
            cand = np.flatnonzero(w > 0)
            thr = np.quantile(err[cand], 1 - trim) if len(cand) > 4 else np.inf
            keep = (w > 0) & (err <= max(thr, 0.25))
    if sol is None:
        return None
    a_, b_, tx, ty = sol
    pred = np.stack([a_ * p[:, 0] - b_ * p[:, 1] + tx, b_ * p[:, 0] + a_ * p[:, 1] + ty], axis=1)
    err = np.hypot(*(pred - v).T)
    return {"scale": float(math.hypot(1 + a_, b_)), "rot_deg": float(math.degrees(math.atan2(b_, 1 + a_))),
            "tx": float(tx), "ty": float(ty), "rms": float(np.sqrt(np.mean(err[keep] ** 2))) if keep.any() else 0.0,
            "n": int(keep.sum()), "inlier_ratio": float(keep.sum() / max(1, (w > 0).sum()))}


def reliable_blocks(bm: dict, min_peak: float = 0.35, min_texture: float = 3.0) -> np.ndarray:
    return (bm["peak"] >= min_peak) & (bm["texture"] >= min_texture)


def global_motion(gray: np.ndarray, stride: int = 1, block: int = 32, min_peak: float = 0.35,
                  min_texture: float = 3.0) -> list[dict | None]:
    """Similarity fit between frame i and i + stride for every i (None when unreliable)."""
    g = np.asarray(gray, dtype=np.float32)
    H, W = g.shape[1:3]
    out: list[dict | None] = []
    for i in range(len(g) - stride):
        bm = block_motion(g[i], g[i + stride], block)
        ok = reliable_blocks(bm, min_peak, min_texture)
        fit = fit_similarity(bm["centres"][ok], bm["vectors"][ok], center=((W - 1) / 2, (H - 1) / 2)) \
            if ok.sum() >= 4 else None
        if fit is not None:
            fit["reliable_ratio"] = float(ok.mean())
        out.append(fit)
    return out


def scale_search(a: np.ndarray, b: np.ndarray, scales: Iterable[float], crop: float = 0.7) -> tuple[float, float]:
    """Best scale s such that b ~ a zoomed by s about the centre (after a translation fix). Returns (s, ncc)."""
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    H, W = a.shape
    y0, x0 = int(H * (1 - crop) / 2), int(W * (1 - crop) / 2)
    best = (1.0, -1.0)
    for s in scales:
        wa = warp_similarity(a, s)
        dx, dy, _ = phase_correlation(wa, b)
        wa = warp_similarity(a, s, float(dx), float(dy))
        c = ncc(wa[y0:H - y0, x0:W - x0], b[y0:H - y0, x0:W - x0])
        if c > best[1]:
            best = (float(s), c)
    return best


def frame_diffs(gray: np.ndarray) -> np.ndarray:
    """Mean absolute grey difference between consecutive frames (length N-1)."""
    g = np.asarray(gray, dtype=np.float32)
    if len(g) < 2:
        return np.zeros(0, dtype=np.float32)
    return np.abs(np.diff(g, axis=0)).mean(axis=tuple(range(1, g.ndim))).astype(np.float32)


def channel_hists(rgb: np.ndarray, bins: int = 16) -> np.ndarray:
    """Normalised per-channel histograms, shape (N, 3, bins)."""
    a = as_rgb(np.asarray(rgb))
    q = (a.astype(np.int32) * bins) // 256
    n = a.shape[0]
    out = np.zeros((n, 3, bins), dtype=np.float32)
    flat = q.reshape(n, -1, 3)
    for c in range(3):
        for i in range(n):
            out[i, c] = np.bincount(flat[i, :, c], minlength=bins)[:bins]
    return out / max(1, flat.shape[1])


def hist_distances(rgb: np.ndarray, bins: int = 16) -> np.ndarray:
    """Per consecutive pair: mean over channels of half the L1 histogram distance (0 = same, 1 = disjoint)."""
    h = channel_hists(rgb, bins)
    if len(h) < 2:
        return np.zeros(0, dtype=np.float32)
    return (0.5 * np.abs(np.diff(h, axis=0)).sum(axis=2)).mean(axis=1).astype(np.float32)


def detect_cuts(frames: np.ndarray, fps: float, abs_thr: float = 0.3, rel_k: float = 3.0,
                min_shot_s: float = 0.25) -> list[int]:
    """Indices i where a hard cut sits between frame i-1 and i (histogram + pixel difference spikes)."""
    f = np.asarray(frames)
    if len(f) < 2:
        return []
    small = np.stack([downsample(x, max(1, f.shape[2] // 64)) for x in f]) if f.shape[2] > 96 else f.astype(np.float32)
    hd = hist_distances(small.astype(np.uint8))
    pd = frame_diffs(as_gray(small)) / 64.0
    score = 0.5 * hd + 0.5 * np.minimum(1.0, pd)
    win = max(2, int(round(fps)))
    cuts: list[int] = []
    for i, s in enumerate(score):
        lo, hi = max(0, i - win), min(len(score), i + win + 1)
        neigh = np.delete(score[lo:hi], i - lo)
        base = float(np.median(neigh)) if neigh.size else 0.0
        if s >= abs_thr and s >= rel_k * base + 0.05:
            if cuts and (i + 1 - cuts[-1]) < min_shot_s * fps:
                if s > score[cuts[-1] - 1]:
                    cuts[-1] = i + 1
                continue
            cuts.append(i + 1)
    return cuts


def shot_ranges(n_frames: int, fps: float, t0: float, cuts: list[int] | None = None,
                shots_s: list[tuple[float, float]] | None = None) -> list[tuple[int, int]]:
    """Frame index ranges [start, end) per shot from cut indices or (start_s, end_s) pairs."""
    if shots_s:
        out = []
        for a, b in shots_s:
            i0 = max(0, int(round((a - t0) * fps)))
            i1 = min(n_frames, int(round((b - t0) * fps)))
            if i1 - i0 >= 2:
                out.append((i0, i1))
        if out:
            return out
    edges = [0] + list(cuts or []) + [n_frames]
    return [(a, b) for a, b in zip(edges[:-1], edges[1:]) if b - a >= 1]


def cluster_vectors(vecs: np.ndarray, tol: float, min_count: int = 2) -> list[np.ndarray]:
    """Greedy density clustering of 2-D vectors: repeatedly take the point with most neighbours within
    ``tol`` and claim everything within ``tol`` of that group's mean. Returns index arrays."""
    v = np.asarray(vecs, dtype=np.float64)
    left = np.arange(len(v))
    out: list[np.ndarray] = []
    while len(left) >= min_count:
        d = np.hypot(*(v[left][:, None, :] - v[left][None, :, :]).transpose(2, 0, 1))
        counts = (d <= tol).sum(axis=1)
        seed = int(np.argmax(counts))
        if counts[seed] < min_count:
            break
        members = left[d[seed] <= tol]
        centre = v[members].mean(axis=0)
        members = left[np.hypot(*(v[left] - centre).T) <= tol]
        out.append(members)
        left = np.setdiff1d(left, members)
    return out


def block_tracks(gray: np.ndarray, block: int = 32, step: int = 16, max_pairs: int = 30, stride: int = 1,
                 min_peak: float = 0.35, min_texture: float = 3.0) -> dict:
    """Per-block velocity statistics over a shot (grey frames of one shot).

    Block motion is measured between frames i and i + stride for up to ``max_pairs`` evenly spaced
    pairs. For each block: median velocity over reliable pairs (px/frame at the given stride),
    share of pairs that were reliable, spread of the reliable vectors, texture and how much the
    block changes (mean abs difference between paired frames).
    """
    g = np.asarray(gray, dtype=np.float32)
    n = len(g)
    idx = list(range(0, max(0, n - stride)))
    if len(idx) > max_pairs:
        idx = [idx[int(round(k))] for k in np.linspace(0, len(idx) - 1, max_pairs)]
    vecs, rel, change, tex = [], [], [], []
    centres = None
    for i in idx:
        bm = block_motion(g[i], g[i + stride], block, step)
        centres = bm["centres"]
        vecs.append(bm["vectors"] / stride)
        rel.append(reliable_blocks(bm, min_peak, min_texture))
        tex.append(bm["texture"])
        H, W = g.shape[1:]
        ys, xs = block_grid(H, W, block, step)
        d = np.abs(g[i + stride] - g[i])
        change.append(np.array([d[y:y + block, x:x + block].mean() for y in ys for x in xs]))
    if centres is None:
        return {"centres": np.zeros((0, 2)), "velocity": np.zeros((0, 2)), "reliable_share": np.zeros(0),
                "spread": np.zeros(0), "texture": np.zeros(0), "change": np.zeros(0), "pairs": 0}
    V, R = np.stack(vecs), np.stack(rel)
    vel = np.zeros((V.shape[1], 2), dtype=np.float32)
    spread = np.full(V.shape[1], np.inf, dtype=np.float32)
    for b in range(V.shape[1]):
        ok = R[:, b]
        if ok.any():
            vel[b] = np.median(V[ok, b], axis=0)
            spread[b] = float(np.median(np.hypot(*(V[ok, b] - vel[b]).T)))
    return {"centres": centres, "velocity": vel, "reliable_share": R.mean(axis=0), "spread": spread,
            "texture": np.stack(tex).mean(axis=0), "change": np.stack(change).mean(axis=0), "pairs": len(idx),
            "block": block}


def _sim_predict(fit: dict, p: np.ndarray, center: tuple[float, float]) -> np.ndarray:
    s, th = fit["scale"], math.radians(fit["rot_deg"])
    a_, b_ = s * math.cos(th) - 1, s * math.sin(th)
    X, Y = p[:, 0] - center[0], p[:, 1] - center[1]
    return np.stack([a_ * X - b_ * Y + fit["tx"], b_ * X + a_ * Y + fit["ty"]], axis=1)


def motion_layers(tracks: dict, frame_hw: tuple[int, int], tol: float = 0.6, min_blocks: int = 3,
                  min_reliable: float = 0.6, max_spread: float = 0.75, min_texture: float = 4.0,
                  nonrigid_change: float = 6.0) -> dict:
    """Split a shot's blocks into coherent motion layers by sequential similarity fits.

    Rigid blocks (reliable in >= ``min_reliable`` of pairs, vector spread <= ``max_spread`` px/frame)
    are grouped greedily: seed with the densest velocity cluster, fit a similarity motion (pan +
    zoom + rotation) to it, take every remaining block within ``tol`` px/frame of the model, refit,
    repeat until fewer than ``min_blocks`` remain. Textured blocks that change a lot but are rarely
    reliable are ``nonrigid`` (water, crowds, particles); low-texture blocks are ``flat``.
    """
    H, W = frame_hw
    c = ((W - 1) / 2.0, (H - 1) / 2.0)
    P, V = tracks["centres"], tracks["velocity"]
    nb = len(P)
    textured = tracks["texture"] >= min_texture
    rigid = textured & (tracks["reliable_share"] >= min_reliable) & (tracks["spread"] <= max_spread)
    nonrigid = textured & ~rigid & (tracks["reliable_share"] < 0.5) & (tracks["change"] >= nonrigid_change)
    remaining = np.flatnonzero(rigid)
    layers = []
    while len(remaining) >= min_blocks:
        clusters = cluster_vectors(V[remaining], tol, min_count=min(min_blocks, len(remaining)))
        if not clusters:
            break
        members = remaining[max(clusters, key=len)]
        fit = None
        for _ in range(3):
            if len(members) >= 6:
                f = fit_similarity(P[members], V[members], center=c, trim=0.0, iters=1)
            else:
                m = V[members].mean(axis=0)
                f = {"scale": 1.0, "rot_deg": 0.0, "tx": float(m[0]), "ty": float(m[1]), "rms": 0.0,
                     "n": len(members), "inlier_ratio": 1.0}
            if f is None:
                break
            err = np.hypot(*(_sim_predict(f, P[remaining], c) - V[remaining]).T)
            grown = remaining[err <= tol]
            fit = f
            if len(grown) <= len(members) and set(grown.tolist()) == set(members.tolist()):
                break
            members = grown if len(grown) >= min_blocks else members
        if fit is None or len(members) < min_blocks:
            break
        layers.append({"blocks": members, "fit": fit})
        remaining = np.setdiff1d(remaining, members)
    return {"layers": layers, "rigid": rigid, "nonrigid": nonrigid, "flat": ~textured,
            "unassigned": remaining, "n_blocks": nb, "center": c}


# =============================================================== text localisation

def text_candidates(rgb: np.ndarray, edge_thr: float = 30.0, smear_frac: float = 0.012, density_thr: float = 0.18,
                    min_h_px: int = 6, max_h_frac: float = 0.3, min_transitions: float = 1.5,
                    merge_lines: bool = True, line_gap_factor: float = 1.2) -> list[dict]:
    """Text-like regions from edge density (no OCR).

    Strong Sobel edges are smeared horizontally so that glyphs of one line merge; connected regions
    are kept when their height, edge density and per-row edge transitions look like text, and word
    boxes on one line are merged into line boxes (``parts`` = number of merged pieces).
    Overlay text (captions, titles, labels) with clear contrast is found reliably; low-contrast,
    tiny, rotated or handwritten text is missed, and fine regular textures (grilles, foliage,
    brick) can be returned as false positives.
    """
    gray = as_gray(rgb)
    H, W = gray.shape
    mag = grad_mag(gray)
    edge = mag > edge_thr
    rx = max(2, int(round(smear_frac * max(W, H))))
    dens = box_mean(edge.astype(np.float32), 1, rx)
    cand = dens > density_thr
    cand = erode(dilate(cand, 1, 1), 1, 1)
    _, comps = components(cand, min_area=max(12, min_h_px * min_h_px))
    out = []
    for c in comps:
        x, y, w, h = c["bbox"]
        if h < min_h_px or h > max_h_frac * H or w < 0.5 * min_h_px:
            continue
        x0, x1 = max(0, x - 1), min(W, x + w + 1)
        sub = edge[y:y + h, x0:x1]
        density = float(sub.mean())
        trans = (np.diff(sub.astype(np.int8), axis=1) == 1).sum(axis=1)
        rows = trans[trans > 0]
        per_row = float(np.median(rows)) if rows.size else 0.0
        fill = c["area"] / float(w * h)
        if density < 0.08 or density > 0.85 or per_row < min_transitions or fill < 0.35:
            continue
        out.append({"bbox": [int(x), int(y), int(w), int(h)], "edge_density": density,
                    "row_transitions": per_row, "fill": fill})
    out.sort(key=lambda d: (d["bbox"][1], d["bbox"][0]))
    return merge_line_boxes(out, gap_factor=line_gap_factor) if merge_lines else out


def merge_line_boxes(boxes: list[dict], gap_factor: float = 1.2, min_v_overlap: float = 0.6) -> list[dict]:
    """Merge word boxes that sit on one text line (vertical overlap >= min_v_overlap of the smaller
    height, similar heights, horizontal gap <= gap_factor x height) into line boxes."""
    items = [dict(b, bbox=list(b["bbox"]), parts=b.get("parts", 1)) for b in boxes]
    changed = True
    while changed:
        changed = False
        items.sort(key=lambda d: d["bbox"][0])
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i]["bbox"], items[j]["bbox"]
                top, bot = max(a[1], b[1]), min(a[1] + a[3], b[1] + b[3])
                hmin, hmax = min(a[3], b[3]), max(a[3], b[3])
                if bot - top < min_v_overlap * hmin or hmax > 1.6 * hmin:
                    continue
                gap = max(a[0], b[0]) - min(a[0] + a[2], b[0] + b[2])
                if gap > gap_factor * hmax:
                    continue
                x0, y0 = min(a[0], b[0]), min(a[1], b[1])
                x1, y1 = max(a[0] + a[2], b[0] + b[2]), max(a[1] + a[3], b[1] + b[3])
                wa, wb = a[2] * a[3], b[2] * b[3]
                merged = {k: (items[i][k] * wa + items[j][k] * wb) / (wa + wb)
                          for k in ("edge_density", "row_transitions", "fill") if k in items[i] and k in items[j]}
                merged.update(bbox=[x0, y0, x1 - x0, y1 - y0], parts=items[i]["parts"] + items[j]["parts"])
                items[i] = merged
                del items[j]
                changed = True
                break
            if changed:
                break
    items.sort(key=lambda d: (d["bbox"][1], d["bbox"][0]))
    return items


def glyph_mask(rgb: np.ndarray, bbox: Iterable[int], pad: int = 3) -> dict | None:
    """Split a text box into glyph and backing pixels.

    Otsu on luma inside the padded box; the backing is the class that owns most of the pad border
    (glyphs rarely touch it). Returns mask (bool, crop-sized), crop origin, glyph/backing median
    colours, tight glyph bbox (frame pixels) and the luma separation between the classes.
    """
    a = np.asarray(rgb)
    H, W = a.shape[:2]
    x, y, w, h = (int(v) for v in bbox)
    x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(W, x + w + pad), min(H, y + h + pad)
    crop = a[y0:y1, x0:x1].astype(np.float32)
    if crop.shape[0] < 3 or crop.shape[1] < 3:
        return None
    lum = crop @ LUMA_601 if crop.ndim == 3 else crop
    t = otsu(lum)
    hi = lum > t
    border = np.concatenate([hi[0], hi[-1], hi[:, 0], hi[:, -1]])
    glyph = ~hi if border.mean() > 0.5 else hi
    if glyph.sum() < 4 or (~glyph).sum() < 4:
        return None
    # drop speckles and pieces that touch the padded border (background texture, not glyphs)
    labels, comps = components(glyph)
    keep = np.zeros(len(comps) + 2, dtype=bool)
    min_area = max(3, 0.01 * glyph.sum())
    ch, cw = glyph.shape
    for c in comps:
        bx, by, bw, bh = c["bbox"]
        touches = bx == 0 or by == 0 or bx + bw == cw or by + bh == ch
        if c["area"] >= min_area and not (touches and pad > 0 and c["area"] < 0.2 * glyph.sum()):
            keep[c["label"]] = True
    cleaned = keep[labels]
    if cleaned.sum() >= 4:
        glyph = cleaned
    core = erode(glyph, 1) if erode(glyph, 1).sum() >= 8 else glyph
    back = erode(~glyph, 1) if erode(~glyph, 1).sum() >= 8 else ~glyph
    rgbc = crop if crop.ndim == 3 else np.repeat(crop[..., None], 3, axis=-1)
    tb = bbox_of(glyph)
    assert tb is not None
    return {"mask": glyph, "origin": (x0, y0), "glyph_color": np.median(rgbc[core], axis=0),
            "backing_color": np.median(rgbc[back], axis=0),
            "glyph_bbox": [tb[0] + x0, tb[1] + y0, tb[2], tb[3]],
            "separation": float(abs(np.median(lum[glyph]) - np.median(lum[~glyph]))),
            "fill_ratio": float(glyph.mean())}


def track_boxes(frames_boxes: list[list[dict]], iou_thr: float = 0.3, max_gap: int = 1) -> list[dict]:
    """Greedy IoU tracking of per-frame boxes. Each track: {frames: [i...], items: [box dict...]}."""
    tracks: list[dict] = []
    active: list[dict] = []
    for i, boxes in enumerate(frames_boxes):
        pairs = []
        for ti, tr in enumerate(active):
            for bi, bx in enumerate(boxes):
                v = iou(tr["items"][-1]["bbox"], bx["bbox"])
                if v >= iou_thr:
                    pairs.append((v, ti, bi))
        pairs.sort(reverse=True)
        used_t, used_b = set(), set()
        for v, ti, bi in pairs:
            if ti in used_t or bi in used_b:
                continue
            used_t.add(ti)
            used_b.add(bi)
            active[ti]["frames"].append(i)
            active[ti]["items"].append(boxes[bi])
        for bi, bx in enumerate(boxes):
            if bi not in used_b:
                tr = {"frames": [i], "items": [bx]}
                tracks.append(tr)
                active.append(tr)
        active = [tr for tr in active if i - tr["frames"][-1] <= max_gap]
    return tracks


# =============================================================== synthetic fixtures (tests, demos)

def synth_texture(h: int, w: int, seed: int = 0, scales: Iterable[int] = (2, 4, 8, 16), rgb: bool = False,
                  lo: float = 20.0, hi: float = 235.0) -> np.ndarray:
    """Smooth multi-scale random texture (float32, lo..hi). Good for phase correlation tests."""
    rng = np.random.default_rng(seed)
    chans = 3 if rgb else 1
    acc = np.zeros((h, w, chans), dtype=np.float32)
    for s in scales:
        gh, gw = max(2, h // s), max(2, w // s)
        acc += resize(rng.random((gh, gw, chans)).astype(np.float32), h, w) * (s ** 0.5)
    acc -= acc.min()
    acc /= max(1e-6, acc.max())
    out = lo + (hi - lo) * acc
    return out if rgb else out[..., 0]


FONT_5X7 = {
    "A": ".###.|#...#|#...#|#####|#...#|#...#|#...#", "B": "####.|#...#|#...#|####.|#...#|#...#|####.",
    "C": ".###.|#...#|#....|#....|#....|#...#|.###.", "D": "####.|#...#|#...#|#...#|#...#|#...#|####.",
    "E": "#####|#....|#....|####.|#....|#....|#####", "F": "#####|#....|#....|####.|#....|#....|#....",
    "G": ".###.|#...#|#....|#.###|#...#|#...#|.####", "H": "#...#|#...#|#...#|#####|#...#|#...#|#...#",
    "I": ".###.|..#..|..#..|..#..|..#..|..#..|.###.", "J": "..###|...#.|...#.|...#.|...#.|#..#.|.##..",
    "K": "#...#|#..#.|#.#..|##...|#.#..|#..#.|#...#", "L": "#....|#....|#....|#....|#....|#....|#####",
    "M": "#...#|##.##|#.#.#|#.#.#|#...#|#...#|#...#", "N": "#...#|#...#|##..#|#.#.#|#..##|#...#|#...#",
    "O": ".###.|#...#|#...#|#...#|#...#|#...#|.###.", "P": "####.|#...#|#...#|####.|#....|#....|#....",
    "Q": ".###.|#...#|#...#|#...#|#.#.#|#..#.|.##.#", "R": "####.|#...#|#...#|####.|#.#..|#..#.|#...#",
    "S": ".####|#....|#....|.###.|....#|....#|####.", "T": "#####|..#..|..#..|..#..|..#..|..#..|..#..",
    "U": "#...#|#...#|#...#|#...#|#...#|#...#|.###.", "V": "#...#|#...#|#...#|#...#|#...#|.#.#.|..#..",
    "W": "#...#|#...#|#...#|#.#.#|#.#.#|#.#.#|.#.#.", "X": "#...#|#...#|.#.#.|..#..|.#.#.|#...#|#...#",
    "Y": "#...#|#...#|.#.#.|..#..|..#..|..#..|..#..", "Z": "#####|....#|...#.|..#..|.#...|#....|#####",
    "0": ".###.|#...#|#..##|#.#.#|##..#|#...#|.###.", "1": "..#..|.##..|..#..|..#..|..#..|..#..|.###.",
    "2": ".###.|#...#|....#|...#.|..#..|.#...|#####", "3": "#####|...#.|..#..|...#.|....#|#...#|.###.",
    "4": "...#.|..##.|.#.#.|#..#.|#####|...#.|...#.", "5": "#####|#....|####.|....#|....#|#...#|.###.",
    "6": "..##.|.#...|#....|####.|#...#|#...#|.###.", "7": "#####|....#|...#.|..#..|.#...|.#...|.#...",
    "8": ".###.|#...#|#...#|.###.|#...#|#...#|.###.", "9": ".###.|#...#|#...#|.####|....#|...#.|.##..",
    "#": ".#.#.|.#.#.|#####|.#.#.|#####|.#.#.|.#.#.", "%": "##..#|##..#|...#.|..#..|.#...|#..##|#..##",
    "+": ".....|..#..|..#..|#####|..#..|..#..|.....", "!": "..#..|..#..|..#..|..#..|..#..|.....|..#..",
    "?": ".###.|#...#|....#|...#.|..#..|.....|..#..", ".": ".....|.....|.....|.....|.....|.##..|.##..",
    "-": ".....|.....|.....|#####|.....|.....|.....", ":": ".....|.##..|.##..|.....|.##..|.##..|.....",
    " ": ".....|.....|.....|.....|.....|.....|.....",
}


def render_text(text: str, scale: int = 4, sx: int | None = None, sy: int | None = None,
                line_gap: int = 3, align: str = "center") -> np.ndarray:
    """Boolean mask of ``text`` in a 5x7 bitmap font (A-Z, 0-9, # % + ! ? . - : and space).

    Each glyph is 5 x 7 units followed by 1 unit of spacing; a space advances 3 units, so a word
    gap is 4 units (about 0.57 of the cap height). A unit is ``sx`` x ``sy`` pixels.
    """
    sx = sx or scale
    sy = sy or scale

    def line_mask(ln: str) -> np.ndarray:
        adv = [3 if ch == " " else 6 for ch in ln]
        width = max(1, sum(adv) - 1)
        m = np.zeros((7, width), dtype=bool)
        x = 0
        for ch, a in zip(ln, adv):
            if ch != " ":
                for r, row in enumerate(FONT_5X7.get(ch, FONT_5X7["?"]).split("|")):
                    for c, v in enumerate(row):
                        if v == "#":
                            m[r, x + c] = True
            x += a
        return m

    masks = [line_mask(ln) for ln in text.upper().split("\n")]
    width = max(m.shape[1] for m in masks)
    rows = []
    for m in masks:
        pad = width - m.shape[1]
        left = pad // 2 if align == "center" else 0
        rows.append(np.pad(m, ((0, 0), (left, pad - left))))
        rows.append(np.zeros((line_gap, width), dtype=bool))
    full = np.concatenate(rows[:-1], axis=0)
    return np.repeat(np.repeat(full, sy, axis=0), sx, axis=1)


def paste(frame: np.ndarray, mask: np.ndarray, x: int, y: int, color: Iterable[float],
          alpha: float = 1.0) -> np.ndarray:
    """Composite ``color`` through ``mask`` (bool or 0-1 float) at (x, y), clipped to the frame. In place."""
    H, W = frame.shape[:2]
    m = np.asarray(mask, dtype=np.float32)
    mh, mw = m.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + mw), min(H, y + mh)
    if x1 <= x0 or y1 <= y0:
        return frame
    sub = m[y0 - y:y1 - y, x0 - x:x1 - x] * alpha
    col = np.asarray(list(color), dtype=np.float32)
    region = frame[y0:y1, x0:x1].astype(np.float32)
    if region.ndim == 3:
        sub = sub[..., None]
    else:
        col = float(col @ LUMA_601) if col.size == 3 else float(col.ravel()[0])
    frame[y0:y1, x0:x1] = np.clip(region * (1 - sub) + col * sub, 0, 255).astype(frame.dtype)
    return frame


def rounded_rect_mask(h: int, w: int, radius: float = 0.0) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    r = max(0.0, min(radius, h / 2, w / 2))
    if r <= 0:
        return np.ones((h, w), dtype=bool)
    cx = np.clip(xx, r, w - r)
    cy = np.clip(yy, r, h - r)
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
