import shutil

import pytest

from ffmpeg_progress_parser import ProgressParser, run_with_progress, with_progress_flags

BLOCK = """frame=120
fps=60.0
out_time_us=4000000
out_time=00:00:04.000000
speed=2.0x
progress=continue
frame=240
fps=60.0
out_time=00:00:08.000000
speed=N/A
progress=end
"""


def test_blocks():
    p = ProgressParser(duration=8.0)
    snaps = [s for s in (p.feed(l) for l in BLOCK.splitlines()) if s]
    assert len(snaps) == 2
    assert snaps[0]["percent"] == 50.0 and snaps[0]["eta_s"] == 2.0 and snaps[0]["frame"] == 120
    assert snaps[1]["done"] and snaps[1]["percent"] == 100.0 and snaps[1]["speed"] is None


def test_flags():
    assert with_progress_flags(["ffmpeg", "-i", "a"])[:5] == ["ffmpeg", "-progress", "pipe:1", "-nostats", "-nostdin"]
    with pytest.raises(ValueError):
        with_progress_flags(["ls"])


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_real_run():
    seen = []
    rc = run_with_progress(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=64x64:d=1:r=25", "-f", "null", "-"],
                           duration=1.0, on_progress=seen.append, timeout=60)
    assert rc == 0 and seen and seen[-1]["done"]
