import json
import sys
import time
from pathlib import Path

import pytest

import showcase_runner as r

AGENT = r'''
import json, os, subprocess, sys, time
from pathlib import Path
prompt = Path(sys.argv[1]).read_text()
ws = Path(sys.argv[2])
mode = os.environ.get("FAKE_AGENT_MODE", "ok")
def emit(ev):
    print(json.dumps(ev), flush=True)
emit({"type": "system", "subtype": "init", "model": "fake-model-1", "mcp_servers": []})
n = 50 if mode == "greedy" else 2
for i in range(n):
    inp = {"command": "ls"}
    if "catalogue" in prompt and i == 0:
        subprocess.run(["baltor", "search", "deduplicate"], capture_output=True, text=True)
        subprocess.run(["baltor", "read", "dedupe_contacts_skill", "--out", "vendor"], capture_output=True, text=True,
                       cwd=ws)
        inp = {"command": "baltor search deduplicate"}
    if mode == "contaminate" and i == 0 and "catalogue" not in prompt:
        inp = {"command": "python3 /repo/baltor/tools/baltor_catalog.py search x"}
    emit({"type": "assistant", "message": {"id": f"m{i}", "model": "fake-model-1", "content": [
        {"type": "tool_use", "id": f"t{i}", "name": "Bash", "input": inp}],
        "usage": {"input_tokens": 100, "output_tokens": 20}}})
    if mode == "slow":
        time.sleep(30)
(ws / "answer.txt").write_text("42\n")
if mode == "contaminate" and "catalogue" not in prompt:
    (ws / ".baltor").mkdir()
    (ws / ".baltor" / "x").write_text("y")
emit({"type": "result", "subtype": "success", "usage": {"input_tokens": 200, "output_tokens": 40},
      "total_cost_usd": 0.01, "num_turns": 2})
'''

FAKE_TOOL = r'''
import hashlib
from pathlib import Path
FILES = {"SKILL.md": b"---\nname: dedupe-contacts-skill\ndescription: x\n---\nUse blocking keys.\n"}
def _digest():
    return hashlib.sha256("".join(f"{p}\0{hashlib.sha256(b).hexdigest()}\n" for p, b in FILES.items()).encode()).hexdigest()
def load_index():
    return {"release": "rel000000001", "packages": []}
def search(query, kind=None, limit=10):
    return [{"identity": "dedupe_contacts_skill", "kind": "skill", "subkind": None, "version": "1.0.0", "licence": "MIT",
             "size": 1, "digest": _digest(), "summary": "Deduplicate contacts.", "score": 1.0}]
def read_package(identity, expected_digest=None, index=None):
    if identity != "dedupe_contacts_skill":
        raise SystemExit("unknown identity")
    return {"entry": {"identity": identity, "version": "1.0.0", "kind": "skill", "licence": "MIT",
                      "digest": _digest(), "entry": "SKILL.md"}, "files": dict(FILES)}
def place(identity, step_dir, harness="claude-code", merge=False):
    d = Path(step_dir) / ".claude" / "skills" / "dedupe-contacts-skill"
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_bytes(FILES["SKILL.md"])
    return [d / "SKILL.md"]
'''


def arm(mode, addendum, agent, harness="command"):
    a = {"harness": harness, "harness_version": "test", "model": "fake-model-1", "allowed_tools": ["Bash", "Read"],
         "transcript_format": "stream-json", "isolation": "none", "catalogue_access": {"mode": mode},
         "prompt_addendum": addendum}
    if harness == "command":
        a["command"] = [sys.executable, str(agent), "{prompt_file}", "{workspace}"]
    return a


