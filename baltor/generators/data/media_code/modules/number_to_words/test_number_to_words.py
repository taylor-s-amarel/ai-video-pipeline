import pytest

from number_to_words import cardinal, decimal, ordinal, year


@pytest.mark.parametrize("n,w", [(0, "zero"), (14, "fourteen"), (42, "forty-two"), (100, "one hundred"),
                                 (1000, "one thousand"), (1001, "one thousand one"),
                                 (2_500_000, "two million five hundred thousand"), (-7, "minus seven"),
                                 (999_999, "nine hundred ninety-nine thousand nine hundred ninety-nine")])
def test_cardinal(n, w):
    assert cardinal(n) == w


@pytest.mark.parametrize("n,w", [(1, "first"), (2, "second"), (3, "third"), (12, "twelfth"), (20, "twentieth"),
                                 (21, "twenty-first"), (100, "one hundredth"), (1003, "one thousand third")])
def test_ordinal(n, w):
    assert ordinal(n) == w


@pytest.mark.parametrize("n,w", [(1970, "nineteen seventy"), (1905, "nineteen oh five"), (1900, "nineteen hundred"),
                                 (2000, "two thousand"), (2005, "two thousand five"), (2026, "twenty twenty-six"),
                                 (1066, "ten sixty-six"), (800, "eight hundred")])
def test_year(n, w):
    assert year(n) == w


def test_year_thousand_style_and_decimal():
    assert year(2026, style="thousand") == "two thousand twenty-six"
    assert decimal("3.14") == "three point one four"
    assert decimal("-0.5") == "minus zero point five"
    with pytest.raises(ValueError):
        decimal("abc")
    with pytest.raises(ValueError):
        cardinal(10 ** 18)
