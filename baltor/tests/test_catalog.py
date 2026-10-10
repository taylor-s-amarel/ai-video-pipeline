"""Tests for the Baltor component format and the local catalogue tool."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

BALTOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BALTOR / "tools"))

import baltor_catalog as bc  # noqa: E402


def test_every_component_validates():
    report, ok = bc.validate()
    assert not report.errors, "\n".join(report.errors[:50])
    assert len(ok) >= 12


def test_feed_collections_validate():
    assert bc.validate_feeds() == []


def test_all_twelve_kinds_present():
    _, ok = bc.validate()
    kinds = {m["kind"] for _, m in ok}
    assert kinds == set(bc.KIND_DIRS)


def test_package_digest_is_order_independent():
    files = [{"path": "b.txt", "sha256": "1" * 64}, {"path": "a.txt", "sha256": "2" * 64}]
    assert bc.package_digest(files) == bc.package_digest(list(reversed(files)))


def test_release_id_changes_with_content():
    a = [{"identity": "x", "version": "1.0.0", "digest": "a" * 64}]
    b = [{"identity": "x", "version": "1.0.0", "digest": "b" * 64}]
    assert bc.release_id(a) != bc.release_id(b)
    assert len(bc.release_id(a)) == 12


def test_index_matches_files_on_disk():
    index_path = BALTOR / "catalog" / "index.json"
    if not index_path.exists():
        pytest.skip("catalogue not built")
    index = json.loads(index_path.read_text())
    on_disk = {m["identity"] for _, m in bc.validate()[1]}
    in_index = {e["identity"] for e in index["packages"]}
    assert on_disk == in_index, "run: python3 baltor/tools/baltor_catalog.py build"
    sample = index["packages"][:: max(1, len(index["packages"]) // 50)]
    for e in sample:
        data = bc.read_package(e["identity"], e["digest"], index)
        assert set(data["files"]) == {f["path"] for f in e["files"]}


def test_search_finds_house_style():
    if not (BALTOR / "catalog" / "index.json").exists():
        pytest.skip("catalogue not built")
    hits = bc.search("vertical short house style captions yellow title", limit=20)
    assert any(h["identity"] == "short_video_house_style" for h in hits)


def test_read_rejects_wrong_digest():
    if not (BALTOR / "catalog" / "index.json").exists():
        pytest.skip("catalogue not built")
    with pytest.raises(SystemExit):
        bc.read_package("short_video_house_style", "0" * 64)


def test_place_and_lock_round_trip(tmp_path):
    if not (BALTOR / "catalog" / "index.json").exists():
        pytest.skip("catalogue not built")
    step = tmp_path / "step-1"
    for ident in ["short_video_house_style", "short_video_rules_reviewer", "render_short",
                  "video_render_step_instructions", "mp4_qa_probe", "short_video_spec"]:
        bc.place(ident, step, "claude-code")
    assert (step / ".claude/skills/short-video-house-style/SKILL.md").exists()
    assert (step / ".claude/agents/short-video-rules-reviewer.md").exists()
    assert (step / "CLAUDE.md").read_text().count("baltor:video_render_step_instructions") == 1
    bc.place("video_render_step_instructions", step, "claude-code")  # idempotent append
    assert (step / "CLAUDE.md").read_text().count("baltor:video_render_step_instructions") == 1
    assert bc.verify_lock(step) == []
    (step / ".baltor/lib/mp4-qa-probe/mp4_qa_probe.py").write_text("tampered\n")
    assert any("changed" in p for p in bc.verify_lock(step))


def test_validator_catches_bad_packages(tmp_path):
    good = BALTOR / "components" / "skills" / "short-video-house-style"
    bad = tmp_path / "skills" / "wrong-name"
    shutil.copytree(good, bad)
    (bad / "secret.txt").write_text("key = sk-ant-" + "a" * 40 + "\n")
    report = bc.Report()
    bc.validate_package(bad, report, bc.known_subkinds())
    text = "\n".join(report.errors)
    assert "directory name must be" in text
    assert "credential" in text


def test_contract_schema_examples_are_enforced(tmp_path):
    src = BALTOR / "components" / "contract-schemas" / "short-video-spec"
    pkg = tmp_path / "contract-schemas" / "short-video-spec"
    shutil.copytree(src, pkg)
    (pkg / "examples" / "broken.json").write_text(json.dumps({"duration_s": 5}))
    report = bc.Report()
    bc.validate_package(pkg, report, bc.known_subkinds())
    assert any("broken.json does not validate" in e for e in report.errors)
