import datetime as dt
import os
import subprocess

import pytest

import branch_hygiene_report as bh


@pytest.mark.parametrize("name", ["feat/123-add-login", "fix/null-pointer", "deps/bump-ruff", "main", "release/2.4.x"])
def test_good_names(name):
    assert bh.check_name(name) == []


@pytest.mark.parametrize("name,fragment", [
    ("Feature/Login", "pattern"), ("feat/a..b", "'..'"), ("feat/has space", "spaces"),
    ("feat/x.lock", ".lock"), ("my-branch", "pattern"), ("feat/", "end with"),
])
def test_bad_names(name, fragment):
    assert any(fragment in p for p in bh.check_name(name))


def test_parse_for_each_ref():
    now = dt.datetime(2026, 10, 10, tzinfo=dt.timezone.utc)
    out = "feat/a\t2026-09-01T10:00:00+00:00\t[gone]\nfix/b\t2026-10-09T10:00:00+00:00\t\n"
    bs = bh.parse_for_each_ref(out, now)
    assert bs[0].age_days == 38 and bs[0].track == "[gone]" and bs[1].age_days == 0


def git(cwd, *args, env=None):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, env=env)


def test_report_in_real_repo(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@example.org")
    git(tmp_path, "config", "user.name", "T")
    (tmp_path / "a").write_text("1")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "init")
    git(tmp_path, "branch", "feat/merged-one")
    git(tmp_path, "checkout", "-q", "-b", "feat/old-work")
    (tmp_path / "b").write_text("2")
    git(tmp_path, "add", ".")
    env = dict(os.environ, GIT_COMMITTER_DATE="2026-01-01T00:00:00+00:00", GIT_AUTHOR_DATE="2026-01-01T00:00:00+00:00")
    git(tmp_path, "commit", "-q", "-m", "old", env=env)
    git(tmp_path, "checkout", "-q", "main")
    now = dt.datetime(2026, 10, 10, tzinfo=dt.timezone.utc)
    flagged = {b.name: b for b in bh.report("main", 30, cwd=str(tmp_path), now=now)}
    assert flagged["feat/merged-one"].merged
    assert not flagged["feat/old-work"].merged and "no commits" in flagged["feat/old-work"].reasons[0]
    cmds = bh.cleanup_commands(list(flagged.values()))
    assert "git branch -d feat/merged-one" in cmds
    assert any(c.startswith("git branch -D feat/old-work") for c in cmds)


def test_cli_check(capsys):
    assert bh.main(["check", "feat/ok-name"]) == 0
    assert bh.main(["check", "Bad Name"]) == 1
