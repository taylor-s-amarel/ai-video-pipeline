import pytest

from keyframe_track import Keyframe, Track


def test_scalar_linear():
    tr = Track([(0, 0.0), (1, 10.0)])
    assert tr.at(0.5) == pytest.approx(5)
    assert tr.at(-1) == 0 and tr.at(2) == 10


def test_vector_and_easing():
    tr = Track([(0, (0, 0), "out_cubic"), (1, (100, 50))])
    x, y = tr.at(0.5)
    assert x == pytest.approx(87.5) and y == pytest.approx(43.75)


def test_hold_segment():
    tr = Track([(0, 1.0, "hold"), (1, 2.0), (2, 3.0)])
    assert tr.at(0.99) == 1.0
    assert tr.at(1.5) == pytest.approx(2.5)


def test_frames_count_and_sorting():
    tr = Track([(2, 1.0), (0, 0.0)])
    f = tr.frames(10)
    assert len(f) == 21 and f[0] == 0 and f[-1] == 1


def test_json_roundtrip():
    tr = Track([Keyframe(0, (1, 2), "in_sine"), Keyframe(1, (3, 4))])
    assert Track.from_json(tr.to_json()).at(0.5) == tr.at(0.5)


def test_errors():
    with pytest.raises(ValueError):
        Track([])
    with pytest.raises(ValueError):
        Track([(0, 1, "wobble")])
    with pytest.raises(ValueError):
        Track([(0, 1), (0, 2)])
    with pytest.raises(ValueError):
        Track([(0, (1, 2)), (1, (1, 2, 3))]).at(0.5)
