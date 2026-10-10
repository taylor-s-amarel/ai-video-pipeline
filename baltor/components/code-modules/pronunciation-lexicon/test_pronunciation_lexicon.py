import xml.etree.ElementTree as ET

import pytest

from pronunciation_lexicon import Lexicon


def test_apply_whole_words_and_case():
    lex = Lexicon({"Gamboa": "Gam-BOH-ah", "NOAA": "Noah", "earle": "earl"})
    assert lex.apply("Gamboa met NOAA staff; gamboa again.") == "Gam-BOH-ah met Noah staff; gam-BOH-ah again."
    assert lex.apply("Earle and Earlene") == "Earl and Earlene"


def test_longest_first():
    lex = Lexicon({"New York": "Noo York", "York": "Yawk"})
    assert lex.apply("New York and York") == "Noo York and Yawk"


def test_pls_and_json_roundtrip():
    lex = Lexicon({"NOAA": "Noah"}, ipa={"tomato": "təˈmeɪtoʊ"})
    root = ET.fromstring(lex.to_pls().encode())
    assert len(root) == 2
    assert Lexicon.from_json(lex.to_json()).entries == {"NOAA": "Noah"}
    with pytest.raises(ValueError):
        Lexicon({" ": "x"})
