import pytest

from caption_chunker import chunk_text, chunk_words, split_points

TEXT = ("In 1970, five scientists lived underwater for 14 days off the Virgin Islands. "
        "They studied the reef by day and slept in a steel habitat at night.")


def test_limits_respected():
    for chunk in chunk_text(TEXT, max_words=7, max_chars=32):
        assert len(chunk.split()) <= 7
        assert len(chunk) <= 32 or len(chunk.split()) == 1


def test_prefers_punctuation_and_avoids_function_word_endings():
    chunks = chunk_text(TEXT)
    assert any(c.endswith("1970,") for c in chunks)
    assert any(c.endswith("Islands.") for c in chunks)
    for c in chunks[:-1]:
        assert c.split()[-1].lower().strip(",.") not in {"the", "of", "for", "a", "in", "and"}


def test_keeps_numbers_with_units():
    chunks = chunk_text(TEXT)
    assert not any(c.split()[-1] == "14" for c in chunks)


def test_no_text_lost():
    assert " ".join(chunk_text(TEXT)) == " ".join(TEXT.split())
    assert chunk_text("") == []


def test_timed_words_break_at_pause():
    words = [{"word": w, "start": i * 0.3, "end": i * 0.3 + 0.25} for i, w in enumerate("one two three four five six".split())]
    for w in words[3:]:
        w["start"] += 0.8
        w["end"] += 0.8
    chunks = chunk_words(words, max_words=7)
    assert [c["text"] for c in chunks] == ["one two three", "four five six"]
    assert chunks[1]["start"] == pytest.approx(1.7)


def test_validation():
    with pytest.raises(ValueError):
        split_points(["a"], max_words=0)
