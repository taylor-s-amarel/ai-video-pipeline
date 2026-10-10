import shutil
import subprocess

import pytest
from PIL import Image

from gif_palette_export import gif_argv, gif_filter


def test_filter_text_and_validation():
    f = gif_filter(fps=10, width=320, max_colors=64)
    assert "palettegen=max_colors=64:stats_mode=diff" in f and "paletteuse=dither=bayer:bayer_scale=3" in f
    for bad in ({"max_colors": 300}, {"dither": "magic"}, {"stats_mode": "x"}, {"bayer_scale": 9}):
        with pytest.raises(ValueError):
            gif_filter(**bad)
    with pytest.raises(ValueError):
        gif_argv("a.mp4", "b.png")


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_real_gif(tmp_path):
    src, out = tmp_path / "s.mp4", tmp_path / "p.gif"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x180:d=1:r=25",
                    "-pix_fmt", "yuv420p", str(src)], check=True, timeout=60)
    cmd = gif_argv(str(src), str(out), fps=8, width=160, max_colors=32)
    subprocess.run(cmd[:1] + ["-v", "error"] + cmd[1:], check=True, timeout=60)
    with Image.open(out) as im:
        assert im.format == "GIF" and im.size[0] == 160 and im.n_frames >= 7
