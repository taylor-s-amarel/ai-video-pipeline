import json
import shutil
from pathlib import Path

import pytest

import agent_feeds_watchlist_from_repo as w

FIX = Path(__file__).resolve().parent / "fixtures" / "sample_repo"


@pytest.fixture()
def repo(tmp_path):
    layout = json.loads((FIX / "layout.json").read_text())
    layout.pop("_comment")
    for src, dest in layout.items():
        target = tmp_path / "demo" / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(FIX / src, target)
    return tmp_path / "demo"


@pytest.fixture()
def wl(repo):
    return w.build_watchlist(repo, now="2026-10-10T12:00:00Z")


def pkg(wl, eco, name):
    return next(p for p in wl["packages"] if p["ecosystem"] == eco and p["name"] == name)


def test_python_requirements_and_pyproject(wl):
    assert pkg(wl, "PyPI", "examplelib")["pinned"] == "2.30.0"  # pinned runtime entry wins over dev range
    assert pkg(wl, "PyPI", "anthropic")["version"] == ">=0.40,<2"
    k = pkg(wl, "PyPI", "Kokoro_ONNX")
    assert k["pinned"] == "0.4.9" and k["version"] == "==0.4.9"
    assert pkg(wl, "PyPI", "yt-dlp")["version"] is None
    assert pkg(wl, "PyPI", "mypkg")["version"] is None
    assert pkg(wl, "PyPI", "pytest")["dev"] is True
    assert pkg(wl, "PyPI", "moviepy")["version"] == ">=2.0"
    assert pkg(wl, "PyPI", "ruff")["dev"] is True
    assert not any(p["name"] == "local-thing" for p in wl["packages"])
    assert {"name": "python", "version": ">=3.11", "source_file": "pyproject.toml"} in wl["runtimes"]


def test_node_cargo_go(wl):
    assert pkg(wl, "npm", "@anthropic-ai/sdk")["version"] == "^0.30.0"
    assert pkg(wl, "npm", "next")["pinned"] == "15.0.3"
    assert pkg(wl, "npm", "example-merge")["version"] == "^2.0.3"  # npm: alias resolved
    assert pkg(wl, "npm", "@playwright/test")["dev"] is True
    assert not any(p["name"] == "should-not-appear" for p in wl["packages"])  # node_modules skipped
    assert pkg(wl, "crates.io", "tokio")["pinned"] == "1.40.0"
    assert pkg(wl, "crates.io", "serde")["pinned"] is None
    assert pkg(wl, "crates.io", "example-serde")["version"] == "1.0.200"
    assert pkg(wl, "Go", "github.com/spf13/cobra")["pinned"] == "1.9.0"
    assert pkg(wl, "Go", "golang.org/x/net")["version"] == "v0.30.0"
    rts = {(r["name"], r["version"]) for r in wl["runtimes"]}
    assert {("node", ">=20"), ("pnpm", "9.12.0"), ("rust", "1.80"), ("go", "1.23"), ("python", "3.12")} <= rts


def test_containers(wl):
    assert pkg(wl, "Docker", "python")["version"] == "3.12-slim"
    assert pkg(wl, "Docker", "ghcr.io/example/ffmpeg-static")["version"] == "7.1"
    assert pkg(wl, "Docker", "postgres")["pinned"] == "16.4"
    assert pkg(wl, "Docker", "redis")["version"] == "7"
    assert not any(p["name"] in ("base", "scratch") for p in wl["packages"])


def test_mcp_and_harnesses(wl):
    servers = {s["name"]: s for s in wl["mcp_servers"]}
    assert servers["filesystem"]["package"] == "@modelcontextprotocol/server-filesystem"
    assert pkg(wl, "npm", "@modelcontextprotocol/server-filesystem")["pinned"] == "2026.1.14"
    assert servers["fetch"]["ecosystem"] == "PyPI" and servers["fetch"]["package"] == "mcp-server-fetch"
    assert servers["github"]["url"] == "https://api.githubcopilot.com/mcp/"
    assert servers["browser"]["package"] == "mcp/playwright"
    assert servers["context7"]["harness"] == "codex"
    assert servers["everything"]["harness"] == "opencode"
    assert wl["harnesses"] == ["claude-code", "codex", "opencode"]
    assert "mcp" in wl["topics"]


def test_inferred_vendors_products_topics_and_project(wl):
    assert "Anthropic" in wl["vendors"] and "Model Context Protocol" in wl["vendors"]
    assert {"anthropic-sdk", "claude-code", "python", "postgres"} <= set(wl["products"])
    assert {"llm", "tts", "video"} <= set(wl["topics"])
    assert wl["project"] == "video-pipeline-demo"
    assert wl["spec"] == "baltor.agent-feed-watchlist/v1"


def test_merge_keeps_hand_edits(wl):
    old = {"project": "my-name", "topics": ["godot"], "excluded_topics": ["crypto"], "min_severity": "high", "vendors": ["Acme"]}
    merged = w.merge_manual(wl, old)
    assert merged["project"] == "my-name" and merged["min_severity"] == "high"
    assert "godot" in merged["topics"] and "llm" in merged["topics"] and "Acme" in merged["vendors"]
    assert merged["excluded_topics"] == ["crypto"]


def test_cli_writes_file(repo, capsys):
    out = repo / ".baltor" / "feeds" / "watchlist.json"
    assert w.main([str(repo), "--out", str(out)]) == 0
    data = json.loads(out.read_text())
    assert data["packages"] and "wrote" in capsys.readouterr().out


def test_bad_file_does_not_stop_scan(repo):
    (repo / "Cargo.toml").write_text("this is [not toml")
    wl = w.build_watchlist(repo)
    assert any(p["name"] == "examplelib" for p in wl["packages"])
