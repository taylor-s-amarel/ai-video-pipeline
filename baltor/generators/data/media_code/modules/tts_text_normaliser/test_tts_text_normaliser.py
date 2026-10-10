import pytest

from tts_text_normaliser import normalise


@pytest.mark.parametrize("src,expected", [
    ("In 1970, five scientists", "In nineteen seventy, five scientists"),
    ("It cost $2.5M.", "It cost two point five million dollars."),
    ("About 86% of reefs", "About eighty-six percent of reefs"),
    ("1,000 dogs", "one thousand dogs"),
    ("on the 21st floor", "on the twenty-first floor"),
    ("10-20 km away", "ten to twenty kilometers away"),
    ("Dr. Earle & team", "Doctor Earle and team"),
    ("at 3:30 pm", "at three thirty P M"),
    ("at 14:05", "at fourteen oh five"),
    ("It was -5°C", "It was five below zero degrees Celsius"),
    ("50 ft down", "fifty feet down"),
    ("In 2005 and 2026", "In two thousand five and twenty twenty-six"),
    ("2026 people", "two thousand twenty-six people"),
    ("pi is 3.14", "pi is three point one four"),
])
def test_cases(src, expected):
    assert normalise(src) == expected


def test_no_digits_left():
    out = normalise("In 1970, 5 scientists spent 14 days 50 ft down; cost: $2.5M (86%).")
    assert not any(ch.isdigit() for ch in out)
