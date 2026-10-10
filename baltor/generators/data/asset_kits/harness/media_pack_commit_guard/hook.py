#!/usr/bin/env python3
"""PreToolUse hook: refuse a `git commit` that stages media files with no licence record, or files that may not be redistributed.

Every staged media file (images, models, audio, fonts, animations) must appear in an agent media pack
manifest in the repository (``pack.json``, ``pack.lock.json`` or ``*.media-pack.json``), matched by
``file_name`` or ``sha256``. Files whose manifest entry says ``redistribution: forbidden`` or
``project-only`` (Mixamo downloads, BlenderKit Royalty Free, Fab, ShareTextures ...) are blocked
outright: keep them in a git-ignored folder and commit only the manifest.

Claude Code passes the tool call as JSON on stdin; exit code 2 blocks the call and shows stderr.
Original artwork passes once it has a manifest entry (licence: your own, redistribution: allowed); manifests
that are staged or untracked in the same commit count. Set MEDIA_GUARD_OFF=1 to bypass deliberately.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

MEDIA_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".psd", ".kra", ".aseprite",
    ".glb", ".gltf", ".fbx", ".obj", ".blend", ".dae", ".vox", ".bvh", ".lwo",
    ".hdr", ".exr", ".wav", ".ogg", ".mp3", ".flac", ".ttf", ".otf", ".woff2",
    ".riv", ".lottie", ".mp4", ".mov", ".webm",
}
MANIFEST_NAMES = re.compile(r"(^|/)(pack\.json|pack\.lock\.json|[^/]+\.media-pack\.json)$")
BLOCKED = {"forbidden", "project-only"}


def staged_files(root: Path) -> list[str]:
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=AM", "-z"],
                         cwd=root, capture_output=True, text=True).stdout
    return [p for p in out.split("\0") if p]


def load_manifests(root: Path) -> list[dict]:
    listed = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=root,
                            capture_output=True, text=True).stdout.split("\0")
    manifests = []
    for rel in listed:
        if rel and MANIFEST_NAMES.search(rel):
            try:
                data = json.loads((root / rel).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict) and data.get("spec") == "baltor.media-pack/v1":
                manifests.append(data)
    return manifests


def index(manifests: list[dict]) -> tuple[dict, dict]:
    by_name, by_hash = {}, {}
    for m in manifests:
        for a in m.get("assets", []):
            if a.get("file_name"):
                by_name.setdefault(a["file_name"], a)
            if a.get("sha256"):
                by_hash[a["sha256"]] = a
    return by_name, by_hash


def classify(staged: list[tuple[str, str | None]], manifests: list[dict]) -> list[str]:
    """``staged`` holds (path, sha256-or-None). Returns one problem string per offending file."""
    by_name, by_hash = index(manifests)
    problems = []
    for path, digest in staged:
        if Path(path).suffix.lower() not in MEDIA_SUFFIXES:
            continue
        entry = (by_hash.get(digest) if digest else None) or by_name.get(Path(path).name)
        if entry is None:
            problems.append(f"{path}: not listed in any media pack manifest (add source, licence and credit first)")
        elif entry.get("redistribution") in BLOCKED:
            problems.append(f"{path}: licence '{entry.get('licence')}' does not allow redistributing the file "
                            f"(redistribution: {entry.get('redistribution')}); keep it out of git")
    return problems


def main() -> int:
    if os.environ.get("MEDIA_GUARD_OFF") == "1":
        return 0
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (event.get("tool_input") or {}).get("command", "")
    if not re.search(r"\bgit\b[^|;&]*\bcommit\b", command):
        return 0
    root = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or ".")
    staged = []
    for rel in staged_files(root):
        p = root / rel
        digest = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        staged.append((rel, digest))
    problems = classify(staged, load_manifests(root))
    if problems:
        print("Blocked: staged media without a usable licence record:\n  " + "\n  ".join(problems[:20]), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
