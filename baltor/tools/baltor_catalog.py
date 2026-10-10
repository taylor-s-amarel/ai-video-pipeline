#!/usr/bin/env python3
"""Local Baltor catalogue tool.

Validates component packages, builds the catalogue index, release record and
feeds, and implements local equivalents of the Baltor service operations:
``search`` (intelligence_search), ``read`` (provisioning_read), ``place`` and
``lock``.

Usage:
    python baltor/tools/baltor_catalog.py validate [--strict] [--deep] [PATH ...]
    python baltor/tools/baltor_catalog.py build [--date YYYY-MM-DD]
    python baltor/tools/baltor_catalog.py search "query" [--kind skill] [--limit 10]
    python baltor/tools/baltor_catalog.py read IDENTITY [--digest SHA256] [--out DIR]
    python baltor/tools/baltor_catalog.py place IDENTITY STEP_DIR [--harness claude-code] [--merge]
    python baltor/tools/baltor_catalog.py lock STEP_DIR
    python baltor/tools/baltor_catalog.py stats

Only the standard library is required; ``jsonschema`` and ``PyYAML`` are used
when installed for stricter checks.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tomllib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from html import escape as _xml_escape
from pathlib import Path

try:  # optional, stricter checks when present
    import jsonschema  # type: ignore
except ImportError:  # pragma: no cover
    jsonschema = None
try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

BALTOR_DIR = Path(__file__).resolve().parents[1]
COMPONENTS_DIR = BALTOR_DIR / "components"
CATALOG_DIR = BALTOR_DIR / "catalog"
FEEDS_DIR = BALTOR_DIR / "feeds"
SCHEMAS_DIR = BALTOR_DIR / "schemas"
REPO_URL = os.environ.get("BALTOR_REPO_URL", "https://github.com/taylor-s-amarel/ai-video-pipeline")
REPO_BRANCH = os.environ.get("BALTOR_REPO_BRANCH", "main")

KIND_DIRS = {
    "skill": "skills",
    "instruction-file": "instruction-files",
    "rules": "rules",
    "subagent": "subagents",
    "command": "commands",
    "hook": "hooks",
    "plugin-manifest": "plugin-manifests",
    "plugin-marketplace": "plugin-marketplaces",
    "protocol-server-configuration": "protocol-server-configs",
    "harness-settings": "harness-settings",
    "contract-schema": "contract-schemas",
    "code-module": "code-modules",
}
DIR_KINDS = {v: k for k, v in KIND_DIRS.items()}

HOOK_EVENTS = {
    "PreToolUse", "PostToolUse", "UserPromptSubmit", "Stop", "SubagentStop", "SessionStart",
    "SessionEnd", "Notification", "PreCompact",
}
MAX_FILE_BYTES = 256 * 1024
MAX_PACKAGE_BYTES = 512 * 1024
ATTRIBUTION_LICENCES = re.compile(r"\bCC-BY(?!-?NC)|\bCC-BY-SA|\bCC-BY-ND|OFL|Apache-2\.0", re.I)
NONCOMMERCIAL = re.compile(r"\bNC\b|-NC-|NonCommercial", re.I)
SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_-]{24,}"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}"),
    re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
]
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".py", ".js", ".mjs", ".ts", ".gd", ".sh",
    ".cfg", ".ini", ".xml", ".svg", ".glsl", ".frag", ".vert", ".cube", ".csv", ".srt", ".vtt",
    ".ass", ".html", ".css", ".tscn", ".tres", ".sql", ".lua", ".cs", ".jsonl", ".env.example",
}


# --------------------------------------------------------------------------- helpers

def kebab(identity: str) -> str:
    return identity.replace("_", "-")


def snake(name: str) -> str:
    return name.replace("-", "_")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def package_digest(files: list[dict]) -> str:
    lines = "".join(f"{f['path']}\0{f['sha256']}\n" for f in sorted(files, key=lambda f: f["path"]))
    return sha256_bytes(lines.encode("utf-8"))


def package_files(pkg_dir: Path) -> list[Path]:
    out = []
    for p in sorted(pkg_dir.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith((".pyc", ".pyo")) \
                and p.name != ".DS_Store" and ".pytest_cache" not in p.parts:
            out.append(p)
    return out


def front_matter(text: str) -> dict | None:
    """Parse a leading ``---`` YAML block. Returns None when absent or invalid."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end].strip("\n")
    if yaml is not None:
        try:
            data = yaml.safe_load(block)
        except Exception:
            return None
        return data if isinstance(data, dict) else None
    data = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith((" ", "\t", "-")):
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip().strip('"').strip("'")
    return data


_schema_cache: dict[str, dict] = {}


def load_schema(name: str) -> dict:
    if name not in _schema_cache:
        _schema_cache[name] = json.loads((SCHEMAS_DIR / name).read_text())
    return _schema_cache[name]


def known_subkinds() -> set[str]:
    data = json.loads((SCHEMAS_DIR / "subkinds.json").read_text())
    return {v for k, vals in data.items() if isinstance(vals, list) for v in vals}


