import pytest

from word_stagger_timing import frames, schedule, state_at, total_duration


def test_schedule_staggers():
    s = schedule("a b c", start=1.0, stagger=0.1, enter=0.2)
    assert [w["start"] for w in s] == pytest.approx([1.0, 1.1, 1.2])
    assert total_duration(s) == pytest.approx(0.4)


def test_state_caps_opacity_and_rises():
    s = schedule("one two", stagger=0.5, enter=0.2)
    st = state_at(s, 0.1)
    assert 0 < st[0]["opacity"] < 0.98 and st[1]["opacity"] == 0
    done = state_at(s, 5)
    assert all(w["opacity"] == 0.98 and w["dy"] == 0 for w in done)


def test_word_times_override():
    s = schedule(["x", "y"], word_times=[0.3, 0.9])
    assert [w["start"] for w in s] == [0.3, 0.9]
    with pytest.raises(ValueError):
        schedule(["x"], word_times=[0.1, 0.2])


def test_frames_len():
    s = schedule("a b")
    assert len(frames(s, 30, 1.0)) == 31
