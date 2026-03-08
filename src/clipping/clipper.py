"""Extract and manage video clips from source material."""

from pathlib import Path
from dataclasses import dataclass

from src.analysis.content_analyzer import ClipSuggestion
from src.utils.ffmpeg_utils import clip_video, get_duration
from src.utils.fair_use import FairUseCheck, check_fair_use, MAX_CLIP_SECONDS


@dataclass
class ExtractedClip:
    file_path: Path
    start: float
    end: float
    source_path: str
    reason: str
    score: float
    category: str
    fair_use_score: int


def extract_clips(source_path: str | Path,
                   suggestions: list[ClipSuggestion],
                   output_dir: str | Path,
                   max_clips: int = 5) -> list[ExtractedClip]:
    source_path = Path(source_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_duration = get_duration(source_path)
    extracted = []

    for i, clip in enumerate(suggestions[:max_clips]):
        # Enforce fair use limits
        clip_duration = clip.end - clip.start
        if clip_duration > MAX_CLIP_SECONDS:
            clip_end = clip.start + MAX_CLIP_SECONDS
        else:
            clip_end = clip.end

        # Clamp to source bounds
        start = max(0, clip.start)
        end = min(clip_end, source_duration)

        # Run fair use check
        fu_check = FairUseCheck(
            source_path=str(source_path),
            clip_start=start,
            clip_end=end,
            has_commentary=False,  # Not yet; will be set during transformation
            has_visual_transform=False,
            has_attribution=False,
        )
        fu_result = check_fair_use(fu_check)

        # Extract the clip
        clip_path = output_dir / f"clip_{i:03d}_{clip.category}.mp4"
        clip_video(source_path, clip_path, start, end)

        extracted.append(ExtractedClip(
            file_path=clip_path,
            start=start,
            end=end,
            source_path=str(source_path),
            reason=clip.reason,
            score=clip.score,
            category=clip.category,
            fair_use_score=fu_result.score,
        ))

    return extracted
