import math

import pytest

import isometric_projection as ip


@pytest.mark.parametrize("mode", ["iso", "pixel"])
def test_ground_roundtrip(mode):
    for p in [(0, 0), (3, 2), (-1.5, 4.25)]:
        s = ip.project((p[0], p[1], 0), 40, mode, origin=(500, 100))
        assert ip.unproject_ground(s, 40, mode, origin=(500, 100)) == pytest.approx(p)


def test_angles():
    sx, sy = ip.project((1, 0, 0), 1, "iso")
    assert math.degrees(math.atan2(sy, sx)) == pytest.approx(30)
    sx, sy = ip.project((1, 0, 0), 1, "pixel")
    assert sy / sx == pytest.approx(0.5)
    assert ip.project((0, 0, 1), 10)[1] == pytest.approx(-10)


def test_tiles_roundtrip():
    for col, row in [(0, 0), (5, 3), (2, 9)]:
        sx, sy = ip.tile_to_screen(col, row, 128, 64)
        # centre of the diamond is half a tile below its top corner
        assert ip.screen_to_tile(sx, sy + 32, 128, 64) == (col, row)


def test_depth_sort():
    objs = [{"pos": (5, 5, 0)}, {"pos": (0, 0, 0)}, {"pos": (2, 1, 3)}]
    assert [o["pos"] for o in ip.sort_back_to_front(objs)] == [(0, 0, 0), (2, 1, 3), (5, 5, 0)]
    with pytest.raises(ValueError):
        ip.project((0, 0, 0), mode="oblique")
