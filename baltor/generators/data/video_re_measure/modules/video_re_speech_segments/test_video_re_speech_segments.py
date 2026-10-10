import shutil

import numpy as np
import pytest

import video_re_speech_segments as m
import video_re_synth as synth

SEGS = [(0.5, 2.0), (3.0, 4.5)]


def test_speechlike_segments_are_found_within_100_ms():
    x = synth.speechlike(SEGS, 5.5, sr=16000)
    res = m.segments_from_audio(x, 16000)
    found = [(s["start_s"], s["end_s"]) for s in res["segments"]]
    assert len(found) == 2
    for (a, b), (fa, fb) in zip(SEGS, found):
        assert abs(fa - a) <= 0.1 and abs(fb - b) <= 0.1
    assert res["speech_ratio"] == pytest.approx(3.0 / 5.5, abs=0.05)
    assert all(s["syllabic_modulation"] > 0.4 for s in res["segments"])


def test_steady_tone_has_low_syllabic_modulation():
    t = np.arange(int(3 * 16000)) / 16000
    tone = 0.3 * (np.sin(2 * np.pi * 220 * t) + 0.5 * np.sin(2 * np.pi * 440 * t))
    x = np.concatenate([np.zeros(16000), tone, np.zeros(16000)]) + 0.001 * np.random.default_rng(0).standard_normal(5 * 16000)
    res = m.segments_from_audio(x, 16000)
    assert len(res["segments"]) == 1
    assert res["segments"][0]["syllabic_modulation"] < 0.2


def test_noise_only_has_no_speech():
    x = 0.01 * np.random.default_rng(2).standard_normal(3 * 16000)
    assert m.segments_from_audio(x, 16000)["segments"] == []


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_end_to_end_both_methods(tmp_path):
    p = synth.write_wav(tmp_path / "s.wav", synth.speechlike(SEGS, 5.5, sr=16000), 16000)
    res = m.run(str(p))
    assert res["status"] == "ok" and len(res["segments"]) == 2
    sd = m.run(str(p), method="silencedetect")
    assert sd["status"] == "ok" and len(sd["segments"]) == 2
    assert sd["segments"][0]["start_s"] == pytest.approx(0.5, abs=0.15)
