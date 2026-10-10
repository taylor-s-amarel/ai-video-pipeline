import pytest

from active_word_highlight_ass import highlight_events

WORDS = [{"word": "five", "start": 1.0, "end": 1.3}, {"word": "scientists", "start": 1.35, "end": 1.9},
         {"word": "{lived}", "start": 2.0, "end": 2.3}]


def test_contiguous_events_one_per_word():
    ev = highlight_events(WORDS, cue_end=2.6)
    assert [(a, b) for a, b, _ in ev] == [(1.0, 1.35), (1.35, 2.0), (2.0, 2.6)]
    assert ev[1][2] == "five {\\1c&H1FD2FF&}scientists{\\r} \\{lived\\}"


def test_scale_and_uppercase():
    ev = highlight_events(WORDS[:1], scale=110, uppercase=True)
    assert ev[0][2] == "{\\1c&H1FD2FF&\\fscx110\\fscy110}FIVE{\\r}"
    assert ev[0][1] == 1.3


def test_validation():
    with pytest.raises(ValueError):
        highlight_events(list(reversed(WORDS)))
    assert highlight_events([]) == []
