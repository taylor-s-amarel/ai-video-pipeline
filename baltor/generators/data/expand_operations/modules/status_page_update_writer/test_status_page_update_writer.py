import pytest

import status_page_update_writer as m


@pytest.mark.parametrize("phase", m.PHASES)
def test_drafts_pass_their_own_lint(phase):
    text = m.draft(phase, "Checkout", "Some card payments fail", 30, detail="Saved carts are not affected")
    assert m.lint(text, phase) == [], text


def test_draft_requires_next_update_until_resolved():
    with pytest.raises(ValueError):
        m.draft("investigating", "API", "slow", None)
    assert "within" not in m.draft("resolved", "API", "slow", None)


def test_lint_catches_common_mistakes():
    text = ("We believe the root cause is a bad deploy by an engineer on db-1.internal (10.0.3.7); "
            "pods are in CrashLoopBackOff. It will be fixed by 3pm.")
    issues = " | ".join(m.lint(text, "investigating"))
    for needle in ("speculates", "blame", "promises", "10.0.3.7", "db-1.internal", "CrashLoopBackOff", "no next-update"):
        assert needle in issues


def test_identified_may_name_cause():
    text = "API: We identified a faulty configuration change and are reverting it. Next update within 30 minutes."
    assert m.lint(text, "identified") == []


def test_length_and_caps():
    assert any("characters" in i for i in m.lint("a" * 700 + " next update in 5", "monitoring"))
    assert any("all caps" in i for i in m.lint("SITE DOWN. NEXT UPDATE IN 10", "investigating"))


def test_cli(tmp_path, capsys):
    assert m.main(["draft", "--phase", "monitoring", "--component", "Search", "--impact", "Results are stale"]) == 0
    p = tmp_path / "u.txt"
    p.write_text("Search is broken due to kafka lag")
    assert m.main(["lint", "--phase", "investigating", str(p)]) == 1
