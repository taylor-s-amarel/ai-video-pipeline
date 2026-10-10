---
name: "smithsonian-open-access"
description: "Use for history and science shorts that need museum objects. Smithsonian Open Access publishes CC0 metadata (11M+ records) and CC0 media for objects marked Open Access; this skill shows how to query the metadata dump, check each record's rights, and avoid people/trademark problems."
---

# Smithsonian Open Access (CC0 records)

Use for history and science shorts that need museum objects. Smithsonian Open Access publishes CC0 metadata (11M+ records) and CC0 media for objects marked Open Access; this skill shows how to query the metadata dump, check each record's rights, and avoid people/trademark problems.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

The Open Access metadata repository is CC0-1.0. Media is CC0 only where the record says Open Access; other media keep their own rights.

- `CC0-1.0`: Open Access metadata and media marked CC0 - <https://github.com/Smithsonian/OpenAccess>

Attribution: **optional**. Redistribution of the files: **per-asset**.
Commercial use: **per-asset**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required (CC0 or equivalent). A courtesy credit, if you give one:

```
{title}, {unit}, Smithsonian Institution (Open Access, CC0)
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [OpenAccess metadata (line-delimited JSON)](https://github.com/Smithsonian/OpenAccess)

## How to search

Filter the line-delimited JSON by unit and keywords, keep records whose usage/rights fields say CC0, and follow the
media links they contain. Record the record ID and URL in the manifest so the claim is traceable.

## Import into Godot 4

- Treat downloaded 3D scans like other GLBs: inspect, decimate if heavy, import with `texture-3d` maps.

## Import into Blender

- Import scans with `bpy.ops.import_scene.gltf`; decimate for real-time use.

## Pitfalls

- The GitHub repo is read-only; the archive moved to AWS.
- CC0 does not clear publicity rights of people shown or trademarks on objects.
- Do not caption a historical claim from an object record without checking the record's own description.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "smithsonian-record",
  "title": "Example Open Access record (fill in)",
  "creator": "Smithsonian Institution",
  "source_url": "https://github.com/Smithsonian/OpenAccess",
  "licence": "CC0-1.0",
  "licence_url": "https://github.com/Smithsonian/OpenAccess",
  "attribution": "Object name, Smithsonian Institution (CC0)",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "json",
  "intended_use": [
    "history fact source and image"
  ],
  "fetch": {
    "method": "git",
    "status": "to-fetch"
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
