#!/usr/bin/env python3
"""Run pre-registered Baltor showcase tasks fairly: baseline arm versus Baltor arm.

Lifecycle (every step refuses to continue when the task spec or its files changed
after registration)::

    lint      SPEC.json                      fairness checks before registering
    register  SPEC.json --root showcases     freeze the spec: files_sha256 + spec_sha256, copy to tasks/<id>/
    plan      --root R --task ID             write the run order (ABBA-alternated or seeded random)
    prepare   --root R --task ID --out DIR   export the starting workspace + per-arm prompts (manual runs)
    run       --root R --task ID             run every scheduled trial with the spec's harness adapter
    import    --root R --task ID --from DIR  manual adapter: import externally produced workspaces
    replace   --root R --task ID --run RUN_ID --reason TEXT   exclude a broken run and schedule a new trial
    status    --root R --task ID

Adapters: ``claude-code`` (``claude -p --output-format stream-json`` with an
explicit tool allow-list and a strict MCP config), ``codex`` (``codex exec --json``),
``opencode`` (``opencode run --format json``), ``command`` (any argv template in
the spec) and ``manual`` (import). Budgets (wall time, tool calls, tokens, optional
USD) are enforced live by parsing the event stream and killing the process group.

Catalogue access for the Baltor arm goes through the logged
``showcase_catalogue_gateway`` (a ``baltor`` shim on PATH, or a stdio MCP server
with ``intelligence_search`` / ``provisioning_read``) or a hosted MCP endpoint.
The baseline arm gets an empty MCP config, no shim, no Baltor environment
variables, and a pre-launch check that refuses to start if anything Baltor-shaped
is configured; after the run its workspace and transcript are scanned and a
contaminated run is kept on record with ``included: false``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import platform
import queue
import random
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

VERSION = "1.0.0"
HERE = Path(__file__).resolve().parent
ARMS = ("baseline", "baltor")
TASK_SUBDIRS = ("workspace", "private", "setup", "evaluators")
IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", ".mypy_cache", ".showcase"}
DEFAULT_RULES = {
    "min_trials_per_arm": 3,
    "preferred_trials_per_arm": 5,
    "max_prompt_addendum_chars": 1200,
    "identical_arm_fields": ["harness", "harness_version", "model", "allowed_tools", "extra_args", "isolation",
                             "command", "transcript_format"],
    "catalogue_markers": ["baltor_catalog.py", "intelligence_search", "provisioning_read", "mcp__baltor",
                          "baltor.ai/mcp", ".baltor/", "step.lock.json", "showcase_catalogue_gateway",
                          "/baltor/components/", "/baltor/catalog/"],
    "min_matching_file_bytes": 200,
    "over_budget_statuses": ["timeout", "budget-exceeded"],
}
CATALOGUE_TOOLS_CLAUDE = {
    "search-read": ["Bash(baltor:*)", "Bash(baltor *)"],
    "mcp": ["mcp__baltor__intelligence_search", "mcp__baltor__provisioning_read"],
}
HARNESS_BIN = {"claude-code": "claude", "codex": "codex", "opencode": "opencode"}
TRANSCRIPT_FORMAT = {"claude-code": "stream-json", "codex": "codex-json", "opencode": "opencode-json"}


class ShowcaseError(Exception):
    pass


class BaselineContamination(ShowcaseError):
    pass


# --------------------------------------------------------------------------- small helpers

def load_rules() -> dict:
    rules = json.loads(json.dumps(DEFAULT_RULES))
    p = HERE / "fairness_rules.json"
    if p.exists():
        rules.update(json.loads(p.read_text(encoding="utf-8")))
    return rules


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def spec_hash(spec: dict) -> str:
    """SHA-256 of the canonical JSON of every field except spec_sha256 itself."""
    return sha256_bytes(canonical_json({k: v for k, v in spec.items() if k != "spec_sha256"}))


def walk_files(base: Path, ignore_dirs: set[str] | None = None) -> list[Path]:
    ignore = IGNORE_DIRS if ignore_dirs is None else ignore_dirs
    out = []
    if not base.exists():
        return out
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in ignore)
        for f in sorted(filenames):
            p = Path(dirpath) / f
            if p.is_file() and not p.is_symlink():
                out.append(p)
    return out


def manifest(base: Path) -> dict[str, str]:
    return {p.relative_to(base).as_posix(): sha256_file(p) for p in walk_files(base)}


def manifest_hash(m: dict[str, str]) -> str:
    return sha256_bytes("".join(f"{k}\0{v}\n" for k, v in sorted(m.items())).encode("utf-8"))


def copy_tree(src: Path, dst: Path, ignore_dirs: set[str] | None = None) -> None:
    for p in walk_files(src, ignore_dirs):
        rel = p.relative_to(src)
        d = dst / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, d)


def read_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def find_sibling(identity: str) -> Path | None:
    """Find a sibling code module whether placed (kebab dir) or in generator data (snake dir)."""
    for d in (HERE.parent / identity.replace("_", "-"), HERE.parent / identity, HERE):
        p = d / f"{identity}.py"
        if p.exists():
            return p
    return None


def find_catalog_tool(start: Path | None = None) -> Path | None:
    env = os.environ.get("BALTOR_CATALOG_TOOL")
    if env and Path(env).exists():
        return Path(env).resolve()
    for base in [Path(start or Path.cwd()).resolve(), HERE]:
        for d in [base, *base.parents]:
            p = d / "baltor" / "tools" / "baltor_catalog.py"
            if p.exists():
                return p
    return None


def validate_schema(name: str, instance: dict) -> list[str]:
    path = HERE / "schemas" / f"{name}.schema.json"
    if not path.exists():
        return []
    try:
        import jsonschema  # type: ignore
    except ImportError:  # pragma: no cover
        return []
    schema = read_json(path)
    v = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
            for e in sorted(v.iter_errors(instance), key=lambda e: list(e.absolute_path))]


# --------------------------------------------------------------------------- lint

def _mentions(text: str, needles: list[str]) -> list[str]:
    low = text.lower()
    return [n for n in needles if n and n.lower() in low]


def lint_spec(spec: dict, task_dir: Path | None = None, rules: dict | None = None) -> tuple[list[str], list[str]]:
    """Fairness checks JSON Schema cannot express. Returns (errors, warnings)."""
    rules = rules or load_rules()
    errors: list[str] = []
    warnings: list[str] = []
    arms = spec.get("arms", {})
    base, treat = arms.get("baseline", {}), arms.get("baltor", {})
    for f in rules["identical_arm_fields"]:
        if base.get(f) != treat.get(f):
            errors.append(f"arms differ in '{f}': baseline={base.get(f)!r} baltor={treat.get(f)!r} "
                          "(only catalogue_access and prompt_addendum may differ)")
    if (base.get("catalogue_access") or {}).get("mode") != "none":
        errors.append("baseline arm must have catalogue_access.mode 'none'")
    tmode = (treat.get("catalogue_access") or {}).get("mode")
    if tmode in (None, "none"):
        errors.append("baltor arm needs catalogue access (search-read, mcp or preplaced)")
    if tmode in ("search-read", "mcp") and not (treat.get("prompt_addendum") or "").strip():
        warnings.append("baltor arm has no prompt_addendum: the agent is not told the catalogue exists")
    expected = spec.get("expected_components") or []
    needles = expected + [e.replace("_", "-") for e in expected]
    prompt = spec.get("prompt", "")
    hits = _mentions(prompt, ["baltor"] + needles)
    if hits:
        errors.append(f"the shared prompt mentions {hits}: it must be identical and neutral for both arms")
    hits = _mentions(treat.get("prompt_addendum", ""), needles)
    if hits:
        errors.append(f"baltor prompt_addendum names expected components {hits}: the agent must find them itself")
    hits = _mentions(base.get("prompt_addendum", ""), ["baltor", "catalogue", "catalog"])
    if hits:
        errors.append(f"baseline prompt_addendum mentions {hits}")
    for name in ("baseline", "baltor"):
        if len(arms.get(name, {}).get("prompt_addendum", "")) > rules["max_prompt_addendum_chars"]:
            errors.append(f"{name} prompt_addendum is longer than {rules['max_prompt_addendum_chars']} characters")
    if tmode == "preplaced" and expected and set(expected) != set(treat["catalogue_access"].get("identities", [])):
        warnings.append("preplaced identities differ from expected_components; the analysis will show both")
    shared = json.dumps(spec.get("shared_mcp_servers") or {}).lower()
    if "baltor" in shared:
        errors.append("shared_mcp_servers must not include a Baltor catalogue server (that would leak into the baseline)")

    metrics = spec.get("metrics", [])
    names = [m.get("name") for m in metrics]
    dupes = sorted(n for n, c in Counter(names).items() if c > 1)
    if dupes:
        errors.append(f"duplicate metric names {dupes}")
    primaries = [m["name"] for m in metrics if m.get("primary")]
    if len(primaries) != 1:
        errors.append(f"exactly one metric must be primary (found {primaries or 'none'})")
    thr = (spec.get("success_threshold") or {}).get("metric")
    ranged = all("range" in m for m in metrics)
    if thr and thr not in names and not (thr == "weighted_score" and ranged):
        errors.append(f"success_threshold.metric '{thr}' is not a metric (weighted_score needs a range on every metric)")
    for m in metrics:
        ev = (m.get("evaluator") or {}).get("type")
        kind = m.get("kind")
        if kind in ("llm-judge", "human-judge") and ev != "blind_judge":
            errors.append(f"metric {m.get('name')}: judged metrics must use the blind_judge evaluator")
        if ev == "blind_judge" and kind not in ("llm-judge", "human-judge"):
            errors.append(f"metric {m.get('name')}: blind_judge metrics must have kind llm-judge or human-judge")
        if ev == "metric_from_file" and not (m["evaluator"].get("params") or {}).get("command") \
                and kind != "self-reported":
            errors.append(f"metric {m.get('name')}: a number read from an agent-written file is kind 'self-reported' "
                          "unless a pre-registered command computes it")
        if task_dir is not None and not (spec.get("setup") or {}).get("script"):
            for ref in _private_refs(m.get("evaluator", {}).get("params", {})):
                if not (task_dir / "private" / ref).exists():
                    errors.append(f"metric {m.get('name')}: private:{ref} does not exist in {task_dir / 'private'}")
    trials = spec.get("trials", 0)
    if trials < rules["min_trials_per_arm"]:
        errors.append(f"trials {trials} < {rules['min_trials_per_arm']}")
    elif trials < rules["preferred_trials_per_arm"]:
        warnings.append(f"{trials} trials per arm: an exact two-sided test cannot reach p < 0.05 below 4 per arm; "
                        f"{rules['preferred_trials_per_arm']} are preferred")
    if spec.get("negative_control") and not spec.get("negative_control_rationale"):
        errors.append("negative_control tasks need negative_control_rationale")
    if spec.get("purpose") == "study":
        if base.get("isolation", "none") == "none":
            warnings.append("isolation 'none': user-level skills, agents and MCP servers are visible to both arms; "
                            "use isolation 'home' or a clean container for a study")
        if base.get("harness") == "manual":
            warnings.append("manual harness: usage and timing will be self-reported")
    for inp in spec.get("inputs", []):
        if inp.get("source") in ("url", "kaggle") and "licence" in inp and inp["licence"].lower() in ("unknown", "?"):
            errors.append(f"input {inp.get('name')}: licence must be known before registration")
    if task_dir is not None:
        for d in ("workspace",):
            for p in walk_files(task_dir / d):
                if p.stat().st_size > 50 * 1024 * 1024:
                    errors.append(f"{p}: inputs over 50 MB belong in a setup script that downloads them, not the repo")
    return errors, warnings


def _private_refs(params) -> list[str]:
    out = []
    if isinstance(params, dict):
        for v in params.values():
            out += _private_refs(v)
    elif isinstance(params, list):
        for v in params:
            out += _private_refs(v)
    elif isinstance(params, str) and params.startswith("private:"):
        out.append(params[len("private:"):])
    return out


# --------------------------------------------------------------------------- registration

def task_dir(root: Path, task_id: str) -> Path:
    return Path(root) / "tasks" / task_id


def runs_dir(root: Path, task_id: str) -> Path:
    return Path(root) / "runs" / task_id


def register(spec_path: Path, root: Path, today: str | None = None, registered_by: str | None = None,
             now: str | None = None) -> dict:
    spec_path = Path(spec_path)
    src = read_json(spec_path)
    src_dir = spec_path.parent
    spec = {k: v for k, v in src.items() if k not in ("spec_sha256", "files_sha256")}
    reg_date = today or dt.date.today().isoformat()
    notes = []
    if src.get("preregistered_on") and src["preregistered_on"] != reg_date:
        notes.append(f"preregistered_on {src['preregistered_on']} replaced by the registration date {reg_date}")
    spec["preregistered_on"] = reg_date
    if registered_by:
        spec["registered_by"] = registered_by
    files = {}
    for sub in TASK_SUBDIRS:
        for p in walk_files(src_dir / sub):
            files[p.relative_to(src_dir).as_posix()] = sha256_file(p)
    spec["files_sha256"] = dict(sorted(files.items()))
    spec["spec_sha256"] = spec_hash(spec)
    errors, warnings = lint_spec(spec, src_dir)
    errors += [f"schema: {e}" for e in validate_schema("showcase_task_spec", spec)]
    if errors:
        raise ShowcaseError("cannot register:\n  " + "\n  ".join(errors))
    dest = task_dir(root, spec["id"])
    if (dest / "spec.json").exists():
        existing = read_json(dest / "spec.json")
        if existing.get("spec_sha256") == spec["spec_sha256"]:
            return existing
        raise ShowcaseError(f"{spec['id']} is already registered with different content (sha {existing.get('spec_sha256', '')[:12]}). "
                            "Registered specs are immutable: give the changed task a new id, e.g. "
                            f"{spec['id']}_v{spec.get('version', 1) + 1}.")
    dest.mkdir(parents=True, exist_ok=True)
    for sub in TASK_SUBDIRS:
        if (src_dir / sub).is_dir():
            copy_tree(src_dir / sub, dest / sub, ignore_dirs={"__pycache__", ".pytest_cache"})
    write_json(dest / "spec.json", spec)
    write_json(dest / "registration.json", {
        "task_id": spec["id"], "spec_sha256": spec["spec_sha256"], "registered_at": now or utcnow(),
        "preregistered_on": reg_date, "registered_by": registered_by, "runner_version": VERSION,
        "source": str(spec_path), "warnings": warnings, "notes": notes,
        "evidence": "Commit tasks/<id>/ and publish spec_sha256 before the first run; the commit time is the "
                    "public proof of pre-registration.",
    })
    return spec


def verify_task(root: Path, task_id: str) -> dict:
    d = task_dir(root, task_id)
    if not (d / "spec.json").exists():
        raise ShowcaseError(f"{task_id} is not registered under {root}/tasks")
    spec = read_json(d / "spec.json")
    if spec_hash(spec) != spec.get("spec_sha256"):
        raise ShowcaseError(f"{d / 'spec.json'} was edited after registration (hash mismatch)")
    on_disk = {}
    for sub in TASK_SUBDIRS:
        for p in walk_files(d / sub, ignore_dirs={"__pycache__", ".pytest_cache"}):
            on_disk[p.relative_to(d).as_posix()] = sha256_file(p)
    want = spec.get("files_sha256", {})
    problems = [f"changed: {k}" for k in want if k in on_disk and on_disk[k] != want[k]]
    problems += [f"missing: {k}" for k in want if k not in on_disk]
    problems += [f"added: {k}" for k in on_disk if k not in want]
    if problems:
        raise ShowcaseError(f"{task_id}: task files differ from registration: {problems[:10]}")
    return spec


# --------------------------------------------------------------------------- schedule

def make_schedule(spec: dict) -> list[dict]:
    seed = int(spec["spec_sha256"][:8], 16) ^ int(spec["analysis"]["seed"])
    rng = random.Random(seed)
    first = rng.choice(ARMS)
    second = ARMS[1] if first == ARMS[0] else ARMS[0]
    order = []
    for i in range(1, spec["trials"] + 1):
        if spec["order"] == "alternate":  # ABBA blocks cancel linear drift
            pair = (first, second) if i % 2 == 1 else (second, first)
        else:
            pair = list(ARMS)
            rng.shuffle(pair)
        order += [(pair[0], i), (pair[1], i)]
    return [{"index": k, "arm": arm, "trial": t} for k, (arm, t) in enumerate(order)]


def plan(root: Path, task_id: str) -> list[dict]:
    spec = verify_task(root, task_id)
    path = runs_dir(root, task_id) / "schedule.json"
    if path.exists():
        data = read_json(path)
        if data["spec_sha256"] != spec["spec_sha256"]:
            raise ShowcaseError(f"{path} belongs to a different spec hash")
        return data["items"]
    items = make_schedule(spec)
    write_json(path, {"task_id": task_id, "spec_sha256": spec["spec_sha256"], "order": spec["order"],
                      "items": items})
    return items


# --------------------------------------------------------------------------- staging

def staging_dir(root: Path, spec: dict) -> Path:
    return Path(root) / ".cache" / spec["id"] / spec["spec_sha256"][:12]


def stage(root: Path, spec: dict, allow_network: bool = False) -> Path:
    """Build the starting workspace and private evaluation assets once per registered spec."""
    sdir = staging_dir(root, spec)
    record = runs_dir(root, spec["id"]) / "staging.json"
    if (sdir / "manifest.json").exists():
        m = read_json(sdir / "manifest.json")
        if manifest(sdir / "workspace") != m["workspace"]:
            raise ShowcaseError(f"{sdir}/workspace changed after staging; delete {sdir} to rebuild")
        return sdir
    tdir = task_dir(root, spec["id"])
    tmp = sdir.with_name(sdir.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "workspace").mkdir(parents=True)
    (tmp / "private").mkdir(parents=True)
    copy_tree(tdir / "workspace", tmp / "workspace")
    setup = spec.get("setup")
    if setup:
        if setup.get("network") and not allow_network:
            raise ShowcaseError(f"setup needs network access to {setup.get('hosts')}; rerun with --allow-setup-network "
                                "(Kaggle data also needs your own account and accepted competition rules)")
        missing = [s for s in setup.get("secrets", []) if not os.environ.get(s)]
        if missing:
            raise ShowcaseError(f"setup needs environment variables {missing}")
        proc = subprocess.run([sys.executable, str(tdir / setup["script"]), "--workspace", str(tmp / "workspace"),
                               "--private", str(tmp / "private"), "--seed", str(spec["analysis"]["seed"])],
                              cwd=tdir, capture_output=True, text=True, timeout=setup.get("timeout_s", 3600))
        (tmp / "setup.log").write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
        if proc.returncode:
            raise ShowcaseError(f"setup failed ({proc.returncode}): {proc.stderr.strip()[-500:]}")
    problems = []
    for inp in spec.get("inputs", []):
        matches = list((tmp / "workspace").glob(inp["path_in_workspace"]))
        if not matches:
            problems.append(f"input {inp['name']}: {inp['path_in_workspace']} not in the starting workspace")
        elif inp.get("sha256") and len(matches) == 1 and sha256_file(matches[0]) != inp["sha256"]:
            problems.append(f"input {inp['name']}: sha256 differs from the registered value")
    if problems:
        raise ShowcaseError("; ".join(problems))
    m = {"workspace": manifest(tmp / "workspace"), "private": manifest(tmp / "private")}
    write_json(tmp / "manifest.json", m)
    if record.exists():
        prev = read_json(record)
        if prev["workspace_manifest_sha256"] != manifest_hash(m["workspace"]) or \
                prev["private_manifest_sha256"] != manifest_hash(m["private"]):
            shutil.rmtree(tmp, ignore_errors=True)
            raise ShowcaseError("setup produced different files than the first staging: setup is not deterministic "
                                "or upstream data changed; runs cannot be compared")
    shutil.rmtree(sdir, ignore_errors=True)
    tmp.rename(sdir)
    if not record.exists():
        write_json(record, {"staging_dir": os.path.relpath(sdir, root),
                            "workspace_manifest_sha256": manifest_hash(m["workspace"]),
                            "private_manifest_sha256": manifest_hash(m["private"]), "created_at": utcnow()})
    return sdir


def private_dirs(root: Path, spec: dict) -> list[Path]:
    return [task_dir(root, spec["id"]) / "private", staging_dir(root, spec) / "private"]


def compose_prompt(spec: dict, arm: str) -> str:
    add = (spec["arms"][arm].get("prompt_addendum") or "").strip()
    return spec["prompt"].rstrip() + ("\n\n" + add if add else "") + "\n"


# --------------------------------------------------------------------------- transcript parsing

@dataclass
class Usage:
    fmt: str
    tool_ids: set = field(default_factory=set)
    tool_names: Counter = field(default_factory=Counter)
    msg_usage: dict = field(default_factory=dict)
    final: dict | None = None
    cost: float | None = None
    model: str | None = None
    turns: int | None = None
    mcp_servers: list = field(default_factory=list)
    catalogue_calls: list = field(default_factory=list)
    texts: list = field(default_factory=list)
    _anon: int = 0

    @property
    def tool_calls(self) -> int:
        return len(self.tool_ids)

    def tokens(self) -> dict:
        src = [self.final] if self.final else list(self.msg_usage.values())
        tin = sum(int(u.get("in", 0)) for u in src)
        tout = sum(int(u.get("out", 0)) for u in src)
        cread = sum(int(u.get("cache_read", 0)) for u in src)
        cwrite = sum(int(u.get("cache_write", 0)) for u in src)
        return {"tokens_in": tin, "tokens_out": tout, "tokens_cache_read": cread, "tokens_cache_write": cwrite,
                "tokens_total": tin + tout}

    def has_usage(self) -> bool:
        return bool(self.final or self.msg_usage)

    def _tool(self, tid, name: str, inp) -> None:
        if tid is None:
            self._anon += 1
            tid = f"anon-{self._anon}"
        if tid in self.tool_ids:
            return
        self.tool_ids.add(tid)
        self.tool_names[name or "?"] += 1
        call = catalogue_call_from_tool(name or "", inp)
        if call:
            self.catalogue_calls.append(call)

    def feed(self, line: str) -> None:
        line = line.strip()
        if not line.startswith("{"):
            if line:
                self.texts.append(line[:2000])
            return
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            return
        if not isinstance(ev, dict):
            return
        if self.fmt == "codex-json":
            self._codex(ev)
        elif self.fmt == "opencode-json":
            self._opencode(ev)
        else:
            self._claude(ev)

    def _claude(self, ev: dict) -> None:
        t = ev.get("type")
        if t == "system" and ev.get("subtype") == "init":
            self.model = ev.get("model") or self.model
            self.mcp_servers = [s.get("name") if isinstance(s, dict) else str(s) for s in ev.get("mcp_servers", [])]
        elif t == "assistant":
            msg = ev.get("message") or {}
            self.model = msg.get("model") or self.model
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") in ("tool_use", "server_tool_use"):
                    self._tool(block.get("id"), block.get("name"), block.get("input"))
                elif isinstance(block, dict) and block.get("type") == "text":
                    self.texts.append(str(block.get("text", ""))[:2000])
            u = msg.get("usage")
            if isinstance(u, dict):
                self.msg_usage[msg.get("id") or f"m{len(self.msg_usage)}"] = _claude_usage(u)
        elif t == "result":
            if isinstance(ev.get("usage"), dict):
                self.final = _claude_usage(ev["usage"])
            if ev.get("total_cost_usd") is not None:
                self.cost = float(ev["total_cost_usd"])
            if ev.get("num_turns") is not None:
                self.turns = int(ev["num_turns"])

    def _codex(self, ev: dict) -> None:
        t = ev.get("type", "")
        item = ev.get("item") or {}
        if t in ("item.started", "item.completed") and item.get("type") in (
                "command_execution", "file_change", "mcp_tool_call", "web_search"):
            name = item["type"]
            inp = item
            if item["type"] == "mcp_tool_call":
                name = f"mcp__{item.get('server', '?')}__{item.get('tool', '?')}"
                inp = item.get("arguments") or {}
            elif item["type"] == "command_execution":
                name, inp = "Bash", {"command": item.get("command", "")}
            self._tool(item.get("id"), name, inp)
        elif t == "item.completed" and item.get("type") == "agent_message":
            self.texts.append(str(item.get("text", ""))[:2000])
        elif t == "turn.completed" and isinstance(ev.get("usage"), dict):
            u = ev["usage"]
            cached = int(u.get("cached_input_tokens", 0))
            self.msg_usage[f"turn{len(self.msg_usage)}"] = {
                "in": int(u.get("input_tokens", 0)), "out": int(u.get("output_tokens", 0)),
                "cache_read": cached, "cache_write": 0}
        elif t == "thread.started" and ev.get("model"):
            self.model = ev["model"]

    def _opencode(self, ev: dict) -> None:
        part = ev.get("part") or {}
        t = ev.get("type", "")
        if t == "tool_use" or part.get("type") == "tool":
            state = part.get("state") or {}
            self._tool(part.get("callID") or part.get("id"), part.get("tool", "?"), state.get("input"))
        if t == "step_finish" or part.get("type") == "step-finish":
            tok = part.get("tokens") or {}
            cache = tok.get("cache") or {}
            self.msg_usage[part.get("id") or f"s{len(self.msg_usage)}"] = {
                "in": int(tok.get("input", 0)) + int(cache.get("read", 0)) + int(cache.get("write", 0)),
                "out": int(tok.get("output", 0)) + int(tok.get("reasoning", 0)),
                "cache_read": int(cache.get("read", 0)), "cache_write": int(cache.get("write", 0))}
            if part.get("cost") is not None:
                self.cost = (self.cost or 0.0) + float(part["cost"])
        if t == "text" and part.get("text"):
            self.texts.append(str(part["text"])[:2000])


def _claude_usage(u: dict) -> dict:
    cread = int(u.get("cache_read_input_tokens", 0) or 0)
    cwrite = int(u.get("cache_creation_input_tokens", 0) or 0)
    return {"in": int(u.get("input_tokens", 0) or 0) + cread + cwrite, "out": int(u.get("output_tokens", 0) or 0),
            "cache_read": cread, "cache_write": cwrite}


_BALTOR_CMD = re.compile(r"(?:^|[\s;&|(])baltor\s+(search|read|place)\s+(\"[^\"]*\"|'[^']*'|\S+)")


def catalogue_call_from_tool(name: str, inp) -> dict | None:
    inp = inp if isinstance(inp, dict) else {}
    low = name.lower()
    if low.endswith("intelligence_search"):
        return {"op": "search", "query": str(inp.get("query", "")), "ok": True, "source": "transcript"}
    if low.endswith("provisioning_read"):
        return {"op": "read", "identity": str(inp.get("identity", "")), "ok": True, "source": "transcript"}
    cmd = inp.get("command") if isinstance(inp.get("command"), str) else None
    if cmd:
        m = _BALTOR_CMD.search(cmd)
        if m:
            arg = m.group(2).strip("\"'")
            call = {"op": m.group(1), "ok": True, "source": "transcript"}
            call["query" if m.group(1) == "search" else "identity"] = arg
            return call
    return None


# --------------------------------------------------------------------------- catalogue helpers

def catalogue_file_index(index_path: Path | None, min_bytes: int = 200) -> dict[str, str]:
    """sha256 -> 'identity/path' for every catalogue payload file big enough to be distinctive."""
    if not index_path or not Path(index_path).exists():
        return {}
    out = {}
    for e in read_json(index_path).get("packages", []):
        for f in e.get("files", []):
            if f["path"] != "baltor.json" and f.get("size", 0) >= min_bytes:
                out.setdefault(f["sha256"], f"{e['identity']}/{f['path']}")
    return out


def catalogue_digests(index_path: Path | None) -> dict[str, tuple[str, str]]:
    if not index_path or not Path(index_path).exists():
        return {}
    return {e["identity"]: (e["version"], e["digest"]) for e in read_json(index_path).get("packages", [])}


def verify_items(items: list[dict], index_path: Path | None) -> list[dict]:
    known = catalogue_digests(index_path)
    out = []
    for it in items:
        it = dict(it)
        if not known:
            it["verified"] = None
        else:
            v = known.get(it["identity"])
            it["verified"] = bool(v and (it.get("digest") in ("?", None) or v[1].startswith(it["digest"])))
        out.append(it)
    return out


def scan_contamination(arm: str, workspace: Path, transcript: str, usage: Usage | None,
                       file_index: dict[str, str], rules: dict, catalogue_calls: list[dict]) -> tuple[list[str], list[str]]:
    """Returns (findings, catalogue_files_in_outputs). Findings only matter for the baseline arm."""
    findings: list[str] = []
    matched: list[str] = []
    min_bytes = rules.get("min_matching_file_bytes", 200)
    for p in walk_files(workspace):
        rel = p.relative_to(workspace).as_posix()
        if p.stat().st_size >= min_bytes and file_index:
            hit = file_index.get(sha256_file(p))
            if hit:
                matched.append(f"{rel} == {hit}")
    if arm != "baseline":
        return findings, matched
    findings += [f"output {m} is byte-identical to a catalogue file" for m in matched]
    if (workspace / ".baltor").exists():
        findings.append("workspace contains .baltor/")
    low = transcript.lower()
    for marker in rules["catalogue_markers"]:
        if marker.lower() in low:
            findings.append(f"transcript mentions '{marker}'")
    if usage is not None:
        servers = [s for s in usage.mcp_servers if "baltor" in str(s).lower()]
        if servers:
            findings.append(f"harness reported Baltor MCP servers {servers}")
    if catalogue_calls:
        findings.append(f"{len(catalogue_calls)} catalogue call(s) recorded in the baseline arm")
    return findings, matched


# --------------------------------------------------------------------------- launching

@dataclass
class Launch:
    argv: list[str]
    env: dict
    cwd: Path
    stdin: str | None
    fmt: str
    mcp_config: dict | None = None
    log_path: Path | None = None
    redacted: list[str] = field(default_factory=list)


def _strip_baltor_env(env: dict) -> dict:
    env = {k: v for k, v in env.items() if not k.startswith(("BALTOR_", "SHOWCASE_CATALOGUE"))}
    parts = [p for p in env.get("PATH", "").split(os.pathsep)
             if p and not (Path(p) / "baltor").exists()]
    env["PATH"] = os.pathsep.join(parts)
    return env


def build_launch(spec: dict, arm: str, workspace: Path, trial_dir: Path, *, catalog_tool: Path | None = None,
                 gateway: Path | None = None, guard_hook: Path | None = None, home_dir: Path | None = None,
                 base_env: dict | None = None) -> Launch:
    a = spec["arms"][arm]
    harness = a["harness"]
    mode = a["catalogue_access"]["mode"]
    endpoint = a["catalogue_access"].get("endpoint", "local")
    prompt = compose_prompt(spec, arm)
    (trial_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    env = _strip_baltor_env(dict(base_env if base_env is not None else os.environ))
    if a.get("isolation") == "home" and home_dir is not None:
        home_dir.mkdir(parents=True, exist_ok=True)
        env.update({"HOME": str(home_dir), "XDG_CONFIG_HOME": str(home_dir / ".config"),
                    "XDG_DATA_HOME": str(home_dir / ".local" / "share")})
    tools_dir = trial_dir / "tools"
    log_path = trial_dir / "catalogue_calls.jsonl"
    mcp_servers = dict(spec.get("shared_mcp_servers") or {})
    extra_tools: list[str] = []
    if arm == "baltor" and mode in ("search-read", "mcp") and endpoint == "local":
        if not (catalog_tool and gateway):
            raise ShowcaseError("the baltor arm needs --catalog-tool and the showcase_catalogue_gateway module")
        if mode == "search-read":
            sys.path.insert(0, str(gateway.parent))
            import showcase_catalogue_gateway as gw  # noqa: E402
            gw.write_shim(tools_dir / "bin", log=str(log_path), catalog_tool=str(catalog_tool),
                          workspace=str(workspace), harness=harness if harness in HARNESS_BIN else "claude-code")
            env["PATH"] = str(tools_dir / "bin") + os.pathsep + env.get("PATH", "")
        else:
            mcp_servers["baltor"] = {"command": sys.executable,
                                     "args": [str(gateway), "mcp", "--log", str(log_path), "--catalog-tool",
                                              str(catalog_tool), "--workspace", str(workspace)]}
        extra_tools = CATALOGUE_TOOLS_CLAUDE[mode]
    elif arm == "baltor" and mode == "mcp":
        mcp_servers["baltor"] = {"type": "http", "url": endpoint,
                                 "headers": {"Authorization": "Bearer ${BALTOR_SERVICE_TOKEN}"}}
        if os.environ.get("BALTOR_SERVICE_TOKEN"):
            env["BALTOR_SERVICE_TOKEN"] = os.environ["BALTOR_SERVICE_TOKEN"]
        extra_tools = CATALOGUE_TOOLS_CLAUDE["mcp"]
    mcp_config = {"mcpServers": mcp_servers}
    tools_dir.mkdir(parents=True, exist_ok=True)
    fmt = a.get("transcript_format") or TRANSCRIPT_FORMAT.get(harness, "text")

    if harness == "claude-code":
        mcp_file = tools_dir / "mcp.json"
        write_json(mcp_file, mcp_config)
        argv = ["claude", "-p", "--output-format", "stream-json", "--verbose", "--model", a["model"],
                "--strict-mcp-config", "--mcp-config", str(mcp_file), "--no-session-persistence"]
        if guard_hook:
            settings = {"hooks": {"PreToolUse": [{"matcher": "*", "hooks": [
                {"type": "command", "command": f"{sys.executable} {guard_hook} --arm {arm}", "timeout": 10}]}]}}
            write_json(tools_dir / "settings.json", settings)
            argv += ["--settings", str(tools_dir / "settings.json")]
        if spec["budget"].get("usd"):
            argv += ["--max-budget-usd", str(spec["budget"]["usd"])]
        argv += list(a.get("extra_args", []))
        tools = list(a.get("allowed_tools", [])) + [t for t in extra_tools if t not in a.get("allowed_tools", [])]
        if tools:
            argv += ["--allowedTools", *tools]
        launch = Launch(argv, env, workspace, prompt, fmt, mcp_config, log_path)
    elif harness == "codex":
        argv = ["codex", "exec", "--json", "--model", a["model"], "--skip-git-repo-check", "--cd", str(workspace)]
        for name, srv in mcp_servers.items():
            if "command" in srv:
                argv += ["-c", f"mcp_servers.{name}.command={json.dumps(srv['command'])}",
                         "-c", f"mcp_servers.{name}.args={json.dumps(srv.get('args', []))}"]
            elif "url" in srv:
                argv += ["-c", f"mcp_servers.{name}.url={json.dumps(srv['url'])}"]
        argv += list(a.get("extra_args", [])) + ["-"]
        launch = Launch(argv, env, workspace, prompt, fmt, mcp_config, log_path)
    elif harness == "opencode":
        cfg = {"$schema": "https://opencode.ai/config.json", "mcp": {}}
        for name, srv in mcp_servers.items():
            if "command" in srv:
                cfg["mcp"][name] = {"type": "local", "command": [srv["command"], *srv.get("args", [])], "enabled": True}
            else:
                cfg["mcp"][name] = {"type": "remote", "url": srv["url"], "enabled": True}
        write_json(tools_dir / "opencode.json", cfg)
        env["OPENCODE_CONFIG"] = str(tools_dir / "opencode.json")
        argv = ["opencode", "run", "--format", "json", "--model", a["model"], *a.get("extra_args", []), prompt]
        launch = Launch(argv, env, workspace, None, fmt, mcp_config, log_path)
    elif harness == "command":
        write_json(tools_dir / "mcp.json", mcp_config)
        subs = {"{prompt_file}": str(trial_dir / "prompt.txt"), "{workspace}": str(workspace), "{model}": a["model"],
                "{mcp_config}": str(tools_dir / "mcp.json")}
        argv = []
        for part in a["command"]:
            for k, v in subs.items():
                part = part.replace(k, v)
            argv.append(part)
        launch = Launch(argv, env, workspace, prompt, fmt, mcp_config, log_path)
    else:
        raise ShowcaseError(f"harness '{harness}' is not launched by the runner; use `import` for manual runs")
    launch.redacted = [("<prompt>" if x == prompt else x) for x in launch.argv]
    return launch


def assert_baseline_clean(launch: Launch, workspace: Path, file_index: dict[str, str]) -> None:
    """Refuse to start a baseline trial that could reach the catalogue."""
    problems = []
    for k in launch.env:
        if k.startswith(("BALTOR_", "SHOWCASE_CATALOGUE")):
            problems.append(f"environment variable {k}")
    if shutil.which("baltor", path=launch.env.get("PATH", "")):
        problems.append("a `baltor` executable is on PATH")
    if launch.mcp_config and "baltor" in json.dumps(launch.mcp_config).lower():
        problems.append("MCP config contains a Baltor server")
    if any("mcp_servers.baltor" in x for x in launch.argv):
        problems.append("argv configures a Baltor MCP server")
    if (workspace / ".baltor").exists():
        problems.append("workspace contains .baltor/")
    for p in walk_files(workspace):
        if file_index and p.stat().st_size >= 200 and sha256_file(p) in file_index:
            problems.append(f"starting file {p.relative_to(workspace)} is a catalogue file")
    if problems:
        raise BaselineContamination("baseline arm would see Baltor items: " + "; ".join(problems))


def _kill(proc: subprocess.Popen) -> None:
    try:
        if hasattr(os, "killpg"):
            os.killpg(proc.pid, signal.SIGTERM)
        else:  # pragma: no cover
            proc.terminate()
        proc.wait(timeout=5)
    except Exception:  # noqa: BLE001
        try:
            if hasattr(os, "killpg"):
                os.killpg(proc.pid, signal.SIGKILL)
            else:  # pragma: no cover
                proc.kill()
        except Exception:  # noqa: BLE001
            pass


def execute(launch: Launch, budget: dict, transcript_path: Path, stderr_path: Path) -> dict:
    usage = Usage(launch.fmt)
    exceeded: list[str] = []
    status = None
    message = ""
    start_wall = time.monotonic()
    started = utcnow()
    try:
        stderr_fh = stderr_path.open("w", encoding="utf-8")
        proc = subprocess.Popen(launch.argv, cwd=launch.cwd, env=launch.env, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=stderr_fh, text=True, bufsize=1,
                                start_new_session=True)
    except FileNotFoundError as exc:
        stderr_path.write_text(str(exc), encoding="utf-8")
        transcript_path.write_text("", encoding="utf-8")
        return {"status": "harness-error", "code": None, "message": f"cannot start harness: {exc}", "usage": usage,
                "exceeded": [], "started_at": started, "ended_at": utcnow(), "wall_s": 0.0}
    q: queue.Queue = queue.Queue()

    def reader():
        for line in proc.stdout:  # type: ignore[union-attr]
            q.put(line)
        q.put(None)

    th = threading.Thread(target=reader, daemon=True)
    th.start()
    try:
        if launch.stdin is not None:
            proc.stdin.write(launch.stdin)  # type: ignore[union-attr]
        proc.stdin.close()  # type: ignore[union-attr]
    except BrokenPipeError:
        pass
    with transcript_path.open("w", encoding="utf-8") as tf:
        while True:
            remaining = budget["wall_s"] - (time.monotonic() - start_wall)
            if remaining <= 0:
                status, message = "timeout", f"wall-time budget {budget['wall_s']} s reached"
                exceeded.append("wall_s")
                _kill(proc)
                break
            try:
                line = q.get(timeout=min(remaining, 0.25))
            except queue.Empty:
                continue
            if line is None:
                break
            tf.write(line)
            usage.feed(line)
            if usage.tool_calls > budget["tool_calls"]:
                exceeded.append("tool_calls")
            if usage.has_usage() and usage.tokens()["tokens_total"] > budget["tokens"]:
                exceeded.append("tokens")
            if budget.get("usd") and usage.cost is not None and usage.cost > budget["usd"]:
                exceeded.append("usd")
            if exceeded:
                status, message = "budget-exceeded", f"budget exceeded: {', '.join(exceeded)}"
                _kill(proc)
                break
        th.join(timeout=5)
        while True:
            try:
                line = q.get_nowait()
            except queue.Empty:
                break
            if line:
                tf.write(line)
                usage.feed(line)
    try:
        code = proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        _kill(proc)
        code = proc.returncode
    stderr_fh.close()
    if status is None:
        status = "completed" if code == 0 else "harness-error"
        message = "exited 0" if code == 0 else f"exited {code}"
    return {"status": status, "code": code, "message": message, "usage": usage, "exceeded": sorted(set(exceeded)),
            "started_at": started, "ended_at": utcnow(), "wall_s": round(time.monotonic() - start_wall, 3)}


def harness_version(harness: str, env: dict | None = None) -> str | None:
    binary = HARNESS_BIN.get(harness)
    if not binary or not shutil.which(binary, path=(env or os.environ).get("PATH")):
        return None
    try:
        out = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=30, env=env)
        return (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr).strip() else None
    except Exception:  # noqa: BLE001
        return None


# --------------------------------------------------------------------------- outputs and records

def collect_outputs(workspace: Path, start: dict[str, str]) -> list[dict]:
    out = []
    for p in walk_files(workspace):
        rel = p.relative_to(workspace).as_posix()
        h = sha256_file(p)
        change = "new" if rel not in start else ("unchanged" if start[rel] == h else "modified")
        out.append({"path": rel, "size": p.stat().st_size, "sha256": h, "change": change})
    return out


def missing_outputs(spec: dict, workspace: Path) -> list[str]:
    missing = []
    for o in spec.get("outputs", []):
        if o.get("required") and not any(fnmatch.fnmatch(p.relative_to(workspace).as_posix(), o["path"])
                                         for p in walk_files(workspace)):
            missing.append(o["path"])
    return missing


def cost_estimate(spec: dict, usage: dict) -> tuple[float | None, str]:
    pr = spec.get("pricing")
    if not pr or usage.get("tokens_in") is None:
        return None, "unknown"
    cread = usage.get("tokens_cache_read") or 0
    fresh_in = max(0, (usage.get("tokens_in") or 0) - cread)
    cost = (fresh_in * pr["input_per_mtok"] + (usage.get("tokens_out") or 0) * pr["output_per_mtok"]
            + cread * pr.get("cache_read_per_mtok", pr["input_per_mtok"])) / 1e6
    return round(cost, 6), "price-table"


def new_record(spec: dict, arm: str, trial: int, schedule_index: int, adapter: str) -> dict:
    a = spec["arms"][arm]
    return {
        "spec": "baltor.showcase-run/v1",
        "run_id": f"{spec['id']}/{arm}/{trial}",
        "task_id": spec["id"],
        "spec_sha256": spec["spec_sha256"],
        "purpose": spec["purpose"],
        "arm": arm,
        "trial": trial,
        "schedule_index": schedule_index,
        "adapter": adapter,
        "harness": {"name": a["harness"], "version": None, "version_matches_spec": None, "argv": [],
                    "isolation": a.get("isolation", "none")},
        "model": {"requested": a["model"], "reported": None},
        "started_at": utcnow(), "ended_at": utcnow(), "wall_s": None,
        "usage": {"tool_calls": None, "tokens_in": None, "tokens_out": None, "tokens_total": None, "cost_usd": None,
                  "cost_source": "unknown", "source": "none"},
        "budget": {**{k: spec["budget"][k] for k in ("wall_s", "tool_calls", "tokens")},
                   **({"usd": spec["budget"]["usd"]} if spec["budget"].get("usd") else {}),
                   "exceeded": [], "enforced": []},
        "catalogue": {"mode": a["catalogue_access"]["mode"], "release": None, "calls": [], "downloaded": [],
                      "preplaced": []},
        "contamination": {"checked": False, "clean": True, "findings": []},
        "exit": {"status": "not-run", "code": None, "message": ""},
        "start_manifest_sha256": "0" * 64,
        "start_verified": "unknown",
        "workspace": "workspace",
        "outputs": [],
        "missing_required_outputs": [],
        "transcript": {"path": None, "sha256": None, "format": "none"},
        "logs": {"stderr": None},
        "evaluation": {"status": "pending", "results": [], "success": None},
        "included": True,
        "exclusion_reason": None,
        "environment": {"platform": platform.platform(), "python": platform.python_version(),
                        "runner_version": VERSION},
    }


def finish_record(rec: dict, trial_dir: Path) -> dict:
    errs = validate_schema("showcase_run_record", rec)
    if errs:
        raise ShowcaseError(f"{rec['run_id']}: run record does not match its schema: {errs[:3]}")
    write_json(trial_dir / "run.json", rec)
    return rec


# --------------------------------------------------------------------------- run (live adapters)

@dataclass
class RunOptions:
    catalog_tool: Path | None = None
    catalog_index: Path | None = None
    gateway: Path | None = None
    guard_hook: Path | None = None
    workspace_root: Path | None = None
    allow_version_drift: bool = False
    allow_setup_network: bool = False
    keep_workspaces: bool = False
    dry_run: bool = False
    only: list[str] = field(default_factory=list)
    max_runs: int | None = None


def _index_path(opts: RunOptions) -> Path | None:
    if opts.catalog_index:
        return opts.catalog_index
    if opts.catalog_tool:
        p = Path(opts.catalog_tool).resolve().parents[1] / "catalog" / "index.json"
        return p if p.exists() else None
    return None


def run_trial(root: Path, spec: dict, item: dict, opts: RunOptions) -> dict:
    arm, trial = item["arm"], item["trial"]
    rules = load_rules()
    tdir = runs_dir(root, spec["id"]) / arm / str(trial)
    if (tdir / "run.json").exists():
        raise ShowcaseError(f"{tdir}/run.json exists; runs are never overwritten (use `replace`)")
    sdir = stage(root, spec, opts.allow_setup_network)
    start = read_json(sdir / "manifest.json")["workspace"]
    index_path = _index_path(opts)
    file_index = catalogue_file_index(index_path, rules["min_matching_file_bytes"])
    ws_root = Path(opts.workspace_root or Path(tempfile.gettempdir()) / "baltor-showcase-ws")
    ws_root.mkdir(parents=True, exist_ok=True)
    ext = Path(tempfile.mkdtemp(prefix=f"{spec['id']}-{arm}-{trial}-", dir=ws_root))
    workspace = ext / "workspace"
    workspace.mkdir()
    copy_tree(sdir / "workspace", workspace)
    tdir.mkdir(parents=True, exist_ok=True)
    rec = new_record(spec, arm, trial, item["index"], spec["arms"][arm]["harness"])
    rec["start_manifest_sha256"] = manifest_hash(start)
    rec["start_verified"] = "exact"
    rec["harness"]["workspace_location"] = "outside-repository" if not _inside_repo(workspace) else "inside-repository"
    a = spec["arms"][arm]
    try:
        if arm == "baltor" and a["catalogue_access"]["mode"] == "preplaced":
            if not opts.catalog_tool or not opts.gateway:
                raise ShowcaseError("preplaced mode needs --catalog-tool and the gateway module")
            sys.path.insert(0, str(opts.gateway.parent))
            import showcase_catalogue_gateway as gw  # noqa: E402
            g = gw.Gateway(gw.load_catalog_tool(opts.catalog_tool), tdir / "preplaced.jsonl", workspace,
                           a["harness"] if a["harness"] in HARNESS_BIN else "claude-code")
            for ident in a["catalogue_access"]["identities"]:
                g.place(ident)
            rec["catalogue"]["preplaced"] = verify_items(
                [{k: c[k] for k in ("identity", "version", "digest")} for c in gw.read_log(tdir / "preplaced.jsonl")
                 if c.get("ok")], index_path)
        launch = build_launch(spec, arm, workspace, tdir, catalog_tool=opts.catalog_tool, gateway=opts.gateway,
                              guard_hook=opts.guard_hook, home_dir=ext / "home")
        if arm == "baseline":
            assert_baseline_clean(launch, workspace, file_index)
        version = harness_version(a["harness"], launch.env)
        rec["harness"]["version"] = version
        rec["harness"]["argv"] = launch.redacted
        if a["harness"] in HARNESS_BIN:
            matches = bool(version and a["harness_version"] in version)
            rec["harness"]["version_matches_spec"] = matches
            if not matches and not opts.allow_version_drift and not opts.dry_run:
                raise ShowcaseError(f"{a['harness']} version {version!r} does not match the registered "
                                    f"{a['harness_version']!r} (use --allow-version-drift to record and continue)")
        if opts.dry_run:
            print(f"[dry-run] {rec['run_id']}: cd {workspace} && {' '.join(launch.redacted)}")
            shutil.rmtree(tdir, ignore_errors=True)
            shutil.rmtree(ext, ignore_errors=True)
            return rec
        res = execute(launch, spec["budget"], tdir / "transcript.jsonl", tdir / "stderr.log")
    except BaseException:
        if not opts.keep_workspaces:
            shutil.rmtree(ext, ignore_errors=True)
        if not (tdir / "run.json").exists():
            shutil.rmtree(tdir, ignore_errors=True)
        raise
    usage: Usage = res["usage"]
    tok = usage.tokens() if usage.has_usage() else {}
    rec.update({"started_at": res["started_at"], "ended_at": res["ended_at"], "wall_s": res["wall_s"]})
    rec["exit"] = {"status": res["status"], "code": res["code"], "message": res["message"]}
    rec["model"]["reported"] = usage.model
    u = {"tool_calls": usage.tool_calls if launch.fmt != "text" else None,
         "tokens_in": tok.get("tokens_in"), "tokens_out": tok.get("tokens_out"),
         "tokens_cache_read": tok.get("tokens_cache_read"), "tokens_cache_write": tok.get("tokens_cache_write"),
         "tokens_total": tok.get("tokens_total"), "turns": usage.turns,
         "cost_usd": usage.cost, "cost_source": "harness-reported" if usage.cost is not None else "unknown",
         "source": launch.fmt if launch.fmt != "text" else "none", "tool_names": dict(usage.tool_names)}
    if u["cost_usd"] is None:
        u["cost_usd"], u["cost_source"] = cost_estimate(spec, u)
    rec["usage"] = u
    enforced = ["wall_s"] + (["tool_calls"] if launch.fmt != "text" else []) + (["tokens"] if usage.has_usage() else [])
    if spec["budget"].get("usd") and usage.cost is not None:
        enforced.append("usd")
    rec["budget"]["exceeded"] = res["exceeded"]
    rec["budget"]["enforced"] = enforced
    # catalogue calls: the gateway log is authoritative; the transcript is the fallback (hosted endpoint)
    calls = _read_jsonl(launch.log_path) if launch.log_path else []
    if not calls:
        calls = usage.catalogue_calls
    rec["catalogue"]["calls"] = [_clean_call(c) for c in calls]
    if arm == "baltor":
        rec["catalogue"]["downloaded"] = verify_items(_downloaded(calls), index_path)
        rec["catalogue"]["release"] = _release(index_path)
    transcript_text = (tdir / "transcript.jsonl").read_text(encoding="utf-8", errors="replace")
    findings, matched = scan_contamination(arm, workspace, transcript_text, usage, file_index, rules,
                                           rec["catalogue"]["calls"] if arm == "baseline" else [])
    rec["contamination"] = {"checked": True, "clean": not findings, "findings": findings}
    if matched and arm == "baltor":
        rec["catalogue"]["files_in_outputs"] = matched
    if findings:
        rec["included"], rec["exclusion_reason"] = False, "baseline contamination: " + "; ".join(findings[:3])
    # keep everything the agent produced next to the record
    copy_tree(workspace, tdir / "workspace")
    rec["outputs"] = collect_outputs(tdir / "workspace", start)
    rec["missing_required_outputs"] = missing_outputs(spec, tdir / "workspace")
    rec["transcript"] = {"path": "transcript.jsonl", "sha256": sha256_file(tdir / "transcript.jsonl"),
                         "format": launch.fmt if launch.fmt != "text" else "text"}
    rec["logs"] = {"stderr": "stderr.log"}
    if not opts.keep_workspaces:
        shutil.rmtree(ext, ignore_errors=True)
    return finish_record(rec, tdir)


def _inside_repo(p: Path) -> bool:
    for d in [p, *p.parents]:
        if (d / ".git").exists() and (d / "baltor" / "components").exists():
            return True
    return False


def _read_jsonl(p: Path | None) -> list[dict]:
    if not p or not Path(p).exists():
        return []
    out = []
    for line in Path(p).read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _clean_call(c: dict) -> dict:
    keep = {k: c[k] for k in ("at", "op", "query", "kind", "results", "identity", "version", "digest", "ok", "error",
                              "source") if k in c and c[k] is not None}
    keep.setdefault("ok", True)
    keep.setdefault("source", "self-reported")
    if keep.get("op") not in ("search", "read", "place"):
        keep["op"] = "search"
    return keep


def _downloaded(calls: list[dict]) -> list[dict]:
    seen, out = set(), []
    for c in calls:
        if c.get("op") in ("read", "place") and c.get("ok", True) and c.get("identity"):
            key = (c["identity"], c.get("version"), c.get("digest"))
            if key not in seen:
                seen.add(key)
                out.append({"identity": c["identity"], "version": c.get("version") or "?",
                            "digest": c.get("digest") or "?"})
    return out


def _release(index_path: Path | None) -> str | None:
    if index_path and Path(index_path).exists():
        return read_json(index_path).get("release")
    return None


def pending_items(root: Path, spec: dict) -> list[dict]:
    items = plan(root, spec["id"])
    return [it for it in items if not (runs_dir(root, spec["id"]) / it["arm"] / str(it["trial"]) / "run.json").exists()]


def run_task(root: Path, task_id: str, opts: RunOptions) -> list[dict]:
    spec = verify_task(root, task_id)
    reg = read_json(task_dir(root, task_id) / "registration.json")
    if utcnow() < reg["registered_at"]:
        raise ShowcaseError("the clock is before the registration time")
    if spec["arms"]["baseline"]["harness"] == "manual":
        raise ShowcaseError("this task's harness is 'manual': use `prepare` and `import`")
    done = []
    for it in pending_items(root, spec):
        if opts.only and f"{it['arm']}:{it['trial']}" not in opts.only and it["arm"] not in opts.only:
            continue
        if opts.max_runs is not None and len(done) >= opts.max_runs:
            break
        rec = run_trial(root, spec, it, opts)
        done.append(rec)
        if not opts.dry_run:
            print(f"{rec['run_id']}: {rec['exit']['status']} in {rec['wall_s']} s, "
                  f"{rec['usage']['tool_calls']} tool calls, {rec['usage']['tokens_total']} tokens"
                  + ("" if rec["included"] else f"  EXCLUDED: {rec['exclusion_reason']}"))
    return done


# --------------------------------------------------------------------------- manual adapter

def prepare(root: Path, task_id: str, out: Path, allow_network: bool = False) -> Path:
    """Export the identical starting workspace and each arm's prompt for externally run trials."""
    spec = verify_task(root, task_id)
    sdir = stage(root, spec, allow_network)
    items = plan(root, task_id)
    out = Path(out)
    for it in items:
        d = out / it["arm"] / str(it["trial"])
        if d.exists():
            continue
        copy_tree(sdir / "workspace", d)
        side = d / ".showcase"
        side.mkdir(parents=True, exist_ok=True)
        (side / "PROMPT.md").write_text(compose_prompt(spec, it["arm"]), encoding="utf-8")
        write_json(side / "meta.json", {"task_id": task_id, "spec_sha256": spec["spec_sha256"], "arm": it["arm"],
                                        "trial": it["trial"], "schedule_index": it["index"],
                                        "harness": spec["arms"][it["arm"]]["harness"],
                                        "model": spec["arms"][it["arm"]]["model"], "budget": spec["budget"],
                                        "started_at": None, "ended_at": None, "harness_version": None})
    (out / "RUN_ORDER.md").write_text(
        "# Run order\n\nRun the trials in this order, one at a time, each in its own directory. Fill in "
        "`.showcase/meta.json` (started_at, ended_at, harness_version) and `.showcase/usage.json` "
        "(wall_s, tool_calls, tokens_in, tokens_out, cost_usd). Keep the transcript as `.showcase/transcript.jsonl`. "
        "For the Baltor arm, keep the catalogue log as `.showcase/catalogue_calls.jsonl`. "
        "Never give the baseline arm the catalogue.\n\n"
        + "\n".join(f"{it['index'] + 1}. {it['arm']}/{it['trial']}" for it in items) + "\n", encoding="utf-8")
    return out


