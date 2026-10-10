"""Synthetic calibration media for the video_re_* measurement modules (vendored in every package).

Every generator writes media whose ground truth is known exactly (cut times, pan speed, zoom rate,
click times, panel opacity), so a measurement can be checked against it. Used by the tests; also
handy to calibrate thresholds on a new machine.

Needs numpy, the standard library and ffmpeg (for video encoding only).
"""

from __future__ import annotations

import subprocess
import wave
from pathlib import Path
from typing import Callable, Iterable

import numpy as np

from video_re_common import require


def texture(width: int, height: int, seed: int = 7, smooth: int = 3) -> np.ndarray:
    """Deterministic smoothed-noise RGB texture (uint8) with plenty of detail for motion estimation."""
    rng = np.random.default_rng(seed)
    base = rng.random((height, width, 3)).astype(np.float32)
    for _ in range(smooth):  # separable box blur
        base = (np.roll(base, 1, 0) + base + np.roll(base, -1, 0)) / 3.0
        base = (np.roll(base, 1, 1) + base + np.roll(base, -1, 1)) / 3.0
    base -= base.min()
    base /= max(1e-6, base.max())
    yy, xx = np.mgrid[0:height, 0:width]
    stripes = 0.5 + 0.5 * np.sin(xx / 9.0 + yy / 13.0)
    img = 0.75 * base + 0.25 * stripes[..., None]
    return (img * 255).clip(0, 255).astype(np.uint8)


def encode_frames(path: str | Path, frames: Iterable[np.ndarray], fps: float, size: tuple[int, int],
                  codec: str = "h264", audio: str | Path | None = None) -> Path:
    """Encode RGB uint8 frames (h, w, 3) to a video. codec 'h264' (near-lossless, yuv420p) or 'ffv1' (lossless)."""
    require("ffmpeg")
    path = Path(path)
    w, h = size
    argv = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", f"{fps}", "-i", "-"]
    if audio:
        argv += ["-i", str(audio)]
    if codec == "h264":
        argv += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "10", "-pix_fmt", "yuv420p"]
    elif codec == "ffv1":
        argv += ["-c:v", "ffv1"]
    else:
        raise ValueError("codec must be h264 or ffv1")
    if audio:
        argv += ["-c:a", "aac" if path.suffix == ".mp4" else "pcm_s16le", "-shortest"]
    argv.append(str(path))
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for f in frames:
            if f.shape != (h, w, 3):
                raise ValueError(f"frame shape {f.shape} != {(h, w, 3)}")
            proc.stdin.write(np.ascontiguousarray(f, dtype=np.uint8).tobytes())
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode() if proc.stderr else ""
        if proc.wait() != 0:
            raise RuntimeError(f"ffmpeg encode failed: {err[-400:]}")
    return path


def lavfi_cuts_video(path: str | Path, seconds_per_shot: float = 1.0, size: tuple[int, int] = (320, 180),
                     fps: int = 25, sources: list[str] | None = None, audio: bool = False) -> tuple[Path, list[float]]:
    """Concatenate distinct lavfi sources with hard cuts. Returns (path, cut times in seconds)."""
    require("ffmpeg")
    w, h = size
    sources = sources or [f"testsrc2=s={w}x{h}:r={fps}", f"color=c=0x2848A0:s={w}x{h}:r={fps}",
                          f"smptebars=s={w}x{h}:r={fps}", f"mandelbrot=s={w}x{h}:r={fps}"]
    argv = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error"]
    for s in sources:
        argv += ["-f", "lavfi", "-t", f"{seconds_per_shot}", "-i", s]
    total = seconds_per_shot * len(sources)
    if audio:
        argv += ["-f", "lavfi", "-t", f"{total}", "-i", "sine=frequency=440:sample_rate=48000"]
    chains = "".join(f"[{i}:v]format=yuv420p,setsar=1[v{i}];" for i in range(len(sources)))
    concat = "".join(f"[v{i}]" for i in range(len(sources))) + f"concat=n={len(sources)}:v=1:a=0[v]"
    argv += ["-filter_complex", chains + concat, "-map", "[v]"]
    if audio:
        argv += ["-map", f"{len(sources)}:a", "-c:a", "aac"]
    argv += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(fps), str(path)]
    subprocess.run(argv, check=True, capture_output=True, timeout=120, stdin=subprocess.DEVNULL)
    cuts = [round(seconds_per_shot * i, 6) for i in range(1, len(sources))]
    return Path(path), cuts