def make_spec(agent, mode="search-read", trials=3, harness="command"):
    return {
        "spec": "baltor.showcase-task/v1", "id": "tiny_answer", "version": 1, "purpose": "dry-run",
        "task_type": "capability", "domain": "coding", "title": "Write the answer file",
        "prompt": "Read input.txt and write the answer to answer.txt in the workspace.",
        "inputs": [{"name": "question", "source": "synthetic", "licence": "CC0-1.0", "path_in_workspace": "input.txt"}],
        "outputs": [{"path": "answer.txt", "required": True}],
        "budget": {"wall_s": 60, "tool_calls": 10, "tokens": 100000},
        "over_budget": "score-as-failure",
        "arms": {"baseline": arm("none", "", agent, harness),
                 "baltor": arm(mode, "You can search a component catalogue with the `baltor` command.", agent,
                               harness)},
        "metrics": [{"name": "answered", "direction": "higher", "kind": "deterministic",
                     "evaluator": {"type": "files_present", "params": {"paths": ["answer.txt"]}}, "weight": 1,
                     "primary": True, "on_missing": 0}],
        "success_threshold": {"metric": "answered", "op": ">=", "value": 1},
        "trials": trials, "order": "alternate", "negative_control": False,
        "analysis": {"design": "unpaired", "bootstrap_resamples": 2000, "ci_level": 0.95, "seed": 7, "alpha": 0.05},
        "disclosures": {"conflict_of_interest": "Same team wrote the components and the task."},
    }


@pytest.fixture()
def env(tmp_path, monkeypatch):
    agent = tmp_path / "agent.py"
    agent.write_text(AGENT)
    tool = tmp_path / "fake_catalog.py"
    tool.write_text(FAKE_TOOL)
    src = tmp_path / "src"
    (src / "workspace").mkdir(parents=True)
    (src / "workspace" / "input.txt").write_text("What is six times seven?\n")
    (src / "private").mkdir()
    (src / "private" / "answer.txt").write_text("42\n")
    spec = make_spec(agent)
    (src / "spec.json").write_text(json.dumps(spec))
    root = tmp_path / "showcases"
    monkeypatch.delenv("FAKE_AGENT_MODE", raising=False)
    return {"tmp": tmp_path, "agent": agent, "tool": tool, "src": src, "root": root, "spec": spec}


def opts(e, **kw):
    return r.RunOptions(catalog_tool=e["tool"], gateway=r.find_sibling("showcase_catalogue_gateway"),
                        workspace_root=e["tmp"] / "ws", **kw)


# ----------------------------------------------------------------- lint and registration

def test_lint_catches_unfair_specs(env):
    spec = env["spec"]
    assert r.lint_spec(spec)[0] == []
    bad = json.loads(json.dumps(spec))
    bad["arms"]["baltor"]["model"] = "bigger-model"
    assert any("model" in e for e in r.lint_spec(bad)[0])
    bad = json.loads(json.dumps(spec))
    bad["arms"]["baseline"]["prompt_addendum"] = "No catalogue for you."
    assert any("baseline prompt_addendum" in e for e in r.lint_spec(bad)[0])
    bad = json.loads(json.dumps(spec))
    bad["expected_components"] = ["dedupe_contacts_skill"]
    bad["prompt"] += " Use dedupe-contacts-skill."
    assert any("shared prompt" in e for e in r.lint_spec(bad)[0])
    bad = json.loads(json.dumps(spec))
    bad["metrics"].append(dict(bad["metrics"][0], name="judged", kind="llm-judge"))
    errs = r.lint_spec(bad)[0]
    assert any("exactly one metric must be primary" in e for e in errs)
    assert any("blind_judge" in e for e in errs)
    bad = json.loads(json.dumps(spec))
    bad["arms"]["baseline"]["catalogue_access"] = {"mode": "mcp"}
    assert any("baseline arm must" in e for e in r.lint_spec(bad)[0])
    assert any("3 trials" in w for w in r.lint_spec(spec)[1])


def test_register_freezes_spec_and_files(env):
    spec = r.register(env["src"] / "spec.json", env["root"], today="2026-10-10", now="2026-10-10T00:00:00Z")
    assert spec["preregistered_on"] == "2026-10-10"
    assert set(spec["files_sha256"]) == {"workspace/input.txt", "private/answer.txt"}
    assert spec["spec_sha256"] == r.spec_hash(spec)
    assert r.register(env["src"] / "spec.json", env["root"], today="2026-10-10")["spec_sha256"] == spec["spec_sha256"]
    changed = dict(env["spec"], title="A different title")
    (env["src"] / "spec.json").write_text(json.dumps(changed))
    with pytest.raises(r.ShowcaseError, match="immutable"):
        r.register(env["src"] / "spec.json", env["root"], today="2026-10-10")
    (env["root"] / "tasks" / "tiny_answer" / "private" / "answer.txt").write_text("41\n")
    with pytest.raises(r.ShowcaseError, match="differ from registration"):
        r.verify_task(env["root"], "tiny_answer")


