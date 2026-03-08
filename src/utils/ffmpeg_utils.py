"""FFmpeg utility functions for the video pipeline."""

import subprocess
import json
import re
from pathlib import Path
from typing import Optional


def run_ffmpeg(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd,
            output=result.stdout, stderr=result.stderr,
        )
    return result


def run_ffprobe(file_path: str | Path) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(file_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def get_duration(file_path: str | Path) -> float:
    info = run_ffprobe(file_path)
    return float(info["format"]["duration"])


def get_video_dimensions(file_path: str | Path) -> tuple[int, int]:
    info = run_ffprobe(file_path)
    for stream in info["streams"]:
        if stream["codec_type"] == "video":
            return int(stream["width"]), int(stream["height"])
    raise ValueError(f"No video stream found in {file_path}")


def extract_audio(video_path: str | Path, output_path: str | Path,
                   sample_rate: int = 16000) -> Path:
    output_path = Path(output_path)
    run_ffmpeg([
        "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", str(sample_rate), "-ac", "1",
        str(output_path)
    ])
    return output_path


def clip_video(input_path: str | Path, output_path: str | Path,
               start: float, end: float) -> Path:
    output_path = Path(output_path)
    duration = end - start
    run_ffmpeg([
        "-ss", str(start), "-i", str(input_path),
        "-t", str(duration), "-c", "copy", "-avoid_negative_ts", "make_zero",
        str(output_path)
    ])
    return output_path


def concat_videos(file_list: list[str | Path], output_path: str | Path,
                   reencode: bool = False) -> Path:
    output_path = Path(output_path)
    list_file = output_path.parent / f"{output_path.stem}_concat.txt"

    with open(list_file, "w") as f:
        for fp in file_list:
            # Use forward slashes for ffmpeg compatibility on Windows
            safe_path = str(Path(fp).resolve()).replace("\\", "/")
            f.write(f"file '{safe_path}'\n")

    if reencode:
        run_ffmpeg([
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(output_path)
        ])
    else:
        run_ffmpeg([
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", str(output_path)
        ])

    list_file.unlink(missing_ok=True)
    return output_path


def overlay_audio(video_path: str | Path, audio_path: str | Path,
                   output_path: str | Path, video_volume: float = 0.15,
                   audio_volume: float = 1.0) -> Path:
    output_path = Path(output_path)
    run_ffmpeg([
        "-i", str(video_path), "-i", str(audio_path),
        "-filter_complex",
        f"[0:a]volume={video_volume}[bg];"
        f"[1:a]volume={audio_volume}[fg];"
        f"[bg][fg]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        str(output_path)
    ])
    return output_path


def burn_subtitles(video_path: str | Path, subtitle_path: str | Path,
                    output_path: str | Path) -> Path:
    output_path = Path(output_path)
    sub_ext = Path(subtitle_path).suffix.lower()

    # Escape path for ffmpeg filter: backslashes, colons, and single quotes
    safe_sub = str(Path(subtitle_path).resolve()).replace("\\", "/").replace(":", "\\:")
    if sub_ext == ".ass":
        vf = f"ass='{safe_sub}'"
    else:
        vf = f"subtitles='{safe_sub}'"

    run_ffmpeg([
        "-i", str(video_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output_path)
    ])
    return output_path


def scale_video(input_path: str | Path, output_path: str | Path,
                width: int, height: int, pad: bool = True) -> Path:
    output_path = Path(output_path)

    if pad:
        vf = (f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
              f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black")
    else:
        vf = f"scale={width}:{height}"

    run_ffmpeg([
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output_path)
    ])
    return output_path


def crop_to_vertical(input_path: str | Path, output_path: str | Path) -> Path:
    """Crop horizontal 16:9 video to vertical 9:16."""
    output_path = Path(output_path)
    run_ffmpeg([
        "-i", str(input_path),
        "-vf", "crop=ih*9/16:ih",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output_path)
    ])
    return output_path


def detect_silence(file_path: str | Path, noise_db: float = -30,
                    min_duration: float = 0.5) -> list[dict]:
    cmd = [
        "ffmpeg", "-i", str(file_path),
        "-af", f"silencedetect=noise={noise_db}dB:d={min_duration}",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stderr = result.stderr

    silences = []
    starts = re.findall(r"silence_start: ([\d.]+)", stderr)
    ends = re.findall(r"silence_end: ([\d.]+)", stderr)

    for s, e in zip(starts, ends):
        silences.append({"start": float(s), "end": float(e)})

    return silences


def add_background_music(video_path: str | Path, music_path: str | Path,
                          output_path: str | Path, music_volume: float = 0.08) -> Path:
    output_path = Path(output_path)
    run_ffmpeg([
        "-i", str(video_path), "-stream_loop", "-1", "-i", str(music_path),
        "-filter_complex",
        f"[1:a]volume={music_volume}[music];"
        f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=3[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(output_path)
    ])
    return output_path
