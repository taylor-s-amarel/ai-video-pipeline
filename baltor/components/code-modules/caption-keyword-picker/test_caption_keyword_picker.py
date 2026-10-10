from caption_keyword_picker import pick, pick_all


def test_numbers_win():
    assert pick("lived underwater for 14 days") == 3
    assert pick("a whopping 86% of the reef") == 2
    assert pick("raised $2.5M in a week") == 1


def test_emphasis_and_proper_nouns():
    assert pick("she studied the coral reef", emphasis={"coral"}) == 3
    assert pick("found by Grace Hopper herself") == 3


def test_longest_content_word():
    assert pick("they slept inside a habitat") == 4


def test_all_stop_words():
    assert pick("and so it was") is None


def test_pick_all_avoids_repeat():
    idx = pick_all(["the habitat was small", "the habitat was cold"])
    assert idx[0] == 1 and idx[1] != 1
