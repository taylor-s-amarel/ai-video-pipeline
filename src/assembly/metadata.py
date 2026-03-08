"""Generate SEO-optimized metadata for video uploads."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.utils.ai_client import ai_chat, parse_json_response


@dataclass
class VideoMetadata:
    title: str
    description: str
    tags: list[str]
    category: str
    hashtags: list[str] = field(default_factory=list)
    attribution: list[dict] = field(default_factory=list)  # [{"creator": ..., "url": ...}]

    def youtube_description(self) -> str:
        desc = self.description

        if self.hashtags:
            desc += "\n\n" + " ".join(f"#{h}" for h in self.hashtags[:15])

        if self.attribution:
            desc += "\n\n--- Credits ---"
            for attr in self.attribution:
                desc += f"\nOriginal: {attr.get('creator', 'Unknown')} - {attr.get('url', '')}"

        desc += "\n\n---\nThis video contains commentary and analysis of third-party content. "
        desc += "All clips are used under fair use for the purpose of criticism, "
        desc += "commentary, and education."

        return desc

    def tiktok_description(self) -> str:
        desc = self.description[:150]  # TikTok limit
        tags = " ".join(f"#{h}" for h in self.hashtags[:5])
        return f"{desc}\n{tags}"

    def save(self, path: str | Path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "title": self.title,
                "description": self.description,
                "tags": self.tags,
                "category": self.category,
                "hashtags": self.hashtags,
                "attribution": self.attribution,
                "youtube_description": self.youtube_description(),
                "tiktok_description": self.tiktok_description(),
            }, f, indent=2, ensure_ascii=False)


METADATA_PROMPT = """Generate SEO-optimized YouTube metadata for this video.

VIDEO TITLE: {title}
VIDEO SUMMARY: {summary}
TOPICS: {topics}
SOURCE CREATORS: {creators}

Return ONLY valid JSON:
{{
    "title": "Optimized title under 70 characters, include main keyword",
    "description": "3-4 paragraph description. First 2 lines are crucial (shown before Show More). Include keywords naturally. Add timestamps if applicable.",
    "tags": ["tag1", "tag2", ... up to 30 tags, mix of broad and specific],
    "category": "Education|Science & Technology|Entertainment|News & Politics|People & Blogs",
    "hashtags": ["hashtag1", "hashtag2", ... up to 15]
}}

SEO RULES:
- Title: front-load the main keyword, under 70 chars, create curiosity
- Description: first 160 chars are most important (Google snippet)
- Tags: include exact-match, broad, and long-tail keywords
- Mix trending and evergreen tags"""


def generate_metadata(title: str, summary: str, topics: list[str],
                       source_creators: list[dict]) -> VideoMetadata:
    creators_str = ", ".join(
        c.get("creator", "Unknown") for c in source_creators
    )

    prompt = METADATA_PROMPT.format(
        title=title,
        summary=summary,
        topics=", ".join(topics),
        creators=creators_str,
    )

    raw = ai_chat(prompt, max_tokens=2048, json_mode=True)
    data = parse_json_response(raw)

    return VideoMetadata(
        title=data.get("title", title),
        description=data.get("description", summary),
        tags=data.get("tags", []),
        category=data.get("category", "Education"),
        hashtags=data.get("hashtags", []),
        attribution=source_creators,
    )