def import_trial(root: Path, task_id: str, arm: str, trial: int, src: Path, *, fixture: bool = False,
                 catalog_index: Path | None = None) -> dict:
    spec = verify_task(root, task_id)
    rules = load_rules()
    items = plan(root, task_id)
    item = next((i for i in items if i["arm"] == arm and i["trial"] == trial), None)
    if item is None:
        raise ShowcaseError(f"{arm}/{trial} is not in the schedule")
    tdir = runs_dir(root, task_id) / arm / str(trial)
    if (tdir / "run.json").exists():
        raise ShowcaseError(f"{tdir}/run.json exists; runs are never overwritten (use `replace`)")
    src = Path(src)
    side = src / ".showcase"
    meta = read_json(side / "meta.json") if (side / "meta.json").exists() else {}
    if meta.get("spec_sha256") not in (None, spec["spec_sha256"]):
        raise ShowcaseError(f"{src}: prepared for spec {meta['spec_sha256'][:12]}, not {spec['spec_sha256'][:12]}")
    if meta.get("arm") not in (None, arm):
        raise ShowcaseError(f"{src}: prepared for arm {meta['arm']}, not {arm}")
    usage_in = read_json(side / "usage.json") if (side / "usage.json").exists() else {}
    tdir.mkdir(parents=True, exist_ok=True)
    rec = new_record(spec, arm, trial, item["index"], "manual")
    copy_tree(src, tdir / "workspace")
    try:
        sdir = stage(root, spec)
        start = read_json(sdir / "manifest.json")["workspace"]
        rec["start_manifest_sha256"] = manifest_hash(start)
        now_files = manifest(tdir / "workspace")
        inputs = [inp["path_in_workspace"] for inp in spec.get("inputs", [])]
        input_keys = [k for k in start if any(fnmatch.fnmatch(k, pat) for pat in inputs)] or list(start)
        rec["start_verified"] = "inputs-match" if all(now_files.get(k) == start[k] for k in input_keys) \
            else "inputs-differ"
    except ShowcaseError:
        start = {}
        rec["start_manifest_sha256"] = manifest_hash({})
    rec["harness"]["version"] = meta.get("harness_version")
    if meta.get("harness_version"):
        rec["harness"]["version_matches_spec"] = spec["arms"][arm]["harness_version"] in meta["harness_version"]
    rec["harness"]["argv"] = ["<external>"]
    rec["model"]["reported"] = meta.get("model_reported")
    rec["started_at"] = meta.get("started_at") or utcnow()
    rec["ended_at"] = meta.get("ended_at") or rec["started_at"]
    rec["wall_s"] = usage_in.get("wall_s")
    tin, tout = usage_in.get("tokens_in"), usage_in.get("tokens_out")
    rec["usage"] = {"tool_calls": usage_in.get("tool_calls"), "tokens_in": tin, "tokens_out": tout,
                    "tokens_total": (tin + tout) if tin is not None and tout is not None else usage_in.get("tokens_total"),
                    "cost_usd": usage_in.get("cost_usd"),
                    "cost_source": "self-reported" if usage_in.get("cost_usd") is not None else "unknown",
                    "source": "self-reported" if usage_in else "none"}
    if rec["usage"]["cost_usd"] is None:
        rec["usage"]["cost_usd"], cs = cost_estimate(spec, rec["usage"])
        rec["usage"]["cost_source"] = cs
    b = spec["budget"]
    exceeded = []
    if rec["wall_s"] is not None and rec["wall_s"] > b["wall_s"]:
        exceeded.append("wall_s")
    if rec["usage"]["tool_calls"] is not None and rec["usage"]["tool_calls"] > b["tool_calls"]:
        exceeded.append("tool_calls")
    if rec["usage"]["tokens_total"] is not None and rec["usage"]["tokens_total"] > b["tokens"]:
        exceeded.append("tokens")
    if b.get("usd") and rec["usage"]["cost_usd"] is not None and rec["usage"]["cost_usd"] > b["usd"]:
        exceeded.append("usd")
    rec["budget"]["exceeded"] = exceeded
    rec["exit"] = {"status": "budget-exceeded" if exceeded else meta.get("exit_status", "imported"),
                   "code": meta.get("exit_code"),
                   "message": ("self-reported usage over budget: " + ", ".join(exceeded)) if exceeded
                   else meta.get("message", "imported from an external run")}
    if rec["exit"]["status"] not in ("completed", "timeout", "budget-exceeded", "harness-error", "crashed", "imported",
                                     "not-run"):
        rec["exit"]["status"] = "imported"
    if (side / "transcript.jsonl").exists():
        shutil.copy2(side / "transcript.jsonl", tdir / "transcript.jsonl")
        rec["transcript"] = {"path": "transcript.jsonl", "sha256": sha256_file(tdir / "transcript.jsonl"),
                             "format": "jsonl"}
    calls = [dict(c, source="self-reported") for c in _read_jsonl(side / "catalogue_calls.jsonl")]
    rec["catalogue"]["calls"] = [_clean_call(c) for c in calls]
    if arm == "baltor":
        rec["catalogue"]["downloaded"] = verify_items(_downloaded(calls), catalog_index)
        rec["catalogue"]["release"] = meta.get("catalogue_release") or _release(catalog_index)
    file_index = catalogue_file_index(catalog_index, rules["min_matching_file_bytes"])
    transcript = (tdir / "transcript.jsonl").read_text(encoding="utf-8", errors="replace") \
        if (tdir / "transcript.jsonl").exists() else ""
    findings, matched = scan_contamination(arm, tdir / "workspace", transcript, None, file_index, rules,
                                           calls if arm == "baseline" else [])
    rec["contamination"] = {"checked": True, "clean": not findings, "findings": findings}
    if findings:
        rec["included"], rec["exclusion_reason"] = False, "baseline contamination: " + "; ".join(findings[:3])
    if matched and arm == "baltor":
        rec["catalogue"]["files_in_outputs"] = matched
    rec["outputs"] = collect_outputs(tdir / "workspace", start)
    rec["missing_required_outputs"] = missing_outputs(spec, tdir / "workspace")
    rec["fixture"] = bool(fixture)
    rec["notes"] = "manual import: timing and usage are self-reported" + (
        "; FIXTURE: fabricated workspace for a pipeline dry run, not an agent result" if fixture else "")
    return finish_record(rec, tdir)


