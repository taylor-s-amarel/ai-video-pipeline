"""AI-generated commentary scripts for transformative content."""

import json
from dataclasses import dataclass, field

from src.analysis.content_analyzer import ContentAnalysis, ClipSuggestion
from src.utils.ai_client import ai_chat, parse_json_response


@dataclass
class CommentarySegment:
    text: str
    timing: str  # "before_clip", "during_clip", "after_clip", "intro", "outro"
    clip_index: int | None = None
    estimated_duration: float = 0.0  # estimated speech duration in seconds


@dataclass
class CommentaryScript:
    title: str
    hook: str
    segments: list[CommentarySegment]
    outro: str
    description: str
    total_commentary_duration: float = 0.0

    def full_narration_text(self) -> str:
        parts = [self.hook]
        parts.extend(s.text for s in self.segments)
        parts.append(self.outro)
        return "\n\n".join(parts)


SCRIPT_PROMPT = """You are a scriptwriter for a commentary/analysis YouTube channel. Write a commentary script for a video analyzing source content.

SOURCE ANALYSIS:
Title: {title}
Summary: {summary}
Topics: {topics}
Sentiment: {sentiment}

CLIPS BEING USED (with context):
{clips_info}

COMMENTARY ANGLES TO EXPLORE:
{angles}

Write a JSON script with this structure:
{{
    "title": "Engaging video title (under 70 chars)",
    "hook": "Opening 2-3 sentences that grab attention. Create curiosity. Under 15 seconds when spoken.",
    "segments": [
        {{
            "text": "Commentary text for this segment (2-4 sentences, substantive analysis)",
            "timing": "before_clip|during_clip|after_clip",
            "clip_index": 0
        }}
    ],
    "outro": "Closing statement with call to action. Under 10 seconds when spoken.",
    "description": "YouTube description (2-3 paragraphs with SEO keywords)"
}}

RULES:
- Hook must create an open loop or curiosity gap
- Each clip MUST have a before_clip AND after_clip commentary segment
- Commentary must be SUBSTANTIVE — actual analysis, not filler like "wow that's crazy"
- Use a conversational but authoritative tone
- Reference specific things said/shown in the clips
- Add educational context, fact-checking, or unique perspective
- Total commentary should be at LEAST 2x the total clip duration
- Description should include relevant keywords naturally
- Do NOT use generic phrases like "let's dive in" or "without further ado"
- Vary sentence structure and pacing"""


def _estimate_speech_duration(text: str) -> float:
    """Estimate speech duration at ~150 words per minute."""
    words = len(text.split())
    return (words / 150) * 60


def generate_commentary(analysis: ContentAnalysis,
                         clips: list[ClipSuggestion]) -> CommentaryScript:
    clips_info = ""
    for i, clip in enumerate(clips):
        clips_info += (
            f"Clip {i}: [{clip.start:.1f}s - {clip.end:.1f}s] "
            f"({clip.category}) - {clip.reason}\n"
            f"  Quote: \"{clip.quote}\"\n\n"
        )

    angles = "\n".join(f"- {a}" for a in analysis.commentary_angles[:5])

    prompt = SCRIPT_PROMPT.format(
        title=analysis.title_suggestions[0] if analysis.title_suggestions else "Untitled",
        summary=analysis.summary,
        topics=", ".join(analysis.topics),
        sentiment=analysis.sentiment,
        clips_info=clips_info,
        angles=angles,
    )

    raw = ai_chat(prompt, max_tokens=4096, json_mode=True)
    data = parse_json_response(raw)

    segments = []
    total_duration = 0.0

    for s in data.get("segments", []):
        duration = _estimate_speech_duration(s["text"])
        total_duration += duration
        segments.append(CommentarySegment(
            text=s["text"],
            timing=s["timing"],
            clip_index=s.get("clip_index"),
            estimated_duration=duration,
        ))

    hook_duration = _estimate_speech_duration(data.get("hook", ""))
    outro_duration = _estimate_speech_duration(data.get("outro", ""))
    total_duration += hook_duration + outro_duration

    return CommentaryScript(
        title=data.get("title", ""),
        hook=data.get("hook", ""),
        segments=segments,
        outro=data.get("outro", ""),
        description=data.get("description", ""),
        total_commentary_duration=total_duration,
    )
