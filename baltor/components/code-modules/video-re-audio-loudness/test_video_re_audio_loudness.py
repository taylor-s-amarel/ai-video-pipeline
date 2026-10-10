import shutil
import subprocess

import numpy as np
import pytest

import video_re_audio_loudness as m
import video_re_synth as synth

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


@ffmpeg
def test_halving_amplitude_lowers_loudness_by_6_db(tmp_path):
    loud = synth.write_wav(tmp_path / "loud.wav", synth.sine(5.0, 48000, 1000, 0.1), 48000)
    quiet = synth.write_wav(tmp_path / "quiet.wav", synth.sine(5.0, 48000, 1000, 0.05), 48000)
    a, b = m.run(str(loud)), m.run(str(quiet))
    assert a["status"] == "ok" and b["status"] == "ok"
    assert a["integrated_lufs"] - b["integrated_lufs"] == pytest.approx(6.02, abs=0.3)
    # a 1 kHz sine with RMS -23 dBFS in a mono file reads about -23 LUFS
    assert a["integrated_lufs"] == pytest.approx(-23.0, abs=0.7)
    assert a["rms_db"] == pytest.approx(-23.0, abs=0.2)
    assert a["true_peak_dbtp"] == pytest.approx(-20.0, abs=0.5)
    assert a["short_term"] and all(s["t_s"] >= 1 for s in a["short_term"])


@ffmpeg
def test_silence_share(tmp_path):
    x = np.concatenate([np.zeros(48000), synth.sine(3.0, 48000, 440, 0.2)])
    p = synth.write_wav(tmp_path / "gap.wav", x, 48000)
    res = m.run(str(p))
    assert res["silence"]["share"] == pytest.approx(0.25, abs=0.05)
    assert res["silence"]["segments"][0]["start_s"] == pytest.approx(0.0, abs=0.05)


@ffmpeg
def test_video_without_audio_is_unavailable(tmp_path):
    out = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=10:d=1",
                    "-c:v", "libx264", "-preset", "ultrafast", str(out)], check=True)
    res = m.run(str(out))
    assert res["status"] == "unavailable" and "integrated_lufs" not in res


def test_summary_parser_treats_gated_silence_as_null():
    text = "Summary:\n\n  Integrated loudness:\n    I:         -70.0 LUFS\n  Loudness range:\n    LRA:   0.0 LU\n"
    assert m.parse_summary(text)["integrated_lufs"] is None
