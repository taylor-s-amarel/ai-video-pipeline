import pytest

from word_caption_aligner import align, norm


def words_from(text, start=0.0, step=0.3):
    return [{"word": w, "start": start + i * step, "end": start + i * step + 0.25} for i, w in enumerate(text.split())]


def test_norm():
    assert norm("Islands.") == "islands" and norm("Fourteen") == "14" and norm("1,000") == "1000"


def test_retimes_drifting_cues_and_reports():
    words = words_from("in 1970 five scientists lived underwater for fourteen days")
    cues = [{"start": 0.0, "end": 3.0, "text": "In 1970, five scientists"},
            {"start": 3.0, "end": 12.8, "text": "lived underwater for 14 days."}]
    r = align(cues, words)
    assert r["cues"][0]["start"] == 0.0 and r["cues"][0]["end"] == pytest.approx(0.9 + 0.25)
    assert r["cues"][1]["start"] == pytest.approx(1.2)
    assert r["cues"][1]["end"] == pytest.approx(2.4 + 0.25)
    rep = r["report"]
    assert rep["match_ratio"] == 1.0
    assert rep["out_of_tolerance"] == 1 and rep["max_abs_drift_s"] == pytest.approx(1.8)


def test_unmatched_cue_is_interpolated():
    words = words_from("alpha beta gamma delta")
    cues = [{"start": 0, "end": 1, "text": "alpha beta"}, {"start": 1, "end": 2, "text": "zzz qqq"},
            {"start": 2, "end": 3, "text": "gamma delta"}]
    r = align(cues, [w for w in words])
    mid = r["cues"][1]
    assert r["report"]["per_cue"][1]["how"] == "unmatched"
    assert r["cues"][0]["end"] <= mid["start"] <= mid["end"] <= r["cues"][2]["start"] + 1e-9


def test_no_overlaps_after_retime():
    words = words_from("a b c d e f", step=0.1)
    cues = [{"start": 0, "end": 1, "text": "a b"}, {"start": 1, "end": 2, "text": "c d"}, {"start": 2, "end": 3, "text": "e f"}]
    out = align(cues, words)["cues"]
    assert all(x["end"] <= y["start"] + 1e-9 for x, y in zip(out, out[1:]))