def pan_frames(n: int, size: tuple[int, int], dx_per_frame: float = 2.0, dy_per_frame: float = 0.0,
               seed: int = 7) -> Iterable[np.ndarray]:
    """A window moving over a large texture. dx>0 moves the window right: the camera pans right and
    the content travels left."""
    w, h = size
    pad = int(abs(dx_per_frame) * n + abs(dy_per_frame) * n) + 8
    tex = texture(w + 2 * pad, h + 2 * pad, seed)
    for i in range(n):
        x = int(round(pad + dx_per_frame * i))
        y = int(round(pad + dy_per_frame * i))
        yield tex[y:y + h, x:x + w]


def zoom_frames(n: int, size: tuple[int, int], rate_per_frame: float = 0.005, seed: int = 11) -> Iterable[np.ndarray]:
    """Centre zoom over a texture: scale(i) = exp(rate * i). rate > 0 zooms in."""
    from PIL import Image

    w, h = size
    big = Image.fromarray(texture(w * 2, h * 2, seed))
    for i in range(n):
        s = float(np.exp(rate_per_frame * i))
        cw, ch = (2 * w) / (1.25 * s), (2 * h) / (1.25 * s)
        cx, cy = w, h
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        yield np.asarray(big.resize((w, h), Image.BILINEAR, box=box))


def write_wav(path: str | Path, samples: np.ndarray, sr: int) -> Path:
    path = Path(path)
    x = np.clip(np.asarray(samples, dtype=np.float64), -1.0, 1.0)
    pcm = (x * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(sr))
        wf.writeframes(pcm.tobytes())
    return path


def clicks(times_s: list[float], duration_s: float, sr: int = 22050, freq: float = 1500.0,
           click_s: float = 0.03, amp: float = 0.6, noise: float = 0.0, seed: int = 3) -> np.ndarray:
    """Decaying sine clicks at known times over optional low noise."""
    n = int(round(duration_s * sr))
    x = np.zeros(n, dtype=np.float64)
    if noise:
        x += noise * np.random.default_rng(seed).standard_normal(n)
    m = int(click_s * sr)
    t = np.arange(m) / sr
    burst = amp * np.sin(2 * np.pi * freq * t) * np.exp(-t / (click_s / 4))
    for c in times_s:
        i = int(round(c * sr))
        j = min(n, i + m)
        if 0 <= i < n:
            x[i:j] += burst[: j - i]
    return x


def sine(duration_s: float, sr: int = 48000, freq: float = 1000.0, amp: float = 0.1) -> np.ndarray:
    t = np.arange(int(round(duration_s * sr))) / sr
    return amp * np.sin(2 * np.pi * freq * t)


def speechlike(segments: list[tuple[float, float]], duration_s: float, sr: int = 16000,
               syllables_per_s: float = 4.0, f0: float = 140.0, noise: float = 0.002, seed: int = 5) -> np.ndarray:
    """Harmonic 'voice' (f0 plus formant-ish harmonics) amplitude-modulated at a syllable rate inside
    the given segments, near-silence elsewhere. Not speech, but it has speech's energy, band and
    syllabic-rate structure, which is what the heuristics measure."""
    n = int(round(duration_s * sr))
    t = np.arange(n) / sr
    rng = np.random.default_rng(seed)
    voice = np.zeros(n)
    for k, a in ((1, 1.0), (2, 0.6), (3, 0.5), (5, 0.35), (8, 0.25), (12, 0.15)):
        voice += a * np.sin(2 * np.pi * f0 * k * t + k)
    voice /= np.max(np.abs(voice))
    env = np.zeros(n)
    for s, e in segments:
        i, j = int(s * sr), int(e * sr)
        tt = t[i:j] - s
        env[i:j] = 0.5 * (1 - np.cos(2 * np.pi * syllables_per_s * tt))  # one bump per syllable
    x = 0.4 * voice * env + noise * rng.standard_normal(n)
    return x


def make_av(path: str | Path, frames_fn: Callable[[], Iterable[np.ndarray]], fps: float, size: tuple[int, int],
            audio: np.ndarray | None = None, sr: int = 48000, codec: str = "h264") -> Path:
    """Video from frames plus optional mono audio samples, muxed in one file."""
    path = Path(path)
    wav = None
    if audio is not None:
        wav = write_wav(path.with_suffix(".tmp.wav"), audio, sr)
    try:
        return encode_frames(path, frames_fn(), fps, size, codec=codec, audio=wav)
    finally:
        if wav is not None and wav.exists():
            wav.unlink()
