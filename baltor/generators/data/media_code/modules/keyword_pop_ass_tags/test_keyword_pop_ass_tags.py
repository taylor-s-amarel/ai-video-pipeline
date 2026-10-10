import shutil
import subprocess

import pytest

from keyword_pop_ass_tags import bgr, escape, pop_line, pop_line_from_words, pop_tags


def test_tags():
    assert pop_tags(0) == "{\\fscx100\\fscy100\\t(0,72,0.5,\\fscx112\\fscy112)\\t(72,180,2,\\fscx100\\fscy100)}"
    assert pop_tags(100, color="#FFD21F").startswith("{\\1c&H1FD2FF&")


def test_line_and_escaping():
    line = pop_line("for {14} days", 1, 500)
    assert "\\{14\\}{\\r}" in line and line.startswith("for {\\1c")
    assert escape("a\\b") == "a\uff3cb"
    with pytest.raises(IndexError):
        pop_line("a b", 5)
    with pytest.raises(ValueError):
        bgr("#FFF")


def test_from_words():
    words = [{"word": "lived", "start": 2.0}, {"word": "14", "start": 2.6}, {"word": "days", "start": 2.9}]
    assert "\\t(600," in pop_line_from_words(words, 1, cue_start=2.0)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_libass_accepts(tmp_path):
    ass = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 320\nPlayResY: 180\n\n[V4+ Styles]\n"
           "Format: Name, Fontname, Fontsize, PrimaryColour, Alignment\nStyle: Default,DejaVu Sans,30,&H00FFFFFF,5\n\n"
           "[Events]\nFormat: Layer, Start, End, Style, Text\n"
           f"Dialogue: 0,0:00:00.00,0:00:01.00,Default,{pop_line('for 14 days', 1, 100)}\n")
    p = tmp_path / "k.ass"
    p.write_text(ass)
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=black:s=320x180:d=0.4:r=10",
                        "-vf", f"ass={p}", "-f", "null", "-"], capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