def find_packages(paths: list[Path] | None = None) -> list[Path]:
    roots = paths or [COMPONENTS_DIR]
    found = []
    for root in roots:
        root = Path(root)
        if root.is_file() and root.name == "baltor.json":
            found.append(root.parent)
            continue
        if (root / "baltor.json").exists():
            found.append(root)
            continue
        found.extend(p.parent for p in root.rglob("baltor.json"))
    return sorted(set(found))


# --------------------------------------------------------------------------- validation

@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def err(self, pkg: Path, msg: str) -> None:
        self.errors.append(f"{_rel(pkg)}: {msg}")

    def warn(self, pkg: Path, msg: str) -> None:
        self.warnings.append(f"{_rel(pkg)}: {msg}")


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(BALTOR_DIR))
    except ValueError:
        return str(p)


def _check_schema(instance, schema_name: str) -> list[str]:
    if jsonschema is None:
        return []
    validator = jsonschema.Draft202012Validator(load_schema(schema_name))
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
            for e in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))]


def validate_package(pkg: Path, report: Report, subkinds: set[str], deep: bool = False) -> dict | None:
    mpath = pkg / "baltor.json"
    try:
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        report.err(pkg, f"baltor.json does not parse: {exc}")
        return None
    for msg in _check_schema(manifest, "component.schema.json"):
        report.err(pkg, f"manifest {msg}")
    if not isinstance(manifest, dict) or "identity" not in manifest or "kind" not in manifest:
        return None

    identity, kind = manifest["identity"], manifest["kind"]
    if pkg.name != kebab(identity):
        report.err(pkg, f"directory name must be '{kebab(identity)}' (identity in kebab case)")
    expected_dir = KIND_DIRS.get(kind)
    if expected_dir and pkg.parent.name != expected_dir and COMPONENTS_DIR in pkg.parents:
        report.err(pkg, f"kind '{kind}' belongs under components/{expected_dir}/")
    sub = manifest.get("subkind")
    if sub and sub not in subkinds:
        report.warn(pkg, f"unknown subkind '{sub}' (add it to schemas/subkinds.json if intended)")

    files = package_files(pkg)
    rel_files = {p.relative_to(pkg).as_posix() for p in files}
    entry = manifest.get("entry", "")
    if entry not in rel_files:
        report.err(pkg, f"entry '{entry}' not found in package")
    for harness, spec in (manifest.get("install") or {}).items():
        for f in spec.get("files", []):
            if f not in rel_files:
                report.err(pkg, f"install.{harness} names missing file '{f}'")

    licence = manifest.get("licence", "")
    if re.search(r"\bCC-BY", licence) and not manifest.get("attribution"):
        report.err(pkg, f"licence {licence} requires an 'attribution' string")
    if NONCOMMERCIAL.search(licence):
        report.warn(pkg, f"licence {licence} is non-commercial; keep it out of paid collections")
        if manifest.get("collection") == "library":
            report.err(pkg, "non-commercial licence cannot be in the paid 'library' collection")
    effects = manifest.get("effects", {})
    if effects.get("network") == "declared" and not effects.get("hosts"):
        report.err(pkg, "effects.network is 'declared' but effects.hosts is empty")
    if effects.get("network") == "none" and effects.get("hosts"):
        report.err(pkg, "effects.hosts is set but effects.network is 'none'")
    if manifest.get("source", {}).get("type") == "third-party" and not manifest.get("source", {}).get("url"):
        report.err(pkg, "third-party source needs source.url")

    total = 0
    for p in files:
        size = p.stat().st_size
        total += size
        rel = p.relative_to(pkg).as_posix()
        if size > MAX_FILE_BYTES:
            report.err(pkg, f"{rel} is {size} bytes (limit {MAX_FILE_BYTES})")
        if p.suffix.lower() in TEXT_SUFFIXES or p.name in {"Dockerfile", "Makefile"}:
            try:
                text = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                report.err(pkg, f"{rel} is not valid UTF-8")
                continue
            for pat in SECRET_PATTERNS:
                if pat.search(text):
                    report.err(pkg, f"{rel} contains something that looks like a credential ({pat.pattern[:24]}...)")
            if p.suffix == ".json":
                try:
                    json.loads(text)
                except Exception as exc:  # noqa: BLE001
                    report.err(pkg, f"{rel} is not valid JSON: {exc}")
            elif p.suffix == ".toml":
                try:
                    tomllib.loads(text)
                except Exception as exc:  # noqa: BLE001
                    report.err(pkg, f"{rel} is not valid TOML: {exc}")
            elif p.suffix in {".yaml", ".yml"} and yaml is not None:
                try:
                    list(yaml.safe_load_all(text))
                except Exception as exc:  # noqa: BLE001
                    report.err(pkg, f"{rel} is not valid YAML: {exc}")
            elif p.suffix == ".py":
                try:
                    compile(text, str(p), "exec")
                except SyntaxError as exc:
                    report.err(pkg, f"{rel} does not compile: {exc}")
    if total > MAX_PACKAGE_BYTES:
        report.err(pkg, f"package is {total} bytes (limit {MAX_PACKAGE_BYTES})")

    _validate_kind(pkg, manifest, rel_files, report, deep)
    return manifest


