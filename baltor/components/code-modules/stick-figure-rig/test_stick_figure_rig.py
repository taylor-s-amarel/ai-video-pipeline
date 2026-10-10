import math

import numpy as np
import pytest

from stick_figure_rig import BONES, POSES, Rig


@pytest.mark.parametrize("name", sorted(POSES))
def test_bone_lengths_preserved(name):
    rig = Rig(scale=1.5)
    pts = rig.pose_points(POSES[name], (500, 900))
    for parent, child, length, _ in BONES:
        assert math.dist(pts[parent], pts[child]) == pytest.approx(length * 1.5)


def test_rest_pose_geometry():
    pts = Rig().pose_points({}, (0, 0))
    assert pts["chest"][1] < 0 < pts["l_foot"][1]  # chest above pelvis, feet below (y down)


def test_wave_raises_right_hand():
    rig = Rig()
    stand = rig.pose_points(POSES["stand"], (0, 0))
    wave = rig.pose_points(POSES["wave"], (0, 0))
    assert wave["r_hand"][1] < stand["r_hand"][1]


def test_render_has_pixels_and_capped_alpha():
    img = Rig().render(POSES["cheer"], size=(400, 600), root=(200, 380))
    a = np.asarray(img)[..., 3]
    assert a.max() == 250 and (a > 0).sum() > 500
    with pytest.raises(ValueError):
        Rig().render({}, opacity=1.0)


def test_unknown_joint():
    with pytest.raises(ValueError):
        Rig().pose_points({"tail": 10})
    with pytest.raises(ValueError):
        Rig(lengths={"tail": 3})
