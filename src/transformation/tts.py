"""Text-to-speech generation using Edge-TTS (free) or ElevenLabs (premium)."""

import asyncio
import subprocess
from pathlib import Path
from dataclasses import dataclass

from config.settings import settings
from src.utils.ffmpeg_utils import get_duration


@dataclass
class TTSResult:
    audio_path: Path
    duration: float
    text: str


async def _edge_tts_generate(text: str, output_path: Path,
                               voice: str | None = None) -> Path:
    import edge_tts
    voice = voice or settings.tts_voice
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    return output_path


def generate_speech_edge(text: str, output_path: str | Path,
                          voice: str | None = None) -> TTSResult:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    asyncio.run(_edge_tts_generate(text, output_path, voice))

    # Verify the mp3 was generated and is not empty/corrupt
    if not output_path.exists() or output_path.stat().st_size < 100:
        # Retry with slightly modified text (add padding)
        padded = text.rstrip('.') + ". "
        asyncio.run(_edge_tts_generate(padded, output_path, voice))

    if not output_path.exists() or output_path.stat().st_size < 100:
        raise RuntimeError(f"edge-tts produced empty/corrupt audio for: {text[:50]}...")

    # Convert to wav for consistent pipeline format
    wav_path = output_path.with_suffix(".wav")
    if output_path.suffix != ".wav":
        conv = subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
            "-i", str(output_path), "-acodec", "pcm_s16le",
            "-ar", "24000", str(wav_path)
        ], capture_output=True, text=True)
        if conv.returncode != 0:
            raise RuntimeError(
                f"ffmpeg mp3-to-wav conversion failed (exit {conv.returncode}): {conv.stderr}"
            )
        output_path.unlink(missing_ok=True)
        output_path = wav_path

    duration = get_duration(output_path)

    return TTSResult(audio_path=output_path, duration=duration, text=text)


def generate_speech_elevenlabs(text: str, output_path: str | Path,
                                voice_id: str | None = None) -> TTSResult:
    from elevenlabs import ElevenLabs

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    voice_id = voice_id or settings.elevenlabs_voice_id

    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )

    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    duration = get_duration(output_path)

    return TTSResult(audio_path=output_path, duration=duration, text=text)


def generate_speech(text: str, output_path: str | Path,
                     provider: str | None = None) -> TTSResult:
    provider = provider or settings.tts_provider

    if provider == "elevenlabs":
        return generate_speech_elevenlabs(text, output_path)
    else:
        return generate_speech_edge(text, output_path)


def tts_to_transcript(tts_segments: list[TTSResult]) -> "TranscriptionResult":
    """Build a TranscriptionResult from TTS results with estimated word timings.

    This avoids re-transcribing TTS audio with whisper — we already know
    the exact text and duration for each segment.
    """
    from src.analysis.transcriber import TranscriptionResult, Segment, WordTimestamp

    segments = []
    offset = 0.0

    for tts in tts_segments:
        words_raw = tts.text.split()
        if not words_raw:
            offset += tts.duration
            continue

        # Distribute duration proportionally by character count
        total_chars = sum(len(w) for w in words_raw)
        word_timestamps = []
        cursor = offset

        for w in words_raw:
            w_duration = (len(w) / max(total_chars, 1)) * tts.duration
            word_timestamps.append(WordTimestamp(
                word=w, start=round(cursor, 3),
                end=round(cursor + w_duration, 3),
            ))
            cursor += w_duration

        segments.append(Segment(
            text=tts.text,
            start=round(offset, 3),
            end=round(offset + tts.duration, 3),
            words=word_timestamps,
        ))
        offset += tts.duration

    return TranscriptionResult(
        text=" ".join(t.text for t in tts_segments),
        segments=segments,
        language="en",
        duration=offset,
    )


def generate_multi_segment(segments: list[dict], output_dir: str | Path,
                            provider: str | None = None) -> list[TTSResult]:
    """Generate TTS for multiple segments.

    Each segment dict should have 'text' and optionally 'filename'.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, seg in enumerate(segments):
        filename = seg.get("filename", f"segment_{i:03d}.mp3")
        output_path = output_dir / filename
        result = generate_speech(seg["text"], output_path, provider)
        results.append(result)

    return results
