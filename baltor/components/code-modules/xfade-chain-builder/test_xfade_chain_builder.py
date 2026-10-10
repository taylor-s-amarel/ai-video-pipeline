import shutil
import subprocess

import pytest

import xfade_chain_builder as xc


def test_offsets_and_total():
    assert xc.offsets([5, 4, 6], [("fade", 0.5), ("slideleft", 0.4)]) == [4.5, 8.1]
    assert xc.total_duration([5, 4, 6], [("fade", 0.5), ("slideleft", 0.4)]) == pytest.approx(14.1)


def test_graph_text():
    g, v, a = xc.build_chain([2, 2], [("dissolve", 0.5)])
    assert g == "[0:v][1:v]xfade=transition=dissolve:duration=0.5:offset=1.5[v1];[0:a][1:a]acrossfade=d=0.5:c1=tri:c2=tri[a1]"
    assert (v, a) == ("[v1]", "[a1]")


def test_validation():
    with pytest.raises(ValueError):
        xc.offsets([2, 2], [("spin", 0.5)])
    with pytest.raises(ValueError):
        xc.offsets([2, 2], [("fade", 3)])
    with pytest.raises(ValueError):
        xc.offsets([2, 1, 2], [("fade", 0.6), ("fade", 0.6)])
    with pytest.raises(ValueError):
        xc.build_chain([2], [])


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_rendered_duration_matches():
    durs = [1.0, 1.0, 1.0]
    trans = [("fade", 0.25), ("wipeleft", 0.25)]
    g, v, a = xc.build_chain(durs, trans)
    argv = ["ffmpeg", "-nostdin", "-v", "error"]
    for c in ("red", "green", "blue"):
        argv += ["-f", "lavfi", "-i", f"color=c={c}:s=64x64:r=20:d=1,format=yuv420p[out0];"
                 f"sine=f=440:d=1[out1]"]
    argv += ["-filter_complex", g, "-map", v, "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1",
             "-map", a, "-f", "null", "-"]
    r = subprocess.run(argv, capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    frames = len(r.stdout) // (64 * 64)
    assert abs(frames - xc.total_duration(durs, trans) * 20) <= 1
