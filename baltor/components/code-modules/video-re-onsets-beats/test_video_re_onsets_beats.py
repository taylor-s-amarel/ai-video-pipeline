import shutil

import numpy as np
import pytest

import video_re_onsets_beats as m
import video_re_synth as synth


def nearest_errors(found, truth):
    found = np.asarray(found)
    return [float(found[np.argmin(np.abs(found - t))] - t) for t in truth]


@pytest.mark.parametrize("period,bpm", [(0.5, 120.0), (0.6, 100.0), (0.4, 150.0)])
def test_click_track_onsets_tempo_and_beats(period, bpm):
    times = list(np.arange(0.5, 8.0, period))
    res = m.analyse_audio(synth.clicks(times, 8.5, 22050, noise=0.002))
    assert len(res["onsets_s"]) == len(times)
    assert max(abs(e) for e in nearest_errors(res["onsets_s"], times)) <= 0.030
    assert res["tempo_bpm"] == pytest.approx(bpm, abs=2.0)
    assert max(abs(e) for e in nearest_errors(res["beats_s"], times)) <= 0.05
    assert len(res["beats_s"]) == len(times)


def test_irregular_onsets_within_30_ms():
    rng = np.random.default_rng(4)
    times = []
    for t in sorted(rng.uniform(0.3, 5.5, 14)):
        if not times or t - times[-1] > 0.1:
            times.append(float(t))
    res = m.analyse_audio(synth.clicks(times, 6.0, 22050, noise=0.002))
    assert len(res["onsets_s"]) == len(times)
    assert max(abs(e) for e in nearest_errors(res["onsets_s"], times)) <= 0.030


def test_silence_has_no_onsets_and_no_tempo():
    res = m.analyse_audio(np.zeros(22050 * 3))
    assert res["onsets_s"] == [] and res["tempo_bpm"] is None and res["beats_s"] == []


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_end_to_end_from_a_file(tmp_path):
    times = list(np.arange(0.5, 6.0, 0.5))
    p = synth.write_wav(tmp_path / "c.wav", synth.clicks(times, 6.5, 44100, noise=0.002), 44100)
    res = m.run(str(p))
    assert res["status"] == "ok"
    assert max(abs(e) for e in nearest_errors(res["onsets_s"], times)) <= 0.030
    assert res["tempo_bpm"] == pytest.approx(120, abs=2)
