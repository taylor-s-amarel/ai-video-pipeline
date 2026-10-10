import pytest

from steps_timing import ffmpeg_hold_filter, hold_frames, stepped_times, steps_value


def test_jump_end():
    assert [steps_value(t, 4, "end") for t in (0, 0.24, 0.25, 0.99, 1)] == [0, 0, 0.25, 0.75, 1]


def test_jump_start():
    assert steps_value(0, 4, "jump-start") == 0.25
    assert steps_value(1, 4, "jump-start") == 1


def test_jump_none_and_both():
    assert steps_value(0, 5, "jump-none") == 0
    assert steps_value(1, 5, "jump-none") == 1
    assert steps_value(0.5, 5, "jump-none") == pytest.approx(0.5)
    assert steps_value(0, 3, "jump-both") == pytest.approx(0.25)
    assert steps_value(1, 3, "jump-both") == pytest.approx(1)


def test_invalid():
    with pytest.raises(ValueError):
        steps_value(0.5, 0)
    with pytest.raises(ValueError):
        steps_value(0.5, 1, "jump-none")
    with pytest.raises(ValueError):
        steps_value(0.5, 2, "sideways")


def test_holds():
    assert hold_frames(8, 2) == [0, 0, 2, 2, 4, 4, 6, 6]
    assert hold_frames(5, 1) == [0, 1, 2, 3, 4]
    assert stepped_times(0.2, 30, 3)[:4] == [0, 0, 0, 0.1]
    assert ffmpeg_hold_filter(2, 30) == "fps=15,fps=30"
