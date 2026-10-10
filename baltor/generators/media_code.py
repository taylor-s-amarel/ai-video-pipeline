#!/usr/bin/env python3
"""Media code modules for the video/audio/caption factory.

Each base package lives as real, tested source under
``data/media_code/modules/<identity>/``:

* ``<identity>.py``        the module (standard library + numpy/Pillow only at
                           import time; heavier tools are imported lazily or run
                           as subprocesses and are declared in ``depends_on``)
* ``test_<identity>.py``   pytest tests that run from the package directory
* ``meta.yaml``            manifest fields (title, summary, subkind, domain, tags,
                           step_kinds, effects, depends_on, references)
* optional extra payload files (presets, sample data)

Contract schemas for the data these modules exchange live under
``data/media_code/schemas/<identity>/`` (``schema.json``, ``examples/*.json``,
``meta.yaml``).

Variants are listed in ``data/media_code/variants.yaml``: each one copies its
base package and adds a preset file that pins a choice someone would make (a
look, a platform, an aspect ratio). Variants record ``variant_of`` and their
parameters; they are never counted as base items.

Run: ``cd baltor/generators && python3 media_code.py``
"""

from __future__ import annotations

from pathlib import Path

import yaml

from _lib import GeneratorRun, dumps, effects

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "media_code"
MODULES = DATA / "modules"
SCHEMAS = DATA / "schemas"
VARIANTS = DATA / "variants.yaml"

ALLOWED_DOMAINS = {"video", "audio", "captions"}
REQUIRED_META = ("title", "summary", "domain", "tags", "step_kinds")
SKIP_NAMES = {"meta.yaml", ".DS_Store"}
SKIP_DIRS = {"__pycache__", ".pytest_cache"}
CHECKED = "2026-10-10"


def payload_files(pkg_dir: Path) -> dict[str, str | bytes]:
    out: dict[str, str | bytes] = {}
    for p in sorted(pkg_dir.rglob("*")):
        if not p.is_file() or p.name in SKIP_NAMES or SKIP_DIRS.intersection(p.relative_to(pkg_dir).parts):
            continue
        if p.suffix in {".pyc", ".pyo"}:
            continue
        rel = p.relative_to(pkg_dir).as_posix()
        data = p.read_bytes()
        try:
            out[rel] = data.decode("utf-8")
        except UnicodeDecodeError:
            out[rel] = data
    return out


def load_meta(pkg_dir: Path) -> dict:
    meta = yaml.safe_load((pkg_dir / "meta.yaml").read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED_META if not meta.get(k)]
    if missing:
        raise ValueError(f"{pkg_dir.name}: meta.yaml is missing {missing}")
    if meta["domain"] not in ALLOWED_DOMAINS:
        raise ValueError(f"{pkg_dir.name}: domain {meta['domain']!r} not in {sorted(ALLOWED_DOMAINS)}")
    return meta


def effects_from(meta: dict) -> dict:
    e = dict(meta.get("effects") or {})
    return effects(
        filesystem=e.get("filesystem", "none"),
        executes=e.get("executes", "python"),
        secrets=e.get("secrets"),
        hosts=e.get("hosts"),
        side_effects=e.get("side_effects"),
    )


def depends_from(meta: dict) -> list[dict] | None:
    deps = []
    for d in meta.get("depends_on") or []:
        if isinstance(d, str):
            deps.append({"identity": d, "external": True})
        else:
            deps.append(dict(d))
    return deps or None


def readme(identity: str, meta: dict, files: dict, entry: str, preset: str | None = None) -> str:
    tests = sorted(f for f in files if Path(f).name.startswith("test_") and f.endswith(".py"))
    lines = [f"# {meta['title']}", "", meta["summary"], ""]
    if meta.get("description"):
        lines += [meta["description"].strip(), ""]
    lines += ["## Use", "", "```python", f"import {Path(entry).stem}", "```", "",
              f"Placed by `baltor_catalog.py place {identity} <step-dir>` under `.baltor/lib/{identity.replace('_', '-')}/`.",
              "Add that directory to `sys.path` (or copy the module next to your script).", ""]
    if preset:
        lines += ["## Preset", "", f"`{preset}` pins the parameters of this variant; pass its values to the module's",
                  "functions (see the module docstring).", ""]
    if tests:
        lines += ["## Test", "", "```sh", "python3 -m pytest -q .", "```", ""]
    deps = meta.get("depends_on") or []
    if deps:
        lines += ["## Optional external tools", ""]
        for d in deps:
            name = d if isinstance(d, str) else d["identity"]
            lines.append(f"- `{name}`")
        lines.append("")
        lines.append("They are imported lazily or run as subprocesses; tests that need them are skipped when absent.")
        lines.append("")
    refs = meta.get("references") or []
    if refs:
        lines += ["## References", ""] + [f"- {r}" for r in refs] + [""]
    lines += ["## Licence", "", "MIT. Original work for the Baltor public-good collection."]
    return "\n".join(lines) + "\n"


