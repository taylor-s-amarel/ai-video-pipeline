"""Download source videos using yt-dlp."""

import subprocess
import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class DownloadResult:
    file_path: Path
    title: str
    duration: float
    uploader: str
    url: str
    description: str
    thumbnail_url: str


def get_video_info(url: str) -> dict:
    cmd = [
        "yt-dlp", "--dump-json", "--no-download",
        "--no-warnings", "--quiet",
        "--js-runtimes", "node", url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def download_video(url: str, output_dir: str | Path,
                    max_height: int = 1080,
                    audio_only: bool = False) -> DownloadResult:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(output_dir / "%(id)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-warnings", "--quiet",
        "--write-info-json",
        "--output", output_template,
        "--restrict-filenames",
        "--js-runtimes", "node",
    ]

    if audio_only:
        cmd.extend([
            "-x", "--audio-format", "wav",
            "--audio-quality", "0",
        ])
    else:
        cmd.extend([
            "-f", f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]",
            "--merge-output-format", "mp4",
        ])

    cmd.append(url)
    subprocess.run(cmd, check=True, capture_output=True, text=True)

    # Find the downloaded file
    info = get_video_info(url)
    video_id = info.get("id", "unknown")

    if audio_only:
        file_path = output_dir / f"{video_id}.wav"
    else:
        file_path = output_dir / f"{video_id}.mp4"

    # Fallback: find any file matching the id
    if not file_path.exists():
        matches = list(output_dir.glob(f"{video_id}.*"))
        media_matches = [m for m in matches if m.suffix not in ('.json', '.txt')]
        if media_matches:
            file_path = media_matches[0]

    return DownloadResult(
        file_path=file_path,
        title=info.get("title", ""),
        duration=float(info.get("duration", 0)),
        uploader=info.get("uploader", info.get("channel", "")),
        url=url,
        description=info.get("description", ""),
        thumbnail_url=info.get("thumbnail", ""),
    )


def download_audio(url: str, output_dir: str | Path) -> DownloadResult:
    return download_video(url, output_dir, audio_only=True)


def search_videos(query: str, max_results: int = 5) -> list[dict]:
    cmd = [
        "yt-dlp",
        f"ytsearch{max_results}:{query}",
        "--dump-json", "--no-download",
        "--no-warnings", "--quiet",
        "--flat-playlist",
        "--js-runtimes", "node",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    results = []
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            results.append(json.loads(line))
    return results
