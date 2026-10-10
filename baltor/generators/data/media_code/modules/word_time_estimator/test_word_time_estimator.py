import pytest

from word_time_estimator import estimate, syllables


@pytest.mark.parametrize("word,n", [("underwater", 4), ("the", 1), ("radio", 3), ("media", 3), ("nation", 2), ("video", 3), ("lived", 1),
                                    ("table", 2), ("habitat", 3), ("1970", 4), ("14", 2), ("make", 1)])
def test_syllables(word, n):
    assert syllables(word) == n


def test_estimate_spans_and_orders():
    est = estimate("In 1970, five scientists lived underwater.", 2.0, 5.4)
    assert est[0]["start"] == 2.0 and est[-1]["end"] == 5.4
    assert all(a["end"] <= b["start"] for a, b in zip(est, est[1:]))
    # pause after the comma
    assert est[2]["start"] - est[1]["end"] > 0.1
    # longer words get more time
    d = {w["word"]: w["end"] - w["start"] for w in est}
    assert d["underwater."] > d["five"]


def test_errors():
    with pytest.raises(ValueError):
        estimate("x", 2, 1)
    assert estimate("", 0, 1) == []
