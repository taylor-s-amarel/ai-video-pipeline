import json
from types import SimpleNamespace

import pytest

import whisper_word_timestamps_adapter as wa

RESULT = {"text": " Hello world", "segments": [
    {"start": 0.0, "end": 1.0, "words": [{"word": " Hello", "start": 0.1, "end": 0.5, "probability": 0.98},
                                         {"word": " ", "start": 0.5, "end": 0.5}]},
    {"start": 1.0, "end": 2.0, "words": [{"word": " world.", "start": 0.45, "end": 0.9, "probability": 0.9}]},
]}


def test_openai_result_normalised_and_monotonic():
    words = wa.from_openai_whisper_result(RESULT)
    assert [w["word"] for w in words] == ["Hello", "world."]
    assert words[1]["start"] == 0.5  # clamped after previous end
    assert wa.from_openai_whisper_result(json.dumps(RESULT)) == words


def test_objects_like_faster_whisper():
    seg = SimpleNamespace(words=[SimpleNamespace(word=" Hi", start=0.0, end=0.2, probability=0.5)])
    assert wa.from_segments([seg]) == [{"word": "Hi", "start": 0.0, "end": 0.2, "probability": 0.5}]


def test_missing_dependency_message(monkeypatch):
    import builtins
    real = builtins.__import__

    def fake(name, *a, **k):
        if name == "faster_whisper":
            raise ImportError("no")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)
    with pytest.raises(RuntimeError, match="pip install faster-whisper"):
        wa.transcribe_faster_whisper("x.wav")
