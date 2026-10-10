import shutil
import subprocess

import pytest

from concat_demuxer_list import argv, compatible, list_text, needs_unsafe, quote


def test_quoting():
    assert quote("it's.mp4") == "'it'\\''s.mp4'"
    with pytest.raises(ValueError):
        quote("a\nb")


def test_list_text_and_trims():
    t = list_text(["a.mp4", {"path": "b.mp4", "inpoint": 1.5, "outpoint": 3}])
    assert t.splitlines() == ["ffconcat version 1.0", "file 'a.mp4'", "file 'b.mp4'", "inpoint 1.500000",
                              "outpoint 3.000000"]
    with pytest.raises(ValueError):
        list_text([{"path": "x", "duration": -1}])


def test_safe_flag_and_compat():
    assert not needs_unsafe(["a.mp4", "dir/b_1-2.mp4"])
    assert needs_unsafe(["/abs/a.mp4"]) and needs_unsafe(["../a.mp4"]) and needs_unsafe(["it's b.mp4"])
    assert "-safe" in argv("l.txt", "o.mp4", paths=["/abs/x.mp4"])
    probs = compatible([{"codec": "h264", "width": 1080}, {"codec": "hevc", "width": 1080}], keys=("codec", "width"))
    assert probs == ["clip 2: codec 'hevc' differs from clip 1 'h264'"]


@pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="ffmpeg missing")
def test_real_concat(tmp_path):
    names = ["one.mp4", "it's two.mp4"]
    for n in names:
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=64x64:d=1:r=10",
                        "-pix_fmt", "yuv420p", str(tmp_path / n)], check=True, timeout=60)
    lst = tmp_path / "list.txt"
    lst.write_text(list_text(names))
    out = tmp_path / "joined.mp4"
    a = argv(str(lst), str(out), paths=names)
    subprocess.run(a[:1] + ["-v", "error"] + a[1:], check=True, timeout=60, cwd=tmp_path)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(out)], capture_output=True, text=True, check=True).stdout)
    assert abs(dur - 2.0) < 0.15
