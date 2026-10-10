#!/usr/bin/env python3
"""Build an agent_feed_watchlist from what a repository actually uses (standard library only).

Reads, without executing anything:

* Python: ``requirements*.txt`` / ``requirements/*.txt`` / ``*.in`` (follows ``-r`` includes),
  ``pyproject.toml`` (PEP 621 dependencies and optional dependencies, PEP 735 dependency groups,
  Poetry and uv tables, ``requires-python``)
* Node: ``package.json`` (dependencies, dev, peer, optional; ``engines.node``; ``packageManager``)
* Rust: ``Cargo.toml`` (dependencies, dev/build, workspace; ``rust-version``)
* Go: ``go.mod`` (``require`` lines and blocks, ``go`` and ``toolchain``)
* Containers: ``Dockerfile`` / ``Containerfile`` ``FROM`` lines (``ARG`` defaults substituted, build
  stages skipped) and ``image:`` lines in compose files
* MCP and harness config: ``.mcp.json`` (Claude Code), ``.codex/config.toml`` (Codex),
  ``opencode.json`` (OpenCode), ``.gemini/settings.json`` (Gemini CLI), ``.cursor/mcp.json`` (Cursor);
  ``.claude/`` or ``CLAUDE.md`` marks Claude Code, ``.pi/`` marks Pi. MCP servers launched with
  npx/bunx/uvx/pipx/docker are added as packages so their advisories match too.

Vendors, products and topics are inferred from a small table of well-known SDKs. Hand edits survive
regeneration with ``--merge`` (topics, excluded topics, vendors, products, min_severity, change_types,
include_prereleases, min_score are kept).

CLI::

    python3 agent_feeds_watchlist_from_repo.py [REPO] --out .baltor/feeds/watchlist.json --merge
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["build_watchlist", "merge_manual", "parse_requirements", "parse_pyproject", "parse_package_json",
           "parse_cargo", "parse_go_mod", "parse_dockerfile", "parse_compose", "parse_mcp_config", "SPEC"]

SPEC = "baltor.agent-feed-watchlist/v1"
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "env", "dist", "build", "target", "vendor", "__pycache__",
             ".tox", ".nox", "site-packages", ".mypy_cache", ".pytest_cache", ".next", ".turbo", "coverage", ".baltor"}
MAX_DEPTH = 4
MAX_FILES = 400

# package (lower-case) -> (vendor, product, topics)
KNOWN = {
    "anthropic": ("Anthropic", "anthropic-sdk", ["llm"]),
    "@anthropic-ai/sdk": ("Anthropic", "anthropic-sdk", ["llm"]),
    "claude-agent-sdk": ("Anthropic", "claude-agent-sdk", ["agents", "llm"]),
    "@anthropic-ai/claude-agent-sdk": ("Anthropic", "claude-agent-sdk", ["agents", "llm"]),
    "@anthropic-ai/claude-code": ("Anthropic", "claude-code", ["agents"]),
    "openai": ("OpenAI", "openai-sdk", ["llm"]),
    "openai-agents": ("OpenAI", "openai-agents", ["agents", "llm"]),
    "@openai/agents": ("OpenAI", "openai-agents", ["agents", "llm"]),
    "@openai/codex": ("OpenAI", "codex", ["agents"]),
    "google-genai": ("Google", "gemini-api", ["llm"]),
    "@google/genai": ("Google", "gemini-api", ["llm"]),
    "google-generativeai": ("Google", "gemini-api", ["llm"]),
    "mistralai": ("Mistral AI", "mistral-api", ["llm"]),
    "cohere": ("Cohere", "cohere-api", ["llm"]),
    "groq": ("Groq", "groq-api", ["llm"]),
    "ollama": ("Ollama", "ollama", ["llm", "local-llm"]),
    "litellm": ("BerriAI", "litellm", ["llm"]),
    "langchain": ("LangChain", "langchain", ["agents", "llm"]),
    "langgraph": ("LangChain", "langgraph", ["agents"]),
    "llama-index": ("LlamaIndex", "llama-index", ["rag", "llm"]),
    "transformers": ("Hugging Face", "transformers", ["ml"]),
    "huggingface-hub": ("Hugging Face", "huggingface-hub", ["ml"]),
    "mcp": ("Model Context Protocol", "mcp-python-sdk", ["mcp"]),
    "fastmcp": ("Model Context Protocol", "fastmcp", ["mcp"]),
    "@modelcontextprotocol/sdk": ("Model Context Protocol", "mcp-typescript-sdk", ["mcp"]),
    "boto3": ("AWS", "aws-sdk", ["cloud"]),
    "stripe": ("Stripe", "stripe-api", ["payments"]),
    "twilio": ("Twilio", "twilio-api", ["messaging"]),
    "supabase": ("Supabase", "supabase", ["database"]),
    "elevenlabs": ("ElevenLabs", "elevenlabs-api", ["tts"]),
    "kokoro": (None, "kokoro-tts", ["tts"]),
    "kokoro-onnx": (None, "kokoro-tts", ["tts"]),
    "piper-tts": (None, "piper-tts", ["tts"]),
    "openai-whisper": ("OpenAI", "whisper", ["speech-to-text"]),
    "faster-whisper": (None, "faster-whisper", ["speech-to-text"]),
    "moviepy": (None, "moviepy", ["video"]),
    "ffmpeg-python": (None, "ffmpeg", ["video"]),
    "opencv-python": (None, "opencv", ["video", "computer-vision"]),
    "yt-dlp": (None, "yt-dlp", ["video"]),
    "google-api-python-client": ("Google", "google-apis", ["cloud"]),
    "playwright": ("Microsoft", "playwright", ["browser-automation"]),
    "@playwright/test": ("Microsoft", "playwright", ["browser-automation"]),
    "next": ("Vercel", "next.js", ["web"]),
    "react": ("Meta", "react", ["web"]),
    "django": (None, "django", ["web"]),
    "fastapi": (None, "fastapi", ["web"]),
}
KNOWN_PREFIX = [("@aws-sdk/", ("AWS", "aws-sdk", ["cloud"])), ("google-cloud-", ("Google Cloud", "google-cloud", ["cloud"])),
                ("@google-cloud/", ("Google Cloud", "google-cloud", ["cloud"])), ("azure-", ("Microsoft Azure", "azure-sdk", ["cloud"])),
                ("@azure/", ("Microsoft Azure", "azure-sdk", ["cloud"])), ("langchain-", ("LangChain", "langchain", ["agents", "llm"])),
                ("@langchain/", ("LangChain", "langchain", ["agents", "llm"])), ("llama-index-", ("LlamaIndex", "llama-index", ["rag"])),
                ("@modelcontextprotocol/server-", ("Model Context Protocol", None, ["mcp"])), ("mcp-server-", (None, None, ["mcp"]))]
RUNTIME_IMAGES = {"python": "python", "node": "node", "golang": "go", "rust": "rust", "ruby": "ruby", "php": "php",
                  "openjdk": "java", "eclipse-temurin": "java", "denoland/deno": "deno", "oven/bun": "bun"}


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _pin(spec: str | None) -> str | None:
    if not spec:
        return None
    m = re.fullmatch(r"\s*(?:===?|=)?\s*v?([0-9][\w.+-]*)\s*", spec)
    if m and "*" not in spec and (spec.strip().startswith(("==", "=")) or re.fullmatch(r"v?[0-9][\w.+-]*", spec.strip())):
        return m.group(1)
    return None


def _pkg(eco: str, name: str, spec: str | None, src: str, dev: bool = False, pinned: str | None = "auto") -> dict:
    spec = (spec or "").strip() or None
    return {"ecosystem": eco, "name": name.strip(), "version": spec,
            "pinned": _pin(spec) if pinned == "auto" else pinned, "dev": dev, "source_file": src}


# --------------------------------------------------------------------------- Python

_REQ = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*(\[[^\]]*\])?\s*(\(?[^;@]*\)?)?\s*(@\s*\S+)?\s*(;.*)?$")


def parse_pep508(line: str) -> tuple[str, str | None] | None:
    m = _REQ.match(line.strip())
    if not m:
        return None
    spec = (m.group(3) or "").strip().strip("()").replace(" ", "") or None
    if m.group(4):  # direct URL reference
        spec = None
    return m.group(1), spec


def parse_requirements(path: Path, root: Path, dev: bool = False, _seen: set | None = None) -> list[dict]:
    seen = _seen if _seen is not None else set()
    if path in seen or not path.is_file():
        return []
    seen.add(path)
    out: list[dict] = []
    src = _rel(path, root)
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = re.sub(r"(^|\s)#.*$", "", raw).strip()
        if not line:
            continue
        inc = re.match(r"^(-r|--requirement|-c|--constraint)\s*=?\s*(\S+)", line)
        if inc:
            out += parse_requirements((path.parent / inc.group(2)).resolve(), root, dev, seen)
            continue
        if line.startswith("-") or "://" in line.split(";")[0] and "@" not in line:
            continue
        parsed = parse_pep508(line)
        if parsed:
            out.append(_pkg("PyPI", parsed[0], parsed[1], src, dev))
    return out


def parse_pyproject(path: Path, root: Path) -> tuple[list[dict], dict]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    src = _rel(path, root)
    pkgs: list[dict] = []
    meta: dict = {}
    project = data.get("project") or {}
    if project.get("name"):
        meta["name"] = project["name"]
    if project.get("requires-python"):
        meta["python"] = project["requires-python"]
    for dep in project.get("dependencies") or []:
        p = parse_pep508(dep)
        if p:
            pkgs.append(_pkg("PyPI", p[0], p[1], src))
    for group in (project.get("optional-dependencies") or {}).values():
        for dep in group:
            p = parse_pep508(dep)
            if p:
                pkgs.append(_pkg("PyPI", p[0], p[1], src, dev=True))
    for group in (data.get("dependency-groups") or {}).values():
        for dep in group:
            if isinstance(dep, str):
                p = parse_pep508(dep)
                if p:
                    pkgs.append(_pkg("PyPI", p[0], p[1], src, dev=True))
    for dep in ((data.get("tool") or {}).get("uv") or {}).get("dev-dependencies") or []:
        p = parse_pep508(dep)
        if p:
            pkgs.append(_pkg("PyPI", p[0], p[1], src, dev=True))
    poetry = (data.get("tool") or {}).get("poetry") or {}
    if poetry.get("name") and "name" not in meta:
        meta["name"] = poetry["name"]
    tables = [(poetry.get("dependencies") or {}, False), (poetry.get("dev-dependencies") or {}, True)]
    tables += [((g or {}).get("dependencies") or {}, True) for g in (poetry.get("group") or {}).values()]
    for table, dev in tables:
        for name, val in table.items():
            spec = val if isinstance(val, str) else (val or {}).get("version")
            if name.lower() == "python":
                meta.setdefault("python", spec)
                continue
            if isinstance(val, dict) and ("path" in val or "git" in val) and not val.get("version"):
                continue
            pkgs.append(_pkg("PyPI", name, spec if spec != "*" else None, src, dev))
    return pkgs, meta


# --------------------------------------------------------------------------- Node / Rust / Go

def parse_package_json(path: Path, root: Path) -> tuple[list[dict], dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return [], {}
    src = _rel(path, root)
    pkgs = []
    for key, dev in (("dependencies", False), ("devDependencies", True), ("peerDependencies", False),
                     ("optionalDependencies", False)):
        for name, spec in (data.get(key) or {}).items():
            if not isinstance(spec, str):
                continue
            if spec.startswith("npm:"):  # alias: "x": "npm:real-name@^1.0"
                real, _, spec = spec[4:].rpartition("@")
                name = real or name
            pkgs.append(_pkg("npm", name, spec, src, dev))
    meta = {"name": data.get("name")} if data.get("name") else {}
    if (data.get("engines") or {}).get("node"):
        meta["node"] = data["engines"]["node"]
    if isinstance(data.get("packageManager"), str):
        meta["package_manager"] = data["packageManager"]
    return pkgs, meta


def parse_cargo(path: Path, root: Path) -> tuple[list[dict], dict]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    src = _rel(path, root)
    pkgs = []
    tables = [(data.get("dependencies") or {}, False), (data.get("dev-dependencies") or {}, True),
              (data.get("build-dependencies") or {}, True),
              (((data.get("workspace") or {}).get("dependencies")) or {}, False)]
    for table, dev in tables:
        for name, val in table.items():
            if isinstance(val, str):
                spec = val
            else:
                if (val or {}).get("workspace") or ("path" in (val or {}) and not val.get("version")) or \
                        ("git" in (val or {}) and not val.get("version")):
                    continue
                spec = (val or {}).get("version")
                name = (val or {}).get("package", name)
            pkgs.append(_pkg("crates.io", name, spec, src, dev, pinned=_pin(spec) if spec and spec.startswith("=") else None))
    pkg = data.get("package") or {}
    meta = {"name": pkg.get("name")} if pkg.get("name") else {}
    if isinstance(pkg.get("rust-version"), str):
        meta["rust"] = pkg["rust-version"]
    return pkgs, meta


def parse_go_mod(path: Path, root: Path) -> tuple[list[dict], dict]:
    src = _rel(path, root)
    pkgs, meta = [], {}
    in_block = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        if line.startswith("module "):
            meta["name"] = line.split()[1]
        elif line.startswith("go "):
            meta["go"] = line.split()[1]
        elif line.startswith("toolchain "):
            meta["toolchain"] = line.split()[1]
        elif line.startswith("require ("):
            in_block = True
        elif in_block and line == ")":
            in_block = False
        elif in_block or line.startswith("require "):
            parts = line.replace("require ", "", 1).split()
            if len(parts) >= 2:
                pkgs.append(_pkg("Go", parts[0], parts[1], src, pinned=parts[1].lstrip("v")))
    return pkgs, meta


# --------------------------------------------------------------------------- containers

def _image(ref: str, src: str) -> dict | None:
    ref = ref.strip().strip("'\"")
    if not ref or ref == "scratch" or "$" in ref:
        return None
    ref = ref.split("@", 1)[0]
    name, tag = (ref.rsplit(":", 1) + ["latest"])[:2] if ":" in ref.split("/")[-1] else (ref, "latest")
    for prefix in ("docker.io/library/", "docker.io/", "index.docker.io/library/"):
        if name.startswith(prefix):
            name = name[len(prefix):]
    return _pkg("Docker", name, tag, src, pinned=tag if tag != "latest" else None)


def parse_dockerfile(path: Path, root: Path) -> list[dict]:
    src = _rel(path, root)
    args: dict[str, str] = {}
    stages: set[str] = set()
    out = []
    text = re.sub(r"\\\r?\n", " ", path.read_text(encoding="utf-8", errors="replace"))
    for raw in text.splitlines():
        line = raw.strip()
        m = re.match(r"(?i)^ARG\s+([A-Za-z_][\w]*)=(\S+)", line)
        if m:
            args[m.group(1)] = m.group(2).strip("'\"")
            continue
        m = re.match(r"(?i)^FROM\s+(?:--platform=\S+\s+)?(\S+)(?:\s+AS\s+(\S+))?", line)
        if not m:
            continue
        ref = re.sub(r"\$\{?([A-Za-z_]\w*)(?::-([^}]*))?\}?", lambda x: args.get(x.group(1), x.group(2) or x.group(0)),
                     m.group(1))
        if m.group(2):
            stages.add(m.group(2).lower())
        if ref.lower() in stages:
            continue
        img = _image(ref, src)
        if img:
            out.append(img)
    return out


def parse_compose(path: Path, root: Path) -> list[dict]:
    src = _rel(path, root)
    out = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^\s*image:\s*(\S+)", raw)
        if m:
            img = _image(m.group(1), src)
            if img:
                out.append(img)
    return out


# --------------------------------------------------------------------------- MCP and harness config

_VALUE_FLAGS = {"-e", "--env", "-v", "--volume", "--name", "--network", "-p", "--publish", "--mount", "-w", "--workdir",
                "--entrypoint", "--platform", "-u", "--user", "--from", "--with", "--python", "--index-url"}


def _launch_package(command: str, args: list) -> tuple[str | None, str | None, str | None]:
    """(ecosystem, package, version) for servers started by npx/bunx/pnpm dlx/uvx/pipx/docker."""
    cmd = Path(str(command or "")).name.lower()
    args = [str(a) for a in args or []]
    if cmd in ("pnpm", "yarn") and args and args[0] == "dlx":
        cmd, args = "npx", args[1:]
    if cmd in ("pipx", "uv") and args and args[0] in ("run", "tool"):
        args = args[1:] if args[0] == "run" else args[2:]
        cmd = "uvx"
    eco = {"npx": "npm", "bunx": "npm", "uvx": "PyPI", "docker": "Docker", "podman": "Docker"}.get(cmd)
    if not eco:
        return None, None, None
    if eco == "Docker":
        if not args or args[0] != "run":
            return None, None, None
        args = args[1:]
    skip = False
    for a in args:
        if skip:
            skip = False
            continue
        if a in _VALUE_FLAGS:
            skip = True
            continue
        if a.startswith("-"):
            continue
        if eco == "Docker":
            img = _image(a, "")
            return ("Docker", img["name"], img["version"]) if img else (None, None, None)
        if eco == "npm":
            m = re.fullmatch(r"(@?[^@]+)(?:@(.+))?", a)
        else:
            m = re.fullmatch(r"([A-Za-z0-9][\w.-]*)(?:(?:==|@)(.+))?", a)
        if m:
            return eco, m.group(1), m.group(2)
        return None, None, None
    return None, None, None


def _servers_to_entries(servers: dict, harness: str, src: str) -> tuple[list[dict], list[dict]]:
    entries, pkgs = [], []
    for name, srv in (servers or {}).items():
        if not isinstance(srv, dict):
            continue
        command = srv.get("command")
        args = srv.get("args") or []
        if isinstance(command, list):  # opencode: "command": ["npx", "-y", "pkg"]
            command, args = (command[0] if command else ""), command[1:]
        eco, package, version = _launch_package(command, args)
        entry = {"name": name, "package": package, "ecosystem": eco, "url": srv.get("url") or srv.get("httpUrl"),
                 "harness": harness, "source_file": src}
        entries.append(entry)
        if package:
            pkgs.append(_pkg(eco, package, version, src))
    return entries, pkgs


def parse_mcp_config(path: Path, root: Path, harness: str) -> tuple[list[dict], list[dict]]:
    src = _rel(path, root)
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".toml":
        data = tomllib.loads(text)
        return _servers_to_entries(data.get("mcp_servers") or {}, harness, src)
    text = re.sub(r"^\s*//.*$", "", text, flags=re.M)  # opencode.jsonc line comments
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return [], []
    servers = data.get("mcpServers") or data.get("mcp") or data.get("servers") or {}
    return _servers_to_entries(servers, harness, src)


# --------------------------------------------------------------------------- walk and assemble

def _walk(root: Path):
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).relative_to(root).parts)
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not (d.startswith(".") and d not in
                             (".codex", ".claude", ".gemini", ".cursor", ".pi", ".opencode", ".github", ".devcontainer")))
        if depth >= MAX_DEPTH:
            dirnames[:] = []
        for fn in sorted(filenames):
            count += 1
            if count > MAX_FILES * 50:
                return
            yield Path(dirpath) / fn


def _known(name: str):
    n = name.lower()
    if n in KNOWN:
        return KNOWN[n]
    n = re.sub(r"[_.]+", "-", n)
    if n in KNOWN:
        return KNOWN[n]
    for prefix, val in KNOWN_PREFIX:
        if n.startswith(prefix):
            return val
    return None


def _runtime_version(spec: str | None) -> str | None:
    if not spec:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", spec)
    return m.group(1) if m else spec


def build_watchlist(repo: str | os.PathLike = ".", *, project: str | None = None, now: str | None = None) -> dict:
    root = Path(repo).resolve()
    packages: list[dict] = []
    runtimes: list[dict] = []
    mcp: list[dict] = []
    harnesses: set[str] = set()
    names: list[str] = []
    seen_req: set = set()
    for path in _walk(root):
        rel = _rel(path, root)
        fn = path.name
        low = fn.lower()
        try:
            if (low.startswith("requirements") and low.endswith((".txt", ".in"))) or \
                    (path.parent.name == "requirements" and low.endswith((".txt", ".in"))):
                packages += parse_requirements(path, root, dev=any(t in low for t in ("dev", "test", "lint", "doc")), _seen=seen_req)
            elif fn == "pyproject.toml":
                pk, meta = parse_pyproject(path, root)
                packages += pk
                names.append(meta.get("name") or "")
                if meta.get("python"):
                    runtimes.append({"name": "python", "version": meta["python"], "source_file": rel})
            elif fn == "package.json":
                pk, meta = parse_package_json(path, root)
                packages += pk
                names.append(meta.get("name") or "")
                if meta.get("node"):
                    runtimes.append({"name": "node", "version": meta["node"], "source_file": rel})
                if meta.get("package_manager"):
                    pm, _, ver = meta["package_manager"].partition("@")
                    runtimes.append({"name": pm, "version": ver.split("+")[0] or None, "source_file": rel})
            elif fn == "Cargo.toml":
                pk, meta = parse_cargo(path, root)
                packages += pk
                names.append(meta.get("name") or "")
                if meta.get("rust"):
                    runtimes.append({"name": "rust", "version": meta["rust"], "source_file": rel})
            elif fn == "go.mod":
                pk, meta = parse_go_mod(path, root)
                packages += pk
                names.append((meta.get("name") or "").rsplit("/", 1)[-1])
                if meta.get("go"):
                    runtimes.append({"name": "go", "version": meta["go"], "source_file": rel})
            elif fn in ("Dockerfile", "Containerfile") or low.endswith(".dockerfile") or low.startswith("dockerfile."):
                imgs = parse_dockerfile(path, root)
                packages += imgs
                for img in imgs:
                    rt = RUNTIME_IMAGES.get(img["name"])
                    if rt:
                        runtimes.append({"name": rt, "version": _runtime_version(img["version"]), "source_file": rel})
            elif re.fullmatch(r"(docker-)?compose(\.[\w-]+)?\.ya?ml", low):
                packages += parse_compose(path, root)
            elif rel == ".mcp.json":
                harnesses.add("claude-code")
                e, pk = parse_mcp_config(path, root, "claude-code")
                mcp += e
                packages += pk
            elif rel == ".codex/config.toml":
                harnesses.add("codex")
                e, pk = parse_mcp_config(path, root, "codex")
                mcp += e
                packages += pk
            elif rel in ("opencode.json", "opencode.jsonc", ".opencode/opencode.json"):
                harnesses.add("opencode")
                e, pk = parse_mcp_config(path, root, "opencode")
                mcp += e
                packages += pk
            elif rel == ".gemini/settings.json":
                harnesses.add("gemini-cli")
                e, pk = parse_mcp_config(path, root, "gemini-cli")
                mcp += e
                packages += pk
            elif rel == ".cursor/mcp.json":
                harnesses.add("cursor")
                e, pk = parse_mcp_config(path, root, "cursor")
                mcp += e
                packages += pk
            elif rel in ("CLAUDE.md", ".claude/settings.json", ".claude/settings.local.json"):
                harnesses.add("claude-code")
            elif rel.startswith(".pi/"):
                harnesses.add("pi")
        except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:  # one bad file never stops the scan
            print(f"warning: skipped {rel}: {exc}", file=sys.stderr)
    if (root / ".claude").is_dir():
        harnesses.add("claude-code")
    if (root / ".pi").is_dir():
        harnesses.add("pi")
    if (root / ".opencode").is_dir():
        harnesses.add("opencode")

    # dedupe packages: keep the most specific entry per (ecosystem, name); a runtime dependency wins over dev
    best: dict[tuple[str, str], dict] = {}
    for p in packages:
        key = (p["ecosystem"], re.sub(r"[-_.]+", "-", p["name"].lower()) if p["ecosystem"] == "PyPI" else p["name"].lower())
        cur = best.get(key)
        if cur is None or (cur["dev"] and not p["dev"]) or (not cur["pinned"] and p["pinned"]) or \
                (not cur["version"] and p["version"]):
            best[key] = p
    pkgs = sorted(best.values(), key=lambda p: (p["ecosystem"], p["name"].lower()))
    vendors, products, topics = set(), set(), set()
    for p in pkgs:
        k = _known(p["name"])
        if k:
            v, prod, tps = k
            if v:
                vendors.add(v)
            if prod:
                products.add(prod)
            topics.update(tps)
    for rt in runtimes:
        products.add(rt["name"])
    for p in pkgs:
        if p["ecosystem"] == "Docker":
            products.add(p["name"].rsplit("/", 1)[-1])
    for h in harnesses:
        products.add(h)
    if mcp:
        topics.add("mcp")
    rt_seen, rts = set(), []
    for rt in runtimes:
        key = (rt["name"], rt.get("version"))
        if key not in rt_seen:
            rt_seen.add(key)
            rts.append(rt)
    project = project or next((n for n in names if n), None) or root.name
    return {
        "spec": SPEC,
        "project": project,
        "generated": now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": ".",
        "ecosystems": sorted({p["ecosystem"] for p in pkgs}),
        "packages": pkgs,
        "runtimes": rts,
        "vendors": sorted(vendors),
        "products": sorted(products),
        "mcp_servers": mcp,
        "harnesses": sorted(harnesses),
        "topics": sorted(topics),
        "excluded_topics": [],
        "min_severity": "medium",
        "include_prereleases": False,
        "min_score": 30,
    }


MANUAL_KEYS = ("excluded_topics", "min_severity", "change_types", "include_prereleases", "min_score")


def merge_manual(new: dict, old: dict) -> dict:
    """Keep hand-maintained fields from an existing watchlist."""
    out = dict(new)
    for key in MANUAL_KEYS:
        if key in old:
            out[key] = old[key]
    for key in ("topics", "vendors", "products"):
        out[key] = sorted(set(new.get(key) or []) | set(old.get(key) or []))
    if old.get("project"):
        out["project"] = old["project"]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build an Agent Feeds watchlist from a repository's manifests.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--out", help="write here (default: print)")
    ap.add_argument("--merge", action="store_true", help="keep hand edits from an existing --out file")
    ap.add_argument("--project")
    a = ap.parse_args(argv)
    wl = build_watchlist(a.repo, project=a.project)
    if a.out:
        out = Path(a.out)
        if a.merge and out.exists():
            wl = merge_manual(wl, json.loads(out.read_text(encoding="utf-8")))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(wl, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {out}: {len(wl['packages'])} packages, {len(wl['mcp_servers'])} MCP servers, "
              f"harnesses {', '.join(wl['harnesses']) or 'none'}")
    else:
        json.dump(wl, sys.stdout, indent=2, ensure_ascii=False)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