def _read(pkg: Path, rel: str) -> str:
    return (pkg / rel).read_text(encoding="utf-8")


def _validate_kind(pkg: Path, m: dict, rel_files: set[str], report: Report, deep: bool) -> None:
    kind = m["kind"]
    entry = m.get("entry", "")
    if entry not in rel_files:
        return
    if kind == "skill":
        if not entry.endswith("SKILL.md"):
            report.err(pkg, "a skill's entry must be SKILL.md")
            return
        fm = front_matter(_read(pkg, entry))
        if not fm or not fm.get("name") or not fm.get("description"):
            report.err(pkg, "SKILL.md needs front matter with 'name' and 'description'")
        else:
            if fm["name"] != kebab(m["identity"]):
                report.err(pkg, f"SKILL.md name '{fm['name']}' must equal '{kebab(m['identity'])}'")
            if len(str(fm["name"])) > 64:
                report.err(pkg, "SKILL.md name must be at most 64 characters")
            if len(str(fm["description"])) > 1024:
                report.err(pkg, "SKILL.md description must be at most 1024 characters")
    elif kind in {"subagent", "command"}:
        fm = front_matter(_read(pkg, entry))
        need = ("name", "description") if kind == "subagent" else ("description",)
        if not fm or any(not fm.get(k) for k in need):
            report.err(pkg, f"{entry} needs front matter with {', '.join(need)}")
    elif kind == "hook":
        if "hook.json" not in rel_files:
            report.err(pkg, "a hook needs hook.json")
            return
        spec = json.loads(_read(pkg, "hook.json"))
        events = spec.get("events") or ([spec["event"]] if "event" in spec else [])
        if not events or any(e not in HOOK_EVENTS for e in events):
            report.err(pkg, f"hook.json events must be from {sorted(HOOK_EVENTS)}")
        if not spec.get("command"):
            report.err(pkg, "hook.json needs 'command'")
    elif kind == "contract-schema":
        try:
            schema = json.loads(_read(pkg, entry))
        except Exception:
            return
        if jsonschema is not None:
            cls = jsonschema.validators.validator_for(schema, default=jsonschema.Draft202012Validator)
            try:
                cls.check_schema(schema)
            except Exception as exc:  # noqa: BLE001
                report.err(pkg, f"{entry} is not a valid JSON Schema: {str(exc).splitlines()[0]}")
                return
            examples = sorted(f for f in rel_files if f.startswith("examples/") and f.endswith(".json"))
            if not examples:
                report.err(pkg, "a contract schema needs at least one examples/*.json")
            for ex in examples:
                inst = json.loads(_read(pkg, ex))
                errs = list(cls(schema).iter_errors(inst))
                if ex.startswith("examples/invalid"):
                    if not errs:
                        report.err(pkg, f"{ex} is meant to be invalid but validates")
                elif errs:
                    report.err(pkg, f"{ex} does not validate: {errs[0].message}")
    elif kind == "protocol-server-configuration":
        if "mcp.json" not in rel_files:
            report.err(pkg, "a protocol server configuration needs mcp.json (Claude Code format)")
        else:
            data = json.loads(_read(pkg, "mcp.json"))
            if not isinstance(data.get("mcpServers"), dict) or not data["mcpServers"]:
                report.err(pkg, "mcp.json needs a non-empty 'mcpServers' object")
            else:
                for name, srv in data["mcpServers"].items():
                    if not ("command" in srv or "url" in srv):
                        report.err(pkg, f"mcp.json server '{name}' needs 'command' or 'url'")
        if "codex.toml" in rel_files:
            data = tomllib.loads(_read(pkg, "codex.toml"))
            if not isinstance(data.get("mcp_servers"), dict):
                report.err(pkg, "codex.toml needs an [mcp_servers.<name>] table")
        if "opencode.json" in rel_files:
            data = json.loads(_read(pkg, "opencode.json"))
            if not isinstance(data.get("mcp"), dict):
                report.err(pkg, "opencode.json needs an 'mcp' object")
    elif kind == "plugin-manifest":
        data = json.loads(_read(pkg, entry))
        if not data.get("name"):
            report.err(pkg, f"{entry} needs 'name'")
    elif kind == "plugin-marketplace":
        data = json.loads(_read(pkg, entry))
        if not data.get("name") or not isinstance(data.get("plugins"), list) or not data.get("owner"):
            report.err(pkg, f"{entry} needs 'name', 'owner' and a 'plugins' list")
    elif kind == "code-module" and deep:
        for rel in sorted(rel_files):
            if rel.endswith((".js", ".mjs")) and shutil.which("node"):
                proc = subprocess.run(["node", "--check", str(pkg / rel)], capture_output=True, text=True)
                if proc.returncode:
                    report.err(pkg, f"{rel} fails node --check: {proc.stderr.strip()[:200]}")


