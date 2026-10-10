import json
import shutil
import sys
import types

import pytest

import video_re_synth as synth
import video_re_transcribe_adapter as m

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


@pytest.fixture
def audio_file(tmp_path):
    return str(synth.write_wav(tmp_path / "a.wav", synth.speechlike([(0.2, 1.8)], 2.0), 16000))


@ffmpeg
def test_unavailable_when_no_engine(monkeypatch, audio_file):
    monkeypatch.setattr(m, "engine_available", lambda name: False)
    res = m.run(audio_file)
    assert res["status"] == "unavailable" and len(res["tried"]) == 3


@ffmpeg
def test_fake_faster_whisper_words_and_masking(monkeypatch, audio_file):
    W = types.SimpleNamespace
    seg = W(start=0.2, end=1.8, text=" In 1970 five SCIENTISTS",
            words=[W(start=0.2, end=0.4, word=" In", probability=0.9), W(start=0.4, end=0.9, word=" 1970", probability=0.9),
                   W(start=0.9, end=1.2, word=" five", probability=0.9), W(start=1.2, end=1.8, word=" SCIENTISTS", probability=0.8)])

    class FakeModel:
        def __init__(self, name, device, compute_type, local_files_only):
            assert local_files_only is True  # no download unless asked
        def transcribe(self, path, word_timestamps):
            return iter([seg]), W(language="en")

    monkeypatch.setitem(sys.modules, "faster_whisper", types.SimpleNamespace(WhisperModel=FakeModel))
    monkeypatch.setattr(m, "engine_available", lambda name: name == "faster-whisper")
    res = m.run(audio_file, text_mode="masked")
    assert res["status"] == "ok" and res["engine"] == "faster-whisper" and res["language"] == "en"
    assert [w["word"] for w in res["words"]] == ["Word", "{n}", "word", "WORD"]
    assert res["segments"][0]["text"] == "Word {n} word WORD"
    assert res["word_count"] == 4 and res["words_estimated"] is False


def test_openai_whisper_refuses_to_download_by_default(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        m._openai_whisper("x.wav", "small", allow_download=False)


def test_whisper_cpp_json_parsing():
    data = {"result": {"language": "en"}, "transcription": [
        {"offsets": {"from": 0, "to": 300}, "text": " Hello"},
        {"offsets": {"from": 300, "to": 700}, "text": " there."},
        {"offsets": {"from": 1800, "to": 2100}, "text": " Next"}]}
    res = m.parse_whisper_cpp_json(data)
    assert [w["word"] for w in res["words"]] == ["Hello", "there.", "Next"]
    assert [(s["start_s"], s["end_s"]) for s in res["segments"]] == [(0.0, 0.7), (1.8, 2.1)]


def test_from_srt_file_estimates_word_times(tmp_path):
    p = tmp_path / "t.srt"
    p.write_text("1\n00:00:01,000 --> 00:00:03,000\nfour words right here\n")
    res = m.run("unused.mp4", from_path=str(p))
    assert res["engine"] == "file" and res["words_estimated"] is True
    assert [w["start_s"] for w in res["words"]] == [1.0, 1.5, 2.0, 2.5]


def test_from_whisper_json_file(tmp_path):
    p = tmp_path / "t.json"
    p.write_text(json.dumps({"language": "en", "segments": [
        {"start": 0.0, "end": 1.0, "text": "hi you", "words": [{"word": "hi", "start": 0.0, "end": 0.4},
                                                               {"word": "you", "start": 0.5, "end": 1.0}]}]}))
    res = m.run("unused.mp4", from_path=str(p), text_mode="none")
    assert res["word_count"] == 2 and res["words"][1]["word"] == "" and res["segments"][0]["text"] == ""