def test_schedule_is_abba_and_deterministic(env):
    spec = r.register(env["src"] / "spec.json", env["root"], today="2026-10-10")
    s1 = r.make_schedule(spec)
    assert s1 == r.make_schedule(spec)
    assert len(s1) == 6
    for t in (1, 2, 3):
        pair = [x for x in s1 if x["trial"] == t]
        assert {p["arm"] for p in pair} == {"baseline", "baltor"}
        assert abs(pair[0]["index"] - pair[1]["index"]) == 1
    assert s1[0]["arm"] != s1[2]["arm"]  # ABBA: second block starts with the other arm


# ----------------------------------------------------------------- live runs (command adapter)

def test_live_runs_record_everything(env):
    r.register(env["src"] / "spec.json", env["root"], today="2026-10-10")
    recs = r.run_task(env["root"], "tiny_answer", opts(env))
    assert len(recs) == 6
    by = {x["run_id"]: x for x in recs}
    base = by["tiny_answer/baseline/1"]
    treat = by["tiny_answer/baltor/1"]
    assert base["exit"]["status"] == "completed" and base["included"] and base["contamination"]["clean"]
    assert base["catalogue"]["calls"] == [] and base["catalogue"]["mode"] == "none"
    assert treat["catalogue"]["calls"][0]["source"] == "gateway-log"
    assert [c["op"] for c in treat["catalogue"]["calls"]] == ["search", "read"]
    assert treat["catalogue"]["downloaded"][0]["identity"] == "dedupe_contacts_skill"
    assert treat["usage"]["tool_calls"] == 2 and treat["usage"]["tokens_total"] == 240
    assert treat["usage"]["cost_usd"] == pytest.approx(0.01) and treat["usage"]["cost_source"] == "harness-reported"
    outs = {o["path"]: o for o in treat["outputs"]}
    assert outs["answer.txt"]["change"] == "new" and outs["input.txt"]["change"] == "unchanged"
    assert "vendor/SKILL.md" in outs
    assert base["start_manifest_sha256"] == treat["start_manifest_sha256"]
    assert (env["root"] / "runs" / "tiny_answer" / "baltor" / "1" / "transcript.jsonl").exists()
    with pytest.raises(r.ShowcaseError, match="never overwritten"):
        r.run_trial(env["root"], r.verify_task(env["root"], "tiny_answer"),
                    {"index": 0, "arm": "baseline", "trial": 1}, opts(env))


def test_tool_call_budget_kills_the_run(env, monkeypatch):
    r.register(env["src"] / "spec.json", env["root"], today="2026-10-10")
    monkeypatch.setenv("FAKE_AGENT_MODE", "greedy")
    rec = r.run_task(env["root"], "tiny_answer", opts(env, only=["baseline:1"]))[0]
    assert rec["exit"]["status"] == "budget-exceeded"
    assert rec["budget"]["exceeded"] == ["tool_calls"]
    assert rec["usage"]["tool_calls"] >= 11


def test_wall_time_budget(env, monkeypatch, tmp_path):
    monkeypatch.setenv("FAKE_AGENT_MODE", "slow")
    ws = tmp_path / "wsx"
    ws.mkdir()
    prompt = tmp_path / "p.txt"
    prompt.write_text("hello")
    launch = r.Launch([sys.executable, str(env["agent"]), str(prompt), str(ws)], dict(__import__("os").environ), ws,
                      None, "stream-json")
    t0 = time.monotonic()
    res = r.execute(launch, {"wall_s": 1, "tool_calls": 100, "tokens": 10 ** 9}, tmp_path / "t.jsonl",
                    tmp_path / "e.log")
    assert res["status"] == "timeout" and res["exceeded"] == ["wall_s"]
    assert time.monotonic() - t0 < 20


