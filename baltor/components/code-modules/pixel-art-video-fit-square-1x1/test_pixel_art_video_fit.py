import numpy as np
from PIL import Image

import pixel_art_video_fit as f


def checker(w, h):
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., 3] = 255
    arr[::2, ::2, :3] = 255
    arr[1::2, 1::2, :3] = 255
    return Image.fromarray(arr, "RGBA")


def test_integer_scale_respects_safe_area():
    # 160x144 handheld frame in a 1080x1920 short: 6% side margins leave 950 px -> x5 (x6 would be 960)
    assert f.integer_scale((160, 144), (1080, 1920), (0.06, 0.12)) == 5
    assert f.integer_scale((160, 144), (1080, 1920), (0.05, 0.12)) == 6
    assert f.integer_scale((320, 180), (1920, 1080), (0.06, 0.08)) == 5
    assert f.integer_scale((4000, 4000), (1080, 1920), (0.06, 0.12)) == 1


def test_fit_produces_exact_blocks_and_size():
    img = checker(16, 16)
    out, info = f.fit(img, (1080, 1920), (0.06, 0.12), bg="#102030")
    assert out.size == (1080, 1920)
    s = info.scale
    arr = np.asarray(out)
    x, y = info.offset
    block = arr[y:y + s, x:x + s, :3]
    assert (block == block[0, 0]).all()  # one source pixel -> one solid s x s block
    assert arr[0, 0, :3].tolist() == [0x10, 0x20, 0x30]
    assert info.size == (16 * s, 16 * s)


def test_upper_third_anchor():
    out, info = f.fit(checker(32, 8), (1080, 1920), (0.06, 0.12), anchor="upper-third")
    assert info.offset[1] + info.size[1] / 2 <= 1920 / 3 + 1


def test_tile_background_is_scaled_too():
    tile = Image.new("RGBA", (2, 2), (200, 0, 0, 255))
    tile.putpixel((0, 0), (0, 0, 200, 255))
    out, info = f.fit(checker(8, 8), (200, 200), (0.25, 0.25), tile=tile)
    arr = np.asarray(out)
    s = info.scale
    assert arr[0, 0, :3].tolist() == [0, 0, 200]
    assert arr[0, s, :3].tolist() == [200, 0, 0]


def test_sequence_uses_one_scale(tmp_path):
    paths = []
    for i, size in enumerate([(16, 16), (20, 18), (12, 12)]):
        p = tmp_path / f"f{i}.png"
        checker(*size).save(p)
        paths.append(p)
    info = f.fit_sequence(paths, tmp_path / "out", (1080, 1920), (0.06, 0.12))
    assert info.scale == f.integer_scale((20, 18), (1080, 1920), (0.06, 0.12))
    assert len(list((tmp_path / "out").glob("*.png"))) == 3


def test_cli_preset_file(tmp_path):
    src = tmp_path / "in.png"
    checker(10, 10).save(src)
    preset = tmp_path / "p.json"
    preset.write_text('{"size": [400, 400], "margin": [0.0, 0.0]}')
    out = tmp_path / "out.png"
    assert f.main([str(src), "--out", str(out), "--preset-file", str(preset)]) == 0
    assert Image.open(out).size == (400, 400)