def packages_from_generator(generator: str) -> list[Path]:
    gen = generator.removeprefix("baltor/")
    out = []
    for manifest in COMPONENTS_DIR.rglob("baltor.json"):
        try:
            if json.loads(manifest.read_text()).get("provenance", {}).get("generator") == gen:
                out.append(manifest.parent)
        except Exception:  # noqa: BLE001
            out.append(manifest.parent)
    return sorted(out)


def validate(paths: list[Path] | None = None, deep: bool = False,
             generator: str | None = None) -> tuple[Report, list[tuple[Path, dict]]]:
    report = Report()
    subkinds = known_subkinds()
    seen: dict[str, Path] = {}
    ok: list[tuple[Path, dict]] = []
    if generator:
        paths = packages_from_generator(generator)
        if not paths:
            report.errors.append(f"no packages from generator {generator}")
            return report, ok
    for pkg in find_packages(paths):
        m = validate_package(pkg, report, subkinds, deep=deep)
        if not m:
            continue
        ident = m.get("identity")
        if ident in seen:
            report.err(pkg, f"identity '{ident}' already used by {_rel(seen[ident])}")
        else:
            seen[ident] = pkg
        ok.append((pkg, m))
    idents = set(seen)
    for pkg, m in ok:
        v = m.get("variant_of")
        if v and v not in idents and paths is None:
            report.err(pkg, f"variant_of '{v}' does not exist")
        for dep in m.get("depends_on", []):
            if not dep.get("external") and dep["identity"] not in idents and paths is None:
                report.err(pkg, f"depends_on '{dep['identity']}' does not exist (mark external: true if outside)")
    return report, ok


# --------------------------------------------------------------------------- build

def index_entry(pkg: Path, m: dict) -> dict:
    files = []
    for p in package_files(pkg):
        data = p.read_bytes()
        files.append({"path": p.relative_to(pkg).as_posix(), "size": len(data), "sha256": sha256_bytes(data)})
    keep = ["identity", "title", "kind", "subkind", "version", "summary", "licence", "attribution", "collection",
            "domain", "tags", "step_kinds", "effects", "harnesses", "entry", "variant_of", "depends_on", "source"]
    entry = {k: m[k] for k in keep if k in m}
    entry["path"] = pkg.relative_to(BALTOR_DIR).as_posix()
    entry["files"] = files
    entry["size"] = sum(f["size"] for f in files)
    entry["digest"] = package_digest(files)
    return entry


def release_id(entries: list[dict]) -> str:
    lines = sorted(f"{e['identity']}@{e['version']}#{e['digest']}" for e in entries)
    return sha256_bytes("\n".join(lines).encode())[:12]


def build(date: str | None = None, quiet: bool = False) -> dict:
    report, ok = validate()
    if report.errors:
        for e in report.errors[:200]:
            print("ERROR", e, file=sys.stderr)
        raise SystemExit(f"{len(report.errors)} validation error(s); fix them before building")
    entries = sorted((index_entry(p, m) for p, m in ok), key=lambda e: e["identity"])
    rid = release_id(entries)
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    rel_path = CATALOG_DIR / "release.json"
    prev = json.loads(rel_path.read_text()) if rel_path.exists() else None
    prev_index = {}
    idx_path = CATALOG_DIR / "index.json"
    if idx_path.exists():
        try:
            prev_index = {e["identity"]: e["digest"] for e in json.loads(idx_path.read_text())["packages"]}
        except Exception:  # noqa: BLE001
            prev_index = {}
    cur = {e["identity"]: e["digest"] for e in entries}
    if prev and prev.get("release") == rid:
        release = prev
    else:
        withdrawn = sorted(set(prev_index) - set(cur))
        previously_withdrawn = sorted(set((prev or {}).get("withdrawn_all", [])) | set(withdrawn))
        reused = sorted(set(previously_withdrawn) & set(cur))
        if reused:
            raise SystemExit(f"withdrawn identities cannot be reused: {reused[:10]}")
        release = {
            "spec": "baltor.release/v1",
            "release": rid,
            "previous": (prev or {}).get("release"),
            "created": date or _dt.date.today().isoformat(),
            "packages": len(entries),
            "files": sum(len(e["files"]) for e in entries),
            "distinct_files": len({f["sha256"] for e in entries for f in e["files"]}),
            "bytes": sum(e["size"] for e in entries),
            "added": sorted(set(cur) - set(prev_index)),
            "changed": sorted(i for i in cur if i in prev_index and prev_index[i] != cur[i]),
            "withdrawn": withdrawn,
            "withdrawn_all": previously_withdrawn,
        }
    stats = catalog_stats(entries)
    release["by_kind"] = stats["by_kind"]
    index = {"spec": "baltor.index/v1", "release": rid, "packages": entries}
    _write_json(idx_path, index, compact=True)
    _write_json(rel_path, release)
    _write_json(CATALOG_DIR / "stats.json", stats)
    (CATALOG_DIR / "CATALOG.md").write_text(render_catalog_md(entries, release, stats), encoding="utf-8")
    build_feeds(entries, release)
    if not quiet:
        print(f"release {rid}: {len(entries)} packages, {release['files']} files, "
              f"{release['distinct_files']} distinct files; {len(report.warnings)} warning(s)")
    return release


