"""Write a render manifest: exactly what went into a video and what came out.

The manifest records every input file with its SHA-256 and size, the tool
versions, the render parameters and the outputs with their digests, so a
render can be reproduced, audited for licences, and never resent by mistake
as "new" work (compare output digests with earlier manifests).

Usage::

    from render_manifest_writer import build_manifest, write_manifest, find_duplicates
    m = build_manifest("sylvia-earle-v3", inputs={"photo": "a.jpg", "music": "m.mp3"},
                       outputs={"video": "out.mp4"}, params={"fps": 30, "crf": 18},
                       tools={"ffmpeg": "6.1.1"}, credits=["Music: ... CC BY 4.0"])
    write_manifest(m, "out.manifest.json")
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

SCHEMA = "baltor.render-manifest/v1"


def sha256_file(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _entry(role: str, path: str) -> dict:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    return {"role": role, "path": p.as_posix(), "bytes": p.stat().st_size, "sha256": sha256_file(path)}


def build_manifest(job_id: str, inputs: dict, outputs: dict, params: dict | None = None, tools: dict | None = None,
                   credits: list[str] | None = None, created: str | None = None, notes: str | None = None) -> dict:
    if not job_id or any(c.isspace() for c in job_id):
        raise ValueError("job_id must be a non-empty token without spaces")
    m = {
        "schema": SCHEMA,
        "job_id": job_id,
        "inputs": [_entry(role, path) for role, path in sorted(inputs.items())],
        "outputs": [_entry(role, path) for role, path in sorted(outputs.items())],
        "params": params or {},
        "tools": tools or {},
        "credits": credits or [],
    }
    if created:
        m["created"] = created
    if notes:
        m["notes"] = notes
    return m


def write_manifest(manifest: dict, path: str) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def verify(manifest: dict, base_dir: str = ".") -> list[str]:
    problems = []
    for e in manifest["inputs"] + manifest["outputs"]:
        p = Path(base_dir) / e["path"]
        if not p.is_file():
            problems.append(f"missing {e['role']}: {e['path']}")
        elif sha256_file(str(p)) != e["sha256"]:
            problems.append(f"changed {e['role']}: {e['path']}")
    return problems


def find_duplicates(manifests: list[dict]) -> list[tuple[str, str, str]]:
    """(sha256, first job, later job) for outputs that were delivered before under another job."""
    seen: dict[str, str] = {}
    dups = []
    for m in manifests:
        for o in m["outputs"]:
            if o["sha256"] in seen and seen[o["sha256"]] != m["job_id"]:
                dups.append((o["sha256"], seen[o["sha256"]], m["job_id"]))
            else:
                seen.setdefault(o["sha256"], m["job_id"])
    return dups
