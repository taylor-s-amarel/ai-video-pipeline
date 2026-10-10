import pytest

from layout_grid_system import Grid


def test_full_span_matches_content():
    g = Grid((1080, 1920), columns=12, margin=(60, 96), gutter=24, baseline=24)
    x, w = g.span(0, 12)
    assert x == 60 and w == pytest.approx(960)
    assert g.rows == (1920 - 192) // 24


def test_rect_and_snap():
    g = Grid((1080, 1920))
    x, y, w, h = g.rect(1, 10, 10, 12)
    assert y == 96 + 240 and h == 288 and x > 60
    assert g.snap_y(437) in (432, 456)
    assert g.snap_y(-50) == 96


def test_validation():
    g = Grid((1080, 1920))
    with pytest.raises(ValueError):
        g.span(10, 4)
    with pytest.raises(ValueError):
        g.rect(0, 1, g.rows - 1, 5)
    with pytest.raises(ValueError):
        Grid((100, 100), columns=12, margin=(50, 0), gutter=10)
    assert len(g.guides()["columns"]) == 12