def _write_json(path: Path, data, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        text = json.dumps(data, separators=(",", ":"), ensure_ascii=False, sort_keys=False)
    else:
        text = json.dumps(data, indent=2, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")


def catalog_stats(entries: list[dict]) -> dict:
    by_kind = Counter(e["kind"] for e in entries)
    return {
        "packages": len(entries),
        "by_kind": dict(sorted(by_kind.items(), key=lambda kv: (-kv[1], kv[0]))),
        "by_subkind": dict(Counter(e.get("subkind") or "-" for e in entries).most_common()),
        "by_domain": dict(Counter(e.get("domain") or "-" for e in entries).most_common()),
        "by_licence": dict(Counter(e["licence"] for e in entries).most_common()),
        "by_collection": dict(Counter(e["collection"] for e in entries).most_common()),
        "variants": sum(1 for e in entries if e.get("variant_of")),
        "base_items": sum(1 for e in entries if not e.get("variant_of")),
    }


def render_catalog_md(entries: list[dict], release: dict, stats: dict) -> str:
    out = [f"# Baltor component catalogue\n",
           f"Release `{release['release']}` · {release['created']} · {release['packages']:,} packages · "
           f"{release['files']:,} files ({release['distinct_files']:,} distinct) · "
           f"{stats['base_items']:,} base items and {stats['variants']:,} generated variants.\n",
           "Generated by `baltor/tools/baltor_catalog.py build`. Do not edit by hand.\n",
           "## By kind\n", "| Kind | Packages |", "|---|---:|"]
    out += [f"| {k} | {v:,} |" for k, v in stats["by_kind"].items()]
    out += ["\n## By domain\n", "| Domain | Packages |", "|---|---:|"]
    out += [f"| {k} | {v:,} |" for k, v in stats["by_domain"].items()]
    out += ["\n## By subkind\n", "| Subkind | Packages |", "|---|---:|"]
    out += [f"| {k} | {v:,} |" for k, v in stats["by_subkind"].items()]
    out += ["\n## By licence\n", "| Licence | Packages |", "|---|---:|"]
    out += [f"| {k} | {v:,} |" for k, v in stats["by_licence"].items()]
    out += ["\n## Base items\n", "Variants are listed in `index.json` under their `variant_of` base.\n"]
    by_kind = defaultdict(list)
    for e in entries:
        if not e.get("variant_of"):
            by_kind[e["kind"]].append(e)
    for kind in sorted(by_kind):
        out.append(f"\n### {kind} ({len(by_kind[kind]):,})\n")
        out.append("| Identity | Summary | Licence |")
        out.append("|---|---|---|")
        for e in by_kind[kind]:
            summary = e["summary"].replace("|", "\\|")
            out.append(f"| [`{e['identity']}`]({_rel_link(e)}) | {summary} | {e['licence']} |")
    return "\n".join(out) + "\n"


def _rel_link(e: dict) -> str:
    return "../" + e["path"] + "/" + e["entry"]


# --------------------------------------------------------------------------- feeds

def load_feed_collections() -> list[dict]:
    cols = []
    if not FEEDS_DIR.exists():
        return cols
    for p in sorted(FEEDS_DIR.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        errs = _check_schema(data, "feed-collection.schema.json")
        if errs:
            raise SystemExit(f"feeds/{p.name}: {errs[0]}")
        if data["id"] != p.stem:
            raise SystemExit(f"feeds/{p.name}: id '{data['id']}' must equal the file name")
        ids = [i["id"] for i in data["items"]]
        dupes = [i for i, n in Counter(ids).items() if n > 1]
        if dupes:
            raise SystemExit(f"feeds/{p.name}: duplicate item ids {dupes[:5]}")
        cols.append(data)
    return cols


def validate_feeds() -> list[str]:
    errors = []
    if not FEEDS_DIR.exists():
        return errors
    for p in sorted(FEEDS_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"feeds/{p.name}: {exc}")
            continue
        errors += [f"feeds/{p.name}: {e}" for e in _check_schema(data, "feed-collection.schema.json")]
        if isinstance(data, dict) and data.get("id") != p.stem:
            errors.append(f"feeds/{p.name}: id must equal file name")
        if isinstance(data, dict):
            ids = [i.get("id") for i in data.get("items", [])]
            errors += [f"feeds/{p.name}: duplicate item id {i}" for i, n in Counter(ids).items() if n > 1]
    return errors


def _feed_url(name: str) -> str:
    return f"{REPO_URL}/blob/{REPO_BRANCH}/baltor/catalog/feeds/{name}"


def build_feeds(entries: list[dict], release: dict) -> None:
    out_dir = CATALOG_DIR / "feeds"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    collections = load_feed_collections()
    comp_items = []
    for e in sorted(entries, key=lambda e: e["identity"]):
        if e.get("variant_of"):
            continue
        comp_items.append({
            "id": kebab(e["identity"]), "title": e["title"],
            "url": f"{REPO_URL}/tree/{REPO_BRANCH}/baltor/{e['path']}",
            "summary": e["summary"], "kind": "repository", "licence": e["licence"],
            "verified_on": release["created"], "verification": "fetched",
            "tags": [e["kind"]] + ([e["subkind"]] if e.get("subkind") else []) + e["tags"][:6],
        })
    collections.append({
        "spec": "baltor.feed-collection/v1", "id": "components",
        "title": "Baltor components in this repository",
        "description": f"Base components in release {release['release']} ({len(comp_items)} items; variants omitted).",
        "updated": release["created"], "items": comp_items,
    })
    index_rows = []
    for col in collections:
        cid = col["id"]
        jf = {
            "version": "https://jsonfeed.org/version/1.1",
            "title": col["title"],
            "home_page_url": f"{REPO_URL}/tree/{REPO_BRANCH}/baltor",
            "feed_url": _feed_url(f"{cid}.json"),
            "description": col["description"],
            "items": [{
                "id": f"{cid}/{it['id']}", "url": it["url"], "title": it["title"],
                "content_text": it["summary"], "summary": it["summary"],
                "date_published": _rfc3339(it.get("date_published") or it["verified_on"]),
                "tags": it.get("tags", []) + [it["kind"]],
                "_baltor": {k: it[k] for k in ("kind", "licence", "licence_url", "verified_on", "verification",
                                                "notes", "cautions", "feed_url", "feed_format", "poll_interval_h",
                                                "auth", "vendor", "products", "change_types", "terms_note") if k in it},
            } for it in col["items"]],
        }
        _write_json(out_dir / f"{cid}.json", jf)
        (out_dir / f"{cid}.xml").write_text(_rss(col), encoding="utf-8")
        (out_dir / f"{cid}.md").write_text(_feed_md(col), encoding="utf-8")
        index_rows.append((cid, col["title"], len(col["items"])))
    lines = ["# Agent feeds\n", "Each collection is available as JSON Feed 1.1 (`.json`), RSS 2.0 (`.xml`) and Markdown (`.md`).\n",
             "| Collection | Items | Formats |", "|---|---:|---|"]
    lines += [f"| {t} | {n} | [json]({c}.json) · [rss]({c}.xml) · [md]({c}.md) |" for c, t, n in index_rows]
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _rfc3339(date: str) -> str:
    return date if "T" in date else f"{date}T00:00:00Z"


def _rfc822(date: str) -> str:
    try:
        d = _dt.datetime.fromisoformat(date.replace("Z", "+00:00"))
    except ValueError:
        d = _dt.datetime(2026, 1, 1)
    if d.tzinfo is None:
        d = d.replace(tzinfo=_dt.timezone.utc)
    return d.strftime("%a, %d %b %Y %H:%M:%S +0000")


def _rss(col: dict) -> str:
    items = []
    for it in col["items"]:
        cats = "".join(f"<category>{_xml_escape(t)}</category>" for t in it.get("tags", []))
        items.append(
            f"<item><title>{_xml_escape(it['title'])}</title><link>{_xml_escape(it['url'])}</link>"
            f"<guid isPermaLink=\"false\">{_xml_escape(col['id'] + '/' + it['id'])}</guid>"
            f"<description>{_xml_escape(it['summary'])}</description>"
            f"<pubDate>{_rfc822(it.get('date_published') or it['verified_on'])}</pubDate>{cats}</item>")
    return ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<rss version=\"2.0\"><channel>"
            f"<title>{_xml_escape(col['title'])}</title><link>{_xml_escape(_feed_url(col['id'] + '.xml'))}</link>"
            f"<description>{_xml_escape(col['description'])}</description>" + "".join(items) + "</channel></rss>\n")


def _feed_md(col: dict) -> str:
    out = [f"# {col['title']}\n", col["description"] + "\n", f"Updated {col['updated']}. {len(col['items'])} items.\n",
           "| Item | Kind | Licence | Summary |", "|---|---|---|---|"]
    for it in col["items"]:
        s = it["summary"].replace("|", "\\|").replace("\n", " ")
        out.append(f"| [{it['title']}]({it['url']}) | {it['kind']} | {it.get('licence', '')} | {s} |")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- search / read / place / lock

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def load_index() -> dict:
    p = CATALOG_DIR / "index.json"
    if not p.exists():
        raise SystemExit("catalog/index.json not found; run 'build' first")
    return json.loads(p.read_text(encoding="utf-8"))


def search(query: str, kind: str | None = None, limit: int = 10, include_variants: bool = False,
           index: dict | None = None) -> list[dict]:
    """BM25 over identity, title, summary, tags, subkind and domain. Returns small references."""
    index = index or load_index()
    docs = [e for e in index["packages"]
            if (not kind or e["kind"] == kind) and (include_variants or not e.get("variant_of"))]
    if not docs:
        return []
    fields = []
    for e in docs:
        text = " ".join([e["identity"].replace("_", " "), e["title"], e["title"], e["summary"],
                         " ".join(e.get("tags", [])), e.get("subkind") or "", e.get("domain") or "", e["kind"]])
        fields.append(_tokens(text))
    n = len(fields)
    avg = sum(len(f) for f in fields) / n
    df = Counter(t for f in fields for t in set(f))
    q = _tokens(query)
    k1, b = 1.4, 0.75
    scored = []
    for e, toks in zip(docs, fields):
        tf = Counter(toks)
        s = 0.0
        for t in q:
            if t not in tf:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(toks) / avg))
        if s > 0:
            scored.append((s, e))
    scored.sort(key=lambda se: (-se[0], se[1]["identity"]))
    return [{"identity": e["identity"], "kind": e["kind"], "subkind": e.get("subkind"), "version": e["version"],
             "licence": e["licence"], "size": e["size"], "digest": e["digest"], "summary": e["summary"],
             "score": round(s, 3)} for s, e in scored[:limit]]


