import pytest

from typewriter_reveal_timing import ass_events, duration, reveal_schedule, visible_at


def test_constant_rate_without_punctuation():
    s = reveal_schedule("abcd", cps=10)
    assert s == pytest.approx([0, 0.1, 0.2, 0.3])


def test_pause_after_comma_and_spaces_free():
    s = reveal_schedule("a, b", cps=10)
    # 'a' at 0, ',' at .1, ' ' at .2 + .12 pause, 'b' same time as space (spaces cost nothing)
    assert s == pytest.approx([0, 0.1, 0.32, 0.32])


def test_no_pause_inside_numbers():
    s = reveal_schedule("3.14", cps=10)
    assert s == pytest.approx([0, 0.1, 0.2, 0.3])


def test_visible_at_and_duration():
    text = "Hello."
    s = reveal_schedule(text, cps=10, start=1.0)
    assert visible_at(text, s, 1.25) == "Hel"
    assert duration(s, 10) == pytest.approx(0.6)


def test_ass_events_keep_layout():
    ev = ass_events("Hi {x}", start=0, end=5, cps=10)
    assert ev[0][2].startswith("H{\\alpha&HFF&}")
    assert ev[-1][2] == "Hi \\{x\\}"
    assert all(a < b for a, b, _ in ev)
    with pytest.raises(ValueError):
        reveal_schedule("x", cps=0)
