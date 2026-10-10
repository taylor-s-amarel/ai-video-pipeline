import shutil
import subprocess

import pytest

import ffmpeg_detect_log_parser as d

LOG = """[blackdetect @ 0x1] black_start:0 black_end:1.5 black_duration:1.5
[Parsed_metadata_2 @ 0x2] lavfi.freezedetect.freeze_start: 3.2
[Parsed_metadata_2 @ 0x2] lavfi.freezedetect.freeze_duration: 2.4
[Parsed_metadata_2 @ 0x2] lavfi.freezedetect.freeze_end: 5.6
[silencedetect @ 0x3] silence_start: -0.01
[silencedetect @ 0x3] silence_end: 2.5 | silence_duration: 2.51
[silencedetect @ 0x3] silence_start: 9.0
[Parsed_cropdetect_0 @ 0x4] x1:0 x2:1919 y1:140 y2:939 w:1920 h:800 x:0 y:140 pts:1 t:0.04 crop=1920:800:0:140
[Parsed_cropdetect_0 @ 0x4] x1:0 x2:1919 y1:140 y2:939 w:1920 h:800 x:0 y:140 pts:2 t:0.08 crop=1920:800:0:140
"""


def test_parsers():
    assert d.parse_black(LOG) == [{"start": 0.0, "end": 1.5, "duration": 1.5}]
    assert d.parse_freeze(LOG) == [{"start": 3.2, "end": 5.6, "duration": 2.4}]
    assert d.parse_silence(LOG) == [{"start": 0.0, "end": 2.5, "duration": 2.51}, {"start": 9.0, "end": None, "duration": None}]
    assert d.parse_crop(LOG) == (1920, 800, 0, 140)
    assert d.parse_crop("") is None


def test_argv():
    a = d.analyse_argv("x.mp4", audio=False)
    assert "-an" in a and a[-3:] == ["-f", "null", "-"]


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_real_black_and_silence(tmp_path):
    p = tmp_path / "t.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error",
                    "-f", "lavfi", "-i", "color=black:s=64x64:d=1:r=10[a];color=red:s=64x64:d=2:r=10[b];[a][b]concat=n=2:v=1:a=0[out0]",
                    "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "3", "-pix_fmt", "yuv420p", str(p)],
                   check=True, timeout=60)
    rep = d.analyse(str(p), black_min_s=0.5, silence_min_s=1.0)
    assert rep["black"] and rep["black"][0]["end"] == pytest.approx(1.0, abs=0.15)
    assert rep["silence"] and rep["silence"][0]["start"] == 0.0
