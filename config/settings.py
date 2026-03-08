"""Central configuration for the AI Video Pipeline."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class PlatformExport:
    """Export settings per platform."""
    YOUTUBE = {
        "width": 1920, "height": 1080, "aspect": "16:9",
        "codec": "libx264", "preset": "slow", "crf": 18,
        "audio_codec": "aac", "audio_bitrate": "192k",
        "max_duration": None, "format": "mp4",
    }
    YOUTUBE_4K = {
        "width": 3840, "height": 2160, "aspect": "16:9",
        "codec": "libx265", "preset": "slow", "crf": 20,
        "audio_codec": "aac", "audio_bitrate": "256k",
        "max_duration": None, "format": "mp4",
    }
    SHORTS = {
        "width": 1080, "height": 1920, "aspect": "9:16",
        "codec": "libx264", "preset": "medium", "crf": 20,
        "audio_codec": "aac", "audio_bitrate": "128k",
        "max_duration": 60, "format": "mp4",
    }
    TIKTOK = {
        "width": 1080, "height": 1920, "aspect": "9:16",
        "codec": "libx264", "preset": "medium", "crf": 20,
        "audio_codec": "aac", "audio_bitrate": "128k",
        "max_duration": 180, "format": "mp4",
    }
    REELS = {
        "width": 1080, "height": 1920, "aspect": "9:16",
        "codec": "libx264", "preset": "medium", "crf": 20,
        "audio_codec": "aac", "audio_bitrate": "128k",
        "max_duration": 90, "format": "mp4",
    }
    TWITTER = {
        "width": 1280, "height": 720, "aspect": "16:9",
        "codec": "libx264", "preset": "medium", "crf": 22,
        "audio_codec": "aac", "audio_bitrate": "128k",
        "max_duration": 140, "format": "mp4",
    }


class FairUsePolicy:
    """Fair use compliance thresholds."""
    MAX_CLIP_SECONDS = 30
    MAX_SOURCE_PERCENTAGE = 0.10  # 10% of source
    REQUIRE_COMMENTARY = True
    REQUIRE_VISUAL_TRANSFORM = True
    REQUIRE_ATTRIBUTION = True


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = {"env_file": str(BASE_DIR / ".env"), "extra": "ignore"}

    # ── LLM API Keys ──
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""
    cerebras_api_key: str = ""
    sambanova_api_key: str = ""
    mistral_api_key: str = ""
    openrouter_api_key: str = ""
    github_token: str = ""
    siliconcloud_api_key: str = ""
    novita_api_key: str = ""
    cloudflare_api_key: str = ""
    cloudflare_account_id: str = ""
    together_api_key: str = ""

    # ── Ollama (local) ──
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # ── Image Generation Keys ──
    stability_api_key: str = ""
    replicate_api_token: str = ""
    stable_horde_api_keys: str = ""
    pollinations_api_key: str = ""

    # ── TTS Keys ──
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # ── Social Platform Keys ──
    youtube_api_key: str = ""
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "ai_video_pipeline/1.0"

    # ── Directories ──
    output_dir: Path = BASE_DIR / "output"
    assets_dir: Path = BASE_DIR / "assets"
    temp_dir: Path = BASE_DIR / "temp"

    # ── Pipeline ──
    max_source_clip_seconds: int = 30
    default_platform: str = "youtube"
    auto_publish: bool = False
    require_human_review: bool = True

    # ── Hardware ──
    use_gpu: bool = True
    ffmpeg_hwaccel: str = "auto"

    # ── AI Model Settings ──
    ai_provider: str = "ollama"
    ai_model: str = "llama3.2"
    whisper_model: str = "base"

    # ── Image Generation Settings ──
    image_provider: str = "pollinations"  # together, stable_horde, pollinations, dalle, stability
    image_model: str = ""  # Provider-specific model override

    # ── TTS ──
    tts_provider: str = "edge-tts"
    tts_voice: str = "en-US-ChristopherNeural"

    def get_platform_settings(self, platform: str) -> dict:
        platform_map = {
            "youtube": PlatformExport.YOUTUBE,
            "youtube_4k": PlatformExport.YOUTUBE_4K,
            "shorts": PlatformExport.SHORTS,
            "tiktok": PlatformExport.TIKTOK,
            "reels": PlatformExport.REELS,
            "twitter": PlatformExport.TWITTER,
        }
        return platform_map.get(platform, PlatformExport.YOUTUBE)


settings = Settings()
