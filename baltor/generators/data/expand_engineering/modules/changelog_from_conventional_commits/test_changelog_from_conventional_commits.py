import json
import subprocess

import changelog_from_conventional_commits as cl

MSGS = [
    ("a1b2c3d4", "feat(cli): add --dry-run flag"),
    ("b2c3d4e5", "fix: handle empty config file"),
    ("c3d4e5f6", "docs: fix typo"),
    ("d4e5f6a7", "refactor!: rename load() to read()\n\nBREAKING CHANGE: load() is gone, call read()"),
    ("e5f6a7b8", "fix(security): escape HTML in error page"),
    ("f6a7b8c9", "perf: cache parsed templates"),
    ("0a1b2c3d", "Merge branch 'x'"),
]


def entries():
    return [e for sha, m in MSGS if (e := cl.classify(m, sha))]


def test_classification():
    secs = {e.text: e.section for e in entries()}
    assert secs["**cli:** add --dry-run flag"] == "Added"
    assert secs["handle empty config file"] == "Fixed"
    assert any(t.startswith("**BREAKING:**") and s == "Changed" for t, s in secs.items())
    assert secs["**security:** escape HTML in error page"] == "Security"
    assert "fix typo" not in " ".join(secs)


def test_bump_and_next_version():
    es = entries()
    assert cl.bump_for(es) == "major"
    assert cl.next_version("1.4.0", "major") == "2.0.0"
    assert cl.next_version("0.4.0", "major") == "0.5.0"
    assert cl.bump_for([e for e in es if not e.breaking]) == "minor"


def test_render_order_and_links():
    out = cl.render("2.0.0", entries(), "2026-10-10", "https://example.org/c/{sha}")
    assert out.startswith("## [2.0.0] - 2026-10-10")
    assert out.index("### Added") < out.index("### Changed") < out.index("### Fixed") < out.index("### Security")
    assert "([a1b2c3d](https://example.org/c/a1b2c3d4))" in out


def test_insert_under_unreleased():
    existing = "# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2026-01-01\n\n### Added\n\n- first\n"
    new = cl.insert_into_changelog(existing, "## [1.1.0] - 2026-10-10\n\n### Fixed\n\n- x\n")
    assert new.index("## [Unreleased]") < new.index("## [1.1.0]") < new.index("## [1.0.0]")


def test_cli_with_messages(tmp_path, capsys):
    p = tmp_path / "m.json"
    p.write_text(json.dumps([{"sha": s, "message": m} for s, m in MSGS]))
    target = tmp_path / "CHANGELOG.md"
    assert cl.main(["--messages", str(p), "--current", "1.4.0", "--date", "2026-10-10", "--write", str(target)]) == 0
    assert "## [2.0.0] - 2026-10-10" in capsys.readouterr().out
    assert "## [Unreleased]" in target.read_text()


def test_git_log_reader(tmp_path):
    run = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    run("init", "-q")
    run("config", "user.email", "t@example.org")
    run("config", "user.name", "T")
    for i, msg in enumerate(["feat: one", "fix: two\n\nbody line"]):
        (tmp_path / f"f{i}").write_text(str(i))
        run("add", ".")
        run("commit", "-q", "-m", msg)
    pairs = cl.git_messages(None, "HEAD", cwd=str(tmp_path))
    assert [m.splitlines()[0] for _, m in pairs] == ["fix: two", "feat: one"]
    assert all(len(sha) == 40 for sha, _ in pairs)