def get_entry(identity: str, index: dict | None = None) -> dict:
    index = index or load_index()
    for e in index["packages"]:
        if e["identity"] == identity:
            return e
    raise SystemExit(f"unknown identity '{identity}'")


def read_package(identity: str, expected_digest: str | None = None, index: dict | None = None) -> dict:
    """Local provisioning_read: returns the package bytes after checking every digest."""
    e = get_entry(identity, index)
    if expected_digest and not e["digest"].startswith(expected_digest):
        raise SystemExit(f"digest mismatch for {identity}: catalogue has {e['digest']}, request named {expected_digest}")
    pkg = BALTOR_DIR / e["path"]
    files = {}
    for f in e["files"]:
        data = (pkg / f["path"]).read_bytes()
        if sha256_bytes(data) != f["sha256"]:
            raise SystemExit(f"{identity}: {f['path']} changed since the catalogue was built; run 'build'")
        files[f["path"]] = data
    return {"entry": e, "files": files}


PLACEMENT = {
    "skill": {"claude-code": ".claude/skills/{name}/", "default": ".agents/skills/{name}/"},
    "instruction-file": {"claude-code": "CLAUDE.md", "default": "AGENTS.md"},
    "rules": {"default": ".baltor/rules/{name}.md"},
    "subagent": {"claude-code": ".claude/agents/{name}.md", "opencode": ".opencode/agent/{name}.md",
                 "default": ".baltor/agents/{name}.md"},
    "command": {"claude-code": ".claude/commands/{name}.md", "opencode": ".opencode/command/{name}.md",
                "default": ".baltor/commands/{name}.md"},
    "hook": {"default": ".baltor/hooks/{name}/"},
    "protocol-server-configuration": {"claude-code": ".mcp.json", "codex": ".codex/config.toml",
                                      "opencode": "opencode.json", "default": ".mcp.json"},
    "harness-settings": {"default": ".baltor/settings/{name}/"},
    "plugin-manifest": {"default": ".claude-plugin/"},
    "plugin-marketplace": {"default": ".claude-plugin/"},
    "code-module": {"default": ".baltor/lib/{name}/"},
    "contract-schema": {"default": ".baltor/schemas/{name}/"},
}


