import numpy as np
import pytest
from PIL import Image

import lospec_palette_quantiser as q

# An original 4-colour test palette (not taken from Lospec).
PAL = [(16, 16, 24), (90, 110, 70), (200, 180, 120), (250, 245, 230)]
HEX = "101018\n5a6e46\n#c8b478\nfaf5e6\n"
GPL = "GIMP Palette\nName: test\nColumns: 4\n#\n 16  16  24\tInk\n 90 110  70\tMoss\n200 180 120\tSand\n250 245 230\tPaper\n"
PAL_JASC = "JASC-PAL\n0100\n4\n16 16 24\n90 110 70\n200 180 120\n250 245 230\n"
TXT = ";paint.net palette\nFF101018\nFF5A6E46\nFFC8B478\nFFFAF5E6\n"


@pytest.mark.parametrize("text,fmt", [(HEX, "hex"), (GPL, "gpl"), (PAL_JASC, "pal"), (TXT, "txt")])
def test_palette_formats(text, fmt):
    assert q.parse_palette(text, fmt) == PAL


def test_bad_palettes():
    with pytest.raises(ValueError):
        q.parse_palette("not a palette", "gpl")
    with pytest.raises(ValueError):
        q.parse_palette("", "hex")


def test_png_palette_strip(tmp_path):
    strip = Image.new("RGBA", (4, 1))
    for i, c in enumerate(PAL):
        strip.putpixel((i, 0), c + (255,))
    p = tmp_path / "pal.png"
    strip.save(p)
    assert q.load_palette(p) == PAL


def gradient(w=64, h=8):
    x = np.linspace(0, 255, w)
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :, 0] = x
    arr[:, :, 1] = x
    arr[:, :, 2] = x
    arr[:, :, 3] = 255
    return Image.fromarray(arr, "RGBA")


@pytest.mark.parametrize("dither", ["none", "bayer4", "bayer8", "floyd"])
def test_output_uses_only_palette_colours(dither):
    out = q.quantise(gradient(), PAL, dither=dither)
    rep = q.palette_report(out, PAL)
    assert rep["off_palette_pixels"] == 0
    assert rep["colours_used"] >= 3


def test_palette_colours_map_to_themselves():
    arr = np.array([[c + (255,) for c in PAL]], dtype=np.uint8)
    out = np.asarray(q.quantise(Image.fromarray(arr, "RGBA"), PAL))
    assert out[0, :, :3].tolist() == [list(c) for c in PAL]


def test_alpha_is_thresholded():
    arr = np.zeros((1, 3, 4), dtype=np.uint8)
    arr[0, :, 3] = [0, 100, 200]
    out = np.asarray(q.quantise(Image.fromarray(arr, "RGBA"), PAL, alpha_threshold=128))
    assert out[0, :, 3].tolist() == [0, 0, 255]


def test_bayer_mixes_two_colours_on_flat_midtone():
    two = [(0, 0, 0), (255, 255, 255)]
    flat = Image.new("RGBA", (16, 16), (128, 128, 128, 255))
    plain = q.palette_report(q.quantise(flat, two, dither="none"), two)
    dithered = q.palette_report(q.quantise(flat, two, dither="bayer4", strength=1.0), two)
    assert plain["colours_used"] == 1
    assert dithered["colours_used"] == 2


def test_bayer8_matrix_is_permutation():
    m = (q._bayer(8) * 64).round().astype(int)
    assert sorted(m.ravel().tolist()) == list(range(64))
    assert (q._bayer(4) == q.BAYER4).all()


def test_check_cli(tmp_path, capsys):
    pal = tmp_path / "p.hex"
    pal.write_text(HEX)
    src = tmp_path / "in.png"
    gradient().save(src)
    out = tmp_path / "out.png"
    assert q.main(["check", str(src), "--palette", str(pal)]) == 1
    assert q.main(["quantise", str(src), "--palette", str(pal), "--out", str(out), "--dither", "bayer4"]) == 0
    assert q.main(["check", str(out), "--palette", str(pal)]) == 0
