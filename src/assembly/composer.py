"""Final video composition — assembles clips, commentary, captions, and music."""

import shutil
from pathlib import Path
from dataclasses import dataclass, field

from config.settings import settings, PlatformExport
from src.utils.ffmpeg_utils import (
    run_ffmpeg, concat_videos, overlay_audio, burn_subtitles,
    scale_video, get_duration, add_background_music,
)


@dataclass
class ComposedVideo:
    file_path: Path
    duration: float
    platform: str
    width: int
    height: int


@dataclass
class CompositionPlan:
    """Describes the structure of the final video."""
    # Ordered list of segments to assemble
    segments: list[dict] = field(default_factory=list)
    # Each segment dict: {"type": "commentary"|"clip"|"transition", "file": Path, ...}


def compose_commentary_video(
    commentary_audio_segments: list[Path],
    source_clips: list[Path],
    caption_file: Path | None,
    background_music: Path | None,
    output_path: str | Path,
    platform: str = "youtube",
    background_image: Path | None = None,
) -> ComposedVideo:
    """Compose a full commentary video.

    Structure: [hook_audio + bg] -> [clip1] -> [commentary1 + bg] -> [clip2] -> ...
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    platform_settings = settings.get_platform_settings(platform)
    width = platform_settings["width"]
    height = platform_settings["height"]

    temp_dir = output_path.parent / f"_temp_{output_path.stem}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # If we have a background image, create video segments from audio
    # Otherwise, we'll create a simple black background
    segment_files = []
    seg_index = 0

    # Interleave commentary audio (rendered as video) with source clips
    clip_idx = 0
    for i, audio_seg in enumerate(commentary_audio_segments):
        # Create a video from commentary audio (with background)
        commentary_video = temp_dir / f"seg_{seg_index:03d}_commentary.mp4"
        audio_duration = get_duration(audio_seg)

        if background_image and background_image.exists():
            # Use image as background for commentary segments
            run_ffmpeg([
                "-loop", "1", "-i", str(background_image),
                "-i", str(audio_seg),
                "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                "-tune", "stillimage",
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                       f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
                "-pix_fmt", "yuv420p",
                "-t", str(audio_duration),
                "-shortest",
                str(commentary_video),
            ])
        else:
            # Black background with audio
            run_ffmpeg([
                "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:r=30:d={audio_duration}",
                "-i", str(audio_seg),
                "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
                "-pix_fmt", "yuv420p",
                "-shortest",
                str(commentary_video),
            ])

        segment_files.append(commentary_video)
        seg_index += 1

        # Insert a source clip after commentary (except after the last segment)
        if clip_idx < len(source_clips):
            # Scale clip to match output dimensions
            scaled_clip = temp_dir / f"seg_{seg_index:03d}_clip.mp4"
            scale_video(source_clips[clip_idx], scaled_clip, width, height)
            segment_files.append(scaled_clip)
            seg_index += 1
            clip_idx += 1

    if not segment_files:
        raise ValueError("No segments to compose")

    # Concatenate all segments (reencode for consistent format)
    raw_video = temp_dir / "raw_concat.mp4"
    concat_videos(segment_files, raw_video, reencode=True)

    # Burn captions if provided
    if caption_file and caption_file.exists():
        captioned_video = temp_dir / "captioned.mp4"
        burn_subtitles(raw_video, caption_file, captioned_video)
        current_video = captioned_video
    else:
        current_video = raw_video

    # Add background music if provided
    if background_music and background_music.exists():
        music_video = temp_dir / "with_music.mp4"
        add_background_music(current_video, background_music, music_video,
                              music_volume=0.06)
        current_video = music_video

    # Final encode with platform settings
    codec = platform_settings["codec"]
    crf = platform_settings["crf"]
    preset = platform_settings["preset"]
    audio_bitrate = platform_settings["audio_bitrate"]

    final_args = [
        "-i", str(current_video),
        "-c:v", codec, "-preset", preset, "-crf", str(crf),
        "-c:a", "aac", "-b:a", audio_bitrate,
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    ]

    max_dur = platform_settings.get("max_duration")
    if max_dur:
        final_args.extend(["-t", str(max_dur)])

    final_args.append(str(output_path))
    run_ffmpeg(final_args)

    # Cleanup temp directory
    shutil.rmtree(temp_dir, ignore_errors=True)

    return ComposedVideo(
        file_path=output_path,
        duration=get_duration(output_path),
        platform=platform,
        width=width,
        height=height,
    )