def import_all(root: Path, task_id: str, src: Path, *, fixture: bool = False,
               catalog_index: Path | None = None) -> list[dict]:
    """Import SRC/<arm>/<trial>/ for every scheduled trial, in schedule order."""
    spec = verify_task(root, task_id)
    out = []
    for it in pending_items(root, spec):
        d = Path(src) / it["arm"] / str(it["trial"])
        if d.is_dir():
            out.append(import_trial(root, task_id, it["arm"], it["trial"], d, fixture=fixture,
                                    catalog_index=catalog_index))
    return out


def replace(root: Path, task_id: str, run_id: str, reason: str) -> dict:
    """Exclude a broken run (kept on disk and in reports) and schedule one extra trial for that arm."""
    spec = verify_task(root, task_id)
    _, arm, trial = run_id.split("/")
    p = runs_dir(root, task_id) / arm / trial / "run.json"
    rec = read_json(p)
    if not rec["included"]:
        raise ShowcaseError(f"{run_id} is already excluded")
    rec["included"] = False
    rec["exclusion_reason"] = f"replaced: {reason}"
    write_json(p, rec)
    sched_path = runs_dir(root, task_id) / "schedule.json"
    sched = read_json(sched_path)
    new_trial = max(i["trial"] for i in sched["items"] if i["arm"] == arm) + 1
    item = {"index": len(sched["items"]), "arm": arm, "trial": new_trial, "replaces": run_id, "reason": reason}
    sched["items"].append(item)
    write_json(sched_path, sched)
    return item


