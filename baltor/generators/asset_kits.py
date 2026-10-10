#!/usr/bin/env python3
"""2D/3D/animation asset kits, Godot asset packs and agent-ready media packs.

Data lives under ``data/asset_kits/``:

* ``feeds/assets-*.yaml``  source collections -> ``baltor/feeds/assets-*.json`` (validated)
* ``schemas/<identity>/``  contract schemas (schema.json); examples are built here
* ``sources/*.yaml``       one skill per asset source (SKILL.md + source.json)
* ``packs/catalog.yaml``   verified asset pointers; ``packs/packs.yaml`` starter packs
                           (skill + pack.json manifest + CREDITS.preview.md; never media files)
* ``modules/<identity>/``  tested Python code modules (module, test, meta.yaml, fixtures)
* ``harness/``             hook script and tests

Every URL in the data was verified on 2026-10-10 (fetched on GitHub, or confirmed in search
results); feed items record which. Run: ``cd baltor/generators && python3 asset_kits.py``
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import yaml

sys.dont_write_bytecode = True

from _lib import BALTOR_DIR, GeneratorRun, agent_md, command_md, dumps, effects, kebab, skill_md

try:
    import jsonschema
except ImportError:  # pragma: no cover - validation is skipped without jsonschema
    jsonschema = None

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "asset_kits"
FEEDS_OUT = BALTOR_DIR / "feeds"
FEED_PREFIX = "assets-"
CHECKED = "2026-10-10"
DOMAIN = "asset-pipeline"
SKIP_DIRS = {"__pycache__", ".pytest_cache"}
CC0_DEED = "https://creativecommons.org/publicdomain/zero/1.0/deed.en"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


FETCHER = _load_module("media_pack_fetcher", DATA / "modules/media_pack_fetcher/media_pack_fetcher.py")
CHECKER = _load_module("asset_licence_checker", DATA / "modules/asset_licence_checker/asset_licence_checker.py")
MANIFEST_SCHEMA = json.loads((DATA / "schemas/agent_media_pack_manifest/schema.json").read_text())
SOURCE_SCHEMA = json.loads((DATA / "schemas/asset_source_profile/schema.json").read_text())


def _validator(schema: dict):
    if jsonschema is None:
        return None
    return jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())


def _check(schema: dict, instance: dict, what: str) -> None:
    v = _validator(schema)
    if v is None:
        return
    errors = sorted(v.iter_errors(instance), key=lambda e: list(e.absolute_path))
    if errors:
        e = errors[0]
        raise ValueError(f"{what}: {'/'.join(map(str, e.absolute_path))}: {e.message}")


# --------------------------------------------------------------------------- feeds

def build_feeds() -> dict:
    schema = json.loads((BALTOR_DIR / "schemas/feed-collection.schema.json").read_text())
    written, stats = set(), {"collections": 0, "items": 0, "by_verification": {}}
    for src in sorted((DATA / "feeds").glob(f"{FEED_PREFIX}*.yaml")):
        raw = yaml.safe_load(src.read_text(encoding="utf-8"))
        defaults = raw.get("defaults", {})
        items, seen = [], set()
        for it in raw["items"]:
            item = {"id": it["id"], "title": it["title"], "url": it["url"], "summary": it["summary"].strip(),
                    "kind": it.get("kind", defaults.get("kind", "media-source")), "verified_on": CHECKED,
                    "verification": it.get("verification", defaults.get("verification", "search-result"))}
            lic = it.get("licence", defaults.get("licence"))
            if lic:
                item["licence"] = lic
            if it.get("licence_url"):
                item["licence_url"] = it["licence_url"]
            if it.get("tags"):
                item["tags"] = list(it["tags"])
            if it.get("notes"):
                item["notes"] = it["notes"]
            if it.get("cautions"):
                item["cautions"] = list(it["cautions"])
            if item["id"] in seen:
                raise ValueError(f"{src.name}: duplicate item id {item['id']}")
            seen.add(item["id"])
            items.append(item)
            stats["by_verification"][item["verification"]] = stats["by_verification"].get(item["verification"], 0) + 1
        col = {"spec": "baltor.feed-collection/v1", "id": raw["id"], "title": raw["title"],
               "description": " ".join(raw["description"].split()), "updated": CHECKED,
               "tags": list(raw.get("tags", [])), "items": items}
        if raw["id"] != src.stem or not raw["id"].startswith(FEED_PREFIX):
            raise ValueError(f"{src.name}: collection id must equal the file stem and start with {FEED_PREFIX}")
        _check(schema, col, f"feed {raw['id']}")
        out = FEEDS_OUT / f"{raw['id']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(dumps(col), encoding="utf-8")
        written.add(out.name)
        stats["collections"] += 1
        stats["items"] += len(items)
    for stale in FEEDS_OUT.glob(f"{FEED_PREFIX}*.json"):
        if stale.name not in written:
            stale.unlink()
    return stats


# --------------------------------------------------------------------------- catalogue -> manifest assets

KIND_DEFAULTS = {
    "cc0-kenney": {"creator": "Kenney", "licence": "CC0-1.0", "licence_url": "https://kenney.nl/support",
                   "credit": "{title} by Kenney (kenney.nl), CC0"},
    "cc0-quaternius": {"creator": "Quaternius", "licence": "CC0-1.0", "licence_url": "{source_url}",
                       "credit": "{title} by Quaternius (quaternius.com), CC0"},
    "cc0-kaykit": {"creator": "Kay Lousberg", "licence": "CC0-1.0", "licence_url": CC0_DEED,
                   "credit": "{title} by Kay Lousberg (KayKit), CC0",
                   "restrictions": ["Author asks: do not resell unmodified copies or claim them as your own."]},
    "cc0-itch": {"licence": "CC0-1.0", "licence_url": CC0_DEED, "credit": "{title} by {creator}, CC0"},
    "cc0-oga": {"licence": "CC0-1.0", "licence_url": "{source_url}", "credit": "{title} by {creator}, CC0"},
    "cc0-polyhaven": {"creator": "Poly Haven", "licence": "CC0-1.0", "licence_url": "https://docs.polyhaven.com/en/faq",
                      "credit": "{title} from Poly Haven (polyhaven.com), CC0", "method": "api"},
    "cc0-ambientcg": {"creator": "ambientCG", "licence": "CC0-1.0", "licence_url": "https://docs.ambientcg.com/license/",
                      "credit": "Materials from ambientCG.com, CC0", "method": "api"},
    "cc0-cgbookcase": {"creator": "cgbookcase", "licence": "CC0-1.0", "licence_url": "https://www.cgbookcase.com/",
                       "credit": "Textures from cgbookcase.com, CC0"},
    "cc0-github": {"licence": "CC0-1.0", "licence_url": "{source_url}", "credit": "{title} ({creator}), CC0"},
    "nasa": {"creator": "NASA", "licence": "Public domain statement (NASA) + NASA usage guidelines",
             "licence_url": "https://github.com/nasa/NASA-3D-Resources", "credit": "{title} 3D model, NASA 3D Resources",
             "restrictions": ["Do not use NASA insignia or imply NASA endorsement (NASA media usage guidelines)."]},
    "mit-github": {"licence": "MIT", "licence_url": "{source_url}", "credit": "{title} by {creator} (MIT)",
                   "redistribution": "allowed-with-licence"},
    "isc-github": {"licence": "ISC", "licence_url": "{source_url}", "credit": "{title} by {creator} (ISC)",
                   "redistribution": "allowed-with-licence"},
    "mit-cc0-github": {"licence": "MIT (code), CC0-1.0 (assets)", "licence_url": "{source_url}",
                       "credit": "{title} by {creator}: code MIT, assets CC0", "redistribution": "allowed-with-licence"},
    "ccby4-github": {"licence": "CC-BY-4.0", "licence_url": "https://creativecommons.org/licenses/by/4.0/deed.en",
                     "credit": "{title}, CC-BY 4.0", "required": True, "redistribution": "allowed-with-licence"},
    "ccby3-gameicons": {"licence": "CC-BY-3.0", "licence_url": "https://creativecommons.org/licenses/by/3.0/deed.en",
                        "credit": "Icon by {creator}. Available on https://game-icons.net (CC BY 3.0)", "required": True,
                        "redistribution": "allowed-with-licence"},
    "ofl-font": {"licence": "OFL-1.1", "credit": "Font: {title} by {creator} (SIL OFL 1.1)",
                 "redistribution": "allowed-with-licence"},
    "palette": {"licence": "No licence stated (credit the palette author)", "licence_url": "{source_url}",
                "credit": "Palette: {title} by {creator} (lospec.com)", "redistribution": "project-only"},
}
GODOT_HINTS = {
    "pixel": {"importer": "texture", "preset": "pixel-art-2d"},
    "pixel-off-2d": {"importer": "texture", "preset": "smooth-2d"},
    "smooth": {"importer": "texture", "preset": "smooth-2d"},
    "ui": {"importer": "texture", "preset": "ui-lossless"},
    "scene": {"importer": "scene"},
    "texture3d": {"importer": "texture", "preset": "texture-3d"},
}
FORMAT_ROLE_IMPORTER = {"ttf": "font", "wav": "audio", "ogg": "audio"}
GITHUB_HOSTS = ("https://github.com/", "https://raw.githubusercontent.com/")


def catalogue_asset(key: str, entry: dict, intended_use: list[str]) -> dict:
    kd = KIND_DEFAULTS[entry["kind"]]
    creator = entry.get("creator", kd.get("creator", ""))
    title = entry["title"]
    fmt = {"title": title, "creator": creator, "source_url": entry["source_url"]}
    licence_url = entry.get("licence_url") or kd.get("licence_url", "{source_url}").format(**fmt)
    credit = entry.get("credit") or kd["credit"].format(**fmt)
    asset = {"id": key, "title": title}
    if creator:
        asset["creator"] = creator
    asset["source_url"] = entry["source_url"]
    if entry.get("download_url"):
        asset["download_url"] = entry["download_url"]
    asset.update({
        "licence": kd["licence"], "licence_url": licence_url, "attribution": credit,
        "attribution_required": bool(kd.get("required", False)),
        "redistribution": kd.get("redistribution", "allowed"),
        "commercial_use": "allowed",
        "format": entry["format"],
    })
    restrictions = list(kd.get("restrictions", [])) + list(entry.get("restrictions", []))
    if entry.get("draco"):
        restrictions.append("GLB requires KHR_draco_mesh_compression and uses WebP textures (checked 2026-10-10).")
    if restrictions:
        asset["restrictions"] = restrictions
    if entry.get("file_name"):
        asset["file_name"] = entry["file_name"]
    if entry.get("sha256"):
        asset["sha256"] = entry["sha256"]
        asset["bytes"] = entry["bytes"]
    asset["intended_use"] = list(intended_use)
    method = entry.get("method") or ("direct" if entry.get("download_url") else kd.get("method", "manual-page"))
    status = "fetched" if entry.get("sha256") else "to-fetch"
    fetch = {"method": method, "status": status}
    if status == "fetched":
        fetch["fetched_on"] = CHECKED
    if entry.get("note"):
        fetch["notes"] = entry["note"]
    asset["fetch"] = fetch
    hints = {}
    if entry.get("godot"):
        hints["godot"] = dict(GODOT_HINTS[entry["godot"]])
    elif entry["format"] in FORMAT_ROLE_IMPORTER:
        hints["godot"] = {"importer": FORMAT_ROLE_IMPORTER[entry["format"]]}
    elif entry["format"] == "glb":
        hints["godot"] = {"importer": "scene"}
    if entry["format"] == "glb":
        hints["blender"] = {"operator": "bpy.ops.import_scene.gltf"}
    if entry.get("role"):
        hints["video"] = {"role": entry["role"]}
    elif entry.get("kind") == "ofl-font":
        hints["video"] = {"role": "font"}
    if hints:
        asset["import_hints"] = hints
    how = entry.get("how") or ("fetched" if entry["source_url"].startswith(GITHUB_HOSTS) else "search-result")
    asset["verification"] = {"on": CHECKED, "how": how}
    return asset


def pack_manifest(pack: dict, catalogue: dict) -> dict:
    assets = [catalogue_asset(k, catalogue[k], [", ".join(uses)]) for k, uses in pack["assets"].items()]
    status = "partially-fetched" if any(a["fetch"]["status"] == "fetched" for a in assets) else "manifest-only"
    m = {"spec": "baltor.media-pack/v1", "pack_id": kebab(pack["id"]), "title": pack["title"],
         "purpose": " ".join(pack["description"].split()), "status": status, "created": CHECKED,
         "verified_on": CHECKED, "targets": list(pack.get("targets", ["ffmpeg-video"])),
         "frame": pack.get("frame", {"width": 1080, "height": 1920, "fps": 30}),
         "licence_policy": {"allow_non_commercial": False, "allow_share_alike": False, "require_redistributable": False,
                            "notes": "Monetised-video policy: no NC or ND assets; credit every CC-BY asset in the description."},
         "credits_file": "CREDITS.md",
         "notes": ["Manifest only: no media files are included. Fetch direct assets with the media_pack_fetcher "
                   "module; open manual-page sources in a browser and record sha256 after download."],
         "assets": assets}
    _check(MANIFEST_SCHEMA, m, f"pack {pack['id']}")
    return m


# --------------------------------------------------------------------------- SKILL.md renderers

def _bullets(items) -> str:
    return "\n".join(f"- {x}" for x in items)


def source_profile(s: dict) -> dict:
    prof = {"spec": "baltor.asset-source/v1", "source_id": kebab(s["id"]), "name": s["name"], "homepage": s["homepage"],
            "licence_summary": " ".join(s["licence_summary"].split()), "licences": s["licences"],
            "attribution": s["attribution"], "redistribution": s["redistribution"], "commercial_use": s["commercial_use"],
            "ai_training": s.get("ai_training", "unspecified"), "automated_download": s["automated_download"],
            "formats": s.get("formats", []), "search": s.get("search", []), "cautions": s.get("cautions", []),
            "verified": {"on": CHECKED, "how": "mixed"}}
    if s.get("api"):
        prof["api"] = s["api"]
    _check(SOURCE_SCHEMA, prof, f"source {s['id']}")
    return prof


def source_skill_body(s: dict) -> str:
    example = copy.deepcopy(s["example_asset"])
    example.setdefault("verification", {"on": CHECKED, "how": "manual"})
    wrapper = {"spec": "baltor.media-pack/v1", "pack_id": "example-pack", "title": "Example", "purpose": "Schema check for the example entry.",
               "status": "manifest-only", "assets": [example]}
    if example["fetch"]["status"] == "fetched":
        wrapper["status"] = "partially-fetched"
    _check(MANIFEST_SCHEMA, wrapper, f"example asset of {s['id']}")
    links = "\n".join(f"- [{x['label']}]({x['url']})" for x in s.get("search", []))
    licences = "\n".join(f"- `{l['id']}`: {l.get('applies_to', '')} - <{l['url']}>" for l in s["licences"])
    api = ""
    if s.get("api"):
        api = f"\n## API\n\n<{s['api']['url']}> (auth: {s['api'].get('auth', 'none')}). {s['api'].get('notes', '')}\n"
    credit = s["attribution"].get("credit_template") or "No credit line needed."
    credit_intro = {
        "required": "Required. Fill in the braces from each asset page and use the line verbatim:",
        "per-asset": "Depends on each asset's licence. When the asset requires credit, use:",
        "optional": "Not required (CC0 or equivalent). A courtesy credit, if you give one:",
        "never": "Not required by the terms. If you mention the source, keep it to:",
    }[s["attribution"]["required"]]
    return f"""