def test_baseline_contamination_is_recorded_not_dropped(env, monkeypatch):
    r.register(env["src"] / "spec.json", env["root"], today="2026-10-10")
    monkeypatch.setenv("FAKE_AGENT_MODE", "contaminate")
    rec = r.run_task(env["root"], "tiny_answer", opts(env, only=["baseline:1"]))[0]
    assert rec["included"] is False
    assert "contamination" in rec["exclusion_reason"]
    assert any(".baltor" in f for f in rec["contamination"]["findings"])
    assert (env["root"] / "runs" / "tiny_answer" / "baseline" / "1" / "run.json").exists()


def test_assert_baseline_clean(tmp_path):
    ws = tmp_path / "w"
    ws.mkdir()
    ok = r.Launch(["claude"], {"PATH": ""}, ws, "x", "stream-json", {"mcpServers": {}})
    r.assert_baseline_clean(ok, ws, {})
    with pytest.raises(r.BaselineContamination):
        r.assert_baseline_clean(r.Launch(["claude"], {"PATH": "", "BALTOR_SERVICE_TOKEN": "x"}, ws, "x", "t"), ws, {})
    with pytest.raises(r.BaselineContamination):
        r.assert_baseline_clean(r.Launch(["claude"], {"PATH": ""}, ws, "x", "t",
                                         {"mcpServers": {"baltor": {"url": "https://baltor.ai/mcp"}}}), ws, {})
    (ws / "big.md").write_text("z" * 300)
    with pytest.raises(r.BaselineContamination):
        r.assert_baseline_clean(ok, ws, {r.sha256_file(ws / "big.md"): "some_skill/SKILL.md"})


def test_claude_and_codex_launch_shapes(env, tmp_path, monkeypatch):
    monkeypatch.setenv("BALTOR_SERVICE_TOKEN", "not-a-real-token")
    spec = make_spec(env["agent"], mode="mcp", harness="claude-code")
    spec["spec_sha256"] = "0" * 64
    gw = r.find_sibling("showcase_catalogue_gateway")
    for arm_name in ("baseline", "baltor"):
        td = tmp_path / arm_name
        td.mkdir()
        ws = td / "ws"
        ws.mkdir()
        la = r.build_launch(spec, arm_name, ws, td, catalog_tool=env["tool"], gateway=gw)
        assert la.argv[:3] == ["claude", "-p", "--output-format"]
        assert "--strict-mcp-config" in la.argv and la.stdin.startswith("Read input.txt")
        assert "BALTOR_SERVICE_TOKEN" not in la.env
        servers = json.loads((td / "tools" / "mcp.json").read_text())["mcpServers"]
        tools = la.argv[la.argv.index("--allowedTools") + 1:]
        if arm_name == "baseline":
            assert servers == {} and "mcp__baltor__intelligence_search" not in tools
            r.assert_baseline_clean(la, ws, {})
        else:
            assert "baltor" in servers and "mcp__baltor__provisioning_read" in tools
            assert "catalogue" in la.stdin
    spec_codex = make_spec(env["agent"], mode="mcp", harness="codex")
    spec_codex["spec_sha256"] = "0" * 64
    td = tmp_path / "codex"
    (td / "ws").mkdir(parents=True)
    base = r.build_launch(spec_codex, "baseline", td / "ws", td, catalog_tool=env["tool"], gateway=gw)
    treat = r.build_launch(spec_codex, "baltor", td / "ws", td, catalog_tool=env["tool"], gateway=gw)
    assert base.argv[:3] == ["codex", "exec", "--json"] and base.argv[-1] == "-"
    assert not any("mcp_servers" in x for x in base.argv)
    assert any(x.startswith("mcp_servers.baltor.command=") for x in treat.argv)


# ----------------------------------------------------------------- manual adapter

