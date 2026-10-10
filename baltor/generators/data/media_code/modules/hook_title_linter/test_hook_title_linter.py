from hook_title_linter import lint


def test_good_hooks():
    assert lint("SHE LIVED UNDERWATER FOR 14 DAYS", first_caption="In 1970, five scientists") == []
    assert lint("The Moth in Grace Hopper's Logbook") == []
    assert lint("THE MISSING YELLOW BOX", topic_terms=["yellow box"]) == []


def test_bad_hooks():
    assert any("vague" in p for p in lint("YOU WON'T BELIEVE THIS"))
    assert any("nothing concrete" in p for p in lint("SAY IT CLEARLY"))
    assert any("words" in p for p in lint("WOW"))
    assert any("repeats" in p for p in lint("In 1970 five", first_caption="In 1970, five scientists lived"))
    assert any("ellipsis" in p for p in lint("14 dogs and then..."))
    assert any("characters" in p for p in lint("SUPERCALIFRAGILISTIC EXPIALIDOCIOUS 1000000000 TIMES"))
    assert lint("!!!") == ["title has no letters or digits"]
