#!/usr/bin/env python3
"""Logged gateway between the Baltor arm of a showcase and a Baltor catalogue.

The Baltor arm reaches the catalogue only through this gateway, so every search,
read and placement is written to a JSON Lines log that the runner copies into
the run record (identities, versions and digests downloaded). The baseline arm
never gets the gateway.

Three ways in:

* CLI shim, put on PATH as ``baltor`` for ``catalogue_access.mode = search-read``::

      baltor search "deduplicate contacts" [--kind skill] [--limit 10]
      baltor read IDENTITY [--digest SHA256] [--out DIR]
      baltor place IDENTITY [--harness claude-code]

* stdio MCP server for ``mode = mcp``, serving the same two tools as the hosted
  service, ``intelligence_search`` and ``provisioning_read``::

      python3 showcase_catalogue_gateway.py mcp --log calls.jsonl --catalog-tool baltor/tools/baltor_catalog.py --workspace WS

* ``write-shim BIN_DIR`` writes the ``baltor`` shim with the log, tool and workspace baked in.

The catalogue tool is any Python file exposing ``search(query, kind, limit)``,
``read_package(identity, expected_digest)`` and ``place(identity, step_dir, harness)``
(``baltor/tools/baltor_catalog.py`` does). It is loaded from ``--catalog-tool``
or the ``BALTOR_CATALOG_TOOL`` environment variable. The log path comes from
``--log`` or ``SHOWCASE_CATALOGUE_LOG``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import shlex
import stat
import sys
from pathlib import Path

VERSION = "1.0.0"
PROTOCOL_VERSION = "2025-06-18"
MAX_INLINE_FILE = 64 * 1024
MAX_INLINE_TOTAL = 256 * 1024

TOOLS = [
    {
        "name": "intelligence_search",
        "description": "Search the Baltor catalogue. Returns small references: identity, kind, version, licence, size, "
                       "digest and a one-line summary. Read an item with provisioning_read.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What the step needs, in plain words."},
                "kind": {"type": "string", "description": "Optional kind filter, e.g. skill, code-module, subagent."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "provisioning_read",
        "description": "Download one exact catalogue item by identity. The digest is checked. With out_dir the files are "
                       "written there (relative to the workspace); without it, text files are returned inline.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identity": {"type": "string"},
                "expected_digest": {"type": "string", "description": "Optional SHA-256 (or prefix) from search."},
                "out_dir": {"type": "string", "description": "Optional directory inside the workspace."},
            },
            "required": ["identity"],
        },
    },
]


class GatewayError(Exception):
    pass


def load_catalog_tool(path: str | os.PathLike | None):
    path = path or os.environ.get("BALTOR_CATALOG_TOOL")
    if not path:
        raise GatewayError("no catalogue tool: pass --catalog-tool or set BALTOR_CATALOG_TOOL")
    path = Path(path).resolve()
    if not path.exists():
        raise GatewayError(f"catalogue tool not found: {path}")
    spec = importlib.util.spec_from_file_location(f"_baltor_catalog_{abs(hash(str(path)))}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    for name in ("search", "read_package"):
        if not hasattr(mod, name):
            raise GatewayError(f"{path} has no {name}()")
    return mod


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _inside(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


class Gateway:
    def __init__(self, tool, log_path: str | os.PathLike | None, workspace: str | os.PathLike | None = None,
                 harness: str = "claude-code"):
        self.tool = tool
        self.log_path = Path(log_path) if log_path else None
        self.workspace = Path(workspace).resolve() if workspace else None
        self.harness = harness

    # ------------------------------------------------------------------ logging
    def _log(self, entry: dict) -> None:
        entry = {"at": _now(), **entry, "source": "gateway-log"}
        if self.log_path is None:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def release(self) -> str | None:
        try:
            return self.tool.load_index().get("release")
        except BaseException:  # noqa: BLE001 - SystemExit when no index
            return None

    # ------------------------------------------------------------------ operations
    def search(self, query: str, kind: str | None = None, limit: int = 10) -> list[dict]:
        limit = max(1, min(int(limit or 10), 50))
        try:
            hits = self.tool.search(query, kind, limit)
        except SystemExit as exc:
            self._log({"op": "search", "query": query, "kind": kind, "ok": False, "error": str(exc)})
            raise GatewayError(str(exc)) from None
        self._log({"op": "search", "query": query, "kind": kind, "ok": True,
                   "results": [f"{h['identity']}@{h.get('version', '?')}" for h in hits]})
        return hits

    def read(self, identity: str, expected_digest: str | None = None, out_dir: str | None = None) -> dict:
        try:
            data = self.tool.read_package(identity, expected_digest)
        except SystemExit as exc:
            self._log({"op": "read", "identity": identity, "ok": False, "error": str(exc)})
            raise GatewayError(str(exc)) from None
        e = data["entry"]
        result: dict = {"identity": e["identity"], "version": e["version"], "kind": e["kind"],
                        "licence": e.get("licence"), "digest": e["digest"], "entry": e.get("entry"),
                        "files": sorted(data["files"])}
        if out_dir is not None:
            dest = Path(out_dir)
            if self.workspace is not None:
                dest = dest if dest.is_absolute() else self.workspace / dest
                if not _inside(self.workspace, dest):
                    self._log({"op": "read", "identity": identity, "ok": False, "error": "out_dir outside workspace"})
                    raise GatewayError("out_dir must be inside the workspace")
            for rel, blob in data["files"].items():
                p = dest / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(blob)
            result["written_to"] = str(dest)
        else:
            inline, total = {}, 0
            for rel, blob in sorted(data["files"].items()):
                if len(blob) > MAX_INLINE_FILE or total + len(blob) > MAX_INLINE_TOTAL:
                    continue
                try:
                    inline[rel] = blob.decode("utf-8")
                    total += len(blob)
                except UnicodeDecodeError:
                    continue
            result["content"] = inline
            result["omitted"] = sorted(set(data["files"]) - set(inline))
        self._log({"op": "read", "identity": e["identity"], "version": e["version"], "digest": e["digest"], "ok": True})
        return result

    def place(self, identity: str, harness: str | None = None) -> list[str]:
        if self.workspace is None:
            raise GatewayError("place needs a workspace")
        if not hasattr(self.tool, "place"):
            raise GatewayError("catalogue tool has no place()")
        try:
            written = self.tool.place(identity, self.workspace, harness or self.harness)
            e = self.tool.read_package(identity)["entry"]
        except SystemExit as exc:
            self._log({"op": "place", "identity": identity, "ok": False, "error": str(exc)})
            raise GatewayError(str(exc)) from None
        self._log({"op": "place", "identity": e["identity"], "version": e["version"], "digest": e["digest"], "ok": True})
        return [str(Path(p)) for p in written]


# ---------------------------------------------------------------------- log parsing (used by the runner)

def read_log(path: str | os.PathLike) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def downloaded_items(calls: list[dict]) -> list[dict]:
    """Unique identity/version/digest for successful read and place calls, in first-seen order."""
    seen, out = set(), []
    for c in calls:
        if c.get("op") in {"read", "place"} and c.get("ok") and c.get("identity"):
            key = (c["identity"], c.get("version"), c.get("digest"))
            if key not in seen:
                seen.add(key)
                out.append({"identity": c["identity"], "version": c.get("version") or "?",
                            "digest": c.get("digest") or "?"})
    return out


# ---------------------------------------------------------------------- MCP server

def _tool_result(payload, is_error: bool = False) -> dict:
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2, ensure_ascii=False)
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def handle_message(gw: Gateway, msg: dict) -> dict | None:
    method = msg.get("method")
    mid = msg.get("id")
    if mid is None:  # notification
        return None
    try:
        if method == "initialize":
            client = (msg.get("params") or {}).get("protocolVersion") or PROTOCOL_VERSION
            result = {"protocolVersion": client, "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": {"name": "baltor-showcase-gateway", "version": VERSION}}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = msg.get("params") or {}
            name, args = params.get("name"), params.get("arguments") or {}
            try:
                if name == "intelligence_search":
                    result = _tool_result({"results": gw.search(str(args.get("query", "")), args.get("kind"),
                                                                int(args.get("limit") or 10))})
                elif name == "provisioning_read":
                    result = _tool_result(gw.read(str(args.get("identity", "")), args.get("expected_digest"),
                                                  args.get("out_dir")))
                else:
                    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool {name}"}}
            except GatewayError as exc:
                result = _tool_result(str(exc), is_error=True)
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
    except Exception as exc:  # noqa: BLE001
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": str(exc)}}
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def serve_mcp(gw: Gateway, stdin=None, stdout=None) -> None:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            stdout.write(json.dumps({"jsonrpc": "2.0", "id": None,
                                     "error": {"code": -32700, "message": "parse error"}}) + "\n")
            stdout.flush()
            continue
        batch = msg if isinstance(msg, list) else [msg]
        for m in batch:
            resp = handle_message(gw, m)
            if resp is not None:
                stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                stdout.flush()


# ---------------------------------------------------------------------- shim + configs

def write_shim(bin_dir: str | os.PathLike, *, log: str, catalog_tool: str, workspace: str,
               harness: str = "claude-code", python: str | None = None) -> Path:
    bin_dir = Path(bin_dir)
    bin_dir.mkdir(parents=True, exist_ok=True)
    python = python or sys.executable
    args = [python, str(Path(__file__).resolve()), "cli", "--log", str(log), "--catalog-tool", str(catalog_tool),
            "--workspace", str(workspace), "--harness", harness]
    shim = bin_dir / "baltor"
    shim.write_text("#!/bin/sh\n# Baltor catalogue shim for a showcase trial; every call is logged.\nexec "
                    + " ".join(shlex.quote(a) for a in args) + ' "$@"\n', encoding="utf-8")
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return shim


def mcp_server_entry(*, log: str, catalog_tool: str, workspace: str, python: str | None = None) -> dict:
    return {"command": python or sys.executable,
            "args": [str(Path(__file__).resolve()), "mcp", "--log", str(log), "--catalog-tool", str(catalog_tool),
                     "--workspace", str(workspace)]}


# ---------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--log", default=os.environ.get("SHOWCASE_CATALOGUE_LOG"))
        p.add_argument("--catalog-tool", default=os.environ.get("BALTOR_CATALOG_TOOL"))
        p.add_argument("--workspace", default=os.environ.get("SHOWCASE_WORKSPACE"))
        p.add_argument("--harness", default="claude-code")

    cli = sub.add_parser("cli", help="the `baltor` shim: search | read | place")
    common(cli)
    csub = cli.add_subparsers(dest="op", required=True)
    s = csub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--kind")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--json", action="store_true")
    r = csub.add_parser("read")
    r.add_argument("identity")
    r.add_argument("--digest")
    r.add_argument("--out")
    pl = csub.add_parser("place")
    pl.add_argument("identity")
    pl.add_argument("--to-harness", dest="to_harness")
    m = sub.add_parser("mcp", help="serve intelligence_search and provisioning_read over stdio")
    common(m)
    w = sub.add_parser("write-shim", help="write the `baltor` shim into BIN_DIR")
    common(w)
    w.add_argument("bin_dir")
    a = ap.parse_args(argv)

    if a.cmd == "write-shim":
        if not (a.log and a.catalog_tool and a.workspace):
            ap.error("write-shim needs --log, --catalog-tool and --workspace")
        print(write_shim(a.bin_dir, log=a.log, catalog_tool=a.catalog_tool, workspace=a.workspace, harness=a.harness))
        return 0
    try:
        gw = Gateway(load_catalog_tool(a.catalog_tool), a.log, a.workspace, a.harness)
    except GatewayError as exc:
        print(f"baltor: {exc}", file=sys.stderr)
        return 2
    if a.cmd == "mcp":
        serve_mcp(gw)
        return 0
    try:
        if a.op == "search":
            hits = gw.search(a.query, a.kind, a.limit)
            if a.json:
                print(json.dumps(hits, indent=2))
            else:
                for h in hits:
                    sub_ = f"/{h['subkind']}" if h.get("subkind") else ""
                    print(f"{h['identity']}  {h['kind']}{sub_}  v{h['version']}  {h['licence']}  "
                          f"sha256 {h['digest'][:12]}\n    {h['summary']}")
                if not hits:
                    print("no results")
        elif a.op == "read":
            res = gw.read(a.identity, a.digest, a.out)
            if a.out:
                print(f"wrote {len(res['files'])} file(s) of {res['identity']}@{res['version']} to {res['written_to']}; "
                      f"digest {res['digest']}")
            else:
                print(json.dumps(res, indent=2, ensure_ascii=False))
        elif a.op == "place":
            for p in gw.place(a.identity, a.to_harness):
                print("placed", p)
    except GatewayError as exc:
        print(f"baltor: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
