"""Stream raw frames between numpy and ffmpeg through pipes (no temp files).

* ``FrameReader(path, size=None, pix_fmt="rgb24")`` yields numpy frames
  (H, W, C) decoded by ffmpeg, optionally scaled and resampled to an fps;
* ``FrameWriter(path, size, fps)`` accepts numpy frames and encodes them
  with libx264/yuv420p (or any codec args), optionally muxing an audio file.

Both are context managers and close the ffmpeg process cleanly; errors from
ffmpeg are raised with its stderr text.

Usage::

    from ffmpeg_raw_frame_pipe import FrameReader, FrameWriter
    with FrameReader("in.mp4", size=(540, 960)) as rd, FrameWriter("out.mp4", (540, 960), fps=30) as wr:
        for frame in rd:
            wr.write(255 - frame)
"""

from __future__ import annotations

import subprocess

import numpy as np

CHANNELS = {"rgb24": 3, "rgba": 4, "gray": 1, "bgr24": 3}


class FrameReader:
    def __init__(self, path: str, size=None, pix_fmt: str = "rgb24", fps: float | None = None,
                 start: float | None = None, duration: float | None = None):
        if pix_fmt not in CHANNELS:
            raise ValueError(f"pix_fmt must be one of {sorted(CHANNELS)}")
        if size is None:
            raise ValueError("give the output size (w, h); probe the file first if you need the source size")
        self.w, self.h = size
        self.c = CHANNELS[pix_fmt]
        vf = [f"scale={self.w}:{self.h}"]
        if fps:
            vf.insert(0, f"fps={fps:g}")
        a = ["ffmpeg", "-nostdin", "-v", "error"]
        if start is not None:
            a += ["-ss", f"{start:g}"]
        a += ["-i", path]
        if duration is not None:
            a += ["-t", f"{duration:g}"]
        self.argv = a + ["-vf", ",".join(vf), "-f", "rawvideo", "-pix_fmt", pix_fmt, "-"]
        self.proc = None

    def __enter__(self):
        self.proc = subprocess.Popen(self.argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return self

    def __iter__(self):
        n = self.w * self.h * self.c
        while True:
            buf = self.proc.stdout.read(n)
            if len(buf) < n:
                break
            arr = np.frombuffer(buf, np.uint8).reshape(self.h, self.w, self.c)
            yield arr[..., 0] if self.c == 1 else arr

    def __exit__(self, *exc):
        if self.proc:
            self.proc.stdout.close()
            err = self.proc.stderr.read().decode(errors="replace")
            rc = self.proc.wait()
            if rc and exc[0] is None:
                raise RuntimeError(f"ffmpeg reader failed ({rc}): {err.strip()[-500:]}")
        return False


class FrameWriter:
    def __init__(self, path: str, size, fps: float = 30, pix_fmt_in: str = "rgb24", audio: str | None = None,
                 codec_args: list[str] | None = None):
        if pix_fmt_in not in CHANNELS:
            raise ValueError(f"pix_fmt_in must be one of {sorted(CHANNELS)}")
        self.w, self.h = size
        if self.w % 2 or self.h % 2:
            raise ValueError("width and height must be even for yuv420p")
        self.c = CHANNELS[pix_fmt_in]
        a = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", pix_fmt_in,
             "-s", f"{self.w}x{self.h}", "-r", f"{fps:g}", "-i", "-"]
        if audio:
            a += ["-i", audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"]
        a += codec_args or ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p"]
        self.argv = a + [path]
        self.frames = 0
        self.proc = None

    def __enter__(self):
        self.proc = subprocess.Popen(self.argv, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        return self

    def write(self, frame: np.ndarray) -> None:
        f = np.asarray(frame)
        expect = (self.h, self.w) if self.c == 1 else (self.h, self.w, self.c)
        if f.shape != expect or f.dtype != np.uint8:
            raise ValueError(f"frame must be uint8 with shape {expect}, got {f.dtype} {f.shape}")
        self.proc.stdin.write(np.ascontiguousarray(f).tobytes())
        self.frames += 1

    def __exit__(self, *exc):
        if self.proc:
            self.proc.stdin.close()
            err = self.proc.stderr.read().decode(errors="replace")
            rc = self.proc.wait()
            if rc and exc[0] is None:
                raise RuntimeError(f"ffmpeg writer failed ({rc}): {err.strip()[-500:]}")
        return False