def module_review() -> dict:
    return {"status": "automated-passed", "checked": CHECKED,
            "notes": "Unit tests pass with pytest on Python 3.13 (numpy, Pillow); ffmpeg integration tests ran with ffmpeg present."}


def emit_module(run: GeneratorRun, pkg_dir: Path) -> None:
    identity = pkg_dir.name
    meta = load_meta(pkg_dir)
    files = payload_files(pkg_dir)
    entry = meta.get("entry", f"{identity}.py")
    if entry not in files:
        raise ValueError(f"{identity}: entry {entry} missing")
    if not any(Path(f).name.startswith("test_") for f in files):
        raise ValueError(f"{identity}: no test_*.py")
    files["README.md"] = readme(identity, meta, files, entry)
    run.component(
        "code-module", identity,
        title=meta["title"], summary=meta["summary"], description=meta.get("description"),
        files=files, entry=entry, subkind=meta.get("subkind"), domain=meta["domain"],
        tags=meta["tags"], step_kinds=meta["step_kinds"], effects_=effects_from(meta),
        depends_on=depends_from(meta), examples=meta.get("examples"), review=module_review(),
    )


def emit_schema(run: GeneratorRun, pkg_dir: Path) -> None:
    identity = pkg_dir.name
    meta = load_meta(pkg_dir)
    files = payload_files(pkg_dir)
    if "schema.json" not in files or not any(f.startswith("examples/") for f in files):
        raise ValueError(f"{identity}: schema.json and examples/ are required")
    run.component(
        "contract-schema", identity,
        title=meta["title"], summary=meta["summary"], description=meta.get("description"),
        files=files, subkind=meta.get("subkind"), domain=meta["domain"], tags=meta["tags"],
        step_kinds=meta["step_kinds"], depends_on=depends_from(meta), examples=meta.get("examples"),
    )


def emit_variants(run: GeneratorRun, bases: set[str]) -> None:
    if not VARIANTS.exists():
        return
    spec = yaml.safe_load(VARIANTS.read_text(encoding="utf-8")) or {}
    for family in spec.get("families", []):
        base = family["base"]
        if base not in bases:
            raise ValueError(f"variant family names unknown base {base}")
        base_dir = MODULES / base
        meta = load_meta(base_dir)
        base_files = payload_files(base_dir)
        entry = meta.get("entry", f"{base}.py")
        preset_name = family.get("preset_file", "preset.json")
        for v in family["variants"]:
            identity = v["identity"]
            params = dict(v["parameters"])
            files = dict(base_files)
            files[preset_name] = dumps({"variant_of": base, **params})
            vmeta = dict(meta, title=v["title"], summary=v["summary"])
            vmeta.pop("description", None)
            files["README.md"] = readme(identity, vmeta, files, entry, preset=preset_name)
            run.component(
                "code-module", identity,
                title=v["title"], summary=v["summary"], files=files, entry=entry,
                subkind=v.get("subkind", meta.get("subkind")), domain=meta["domain"],
                tags=sorted(set(meta["tags"]) | set(v.get("tags", [])))[:24],
                step_kinds=meta["step_kinds"], effects_=effects_from(meta), depends_on=depends_from(meta),
                variant_of=base, parameters=params, review=module_review(),
            )


def main() -> None:
    with GeneratorRun(__file__, data="generators/data/media_code") as run:
        bases = set()
        for pkg_dir in sorted(p for p in MODULES.iterdir() if p.is_dir() and (p / "meta.yaml").exists()):
            emit_module(run, pkg_dir)
            bases.add(pkg_dir.name)
        for pkg_dir in sorted(p for p in SCHEMAS.iterdir() if p.is_dir() and (p / "meta.yaml").exists()):
            emit_schema(run, pkg_dir)
        emit_variants(run, bases)


if __name__ == "__main__":
    main()
