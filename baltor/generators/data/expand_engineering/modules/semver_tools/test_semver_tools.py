import pytest

import semver_tools as sv


def test_spec_precedence_example():
    # semver.org section 11 example chain
    chain = ["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-beta", "1.0.0-beta.2",
             "1.0.0-beta.11", "1.0.0-rc.1", "1.0.0"]
    parsed = [sv.Version.parse(v) for v in chain]
    assert parsed == sorted(parsed)
    assert sv.compare("1.0.0", "2.0.0") == -1 and sv.compare("2.1.1", "2.1.0") == 1


def test_build_metadata_ignored():
    assert sv.compare("1.0.0+build.1", "1.0.0+build.2") == 0


@pytest.mark.parametrize("bad", ["1", "1.2", "01.2.3", "1.2.3-01", "1.2.3-", "a.b.c"])
def test_invalid(bad):
    with pytest.raises(ValueError):
        sv.Version.parse(bad)


def test_bumps():
    v = sv.Version.parse("1.4.2")
    assert str(v.bump("major")) == "2.0.0"
    assert str(v.bump("minor")) == "1.5.0"
    assert str(v.bump("patch")) == "1.4.3"
    assert str(v.bump("prerelease")) == "1.4.3-rc.0"
    assert str(sv.Version.parse("2.0.0-rc.1").bump("prerelease")) == "2.0.0-rc.2"
    assert str(sv.Version.parse("2.0.0-rc.1").bump("major")) == "2.0.0"


def test_next_version_pre_1_0():
    assert sv.next_version("0.9.3", "major") == "0.10.0"
    assert sv.next_version("0.9.3", "major", pre_major_minor=False) == "1.0.0"
    assert sv.next_version("1.2.3", "none") == "1.2.3"


@pytest.mark.parametrize("version,rng,expected", [
    ("1.4.2", "^1.2.3", True), ("2.0.0", "^1.2.3", False),
    ("0.2.9", "^0.2.3", True), ("0.3.0", "^0.2.3", False),
    ("0.0.3", "^0.0.3", True), ("0.0.4", "^0.0.3", False),
    ("1.2.9", "~1.2.3", True), ("1.3.0", "~1.2.3", False),
    ("1.9.0", "1.x", True), ("2.0.0", "1.x", False),
    ("1.2.7", "1.2.x", True), ("3.0.0", "*", True),
    ("1.5.0", "1.2.3 - 2.3.4", True), ("2.3.5", "1.2.3 - 2.3.4", False),
    ("2.9.9", "1.2.3 - 2", True), ("3.0.0", "1.2.3 - 2", False),
    ("1.0.0", ">=1.0.0 <2.0.0", True), ("2.0.0", ">=1.0.0 <2.0.0", False),
    ("3.1.0", "^1.2 || >=3", True), ("2.5.0", "^1.2 || >=3", False),
    ("1.3.0", ">1.2", True), ("1.2.9", ">1.2", False), ("1.2.9", "<=1.2", True),
])
def test_ranges(version, rng, expected):
    assert sv.satisfies(version, rng) is expected


def test_prerelease_rule():
    assert not sv.satisfies("1.3.0-beta.1", "^1.2.3")
    assert sv.satisfies("1.2.4-beta.2", ">=1.2.4-beta.1 <2")
    assert not sv.satisfies("1.2.5-beta.2", ">=1.2.4-beta.1 <2")
    assert sv.satisfies("1.3.0-beta.1", "^1.2.3", include_prerelease=True)


def test_max_satisfying():
    assert sv.max_satisfying(["1.2.3", "1.4.0", "2.0.0", "1.5.0-rc.1"], "^1.2") == "1.4.0"
    assert sv.max_satisfying(["0.1.0"], ">=1") is None


def test_cli(capsys):
    assert sv.main(["compare", "1.0.0-rc.1", "1.0.0"]) == 0
    assert capsys.readouterr().out.strip() == "-1"
    assert sv.main(["satisfies", "1.4.2", "^1.2"]) == 0
    assert sv.main(["satisfies", "2.4.2", "^1.2"]) == 1
    assert sv.main(["valid", "1.2"]) == 2