def status(root: Path, task_id: str) -> dict:
    spec = verify_task(root, task_id)
    items = plan(root, task_id)
    rows = []
    for it in items:
        p = runs_dir(root, task_id) / it["arm"] / str(it["trial"]) / "run.json"
        rec = read_json(p) if p.exists() else None
        rows.append({**it, "status": rec["exit"]["status"] if rec else "pending",
                     "evaluated": bool(rec and rec["evaluation"]["status"] == "done"),
                     "included": rec["included"] if rec else None})
    return {"task_id": task_id, "spec_sha256": spec["spec_sha256"], "items": rows}


# --------------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def rt(p, task=True):
        p.add_argument("--root", type=Path, default=Path("showcases"))
        if task:
            p.add_argument("--task", required=True)

    li = sub.add_parser("lint")
    li.add_argument("spec", type=Path)
    rg = sub.add_parser("register")
    rg.add_argument("spec", type=Path)
    rt(rg, task=False)
    rg.add_argument("--today")
    rg.add_argument("--by")
    rg.add_argument("--now")
    for name in ("verify", "plan", "status"):
        rt(sub.add_parser(name))
    pr = sub.add_parser("prepare")
    rt(pr)
    pr.add_argument("--out", type=Path, required=True)
    pr.add_argument("--allow-setup-network", action="store_true")
    rn = sub.add_parser("run")
    rt(rn)
    rn.add_argument("--catalog-tool", type=Path, default=None)
    rn.add_argument("--catalog-index", type=Path)
    rn.add_argument("--gateway", type=Path)
    rn.add_argument("--guard-hook", type=Path)
    rn.add_argument("--workspace-root", type=Path)
    rn.add_argument("--only", action="append", default=[], help="arm or arm:trial; repeatable")
    rn.add_argument("--max-runs", type=int)
    rn.add_argument("--allow-version-drift", action="store_true")
    rn.add_argument("--allow-setup-network", action="store_true")
    rn.add_argument("--keep-workspaces", action="store_true")
    rn.add_argument("--dry-run", action="store_true")
    im = sub.add_parser("import")
    rt(im)
    im.add_argument("--from", dest="src", type=Path, required=True,
                    help="a trial directory (with --arm/--trial) or a directory of <arm>/<trial>/")
    im.add_argument("--arm", choices=ARMS)
    im.add_argument("--trial", type=int)
    im.add_argument("--fixture", action="store_true")
    im.add_argument("--catalog-index", type=Path)
    rp = sub.add_parser("replace")
    rt(rp)
    rp.add_argument("--run", required=True)
    rp.add_argument("--reason", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "lint":
            spec = read_json(a.spec)
            errors, warnings = lint_spec(spec, a.spec.parent)
            tmp = dict(spec, files_sha256=spec.get("files_sha256", {}), spec_sha256="0" * 64,
                       preregistered_on=spec.get("preregistered_on", "2026-01-01"))
            errors += [f"schema: {e}" for e in validate_schema("showcase_task_spec", tmp)]
            for w in warnings:
                print("WARN ", w)
            for e in errors:
                print("ERROR", e)
            print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
            return 1 if errors else 0
        if a.cmd == "register":
            spec = register(a.spec, a.root, a.today, a.by, a.now)
            print(f"registered {spec['id']} sha256 {spec['spec_sha256']}")
            return 0
        if a.cmd == "verify":
            spec = verify_task(a.root, a.task)
            print(f"{a.task}: spec and task files match registration ({spec['spec_sha256'][:12]})")
            return 0
        if a.cmd == "plan":
            for it in plan(a.root, a.task):
                print(f"{it['index'] + 1:>3}. {it['arm']:<8} trial {it['trial']}")
            return 0
        if a.cmd == "status":
            print(json.dumps(status(a.root, a.task), indent=2))
            return 0
        if a.cmd == "prepare":
            print(prepare(a.root, a.task, a.out, a.allow_setup_network))
            return 0
        if a.cmd == "run":
            opts = RunOptions(
                catalog_tool=(a.catalog_tool or find_catalog_tool()), catalog_index=a.catalog_index,
                gateway=a.gateway or find_sibling("showcase_catalogue_gateway"),
                guard_hook=a.guard_hook, workspace_root=a.workspace_root,
                allow_version_drift=a.allow_version_drift, allow_setup_network=a.allow_setup_network,
                keep_workspaces=a.keep_workspaces, dry_run=a.dry_run, only=a.only, max_runs=a.max_runs)
            run_task(a.root, a.task, opts)
            return 0
        if a.cmd == "import":
            if a.arm and a.trial:
                recs = [import_trial(a.root, a.task, a.arm, a.trial, a.src, fixture=a.fixture,
                                     catalog_index=a.catalog_index)]
            else:
                recs = import_all(a.root, a.task, a.src, fixture=a.fixture, catalog_index=a.catalog_index)
            for r in recs:
                print(f"imported {r['run_id']}: {r['exit']['status']}"
                      + ("" if r["included"] else f"  EXCLUDED: {r['exclusion_reason']}"))
            return 0
        if a.cmd == "replace":
            print(json.dumps(replace(a.root, a.task, a.run, a.reason), indent=2))
            return 0
    except ShowcaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
