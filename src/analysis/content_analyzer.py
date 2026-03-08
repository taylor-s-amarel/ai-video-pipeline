"""AI-powered content analysis for identifying clip-worthy moments."""

import json
from dataclasses import dataclass, field

from src.analysis.transcriber import TranscriptionResult
from src.utils.ai_client import ai_chat, parse_json_response


@dataclass
class ClipSuggestion:
    start: float
    end: float
    reason: str
    score: float  # 0-1 virality/interest score
    category: str  # "controversial", "funny", "informative", "dramatic", "surprising"
    quote: str  # key quote from the segment


@dataclass
class ContentAnalysis:
    summary: str
    topics: list[str]
    sentiment: str  # overall sentiment
    clip_suggestions: list[ClipSuggestion]
    commentary_angles: list[str]
    title_suggestions: list[str]
    tags: list[str]


ANALYSIS_PROMPT = """You are a content analyst for a video commentary channel. Analyze this transcript and return a JSON response.

SOURCE VIDEO TITLE: {title}
SOURCE CREATOR: {creator}
TRANSCRIPT:
{transcript}

Return ONLY valid JSON with this structure:
{{
    "summary": "2-3 sentence summary of the content",
    "topics": ["topic1", "topic2", ...],
    "sentiment": "positive/negative/neutral/mixed",
    "clip_suggestions": [
        {{
            "start": <start_seconds>,
            "end": <end_seconds>,
            "reason": "why this clip is interesting",
            "score": <0.0-1.0>,
            "category": "controversial|funny|informative|dramatic|surprising",
            "quote": "key quote from this segment"
        }}
    ],
    "commentary_angles": [
        "Angle 1: description of a commentary perspective",
        "Angle 2: ..."
    ],
    "title_suggestions": [
        "Engaging title option 1",
        "Engaging title option 2"
    ],
    "tags": ["relevant", "seo", "tags"]
}}

RULES:
- Each clip_suggestion must be under 30 seconds (end - start <= 30)
- Suggest 3-8 clips ranked by score
- Commentary angles should be substantive and analytical, not generic
- Titles should be engaging but not clickbait
- Focus on moments with high emotional energy, controversy, or insight"""


def analyze_content(transcript: TranscriptionResult,
                     title: str = "", creator: str = "") -> ContentAnalysis:
    # Build timestamped transcript
    timestamped = ""
    for seg in transcript.segments:
        mins = int(seg.start // 60)
        secs = int(seg.start % 60)
        timestamped += f"[{mins:02d}:{secs:02d}] {seg.text}\n"

    prompt = ANALYSIS_PROMPT.format(
        title=title or "Unknown",
        creator=creator or "Unknown",
        transcript=timestamped[:12000],  # Truncate for token limits
    )

    raw = ai_chat(prompt, max_tokens=4096, json_mode=True)
    data = parse_json_response(raw)

    clips = [
        ClipSuggestion(
            start=c["start"], end=c["end"], reason=c["reason"],
            score=c["score"], category=c["category"], quote=c["quote"],
        )
        for c in data.get("clip_suggestions", [])
    ]

    return ContentAnalysis(
        summary=data.get("summary", ""),
        topics=data.get("topics", []),
        sentiment=data.get("sentiment", "neutral"),
        clip_suggestions=sorted(clips, key=lambda c: c.score, reverse=True),
        commentary_angles=data.get("commentary_angles", []),
        title_suggestions=data.get("title_suggestions", []),
        tags=data.get("tags", []),
    )