def place(identity: str, step_dir: Path, harness: str = "claude-code", merge: bool = False) -> list[Path]:
    data = read_package(identity)
    e = data["entry"]
    name = kebab(identity)
    override = (json.loads(data["files"]["baltor.json"]).get("install") or {}).get(harness, {})
    target = override.get("path") or PLACEMENT[e["kind"]].get(harness) or PLACEMENT[e["kind"]]["default"]
    target = target.format(name=name)
    step_dir = Path(step_dir)
    written: list[Path] = []
    payload = {p: b for p, b in data["files"].items() if p != "baltor.json"}
    if override.get("files"):
        payload = {p: b for p, b in payload.items() if p in override["files"]}
    kind = e["kind"]
    if kind == "instruction-file":
        dest = step_dir / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        body = payload[e["entry"]].decode("utf-8")
        marker = f"<!-- baltor:{identity}@{e['version']} -->"
        existing = dest.read_text(encoding="utf-8") if dest.exists() else ""
        if marker not in existing:
            dest.write_text((existing.rstrip() + "\n\n" if existing else "") + marker + "\n" + body, encoding="utf-8")
        written.append(dest)
    elif kind in {"subagent", "command", "rules"}:
        dest = step_dir / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload[e["entry"]])
        written.append(dest)
    elif kind == "protocol-server-configuration":
        written += _place_mcp(payload, step_dir, harness, target, merge)
    else:
        base = step_dir / target
        for rel, blob in payload.items():
            dest = base / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(blob)
            written.append(dest)
    _lock_add(step_dir, e, written, harness)
    return written


