import pytest

from caption_case_styler import style


def test_title_case_rules():
    assert style("the dna of a nasa probe", "title", keep={"DNA", "NASA"}) == "The DNA of a NASA Probe"
    assert style("what it stood for", "title") == "What It Stood For"
    assert style("a well-known fact", "title") == "A Well-Known Fact"


def test_upper_with_keep():
    assert style("the new iPhone and mRNA", "upper", keep={"iPhone", "mRNA"}) == "THE NEW iPhone AND mRNA"


def test_sentence_case():
    assert style("THE REEF WAS ALIVE. THEN NASA CALLED!", "sentence", keep={"NASA"}) == \
        "The reef was alive. Then NASA called!"
    assert style("the reef was alive. then NASA called!", "sentence") == "The reef was alive. Then NASA called!"


def test_whitespace_preserved_and_validation():
    assert style("two  spaces", "upper") == "TWO  SPACES"
    with pytest.raises(ValueError):
        style("x", "camel")
