import pytest

import conventional_commit_parser as cc


def test_simple_feat_is_minor():
    c = cc.parse("feat: allow provided config object to extend other configs")
    assert c.type == "feat" and c.scope is None and c.bump() == "minor"


def test_scope_and_bang_is_breaking():
    c = cc.parse("feat(api)!: send an email to the customer when a product is shipped")
    assert c.scope == "api" and c.breaking and c.bump() == "major"
    assert c.breaking_description.startswith("send an email")


def test_breaking_change_footer_and_multiline_value():
    msg = ("feat: allow provided config object to extend other configs\n\n"
           "Longer body paragraph.\n\nSecond paragraph.\n\n"
           "BREAKING CHANGE: `extends` key in config file is now used\n  for extending other config files\n"
           "Refs: #123")
    c = cc.parse(msg)
    assert c.breaking
    assert c.body == "Longer body paragraph.\n\nSecond paragraph."
    assert [f.token for f in c.footers] == ["BREAKING CHANGE", "Refs"]
    assert "for extending" in c.footers[0].value


def test_breaking_hyphen_synonym_and_hash_separator():
    c = cc.parse("fix: prevent racing of requests\n\nBREAKING-CHANGE: retries removed\nCloses #42")
    assert c.breaking and c.footers[1].token == "Closes" and c.footers[1].value == "42"


def test_missing_blank_line_is_error():
    with pytest.raises(cc.ParseError):
        cc.parse("fix: thing\nbody right away")


@pytest.mark.parametrize("bad", ["Fixed the bug", "feat:missing space", "feat(): empty scope", ": no type", ""])
def test_invalid_headers(bad):
    assert cc.validate(bad)


def test_validate_rejects_unknown_type_and_trailing_period():
    problems = cc.validate("feature: add a thing.")
    assert any("type" in p for p in problems) and any("period" in p for p in problems)


def test_any_type_allowed_when_types_none():
    assert cc.validate("wip: spike", allowed_types=None) == []


def test_comment_lines_ignored_and_merge_skipped():
    assert cc.validate("fix: x\n# Please enter the commit message\n") == []
    assert cc.validate("Merge branch 'main' into feature") == []


def test_highest_bump():
    assert cc.highest_bump(["docs: a", "fix: b", "feat: c"]) == "minor"
    assert cc.highest_bump(["docs: a", "chore!: drop node 18"]) == "major"
    assert cc.highest_bump(["not conventional"]) == "none"


def test_cli_exit_codes(tmp_path, capsys):
    good = tmp_path / "good.txt"
    good.write_text("fix(parser): handle empty input\n")
    bad = tmp_path / "bad.txt"
    bad.write_text("updated stuff\n")
    assert cc.main(["--file", str(good), "--json"]) == 0
    assert '"bump": "patch"' in capsys.readouterr().out
    assert cc.main(["--file", str(bad)]) == 1
