import io
import json
import os
import time

import hook


GOOD = """# Digest

## Releases

- [Godot 4.7.2](https://github.com/godotengine/godot/releases/tag/4.7.2-stable) — 2026-10-08

## Feeds that failed

- https://example.org/broken.xml: HTTP 404
"""

BAD = GOOD.replace("## Feeds that failed", "- Everyone is switching to Godot this week\n\n## Feeds that failed")


def test_problems_in_flags_only_unlinked_bullets_outside_exempt_sections():
    assert hook.problems_in(GOOD) == []
    found = hook.problems_in(BAD)
    assert len(found) == 1 and "Everyone is switching" in found[0]


def test_recent_digests_respects_age(tmp_path):
    new = tmp_path / "a" / "new.md"
    new.parent.mkdir()
    new.write_text(GOOD)
    old = tmp_path / "old.md"
    old.write_text(BAD)
    past = time.time() - 10_000
    os.utime(old, (past, past))
    assert hook.recent_digests(tmp_path, max_age_s=3600) == [new]
    assert hook.recent_digests(tmp_path / "missing", 3600) == []


def run(monkeypatch, tmp_path, text, event):
    (tmp_path / "d.md").write_text(text)
    monkeypatch.setenv("BALTOR_DIGEST_DIR", str(tmp_path))
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(event)))
    return hook.main()


def test_main_blocks_bad_digest_and_allows_good(monkeypatch, tmp_path, capsys):
    assert run(monkeypatch, tmp_path, BAD, {"hook_event_name": "Stop"}) == 2
    assert "without a source link" in capsys.readouterr().err
    assert run(monkeypatch, tmp_path, GOOD, {"hook_event_name": "Stop"}) == 0


def test_main_never_loops_when_stop_hook_already_active(monkeypatch, tmp_path):
    assert run(monkeypatch, tmp_path, BAD, {"stop_hook_active": True}) == 0
