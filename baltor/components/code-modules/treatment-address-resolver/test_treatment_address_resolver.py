import json

import pytest

import treatment_address_resolver as m


def test_catalogue_defines_exactly_2400_unique_addresses():
    addresses = m.all_addresses()
    assert len(addresses) == 2400
    assert len(set(addresses)) == 2400
    assert all(m.ADDRESS.match(a) for a in addresses)


def test_every_story_has_exactly_ten_rows_and_split_is_120_120():
    stories = m.TABLES["stories"]
    assert len(stories) == 240
    assert sum(1 for s in stories.values() if s["family"] == "learning") == 120
    assert sum(1 for s in stories.values() if s["family"] == "fiction") == 120
    for story_id in stories:
        assert len(m.addresses_for(story_id)) == 10


def test_public_safety_group_uses_f20_instead_of_f02():
    addresses = m.addresses_for("EDU101")
    assert "R-EDU101-F20-A01" in addresses
    assert not any("-F02-" in a for a in addresses)
    assert "R-EDU001-F02-A01" in m.addresses_for("EDU001")
    assert not m.is_valid("R-EDU101-F02-A01")


def test_group_four_uses_layered_approach_and_group_three_tactile():
    assert m.is_valid("R-ENT072-F08-A04")
    assert not m.is_valid("R-ENT072-F08-A03")
    assert m.is_valid("R-ENT001-F06-A03")
    assert not m.is_valid("R-ENT001-F06-A04")


def test_learning_stories_never_use_fiction_formats():
    assert not m.is_valid("R-EDU001-F06-A01")
    assert "does not use format F06" in m.problems("R-EDU001-F06-A01")[0]


def test_malformed_and_unknown_addresses():
    assert "not of the form" in m.problems("R-EDU1-F01-A01")[0]
    assert "not one of the 240" in m.problems("R-EDU999-F01-A01")[0]
    with pytest.raises(ValueError):
        m.resolve("R-EDU101-F02-A01")


def test_resolve_joins_intro_and_motion_from_the_group_table():
    rec = m.resolve("R-ENT072-F08-A04")
    assert rec["treatment_group"] == 4
    assert rec["intro"]["id"] == "I30"
    assert rec["motion"]["id"] == "M03"
    assert rec["approach"]["id"] == "A04"
    assert rec["story"]["family"] == "fiction"
    assert "not a screenplay" in rec["status"]
    assert rec["editorial_rule"].startswith("F08")


def test_cli(capsys):
    assert m.main(["--count"]) == 0
    assert capsys.readouterr().out.strip() == "2400"
    assert m.main(["R-EDU001-F01-A01"]) == 0
    assert json.loads(capsys.readouterr().out)["format"]["id"] == "F01"
    assert m.main(["--check", "R-EDU101-F02-A01"]) == 1
    capsys.readouterr()
