"""Audio mixing — combine commentary, source audio, and background music."""

from pathlib import Path
from dataclasses import dataclass
from src.utils.ffmpeg_utils import run_ffmpeg, get_duration


@dataclass
class MixedAudio:
    file_path: Path
    duration: float


def mix_commentary_with_source(
    commentary_path: str | Path,
    source_audio_path: str | Path | None,
    output_path: str | Path,
    source_volume: float = 0.12,
    commentary_volume: float = 1.0,
) -> MixedAudio:
    """Mix commentary voice over ducked source audio."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if source_audio_path and Path(source_audio_path).exists():
        run_ffmpeg([
            "-i", str(commentary_path),
            "-i", str(source_audio_path),
            "-filter_complex",
            f"[0:a]volume={commentary_volume}[voice];"
            f"[1:a]volume={source_volume}[bg];"
            f"[voice][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "[out]",
            "-c:a", "aac", "-b:a", "192k",
            str(output_path),
        ])
    else:
        # Just normalize the commentary
        run_ffmpeg([
            "-i", str(commentary_path),
            "-af", f"volume={commentary_volume},loudnorm=I=-16:LRA=11:TP=-1.5",
            "-c:a", "aac", "-b:a", "192k",
            str(output_path),
        ])

    return MixedAudio(
        file_path=output_path,
        duration=get_duration(output_path),
    )


def add_background_music(
    voice_path: str | Path,
    music_path: str | Path,
    output_path: str | Path,
    music_volume: float = 0.06,
    fade_out_duration: float = 3.0,
) -> MixedAudio:
    """Add looping background music under voice audio with fade-out."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    voice_duration = get_duration(voice_path)

    run_ffmpeg([
        "-i", str(voice_path),
        "-stream_loop", "-1", "-i", str(music_path),
        "-filter_complex",
        f"[1:a]volume={music_volume},"
        f"afade=t=out:st={voice_duration - fade_out_duration}:d={fade_out_duration}[music];"
        f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[out]",
        "-map", "[out]",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(voice_duration),
        str(output_path),
    ])

    return MixedAudio(
        file_path=output_path,
        duration=get_duration(output_path),
    )


def normalize_audio(input_path: str | Path, output_path: str | Path) -> MixedAudio:
    """Loudness-normalize audio to broadcast standards."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    run_ffmpeg([
        "-i", str(input_path),
        "-af", "loudnorm=I=-16:LRA=11:TP=-1.5",
        "-c:a", "aac", "-b:a", "192k",
        str(output_path),
    ])

    return MixedAudio(
        file_path=output_path,
        duration=get_duration(output_path),
    )