# {s['name']}

{" ".join(s['description'].split())}

Checked on {CHECKED}. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

{" ".join(s['licence_summary'].split())}

{licences}

Attribution: **{s['attribution']['required']}**. Redistribution of the files: **{s['redistribution']}**.
Commercial use: **{s['commercial_use']}**. Automated downloading: **{s['automated_download']}**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

{credit_intro}

```
{credit}
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

{links}
{api}
## How to search

{s['search_howto'].strip()}

## Import into Godot 4

{s['godot'].strip()}

## Import into Blender

{s['blender'].strip()}

## Pitfalls

{_bullets(list(s.get('cautions', [])) + list(s.get('pitfalls', [])))}

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{json.dumps(example, indent=2)}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
"""


def pack_skill_body(pack: dict, manifest: dict, findings: list) -> str:
    rows = []
    for a in manifest["assets"]:
        hashed = "yes" if a.get("sha256") else "no"
        rows.append(f"| `{a['id']}` | [{a['title']}]({a['source_url']}) | {a['licence']} | "
                    f"{'required' if a['attribution_required'] else 'optional'} | {a['redistribution']} | "
                    f"{a['fetch']['method']} | {hashed} | {'; '.join(a['intended_use'])} |")
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]
    check_line = (f"`asset_licence_checker --use monetised-video` on {CHECKED}: {len(errors)} error(s), "
                  f"{len(warnings)} warning(s).")
    if warnings:
        check_line += "\n\n" + _bullets(f"{w.asset_id}: {w.message}" for w in warnings)
    excluded = _bullets(pack.get("excluded") or ["Nothing specific beyond the house licence rules."])
    variant = ""
    if pack.get("variant_of"):
        variant = f"\nVariant of `{pack['variant_of']}`: same purpose, different asset family and camera.\n"
    return f"""
# {pack['title']}

{" ".join(pack['description'].split())}
{variant}
**This is a manifest, not a download.** `pack.json` lists where each asset lives, its licence, its exact credit
line and how to import it. No media files are included in this package.

## Assets

| id | source | licence | credit | redistribution | fetch | sha256 recorded | use |
|----|--------|---------|--------|----------------|-------|-----------------|-----|
{chr(10).join(rows)}

## Fetch and credit

```bash
python3 media_pack_fetcher.py pack.json --out assets/{manifest['pack_id']} --dry-run   # see the plan
python3 media_pack_fetcher.py pack.json --out assets/{manifest['pack_id']}             # direct assets only
python3 asset_licence_checker.py assets/{manifest['pack_id']}/pack.lock.json --use monetised-video
```

`manual-page` and `api` assets are opened by hand (or through the source's API skill); after downloading,
record `file_name`, `sha256` and `bytes` in the manifest. `CREDITS.preview.md` shows the credits file the
fetcher will write.

## Licence check

{check_line}

## Look and style

{pack['style'].strip()}

## Assemble

{pack['assemble'].strip()}

## Do not use

{excluded}
"""


# --------------------------------------------------------------------------- harness texts

RULES_MD = """
# Third-party asset rules

1. Every third-party file has a manifest entry before it is used: source page, licence, licence URL, exact
   credit line, redistribution status. Check: `asset_licence_checker pack.json --use <profile>` exits 0.
2. Packages and repositories hold manifests, never third-party media. Check: the media-pack commit guard hook.
3. No NonCommercial (-NC) asset in a monetised video, client work or the paid catalogue.
4. No NoDerivatives (-ND) asset is recoloured, re-rigged, cropped into a new model or otherwise modified.
5. Mixamo, BlenderKit Royalty Free, Fab, store EULA and ShareTextures files are project-only: rendered into the
   work, never committed, uploaded or bundled; never used as ML training data where the terms forbid it.
6. CC-BY / CC-BY-SA / OGA-BY / GPL assets get their credit line in the video description or end card and in CREDITS.md.
7. Share-alike assets that you modify stay under the same licence and are kept apart from differently licensed packages.
8. CC-BY 3.0, CC-BY-SA and GPL art is not shipped on DRM-locked platforms; use CC0 or OGA-BY there.
9. Downloads are automated only where the source allows it (APIs, GitHub raw files); sites that forbid automated
   downloads (ShareTextures) are fetched by hand.
10. Every downloaded file has a SHA-256 in the lock file; a hash mismatch stops the build.
11. Trademarks, logos, insignia and recognisable people are not cleared by CC0 or public-domain status.
12. Fair use is never recorded as a licence.
"""

RULES_JSON = {
    "forbid_in_monetised": ["NC"], "forbid_when_modified": ["ND"],
    "project_only_licences": ["Adobe Mixamo terms", "BlenderKit Royalty Free", "Fab Standard License",
                              "ShareTextures custom", "Store EULA"],
    "attribution_licences": ["CC-BY-*", "CC-BY-SA-*", "OGA-BY-*", "GPL-*"],
    "no_drm_licences": ["CC-BY-3.0", "CC-BY-SA-*", "GPL-*"],
    "require_sha256_after_fetch": True,
    "automated_download_forbidden": ["sharetextures.com"],
    "use_profiles": sorted(CHECKER.PROFILES),
}

AUDITOR_MD = """
You audit the media a project uses before anything is rendered, committed or published.

1. Find every media pack manifest (`pack.json`, `pack.lock.json`, `*.media-pack.json`) and every media file
   (images, models, audio, fonts, Lottie/Rive) in the working tree.
2. For each media file, find its manifest entry by file name or SHA-256 (`sha256sum file`). A file with no entry
   is a FAIL: report its path and ask for source, licence and credit, or replace it with a CC0 asset.
3. Run `python3 asset_licence_checker.py <manifest> --use <profile>` with the profile that matches the
   project (monetised-video, client-work, open-source-repo, baltor-package, drm-platform-game, ai-training).
4. Open the licence URL of anything marked custom, per-asset or unrecognised and read the actual terms. Never
   label anything "fair use OK".
5. Check `CREDITS.md` (or the video description draft) contains every required credit line verbatim.
6. Check that no project-only or forbidden-redistribution files (Mixamo, Royalty Free, Fab, ShareTextures) are
   tracked by git: `git ls-files` must not list them.
7. Report a table: file, source, licence, credit present (yes/no), redistribution ok (yes/no), verdict, fix.
   Say "not checked" for anything you did not verify yourself.
"""

ASSET_PACK_CMD = """
Build an agent media pack manifest for: $ARGUMENTS

1. Decide the look (2D pixel, flat vector, low-poly 3D, photoreal HDRI) and the delivery (1080x1920 video, Godot 4 scene, Blender render).
2. Start from the closest starter-pack skill (stick-figure, low-poly diorama, top-down maze, platformer, isometric town,
   space/NASA, nature backgrounds, UI/caption, farm diorama, this-vs-that, history, animal crowd) and its `pack.json`.
3. Add or swap assets only from sources whose source skill lists a licence you can meet. Prefer CC0; record CC-BY credits.
4. Write `pack.json` that validates against the `agent_media_pack_manifest` schema: one entry per asset with source_url,
   licence, licence_url, exact attribution, redistribution, format, intended_use, fetch method and import hints.
5. Run `python3 asset_licence_checker.py pack.json --use monetised-video` and fix every error.
6. Run `python3 media_pack_fetcher.py pack.json --out assets/<pack> --dry-run`, then without --dry-run; download
   manual-page assets by hand and record their sha256.
7. Commit the manifest, lock file and CREDITS.md - never project-only files.
"""

CREDIT_CMD = """
Refresh credits and licence checks for the media pack(s): $ARGUMENTS (default: every pack.json in the repo)

1. For each manifest, recompute `sha256` of every fetched file on disk and compare with the lock file; report mismatches.
2. Run `python3 asset_licence_checker.py <manifest> --use monetised-video` (or the profile the project states).
3. Regenerate CREDITS.md with `media_pack_fetcher.credits_markdown` (`python3 -c` or the fetcher's lock step).
4. Produce the description credit block: every attribution-required line verbatim, then "Other assets: CC0 (Kenney, Quaternius, ...)".
5. List anything still `to-fetch` or `manual` so the next step knows what is missing.
"""

INSTRUCTIONS_MD = """
## Asset sourcing step

- Use assets only through a media pack manifest (`agent_media_pack_manifest`): source page, licence, licence URL,
  exact credit line, redistribution status, SHA-256 once downloaded. No manifest entry, no use.
- Prefer CC0 sources (Kenney, Quaternius, KayKit free tiers, Poly Haven, ambientCG, NASA 3D Resources); CC-BY is fine
  for videos when the credit line is in the description. Never NC/ND assets in monetised work.
- Mixamo, Royalty Free marketplace and Fab files are project-only: keep them in a git-ignored folder.
- Download automatically only from APIs and GitHub raw URLs (the fetcher's allow-list); fetch other sites by hand.
- Inspect every model with `gltf_glb_inspector` (Draco, scale, triangles) and set Godot import presets with
  `godot_texture_import_presets` before opening the editor.
- Report what you verified and how; write "not checked" for anything you did not check.
"""


# --------------------------------------------------------------------------- components

def payload_files(pkg_dir: Path, skip: set[str] = frozenset({"meta.yaml"})) -> dict[str, str | bytes]:
    out: dict[str, str | bytes] = {}
    for p in sorted(pkg_dir.rglob("*")):
        rel_parts = p.relative_to(pkg_dir).parts
        if not p.is_file() or p.name in skip or SKIP_DIRS.intersection(rel_parts) or p.suffix in {".pyc", ".pyo"}:
            continue
        data = p.read_bytes()
        try:
            out[p.relative_to(pkg_dir).as_posix()] = data.decode("utf-8")
        except UnicodeDecodeError:
            out[p.relative_to(pkg_dir).as_posix()] = data
    return out


def deps_from(meta: dict) -> list[dict]:
    return [dict(d) for d in meta.get("depends_on", [])]


def main() -> None:
    feed_stats = build_feeds()
    catalogue = yaml.safe_load((DATA / "packs/catalog.yaml").read_text(encoding="utf-8"))
    packs = yaml.safe_load((DATA / "packs/packs.yaml").read_text(encoding="utf-8"))
    sources = []
    for f in sorted((DATA / "sources").glob("*.yaml")):
        sources += yaml.safe_load(f.read_text(encoding="utf-8"))

    with GeneratorRun(__file__, data="generators/data/asset_kits") as run:
        # 1. contract schemas -------------------------------------------------------------
        space = next(p for p in packs if p["id"] == "space_nasa_kit")
        valid_space = pack_manifest(space, catalogue)
        mixamo_example = {
            "spec": "baltor.media-pack/v1", "pack_id": "hero-run-cycle", "title": "Hero run cycle (project-only files)",
            "purpose": "Shows how a Mixamo download is recorded: usable in the render, never committed or redistributed.",
            "status": "manifest-only", "created": CHECKED, "targets": ["godot-4", "ffmpeg-video"],
            "assets": [{
                "id": "mixamo-running", "title": "Running", "creator": "Adobe Mixamo", "source_url": "https://www.mixamo.com/",
                "licence": "Adobe Mixamo terms", "licence_url": "https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html",
                "attribution": "", "attribution_required": False, "redistribution": "forbidden", "commercial_use": "allowed",
                "ai_training": "forbidden", "restrictions": ["Keep the FBX in a git-ignored folder.", "Not for ML training."],
                "format": "fbx", "intended_use": ["run cycle for the hero"], "fetch": {"method": "manual-page", "status": "manual"},
                "import_hints": {"godot": {"importer": "scene", "notes": "BoneMap + SkeletonProfileHumanoid"},
                                 "blender": {"operator": "bpy.ops.import_scene.fbx"}},
                "verification": {"on": CHECKED, "how": "search-result"}}]}
        _check(MANIFEST_SCHEMA, mixamo_example, "mixamo example")
        bad_credit = copy.deepcopy(mixamo_example)
        bad_credit["assets"][0].update({"id": "icon", "licence": "CC-BY-3.0", "attribution": "", "attribution_required": False,
                                        "redistribution": "allowed-with-licence", "format": "svg"})
        bad_hash = copy.deepcopy(valid_space)
        bad_hash["assets"][0].pop("sha256")
        bad_direct = copy.deepcopy(mixamo_example)
        bad_direct["assets"][0]["fetch"] = {"method": "direct", "status": "to-fetch"}
        bad_direct["assets"][0]["download_url"] = "https://raw.githubusercontent.com/example/repo/main/Running.fbx"
        run.component(
            "contract-schema", "agent_media_pack_manifest",
            title="Agent media pack manifest",
            summary="JSON Schema for an agent-ready media pack: assets with source URL, licence, licence URL, exact credit, redistribution, sha256 once fetched, format and Godot/Blender/video import hints.",
            description="Manifests point at sources and never contain media. Rules enforced by the schema: CC-BY/OGA-BY "
                        "entries must require attribution and carry a credit line; fetched entries need sha256, bytes and "
                        "file_name; direct fetches need an https download_url; assets whose redistribution is forbidden "
                        "cannot be fetched directly. The space/NASA example records real SHA-256 values measured on 2026-10-10.",
            subkind="rights-manifest", domain=DOMAIN,
            files={"schema.json": dumps(MANIFEST_SCHEMA),
                   "examples/space-nasa-kit.json": dumps(valid_space),
                   "examples/mixamo-project-only.json": dumps(mixamo_example),
                   "examples/invalid-cc-by-without-credit.json": dumps(bad_credit),
                   "examples/invalid-fetched-without-sha256.json": dumps(bad_hash),
                   "examples/invalid-forbidden-direct-download.json": dumps(bad_direct)},
            tags=["assets", "licensing", "manifest", "schema", "credits", "godot", "blender"],
            step_kinds=["plan", "build", "verify", "secure"],
        )
        profiles = {s["id"]: source_profile(s) for s in sources}
        bad_profile = copy.deepcopy(profiles["game_icons_net"])
        bad_profile["attribution"] = {"required": "required"}
        run.component(
            "contract-schema", "asset_source_profile",
            title="Asset source licence profile",
            summary="JSON Schema for a machine-readable profile of one asset source: licences, attribution rule and credit template, redistribution, commercial use, AI training and automated-download policy.",
            subkind="rights-manifest", domain=DOMAIN,
            files={"schema.json": dumps(SOURCE_SCHEMA),
                   "examples/kenney.json": dumps(profiles["kenney_assets_cc0"]),
                   "examples/mixamo.json": dumps(profiles["mixamo_characters_and_animations"]),
                   "examples/cc0-texture-sites.json": dumps(profiles["cc0_texture_sites"]),
                   "examples/invalid-required-credit-without-template.json": dumps(bad_profile)},
            tags=["assets", "licensing", "schema", "sources"],
            step_kinds=["research", "verify"],
        )

        # 2. one skill per source ---------------------------------------------------------
        for s in sources:
            run.component(
                "skill", s["id"], title=s["name"], summary=s["summary"], subkind="media-source", domain=DOMAIN,
                description=" ".join(s["description"].split()),
                files={"SKILL.md": skill_md(kebab(s["id"]), " ".join(s["description"].split()), source_skill_body(s)),
                       "source.json": dumps(profiles[s["id"]])},
                tags=list(dict.fromkeys(["assets", "licensing"] + s["tags"]))[:24],
                step_kinds=["research", "build", "verify"],
                depends_on=[{"identity": "agent_media_pack_manifest"}, {"identity": "asset_source_profile"}],
                source={"type": "original", "url": "https://github.com/taylor-s-amarel/ai-video-pipeline",
                        "notes": f"Describes {s['homepage']} (checked {CHECKED}); contains no third-party media."},
            )

        # 3. starter packs ----------------------------------------------------------------
        pack_ids = {p["id"] for p in packs}
        for p in packs:
            manifest = pack_manifest(p, catalogue)
            findings = CHECKER.check_manifest(manifest, "monetised-video")
            if any(f.level == "error" for f in findings):
                raise ValueError(f"{p['id']} fails the monetised-video licence check: {findings}")
            deps = [{"identity": "agent_media_pack_manifest"}, {"identity": "media_pack_fetcher"},
                    {"identity": "asset_licence_checker"}]
            if p.get("variant_of"):
                assert p["variant_of"] in pack_ids
            run.component(
                "skill", p["id"], title=p["title"], summary=p["summary"], subkind="rights-manifest", domain=DOMAIN,
                description=" ".join(p["description"].split()),
                files={"SKILL.md": skill_md(kebab(p["id"]), " ".join(p["description"].split()), pack_skill_body(p, manifest, findings)),
                       "pack.json": dumps(manifest),
                       "CREDITS.preview.md": FETCHER.credits_markdown(manifest)},
                tags=list(dict.fromkeys(["assets", "media-pack", "manifest"] + p["tags"]))[:24],
                step_kinds=["plan", "build", "render"],
                depends_on=deps, variant_of=p.get("variant_of"),
                parameters={"assets": len(manifest["assets"]), "status": manifest["status"]},
            )

        # 4. code modules -----------------------------------------------------------------
        for mod_dir in sorted((DATA / "modules").iterdir()):
            if not mod_dir.is_dir():
                continue
            meta = yaml.safe_load((mod_dir / "meta.yaml").read_text(encoding="utf-8"))
            e = meta.get("effects", {})
            run.component(
                "code-module", mod_dir.name, title=meta["title"], summary=meta["summary"],
                subkind=meta.get("subkind"), domain=meta.get("domain", DOMAIN), description=meta.get("description"),
                files=payload_files(mod_dir), entry=f"{mod_dir.name}.py",
                tags=meta["tags"], step_kinds=meta["step_kinds"],
                effects_=effects(filesystem=e.get("filesystem", "none"), executes=e.get("executes", "python"),
                                 hosts=e.get("hosts"), side_effects=e.get("side_effects")),
                depends_on=deps_from(meta) or None, examples=meta.get("examples"),
            )

        # 4b. variants that pin a meaningful choice
        godot_dir = DATA / "modules/godot_texture_import_presets"
        godot_files = payload_files(godot_dir)
        for preset, why in [("pixel-art-2d", "crisp 2D pixel art (Kenney Tiny/1-Bit, LPC, itch.io sheets)"),
                            ("pixel-art-3d", "pixel-art textures on 3D meshes with Nearest material filtering"),
                            ("texture-3d", "photoreal PBR maps from Poly Haven/ambientCG (VRAM compressed, mipmaps)"),
                            ("normal-map-3d", "normal maps imported as RGTC with mipmaps")]:
            ident = "godot_texture_import_presets_" + preset.replace("-", "_")
            files = dict(godot_files)
            files["preset.json"] = dumps({"preset": preset, "why": why})
            files["USAGE.md"] = (f"# Godot import preset: {preset}\n\nFor {why}.\n\n```bash\n"
                                 f"python3 godot_texture_import_presets.py apply PROJECT_DIR --preset {preset} --glob 'art/**/*.png'\n"
                                 f"python3 godot_texture_import_presets.py check PROJECT_DIR --preset {preset} --glob 'art/**/*.png'\n"
                                 f"python3 godot_texture_import_presets.py project-settings --preset {preset}\n```\n")
            run.component(
                "code-module", ident, title=f"Godot 4 texture import preset: {preset}",
                summary=f"The Godot texture import preset writer pinned to '{preset}': {why}.",
                subkind="godot", domain=DOMAIN, files=files, entry="godot_texture_import_presets.py",
                tags=["godot", "import", "textures", preset], step_kinds=["build", "verify"],
                effects_=effects(filesystem="write", executes="python"),
                variant_of="godot_texture_import_presets", parameters={"preset": preset},
            )
        fit_dir = DATA / "modules/pixel_art_video_fit"
        fit_files = payload_files(fit_dir)
        fit_mod = _load_module("pixel_art_video_fit", fit_dir / "pixel_art_video_fit.py")
        for preset in ["landscape-16x9", "square-1x1", "portrait-4x5"]:
            p = fit_mod.PRESETS[preset]
            files = dict(fit_files)
            files["preset.json"] = dumps(p)
            run.component(
                "code-module", "pixel_art_video_fit_" + preset.replace("-", "_"),
                title=f"Pixel-art integer scaler preset: {preset} ({p['size'][0]}x{p['size'][1]})",
                summary=f"Pixel-art integer scaler pinned to {p['size'][0]}x{p['size'][1]} with {p['margin']} safe margins; run with --preset-file preset.json.",
                subkind="aspect-format", domain=DOMAIN, files=files, entry="pixel_art_video_fit.py",
                tags=["pixel-art", "scaling", "video", preset], step_kinds=["render"],
                effects_=effects(filesystem="write", executes="python"),
                variant_of="pixel_art_video_fit", parameters={"preset": preset, **p},
            )

        # 5. harness components -----------------------------------------------------------
        run.component(
            "rules", "third_party_asset_rules", title="Third-party asset rules",
            summary="Twelve checkable rules for using free 2D/3D/audio assets: manifest first, no NC in monetised work, no ND edits, project-only files never committed, credits verbatim.",
            subkind="rule-set", domain=DOMAIN,
            files={"RULES.md": RULES_MD, "rules.json": dumps(RULES_JSON)},
            tags=["assets", "licensing", "rules", "credits"], step_kinds=["plan", "review", "secure"],
            depends_on=[{"identity": "asset_licence_checker"}],
        )
        run.component(
            "subagent", "asset_licence_auditor", title="Asset licence auditor",
            summary="Subagent that matches every media file to a manifest entry by name or SHA-256, runs the licence checker for the project's use profile and reports credits and redistribution problems.",
            subkind="review-lens", domain=DOMAIN,
            files={"agent.md": agent_md("asset-licence-auditor",
                                        "Use before rendering, committing or publishing anything that contains third-party images, models, audio, fonts or animations. Audits media against manifests and licences and reports every problem with a fix.",
                                        AUDITOR_MD, tools=["Read", "Bash", "Glob", "Grep"])},
            tags=["assets", "licensing", "review", "subagent"], step_kinds=["review", "verify", "secure"],
            effects_=effects(filesystem="read", executes="shell", side_effects=["runs sha256sum, git ls-files and the licence checker"]),
            harnesses=["claude-code", "opencode", "baltor-harness"],
            depends_on=[{"identity": "asset_licence_checker"}, {"identity": "agent_media_pack_manifest"}],
        )
        run.component(
            "command", "asset_pack", title="/asset-pack",
            summary="Slash command that turns a project idea into a validated, licence-checked media pack manifest, fetches direct assets and writes CREDITS.md.",
            subkind="workflow", domain=DOMAIN,
            files={"command.md": command_md("Build a licence-checked media pack manifest for a project", ASSET_PACK_CMD,
                                            argument_hint="<project idea, e.g. 'top-down maze short about one small adjustment'>")},
            tags=["assets", "command", "manifest"], step_kinds=["plan", "build"],
            harnesses=["claude-code", "opencode", "baltor-harness"],
            depends_on=[{"identity": "media_pack_fetcher"}, {"identity": "asset_licence_checker"}],
        )
        run.component(
            "command", "credit_assets", title="/credit-assets",
            summary="Slash command that re-verifies hashes, re-runs the licence checker and regenerates CREDITS.md and the description credit block for a project's media packs.",
            subkind="attribution", domain=DOMAIN,
            files={"command.md": command_md("Re-check media pack hashes and licences and regenerate credits", CREDIT_CMD,
                                            argument_hint="[path/to/pack.json ...]")},
            tags=["assets", "credits", "command"], step_kinds=["verify", "publish"],
            harnesses=["claude-code", "opencode", "baltor-harness"],
            depends_on=[{"identity": "media_pack_fetcher"}, {"identity": "asset_licence_checker"}],
        )
        hook_dir = DATA / "harness/media_pack_commit_guard"
        hook_files = payload_files(hook_dir)
        cmd = "python3 .baltor/hooks/media-pack-commit-guard/hook.py"
        hook_files["hook.json"] = dumps({"events": ["PreToolUse"], "matcher": "Bash", "command": cmd, "timeout": 30})
        hook_files["settings.fragment.json"] = dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": cmd, "timeout": 30}]}]}})
        run.component(
            "hook", "media_pack_commit_guard", title="Block commits of unlicensed or project-only media",
            summary="PreToolUse hook that refuses a git commit when staged images, models, audio or fonts are missing from every media pack manifest or are marked project-only/forbidden.",
            subkind="guardrail", domain=DOMAIN, files=hook_files,
            tags=["assets", "licensing", "git", "guardrail", "hook"], step_kinds=["secure", "build"],
            effects_=effects(filesystem="read", executes="python",
                             side_effects=["runs git diff --cached, git ls-files and git rev-parse", "hashes staged media files"]),
            depends_on=[{"identity": "agent_media_pack_manifest"}],
        )
        run.component(
            "instruction-file", "asset_sourcing_step_instructions", title="Instructions for an asset sourcing step",
            summary="CLAUDE.md / AGENTS.md section for a step that sources 2D/3D/audio assets: manifest first, CC0 first, project-only files ignored, inspect and preset before import.",
            subkind="step-template", domain=DOMAIN, files={"INSTRUCTIONS.md": INSTRUCTIONS_MD},
            tags=["assets", "instructions", "claude-md", "agents-md"], step_kinds=["plan", "build"],
        )
        skills = [s["id"] for s in sources] + [p["id"] for p in packs]
        run.component(
            "plugin-manifest", "asset_kits_plugin", title="Asset Kits plugin",
            summary="Claude Code plugin manifest bundling the asset source skills, starter-pack manifests, the licence auditor subagent and the /asset-pack and /credit-assets commands.",
            subkind="plugin-bundle", domain=DOMAIN,
            files={"plugin.json": dumps({
                "name": "asset-kits", "version": "1.0.0",
                "description": "Licence-checked 2D/3D/animation asset sourcing for Godot, Blender and short-video pipelines.",
                "author": {"name": "Baltor"}, "license": "MIT",
                "keywords": ["assets", "cc0", "godot", "blender", "licensing", "media-pack"],
                "commands": ["./commands/asset-pack.md", "./commands/credit-assets.md"],
                "agents": ["./agents/asset-licence-auditor.md"],
                "skills": [f"./skills/{kebab(s)}" for s in skills]}),
                "README.md": "# Asset Kits plugin\n\nAssemble with `baltor_catalog.py read <identity> --out ...` for each listed skill, "
                             "command and agent, then place this plugin.json in `.claude-plugin/plugin.json`.\n"},
            tags=["plugin", "assets", "claude-code"], step_kinds=["build"], harnesses=["claude-code"],
            depends_on=[{"identity": s} for s in skills[:10]] + [{"identity": "asset_licence_auditor"},
                                                                   {"identity": "asset_pack"}, {"identity": "credit_assets"}],
        )

    print(f"feeds: {feed_stats['collections']} collection(s), {feed_stats['items']} item(s), "
          f"verification {feed_stats['by_verification']}")


if __name__ == "__main__":
    main()
