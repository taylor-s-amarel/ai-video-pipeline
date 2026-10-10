"""Shared helpers for component generators.

Every generator script uses :class:`GeneratorRun` so that its output is
reproducible and re-runnable: components it no longer produces are pruned, and
every manifest it writes records ``provenance.generator``.

Example::

    from _lib import GeneratorRun, skill_md

    with GeneratorRun(__file__) as run:
        run.component(
            "skill", "apply_frosted_caption_box",
            title="Apply a frosted caption box",
            summary="Puts a blurred, 85% opaque panel behind captions so text stays readable over moving video.",
            files={"SKILL.md": skill_md("apply-frosted-caption-box", "Use when ...", "# Body\\n...")},
            tags=["video", "captions"], step_kinds=["render"], subkind="caption-style", domain="video",
        )
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

BALTOR_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BALTOR_DIR.parent
COMPONENTS_DIR = BALTOR_DIR / "components"
REPO_URL = "https://github.com/taylor-s-amarel/ai-video-pipeline"
ALL_HARNESSES = ["claude-code", "codex", "opencode", "pi", "baltor-harness"]

sys.path.insert(0, str(BALTOR_DIR / "tools"))
from baltor_catalog import KIND_DIRS, kebab  # noqa: E402

DEFAULT_ENTRY = {
    "skill": "SKILL.md",
    "instruction-file": "INSTRUCTIONS.md",
    "rules": "RULES.md",
    "subagent": "agent.md",
    "command": "command.md",
    "hook": "hook.json",
    "plugin-manifest": "plugin.json",
    "plugin-marketplace": "marketplace.json",
    "protocol-server-configuration": "mcp.json",
    "contract-schema": "schema.json",
}

NO_EFFECTS = {"filesystem": "none", "network": "none", "executes": "none", "secrets": []}


def effects(filesystem: str = "none", network: str = "none", executes: str = "none",
            secrets: list[str] | None = None, hosts: list[str] | None = None,
            side_effects: list[str] | None = None) -> dict:
    out: dict[str, Any] = {"filesystem": filesystem, "network": network, "executes": executes,
                           "secrets": list(secrets or [])}
    if hosts:
        out["hosts"] = list(hosts)
        out["network"] = "declared"
    if side_effects:
        out["side_effects"] = list(side_effects)
    return out


def _yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)  # JSON strings are valid YAML double-quoted scalars


def front_matter(fields: dict, body: str) -> str:
    lines = ["---"]
    for k, v in fields.items():
        if isinstance(v, list):
            lines.append(f"{k}: {', '.join(str(x) for x in v)}" if k == "tools" else f"{k}: {json.dumps(v)}")
        else:
            lines.append(f"{k}: {_yaml_scalar(str(v))}")
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body.strip() + "\n"


def skill_md(name: str, description: str, body: str, **extra) -> str:
    """SKILL.md with Claude Code / Agent Skills front matter. ``name`` is kebab case."""
    return front_matter({"name": name, "description": description, **extra}, body)


def agent_md(name: str, description: str, body: str, tools: list[str] | None = None, model: str | None = None) -> str:
    fields: dict[str, Any] = {"name": name, "description": description}
    if tools:
        fields["tools"] = tools
    if model:
        fields["model"] = model
    return front_matter(fields, body)


def command_md(description: str, body: str, argument_hint: str | None = None,
               allowed_tools: list[str] | None = None) -> str:
    fields: dict[str, Any] = {"description": description}
    if argument_hint:
        fields["argument-hint"] = argument_hint
    if allowed_tools:
        fields["allowed-tools"] = ", ".join(allowed_tools)
    return front_matter(fields, body)


def dumps(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


class GeneratorRun:
    """Context manager that writes components and prunes stale ones from the same generator."""

    def __init__(self, generator_file: str, data: str | None = None):
        self.generator = Path(generator_file).resolve().relative_to(BALTOR_DIR).as_posix()
        self.data = data
        self.written: set[Path] = set()
        self.identities: set[str] = set()

    def __enter__(self) -> "GeneratorRun":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            return
        pruned = 0
        for manifest in COMPONENTS_DIR.rglob("baltor.json"):
            pkg = manifest.parent
            if pkg in self.written:
                continue
            try:
                prov = json.loads(manifest.read_text()).get("provenance", {})
            except Exception:  # noqa: BLE001
                continue
            if prov.get("generator") == self.generator:
                shutil.rmtree(pkg)
                pruned += 1
        print(f"{self.generator}: wrote {len(self.written)} component(s), pruned {pruned}")

    def component(self, kind: str, identity: str, *, title: str, summary: str, files: dict[str, str | bytes],
                  tags: list[str], step_kinds: list[str], subkind: str | None = None, domain: str | None = None,
                  description: str | None = None, licence: str = "MIT", attribution: str | None = None,
                  effects_: dict | None = None, harnesses: list[str] | None = None, entry: str | None = None,
                  source: dict | None = None, collection: str = "public-good", depends_on: list[dict] | None = None,
                  variant_of: str | None = None, parameters: dict | None = None, install: dict | None = None,
                  examples: list[str] | None = None, version: str = "1.0.0", review: dict | None = None) -> Path:
        if identity in self.identities:
            raise ValueError(f"{self.generator}: identity '{identity}' written twice")
        self.identities.add(identity)
        if kind not in KIND_DIRS:
            raise ValueError(f"unknown kind {kind}")
        pkg = COMPONENTS_DIR / KIND_DIRS[kind] / kebab(identity)
        if pkg.exists():
            existing = pkg / "baltor.json"
            if existing.exists():
                prov = json.loads(existing.read_text()).get("provenance", {})
                if prov.get("generator") not in (None, self.generator):
                    raise ValueError(f"{identity} already belongs to {prov.get('generator')}")
            shutil.rmtree(pkg)
        pkg.mkdir(parents=True)
        if entry is None:
            entry = DEFAULT_ENTRY.get(kind) or sorted(files)[0]
        manifest: dict[str, Any] = {
            "spec": "baltor.component/v1",
            "identity": identity,
            "title": title,
            "kind": kind,
        }
        if subkind:
            manifest["subkind"] = subkind
        manifest.update({
            "version": version,
            "summary": summary,
        })
        if description:
            manifest["description"] = description
        if domain:
            manifest["domain"] = domain
        manifest["licence"] = licence
        if attribution:
            manifest["attribution"] = attribution
        manifest.update({
            "source": source or {"type": "original", "url": REPO_URL},
            "step_kinds": step_kinds,
            "effects": effects_ or dict(NO_EFFECTS),
            "harnesses": harnesses or list(ALL_HARNESSES),
            "entry": entry,
            "tags": tags,
            "collection": collection,
        })
        if depends_on:
            manifest["depends_on"] = depends_on
        if variant_of:
            manifest["variant_of"] = variant_of
        prov: dict[str, Any] = {"generator": self.generator}
        if self.data:
            prov["data"] = self.data
        if parameters:
            prov["parameters"] = parameters
        manifest["provenance"] = prov
        if install:
            manifest["install"] = install
        if examples:
            manifest["examples"] = examples
        manifest["review"] = review or {"status": "unreviewed"}
        for rel, content in files.items():
            dest = pkg / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                dest.write_bytes(content)
            else:
                dest.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
        (pkg / "baltor.json").write_text(dumps(manifest), encoding="utf-8")
        self.written.add(pkg)
        return pkg
