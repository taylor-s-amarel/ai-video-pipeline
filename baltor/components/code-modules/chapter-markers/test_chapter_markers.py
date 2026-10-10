import json
import shutil
import subprocess

import pytest

from chapter_markers import ffmetadata, mux_argv, youtube_chapters


def test_youtube_ok_and_problems():
    text, probs = youtube_chapters([(0, "Hook"), (12, "FACT 1"), (31, "FACT 2")], duration=64)
    assert text == "00:00 Hook\n00:12 FACT 1\n00:31 FACT 2\n" and probs == []
    _, probs = youtube_chapters([(5, "a"), (8, "b")], duration=20)
    assert any("00:00" in p for p in probs) and any("three" in p for p in probs) and any("< 10s" in p for p in probs)
    text, _ = youtube_chapters([(0, "a"), (1800, "b"), (3700, "c")], duration=4000)
    assert text.splitlines()[2] == "1:01:40 c"


def test_ffmetadata_escaping():
    meta = ffmetadata([(0, "A=B;C"), (10.5, "Two")], duration=20, title="T#1")
    assert meta.startswith(";FFMETADATA1\ntitle=T\\#1\n")
    assert r"title=A\=B\;C" in meta and "START=10500" in meta and "END=20000" in meta
    with pytest.raises(ValueError):
        ffmetadata([(0, "a"), (30, "b")], duration=20)


@pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="ffmpeg missing")
def test_mux_into_mp4(tmp_path):
    vid = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=black:s=64x64:d=3:r=10",
                    "-c:v", "libx264", str(vid)], check=True, timeout=60, stdin=subprocess.DEVNULL)
    meta = tmp_path / "m.txt"
    meta.write_text(ffmetadata([(0, "Intro"), (1.5, "Main")], duration=3), encoding="utf-8")
    out = tmp_path / "o.mp4"
    subprocess.run(mux_argv(str(vid), str(meta), str(out))[:1] + ["-v", "error"] + mux_argv(str(vid), str(meta), str(out))[1:],
                   check=True, timeout=60, stdin=subprocess.DEVNULL)
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_chapters", "-of", "json", str(out)],
                                     capture_output=True, text=True, check=True).stdout)
    assert [c["tags"]["title"] for c in info["chapters"]] == ["Intro", "Main"]
