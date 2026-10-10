import pytest

from phoneme_viseme_map import MAP, SHAPES, letter_at, viseme, visemes_from_phones

ARPABET = ("AA AE AH AO AW AY B CH D DH EH ER EY F G HH IH IY JH K L M N NG OW OY P R S SH T TH UH UW V W Y Z ZH").split()


def test_every_arpabet_phone_mapped():
    for p in ARPABET:
        assert viseme(p) in SHAPES
    assert set(MAP.values()) <= set(SHAPES)


def test_stress_and_case():
    assert viseme("aa1") == "D" and viseme("M") == "A" and viseme("F") == "G"
    with pytest.raises(KeyError):
        viseme("QQ")


def test_cues_merge_and_rest():
    phones = [(0.0, 0.1, "M"), (0.1, 0.12, "AH0"), (0.12, 0.3, "AA1"), (0.6, 0.7, "P")]
    cues = visemes_from_phones(phones, min_s=0.04)
    assert cues[0] == (0.0, 0.12, "A")  # 20 ms AH merged into previous cue
    assert cues[1] == (0.12, 0.3, "D")
    assert cues[2] == (0.3, 0.6, "X")
    assert letter_at(cues, 0.65) == "A" and letter_at(cues, 5) == "X"


def test_invalid_phone_times():
    with pytest.raises(ValueError):
        visemes_from_phones([(0.2, 0.1, "AA")])
