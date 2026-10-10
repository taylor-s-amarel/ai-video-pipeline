import pytest

from thirds_composition_score import achieved_position, reposition_crop, score


def test_score_extremes():
    s = score((1 / 3, 1 / 3))
    assert s["thirds"] == 1.0 and s["distance"] == 0
    c = score((0.5, 0.5))
    assert c["centre"] == 1.0 and c["thirds"] < 0.4
    with pytest.raises(ValueError):
        score((1.5, 0))


def test_reposition_hits_target_when_possible():
    xy = reposition_crop((2000, 1500), (4000, 3000), (1688, 3000), target=(0.5, 1 / 3))
    pos = achieved_position((2000, 1500), xy, (1688, 3000))
    assert pos[0] == pytest.approx(0.5)
    assert xy[1] == 0  # vertical already full height: clamped


def test_reposition_clamps():
    xy = reposition_crop((50, 50), (4000, 3000), (1000, 1000))
    assert xy == (0.0, 0.0)
    with pytest.raises(ValueError):
        reposition_crop((0, 0), (100, 100), (200, 50))
