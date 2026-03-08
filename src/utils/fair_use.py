"""Fair use compliance checker for the video pipeline."""

from dataclasses import dataclass, field
from pathlib import Path
from src.utils.ffmpeg_utils import get_duration


@dataclass
class FairUseCheck:
    source_path: str
    clip_start: float
    clip_end: float
    has_commentary: bool = False
    has_visual_transform: bool = False
    has_attribution: bool = False
    commentary_duration: float = 0.0
    source_purpose: str = ""
    output_purpose: str = ""

    @property
    def clip_duration(self) -> float:
        return self.clip_end - self.clip_start

    @property
    def source_duration(self) -> float:
        try:
            return get_duration(self.source_path)
        except Exception:
            return 0.0

    @property
    def source_percentage(self) -> float:
        sd = self.source_duration
        if sd == 0:
            return 0.0
        return self.clip_duration / sd

    @property
    def commentary_ratio(self) -> float:
        if self.clip_duration == 0:
            return 0.0
        return self.commentary_duration / self.clip_duration


@dataclass
class FairUseResult:
    passed: bool
    score: int  # 0-100
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


MAX_CLIP_SECONDS = 30
MAX_SOURCE_PERCENTAGE = 0.10
MIN_COMMENTARY_RATIO = 2.0  # 2:1 commentary to source


def check_fair_use(check: FairUseCheck) -> FairUseResult:
    issues = []
    warnings = []
    score = 100

    # Clip duration check
    if check.clip_duration > MAX_CLIP_SECONDS:
        issues.append(
            f"Clip is {check.clip_duration:.1f}s, exceeds {MAX_CLIP_SECONDS}s limit"
        )
        score -= 25

    # Source percentage check
    if check.source_percentage > MAX_SOURCE_PERCENTAGE:
        pct = check.source_percentage * 100
        issues.append(
            f"Using {pct:.1f}% of source, exceeds {MAX_SOURCE_PERCENTAGE*100:.0f}% limit"
        )
        score -= 20

    # Commentary check
    if not check.has_commentary:
        issues.append("No commentary/narration added — not transformative")
        score -= 30
    elif check.commentary_ratio < MIN_COMMENTARY_RATIO:
        warnings.append(
            f"Commentary ratio is {check.commentary_ratio:.1f}:1, "
            f"recommend at least {MIN_COMMENTARY_RATIO}:1"
        )
        score -= 10

    # Visual transformation check
    if not check.has_visual_transform:
        warnings.append("No visual transformation applied (captions, overlays, effects)")
        score -= 10

    # Attribution check
    if not check.has_attribution:
        issues.append("No attribution to original creator")
        score -= 15

    # Purpose check
    if check.source_purpose and check.output_purpose:
        if check.source_purpose.lower() == check.output_purpose.lower():
            warnings.append(
                "Source and output serve the same purpose — weaker fair use argument"
            )
            score -= 10

    score = max(0, score)
    passed = len(issues) == 0 and score >= 60

    return FairUseResult(passed=passed, score=score, issues=issues, warnings=warnings)


def check_video_fair_use(clips: list[FairUseCheck]) -> FairUseResult:
    """Check fair use compliance for an entire video with multiple source clips."""
    all_issues = []
    all_warnings = []
    total_score = 0

    for i, clip in enumerate(clips):
        result = check_fair_use(clip)
        prefix = f"Clip {i+1}"
        all_issues.extend(f"[{prefix}] {issue}" for issue in result.issues)
        all_warnings.extend(f"[{prefix}] {warn}" for warn in result.warnings)
        total_score += result.score

    avg_score = total_score // len(clips) if clips else 0
    passed = len(all_issues) == 0 and avg_score >= 60

    return FairUseResult(
        passed=passed, score=avg_score, issues=all_issues, warnings=all_warnings
    )
