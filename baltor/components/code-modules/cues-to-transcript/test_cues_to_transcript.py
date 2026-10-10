from cues_to_transcript import dedupe_rolling, paragraphs, transcript


def test_rolling_dedupe():
    cues = [{"start": 0, "end": 2, "text": "in 1970 five"}, {"start": 2, "end": 4, "text": "in 1970 five\nscientists lived"},
            {"start": 4, "end": 6, "text": "scientists lived underwater"}]
    assert " ".join(c["text"] for c in dedupe_rolling(cues)) == "in 1970 five scientists lived underwater"


def test_paragraph_on_pause():
    cues = [{"start": 0, "end": 1, "text": "First."}, {"start": 1.2, "end": 2, "text": "Still first."},
            {"start": 5, "end": 6, "text": "Second."}]
    p = paragraphs(cues)
    assert [x["text"] for x in p] == ["First. Still first.", "Second."]


def test_timestamps():
    cues = [{"start": 65, "end": 66, "text": "Hello."}, {"start": 3700, "end": 3701, "text": "Later."}]
    assert transcript(cues, timestamps=True) == "[01:05] Hello.\n\n[1:01:40] Later.\n"
    assert transcript([]) == ""
