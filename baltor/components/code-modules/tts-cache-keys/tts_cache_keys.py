"""Content-addressed cache for synthesized speech.

The key is the SHA-256 of canonical JSON describing everything that changes
the audio: engine name and version, model file digest, voice, speed, sample
rate and the exact text after normalisation. Files live at
``<root>/<k[:2]>/<k>.wav`` and are written atomically (temporary file +
``os.replace``), so an interrupted render never leaves a half-written clip
that a later run would reuse.

Usage::

    from tts_cache_keys import TTSCache
    cache = TTSCache(".cache/tts")
    path = cache.get_or_create({"engine": "kokoro-onnx", "voice": "af_heart", "speed": 1.0, "text": line},
                               lambda tmp_path: engine_write_wav(tmp_path))
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

REQUIRED = ("engine", "voice", "text")


def cache_key(params: dict) -> str:
    missing = [k for k in REQUIRED if k not in params]
    if missing:
        raise ValueError(f"cache key needs {missing}")
    canonical = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def file_digest(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


class TTSCache:
    def __init__(self, root: str, suffix: str = ".wav"):
        self.root = Path(root)
        self.suffix = suffix

    def path_for(self, params: dict) -> Path:
        k = cache_key(params)
        return self.root / k[:2] / f"{k}{self.suffix}"

    def get(self, params: dict) -> Path | None:
        p = self.path_for(params)
        return p if p.exists() and p.stat().st_size > 0 else None

    def get_or_create(self, params: dict, create) -> Path:
        """``create(tmp_path)`` must write the audio file at tmp_path."""
        hit = self.get(params)
        if hit:
            return hit
        dest = self.path_for(params)
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=dest.parent, suffix=self.suffix + ".part")
        os.close(fd)
        try:
            create(tmp)
            if os.path.getsize(tmp) == 0:
                raise RuntimeError("creator wrote an empty file")
            os.replace(tmp, dest)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        return dest

    def prune_partials(self) -> int:
        n = 0
        for p in self.root.rglob(f"*{self.suffix}.part"):
            p.unlink()
            n += 1
        return n