def test_prepare_and_import(env):
    spec = make_spec(env["agent"])
    spec["arms"]["baseline"]["harness"] = spec["arms"]["baltor"]["harness"] = "manual"
    for a in spec["arms"].values():
        a.pop("command")
    (env["src"] / "spec.json").write_text(json.dumps(spec))
    r.register(env["src"] / "spec.json", env["root"], today="2026-10-10")
    out = r.prepare(env["root"], "tiny_answer", env["tmp"] / "export")
    d = out / "baltor" / "1"
    assert (d / "input.txt").exists() and "catalogue" in (d / ".showcase" / "PROMPT.md").read_text()
    (d / "answer.txt").write_text("42\n")
    (d / ".showcase" / "usage.json").write_text(json.dumps({"wall_s": 30, "tool_calls": 4, "tokens_in": 900,
                                                            "tokens_out": 100}))
    (d / ".showcase" / "catalogue_calls.jsonl").write_text(json.dumps(
        {"op": "read", "identity": "dedupe_contacts_skill", "version": "1.0.0", "digest": "ab" * 32, "ok": True}) + "\n")
    rec = r.import_trial(env["root"], "tiny_answer", "baltor", 1, d)
    assert rec["adapter"] == "manual" and rec["usage"]["source"] == "self-reported"
    assert rec["start_verified"] == "inputs-match" and rec["exit"]["status"] == "imported"
    assert rec["catalogue"]["downloaded"][0]["identity"] == "dedupe_contacts_skill"
    assert ".showcase/usage.json" not in {o["path"] for o in rec["outputs"]}
    b = out / "baseline" / "1"
    (b / ".showcase" / "usage.json").write_text(json.dumps({"wall_s": 30, "tool_calls": 99, "tokens_in": 1,
                                                            "tokens_out": 1}))
    rec_b = r.import_trial(env["root"], "tiny_answer", "baseline", 1, b)
    assert rec_b["exit"]["status"] == "budget-exceeded" and rec_b["budget"]["exceeded"] == ["tool_calls"]
    item = r.replace(env["root"], "tiny_answer", "tiny_answer/baseline/1", "operator imported the wrong folder")
    assert item["trial"] == 4 and item["replaces"] == "tiny_answer/baseline/1"
    again = json.loads((env["root"] / "runs" / "tiny_answer" / "baseline" / "1" / "run.json").read_text())
    assert again["included"] is False and again["exclusion_reason"].startswith("replaced")
    st = r.status(env["root"], "tiny_answer")
    assert len(st["items"]) == 7


# ----------------------------------------------------------------- transcript parsers

def test_codex_and_opencode_parsers():
    u = r.Usage("codex-json")
    for ev in [{"type": "item.started", "item": {"id": "i1", "type": "command_execution", "command": "baltor search x"}},
               {"type": "item.completed", "item": {"id": "i1", "type": "command_execution", "command": "baltor search x"}},
               {"type": "item.completed", "item": {"id": "i2", "type": "mcp_tool_call", "server": "baltor",
                                                    "tool": "provisioning_read", "arguments": {"identity": "a_b"}}},
               {"type": "turn.completed", "usage": {"input_tokens": 1000, "cached_input_tokens": 400,
                                                    "output_tokens": 50}}]:
        u.feed(json.dumps(ev))
    assert u.tool_calls == 2 and u.tokens()["tokens_total"] == 1050
    assert [c["op"] for c in u.catalogue_calls] == ["search", "read"]
    o = r.Usage("opencode-json")
    for ev in [{"type": "tool_use", "part": {"callID": "c1", "tool": "bash", "state": {"input": {"command": "ls"}}}},
               {"type": "step_finish", "part": {"id": "s1", "tokens": {"input": 10, "output": 5, "reasoning": 1,
                                                                       "cache": {"read": 3, "write": 0}},
                                                "cost": 0.002}}]:
        o.feed(json.dumps(ev))
    assert o.tool_calls == 1 and o.tokens()["tokens_total"] == 19 and o.cost == pytest.approx(0.002)
    c = r.Usage("stream-json")
    c.feed(json.dumps({"type": "assistant", "message": {"id": "m1", "content": [
        {"type": "tool_use", "id": "t1", "name": "mcp__baltor__intelligence_search", "input": {"query": "q"}}],
        "usage": {"input_tokens": 5, "cache_read_input_tokens": 100, "output_tokens": 7}}}))
    c.feed(json.dumps({"type": "assistant", "message": {"id": "m1", "content": [
        {"type": "tool_use", "id": "t1", "name": "mcp__baltor__intelligence_search", "input": {"query": "q"}}],
        "usage": {"input_tokens": 5, "cache_read_input_tokens": 100, "output_tokens": 7}}}))
    assert c.tool_calls == 1 and c.tokens()["tokens_total"] == 112
    assert c.catalogue_calls[0]["op"] == "search"
