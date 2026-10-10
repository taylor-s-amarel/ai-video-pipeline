import pytest

from tts_sentence_chunker import chunks, sentences


def test_sentence_split_ignores_abbreviations_and_decimals():
    s = sentences("Dr. Earle dove 50.5 ft. down off the U.S. coast. It was 1970! Was it cold? Yes.")
    assert s == ["Dr. Earle dove 50.5 ft. down off the U.S. coast.", "It was 1970!", "Was it cold?", "Yes."]


def test_initials_and_quotes():
    s = sentences('J. R. Smith said "Go." Then we left.')
    assert s == ['J. R. Smith said "Go."', "Then we left."]


def test_chunks_pack_and_boundaries():
    script = "One. Two. Three.\n\nFour is here. Five."
    c = chunks(script, max_chars=30)
    assert [x["text"] for x in c] == ["One. Two. Three.", "Four is here. Five."]
    assert [x["boundary"] for x in c] == ["paragraph", "end"]


def test_long_sentence_split_at_commas_then_spaces():
    long = "This sentence, which is rather long, keeps going and going, until it must be split somewhere sensible."
    c = chunks(long, max_chars=40)
    assert all(len(x["text"]) <= 40 for x in c)
    assert " ".join(x["text"] for x in c) == long


def test_validation():
    with pytest.raises(ValueError):
        chunks("x", max_chars=5)
