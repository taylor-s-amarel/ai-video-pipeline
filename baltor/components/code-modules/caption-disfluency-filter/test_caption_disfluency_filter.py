from caption_disfluency_filter import clean_text, clean_words, normalise_punctuation


def test_fillers_repeats_stutters():
    assert clean_text("So, um, the the reef was, uh, w- well alive") == "So, the reef was, well alive"


def test_keeps_meaningful_words():
    assert clean_text("I like the reef, so we stayed") == "I like the reef, so we stayed"


def test_discourse_optional():
    assert clean_text("It was, you know, huge") == "It was, you know, huge"
    assert clean_text("It was, you know, huge", drop_discourse=True) == "It was, huge"


def test_filler_sentence_end_moves_period():
    assert clean_text("That was it um.") == "That was it."


def test_words_keep_timing():
    words = [{"word": "the", "start": 0}, {"word": "the", "start": 0.2}, {"word": "um", "start": 0.4},
             {"word": "reef", "start": 0.6}]
    assert [(w["word"], w["start"]) for w in clean_words(words)] == [("the", 0), ("reef", 0.6)]


def test_punctuation():
    assert normalise_punctuation("“Hi” ,  there !") == '"Hi", there!'
