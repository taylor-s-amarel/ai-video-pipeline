---
name: "ambientcg-materials"
description: "Use when a Blender or Godot scene needs CC0 PBR materials (ground, wood, brick, metal ...) or HDRIs from ambientCG, by hand or through its JSON API. Covers the licence, the frozen v2 versus current v3 API, map naming, and Godot/Blender material setup."
---

# ambientCG PBR materials and HDRIs (CC0, API v2/v3)

Use when a Blender or Godot scene needs CC0 PBR materials (ground, wood, brick, metal ...) or HDRIs from ambientCG, by hand or through its JSON API. Covers the licence, the frozen v2 versus current v3 API, map naming, and Godot/Blender material setup.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

All ambientCG assets are under CC0 1.0 Universal; credit is not required but appreciated.

- `CC0-1.0`: all assets - <https://docs.ambientcg.com/license/>

Attribution: **optional**. Redistribution of the files: **allowed**.
Commercial use: **allowed**. Automated downloading: **api-only**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required (CC0 or equivalent). A courtesy credit, if you give one:

```
Materials from ambientCG.com, CC0
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Asset search](https://ambientcg.com/list)
- [API overview](https://docs.ambientcg.com/api/)
- [API v2 /full_json](https://docs.ambientcg.com/api/v2/full_json/)

## API

<https://docs.ambientcg.com/api/> (auth: none). v2 is frozen; new projects should use v3. The v2 zipContent field now always returns [].

## How to search

Filter the list page, then copy the same filters into an API query. Download the zip at the resolution you need
(2K is plenty for most video shots); each zip holds colour, normal (GL and DX variants), roughness,
displacement and sometimes AO/metalness maps.

## Import into Godot 4

- StandardMaterial3D: albedo = Color map, roughness = Roughness, normal = NormalGL (enable Normal Map),
  heightmap = Displacement if needed. Import maps with `texture-3d` and the normal with `normal-map-3d`.

## Import into Blender

- Principled BSDF: Color -> Base Color; Roughness (Non-Color) -> Roughness; NormalGL (Non-Color) -> Normal Map node.

## Pitfalls

- Watch the technical updates page before relying on API response shapes.
- Use the NormalGL map for both Godot and Blender; the DX map has the green channel flipped.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "ambientcg-wood-026",
  "title": "Wood 026",
  "creator": "ambientCG",
  "source_url": "https://ambientcg.com/view?id=Wood026",
  "licence": "CC0-1.0",
  "licence_url": "https://docs.ambientcg.com/license/",
  "attribution": "Wood 026 from ambientCG.com, CC0",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "zip",
  "intended_use": [
    "table and floor material"
  ],
  "fetch": {
    "method": "api",
    "status": "to-fetch"
  },
  "import_hints": {
    "godot": {
      "importer": "texture",
      "preset": "texture-3d"
    }
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
