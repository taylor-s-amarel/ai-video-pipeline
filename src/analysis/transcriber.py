"""Transcribe audio/video using faster-whisper or OpenAI Whisper."""

import json
from pathlib import Path
from dataclasses import dataclass, field
from src.utils.ffmpeg_utils import extract_audio


@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float
    confidence: float = 1.0


@dataclass
class Segment:
    text: str
    start: float
    end: float
    words: list[WordTimestamp] = field(default_factory=list)


@dataclass
class TranscriptionResult:
    text: str
    segments: list[Segment]
    language: str
    duration: float

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "language": self.language,
            "duration": self.duration,
            "segments": [
                {
                    "text": s.text,
                    "start": s.start,
                    "end": s.end,
                    "words": [
                        {"word": w.word, "start": w.start, "end": w.end,
                         "confidence": w.confidence}
                        for w in s.words
                    ]
                }
                for s in self.segments
            ]
        }

    def save(self, path: str | Path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str | Path) -> "TranscriptionResult":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        segments = []
        for s in data["segments"]:
            words = [
                WordTimestamp(w["word"], w["start"], w["end"], w.get("confidence", 1.0))
                for w in s.get("words", [])
            ]
            segments.append(Segment(s["text"], s["start"], s["end"], words))
        return cls(
            text=data["text"],
            segments=segments,
            language=data["language"],
            duration=data["duration"],
        )


def transcribe(file_path: str | Path, model_size: str = "base",
               language: str | None = None) -> TranscriptionResult:
    """Transcribe audio/video file using faster-whisper."""
    from faster_whisper import WhisperModel

    file_path = Path(file_path)

    # Extract audio if it's a video file
    if file_path.suffix.lower() in ('.mp4', '.mkv', '.avi', '.mov', '.webm'):
        audio_path = file_path.parent / f"{file_path.stem}_audio.wav"
        extract_audio(file_path, audio_path)
    else:
        audio_path = file_path

    import os
    os.environ.setdefault("OMP_NUM_THREADS", "2")

    kwargs = {"word_timestamps": True, "vad_filter": True}
    if language:
        kwargs["language"] = language

    # Try GPU first, fall back to CPU — catch errors at both load AND transcribe time
    raw_segments = info = None
    for device, compute in [("cuda", "float16"), ("cpu", "int8"), ("cpu", "float32")]:
        try:
            kw = {"device": device, "compute_type": compute}
            if device == "cpu":
                kw["cpu_threads"] = 2
            model = WhisperModel(model_size, **kw)
            raw_segments, info = model.transcribe(str(audio_path), **kwargs)
            break
        except Exception:
            continue

    if raw_segments is None:
        raise RuntimeError("Whisper transcription failed on all backends (cuda, cpu/int8, cpu/float32)")

    segments = []
    full_text_parts = []

    for seg in raw_segments:
        words = []
        if seg.words:
            words = [
                WordTimestamp(
                    word=w.word.strip(),
                    start=w.start,
                    end=w.end,
                    confidence=w.probability,
                )
                for w in seg.words
            ]

        segment = Segment(
            text=seg.text.strip(),
            start=seg.start,
            end=seg.end,
            words=words,
        )
        segments.append(segment)
        full_text_parts.append(seg.text.strip())

    # Clean up temp audio
    if audio_path != file_path and audio_path.exists():
        audio_path.unlink()

    return TranscriptionResult(
        text=" ".join(full_text_parts),
        segments=segments,
        language=info.language,
        duration=info.duration,
    )
