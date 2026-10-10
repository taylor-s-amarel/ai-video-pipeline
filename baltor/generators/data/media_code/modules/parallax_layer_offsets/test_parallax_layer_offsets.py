import math

import pytest

import parallax_layer_offsets as pl


def test_near_layers_move_more():
    ts = pl.layer_transforms([2, 5, 10, 40], cam=(1.0, 0, 0), focal=600)
    shifts = [abs(t["dx"]) for t in ts]
    assert shifts == sorted(shifts, reverse=True)
    assert ts[0]["dx"] < 0  # camera right -> scene moves left


def test_infinite_depth_static():
    t = pl.layer_transform(math.inf, cam=(5, 5, 1))
    assert t["dx"] == 0 and t["scale"] == 1


def test_dolly_scales_near_more():
    near, far = pl.layer_transforms([2, 20], cam=(0, 0, 1))
    assert near["scale"] == pytest.approx(2.0)
    assert far["scale"] == pytest.approx(20 / 19)


def test_focal_for_hits_target():
    f = pl.focal_for(10, 1.0, 60)
    assert abs(pl.layer_transform(10, (1.0, 0, 0), f)["dx"]) == pytest.approx(60)


def test_overscan_and_errors():
    path = pl.linear_path((0, 0, 0), (1, 0, 0), 5)
    ox, oy = pl.overscan_px(5, path, 600, 1080, 1920)
    assert ox == 120 and oy == 0
    with pytest.raises(ValueError):
        pl.layer_transform(1, cam=(0, 0, 2))
    with pytest.raises(ValueError):
        pl.layer_transform(0)
