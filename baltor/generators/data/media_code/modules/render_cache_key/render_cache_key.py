"""Deterministic cache keys for render steps, so unchanged work is reused.

A render step's key is the SHA-256 of canonical JSON containing the step
name, its parameters, the content digests of its input files and the keys
of the steps it depends on. Change any input byte or parameter and the key
changes; touch nothing and it stays the same, so cached intermediate clips
(narration, background loops, grid layers) can be reused safely.

Usage::

    from render_cache_key import step_key, Plan
    k_bg = step_key("background", {"style": "waves", "seconds": 64}, inputs=["bg.mp4"])
    k_final = step_key("compose", {"crf": 18}, deps=[k_bg, k_voice])
    plan = Plan(".cache/render"); plan.is_fresh(k_final, "out/final.mp4")
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def file_digest(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def step_key(step: str, params: dict | None = None, inputs: list[str] | None = None,
             deps: list[str] | None = None, version: str = "1") -> str:
    payload = {
        "step": step,
        "version": version,
        "params": params or {},
        "inputs": sorted((Path(p).name, file_digest(p)) for p in (inputs or [])),
        "deps": sorted(deps or []),
    }
    try:
        text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"params must be plain JSON values: {exc}") from exc
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Plan:
    """Remembers which key produced which output file."""

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _stamp(self, output: str) -> Path:
        return self.root / (hashlib.sha256(os.path.abspath(output).encode()).hexdigest()[:16] + ".json")

    def is_fresh(self, key: str, output: str) -> bool:
        st = self._stamp(output)
        if not (Path(output).is_file() and st.is_file()):
            return False
        rec = json.loads(st.read_text())
        return rec.get("key") == key and rec.get("digest") == file_digest(output)

    def record(self, key: str, output: str) -> None:
        self._stamp(output).write_text(json.dumps({"key": key, "output": output, "digest": file_digest(output)}))