def _place_mcp(payload: dict, step_dir: Path, harness: str, target: str, merge: bool) -> list[Path]:
    src_name = {"codex": "codex.toml", "opencode": "opencode.json"}.get(harness, "mcp.json")
    if src_name not in payload:
        src_name = "mcp.json"
    dest = step_dir / target
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src_name == "mcp.json" and merge:
        current = json.loads(dest.read_text()) if dest.exists() else {}
        incoming = json.loads(payload["mcp.json"])
        current.setdefault("mcpServers", {}).update(incoming["mcpServers"])
        dest.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        return [dest]
    if dest.exists() and not merge:
        frag = dest.with_name(dest.name + ".baltor-fragment")
        frag.write_bytes(payload[src_name])
        print(f"{dest} exists; wrote {frag.name} to merge by hand (or rerun with --merge for .mcp.json)")
        return [frag]
    dest.write_bytes(payload[src_name])
    return [dest]


def _lock_path(step_dir: Path) -> Path:
    return Path(step_dir) / ".baltor" / "step.lock.json"


def _lock_add(step_dir: Path, e: dict, written: list[Path], harness: str) -> None:
    lp = _lock_path(step_dir)
    lock = json.loads(lp.read_text()) if lp.exists() else {
        "spec": "baltor.step-lock/v1", "release": load_index()["release"], "harness": harness, "items": []}
    lock["items"] = [i for i in lock["items"] if i["identity"] != e["identity"]]
    lock["items"].append({
        "identity": e["identity"], "version": e["version"], "kind": e["kind"], "digest": e["digest"],
        "licence": e["licence"],
        "placed": [{"path": p.relative_to(step_dir).as_posix(), "sha256": sha256_bytes(p.read_bytes())}
                   for p in written],
    })
    lock["items"].sort(key=lambda i: i["identity"])
    lp.parent.mkdir(parents=True, exist_ok=True)
    lp.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")


def verify_lock(step_dir: Path) -> list[str]:
    lp = _lock_path(step_dir)
    if not lp.exists():
        return [f"{lp} not found"]
    lock = json.loads(lp.read_text())
    problems = [f"lock: {m}" for m in _check_schema(lock, "step-lock.schema.json")]
    for item in lock["items"]:
        for placed in item["placed"]:
            p = Path(step_dir) / placed["path"]
            if not p.exists():
                problems.append(f"{item['identity']}: {placed['path']} is missing")
            elif item["kind"] != "instruction-file" and sha256_bytes(p.read_bytes()) != placed["sha256"]:
                problems.append(f"{item['identity']}: {placed['path']} changed since it was placed")
    return problems


# --------------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("paths", nargs="*", type=Path)
    v.add_argument("--strict", action="store_true", help="treat warnings as errors")
    v.add_argument("--deep", action="store_true", help="also run node --check on JavaScript")
    v.add_argument("--quiet", action="store_true")
    v.add_argument("--generator", help="only packages whose provenance.generator is this path, e.g. generators/video_styles.py")
    b = sub.add_parser("build")
    b.add_argument("--date")
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--kind")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--variants", action="store_true")
    r = sub.add_parser("read")
    r.add_argument("identity")
    r.add_argument("--digest")
    r.add_argument("--out", type=Path)
    pl = sub.add_parser("place")
    pl.add_argument("identity")
    pl.add_argument("step_dir", type=Path)
    pl.add_argument("--harness", default="claude-code")
    pl.add_argument("--merge", action="store_true")
    lk = sub.add_parser("lock")
    lk.add_argument("step_dir", type=Path)
    sub.add_parser("stats")
    a = ap.parse_args(argv)

    if a.cmd == "validate":
        report, ok = validate(a.paths or None, deep=a.deep, generator=a.generator)
        feed_errors = validate_feeds() if not (a.paths or a.generator) else []
        report.errors += feed_errors
        if not a.quiet:
            for w in report.warnings[:300]:
                print("WARN ", w)
        for e in report.errors[:500]:
            print("ERROR", e)
        print(f"{len(ok)} package(s), {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
        return 1 if report.errors or (a.strict and report.warnings) else 0
    if a.cmd == "build":
        build(a.date)
        return 0
    if a.cmd == "search":
        for hit in search(a.query, a.kind, a.limit, a.variants):
            print(f"{hit['score']:>7}  {hit['identity']}  {hit['kind']}"
                  f"{'/' + hit['subkind'] if hit['subkind'] else ''} · {hit['licence']} · {hit['size']} B · "
                  f"sha256 {hit['digest'][:8]}…\n         {hit['summary']}")
        return 0
    if a.cmd == "read":
        data = read_package(a.identity, a.digest)
        if a.out:
            for rel, blob in data["files"].items():
                dest = a.out / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(blob)
            print(f"wrote {len(data['files'])} file(s) to {a.out}; digest {data['entry']['digest']}")
        else:
            e = data["entry"]
            print(json.dumps({k: e[k] for k in ("identity", "version", "kind", "licence", "digest", "files")}, indent=2))
        return 0
    if a.cmd == "place":
        for p in place(a.identity, a.step_dir, a.harness, a.merge):
            print("placed", p)
        return 0
    if a.cmd == "lock":
        problems = verify_lock(a.step_dir)
        for p in problems:
            print("PROBLEM", p)
        print("lock verified" if not problems else f"{len(problems)} problem(s)")
        return 1 if problems else 0
    if a.cmd == "stats":
        print(json.dumps(catalog_stats(load_index()["packages"]), indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
