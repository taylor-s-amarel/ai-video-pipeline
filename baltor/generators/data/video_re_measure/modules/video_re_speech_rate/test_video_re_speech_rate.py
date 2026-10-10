import shutil

import pytest

import video_re_speech_rate as m
import video_re_synth as synth


def timed_words(n, start=0.0, word_s=0.3, gap_s=0.1, long_pause_after=None, long_pause_s=2.0):
    out, t = [], start
    for i in range(n):
        out.append({"start_s": t, "end_s": t + word_s, "word": "w"})
        t += word_s + gap_s
        if long_pause_after is not None and i == long_pause_after:
            t += long_pause_s
    return out


def test_transcript_rate_is_exact():
    res = m.run(transcript={"words": timed_words(150)})  # 150 words, 0.4 s each slot, span 59.9 s
    assert res["method"] == "transcript"
    assert res["speech_wpm"] == pytest.approx(150 * 60 / 59.9, rel=1e-3)
    assert res["articulation_wpm"] == pytest.approx(200.0)
    assert res["pauses"]["count"] == 0


def test_long_pause_is_excluded_from_speaking_time():
    res = m.run(transcript={"words": timed_words(20, long_pause_after=9, long_pause_s=3.0)})
    assert res["speaking_time_s"] == pytest.approx(res["span_s"] - 3.1, abs=1e-6)
    assert res["overall_wpm"] < res["speech_wpm"]
    assert res["pauses"]["longest_s"] == pytest.approx(3.1)


def test_estimated_word_times_are_flagged():
    words = [dict(w, estimated=True) for w in timed_words(10)]
    res = m.run(transcript={"words": words})
    assert res["pauses"] is None and res["confidence"] < 0.9 and res["articulation_wpm"] is None


@pytest.mark.parametrize("rate", [3.0, 4.0, 5.0])
def test_syllable_estimate_tracks_syllable_rate(rate):
    x = synth.speechlike([(0.5, 6.5)], 7.0, sr=16000, syllables_per_s=rate)
    res = m.from_audio(x)
    assert res["syllables_per_s"] == pytest.approx(rate, rel=0.15)
    assert res["speech_wpm"] == pytest.approx(rate * 60 / 1.5, rel=0.15)
    assert res["method"] == "syllable-estimate" and res["confidence"] == 0.4


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_from_a_file(tmp_path):
    p = synth.write_wav(tmp_path / "s.wav", synth.speechlike([(0.5, 5.5)], 6.0, sr=16000, syllables_per_s=4.0), 16000)
    res = m.run(str(p))
    assert res["status"] == "ok" and res["speech_wpm"] == pytest.approx(160, rel=0.15)
