"""Word timestamps from Whisper-family speech recognisers, normalised.

Produces one list shape for every source::

    [{"word": "Hello", "start": 0.12, "end": 0.48, "probability": 0.97}, ...]

Sources:

* ``transcribe_faster_whisper``: runs faster-whisper locally
  (``pip install faster-whisper``; imported lazily). On first use the model
  is downloaded from the Hugging Face Hub and cached on disk.
* ``from_openai_whisper_result``: the dict returned by
  ``whisper.transcribe(..., word_timestamps=True)`` (openai-whisper package)
  or its saved JSON.
* ``from_segments``: any segments list whose items carry ``words`` with
  ``word``/``start``/``end``.

Leading spaces that Whisper puts on tokens are stripped; empty tokens are
dropped; times are made monotonic.

Usage::

    from whisper_word_timestamps_adapter import transcribe_faster_whisper
    words = transcribe_faster_whisper("narration.wav", model_size="small", language="en")
"""

from __future__ import annotations

import json


def _clean(words: list[dict]) -> list[dict]:
    out = []
    last = 0.0
    for w in words:
        token = str(w.get("word", "")).strip()
        if not token:
            continue
        start = max(float(w["start"]), last)
        end = max(float(w["end"]), start)
        item = {"word": token, "start": round(start, 3), "end": round(end, 3)}
        if w.get("probability") is not None:
            item["probability"] = round(float(w["probability"]), 4)
        out.append(item)
        last = end
    return out


def from_segments(segments) -> list[dict]:
    words = []
    for seg in segments:
        for w in (seg.get("words") if isinstance(seg, dict) else getattr(seg, "words", None)) or []:
            if isinstance(w, dict):
                words.append(w)
            else:
                words.append({"word": w.word, "start": w.start, "end": w.end,
                              "probability": getattr(w, "probability", None)})
    return _clean(words)


def from_openai_whisper_result(result) -> list[dict]:
    if isinstance(result, str):
        result = json.loads(result)
    return from_segments(result.get("segments", []))


def transcribe_faster_whisper(audio_path: str, model_size: str = "small", language: str | None = None,
                              device: str = "cpu", compute_type: str = "int8", beam_size: int = 5) -> list[dict]:
    try:
        from faster_whisper import WhisperModel  # lazy: heavy optional dependency
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("faster-whisper is not installed: pip install faster-whisper") from exc
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, _info = model.transcribe(audio_path, word_timestamps=True, language=language, beam_size=beam_size)
    return from_segments(list(segments))
