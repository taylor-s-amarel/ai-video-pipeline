import json
import subprocess
import sys
from pathlib import Path

import pytest

import showcase_catalogue_gateway as g

FAKE_TOOL = r'''
import hashlib, json
from pathlib import Path

ITEMS = {
    "dedupe_contacts_skill": {"kind": "skill", "version": "1.2.0", "licence": "MIT", "summary": "Deduplicate contacts.",
                              "files": {"SKILL.md": b"---\nname: dedupe\n---\nUse blocking keys.\n",
                                        "baltor.json": b"{}"}},
}

def _digest(files):
    lines = "".join(f"{p}\0{hashlib.sha256(b).hexdigest()}\n" for p, b in sorted(files.items()))
    return hashlib.sha256(lines.encode()).hexdigest()

def load_index():
    return {"release": "abc123def456", "packages": []}

def search(query, kind=None, limit=10):
    out = []
    for ident, it in ITEMS.items():
        if any(w in it["summary"].lower() for w in query.lower().split()):
            out.append({"identity": ident, "kind": it["kind"], "subkind": None, "version": it["version"],
                        "licence": it["licence"], "size": 10, "digest": _digest(it["files"]),
                        "summary": it["summary"], "score": 1.0})
    return out[:limit]

def read_package(identity, expected_digest=None, index=None):
    if identity not in ITEMS:
        raise SystemExit(f"unknown identity '{identity}'")
    it = ITEMS[identity]
    d = _digest(it["files"])
    if expected_digest and not d.startswith(expected_digest):
        raise SystemExit("digest mismatch")
    return {"entry": {"identity": identity, "version": it["version"], "kind": it["kind"], "licence": it["licence"],
                      "digest": d, "entry": "SKILL.md"}, "files": dict(it["files"])}

def place(identity, step_dir, harness="claude-code", merge=False):
    data = read_package(identity)
    dest = Path(step_dir) / ".claude" / "skills" / identity.replace("_", "-") / "SKILL.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data["files"]["SKILL.md"])
    return [dest]
'''


@pytest.fixture()
def tool_path(tmp_path):
    p = tmp_path / "fake_catalog.py"
    p.write_text(FAKE_TOOL)
    return p


@pytest.fixture()
def gw(tool_path, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    return g.Gateway(g.load_catalog_tool(tool_path), tmp_path / "calls.jsonl", ws)


def test_search_and_read_are_logged(gw, tmp_path):
    hits = gw.search("deduplicate contacts")
    assert hits[0]["identity"] == "dedupe_contacts_skill"
    res = gw.read("dedupe_contacts_skill", out_dir="vendor/dedupe")
    assert (tmp_path / "ws" / "vendor" / "dedupe" / "SKILL.md").exists()
    calls = g.read_log(tmp_path / "calls.jsonl")
    assert [c["op"] for c in calls] == ["search", "read"]
    assert calls[1]["digest"] == res["digest"] and calls[1]["version"] == "1.2.0"
    assert all(c["source"] == "gateway-log" for c in calls)
    assert g.downloaded_items(calls) == [{"identity": "dedupe_contacts_skill", "version": "1.2.0",
                                         "digest": res["digest"]}]


def test_read_inline_and_errors_are_logged(gw, tmp_path):
    res = gw.read("dedupe_contacts_skill")
    assert "Use blocking keys" in res["content"]["SKILL.md"]
    with pytest.raises(g.GatewayError):
        gw.read("does_not_exist")
    with pytest.raises(g.GatewayError):
        gw.read("dedupe_contacts_skill", out_dir="../escape")
    calls = g.read_log(tmp_path / "calls.jsonl")
    assert [c["ok"] for c in calls] == [True, False, False]
    assert len(g.downloaded_items(calls)) == 1


def test_place_records_digest(gw, tmp_path):
    written = gw.place("dedupe_contacts_skill")
    assert Path(written[0]).exists()
    call = g.read_log(tmp_path / "calls.jsonl")[-1]
    assert call["op"] == "place" and call["ok"] and len(call["digest"]) == 64


def test_mcp_handle_message(gw):
    init = g.handle_message(gw, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                 "params": {"protocolVersion": "2025-03-26"}})
    assert init["result"]["protocolVersion"] == "2025-03-26"
    assert g.handle_message(gw, {"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    names = [t["name"] for t in g.handle_message(gw, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
             ["result"]["tools"]]
    assert names == ["intelligence_search", "provisioning_read"]
    res = g.handle_message(gw, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                "params": {"name": "intelligence_search", "arguments": {"query": "contacts"}}})
    payload = json.loads(res["result"]["content"][0]["text"])
    assert payload["results"][0]["identity"] == "dedupe_contacts_skill"
    bad = g.handle_message(gw, {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                                "params": {"name": "provisioning_read", "arguments": {"identity": "nope"}}})
    assert bad["result"]["isError"] is True
    assert g.handle_message(gw, {"jsonrpc": "2.0", "id": 5, "method": "bogus"})["error"]["code"] == -32601


def test_mcp_server_over_stdio(tool_path, tmp_path):
    log = tmp_path / "mcp.jsonl"
    msgs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "provisioning_read", "arguments": {"identity": "dedupe_contacts_skill"}}},
    ]
    proc = subprocess.run([sys.executable, g.__file__, "mcp", "--log", str(log), "--catalog-tool", str(tool_path),
                           "--workspace", str(tmp_path)],
                          input="\n".join(json.dumps(m) for m in msgs) + "\n", capture_output=True, text=True,
                          timeout=60)
    assert proc.returncode == 0, proc.stderr
    lines = [json.loads(x) for x in proc.stdout.splitlines()]
    assert [x["id"] for x in lines] == [1, 2]
    assert g.read_log(log)[0]["identity"] == "dedupe_contacts_skill"


def test_shim_runs_and_logs(tool_path, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    log = tmp_path / "shim.jsonl"
    shim = g.write_shim(tmp_path / "bin", log=str(log), catalog_tool=str(tool_path), workspace=str(ws))
    proc = subprocess.run([str(shim), "search", "deduplicate"], capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert "dedupe_contacts_skill" in proc.stdout
    proc = subprocess.run([str(shim), "read", "dedupe_contacts_skill", "--out", "lib/dedupe"], capture_output=True,
                          text=True, timeout=60, cwd=ws)
    assert proc.returncode == 0, proc.stderr
    assert (ws / "lib" / "dedupe" / "SKILL.md").exists()
    assert [c["op"] for c in g.read_log(log)] == ["search", "read"]


def test_mcp_server_entry_shape(tmp_path):
    entry = g.mcp_server_entry(log="l.jsonl", catalog_tool="t.py", workspace=str(tmp_path))
    assert entry["args"][1] == "mcp" and "--log" in entry["args"]
