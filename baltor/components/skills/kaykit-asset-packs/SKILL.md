---
name: "kaykit-asset-packs"
description: "Use when a project wants stylised low-poly KayKit models (dungeon, medieval hexagon, platformer, city builder, adventurer and skeleton characters). Covers the CC0 free tiers, paid Extra/Source tiers, the author's no-resale request, GitHub mirrors for scripted download, and import steps."
---

# KayKit packs by Kay Lousberg (CC0, paid extras)

Use when a project wants stylised low-poly KayKit models (dungeon, medieval hexagon, platformer, city builder, adventurer and skeleton characters). Covers the CC0 free tiers, paid Extra/Source tiers, the author's no-resale request, GitHub mirrors for scripted download, and import steps.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Free KayKit tiers are CC0 (free for personal and commercial use, no attribution). The author asks that unmodified copies are not resold or claimed as your own. Extra and Source tiers are paid.

- `CC0-1.0`: free-tier downloads, as stated on each itch.io page - <https://creativecommons.org/publicdomain/zero/1.0/deed.en>

Attribution: **optional**. Redistribution of the files: **allowed**.
Commercial use: **allowed**. Automated downloading: **unspecified**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required (CC0 or equivalent). A courtesy credit, if you give one:

```
KayKit assets by Kay Lousberg (kaylousberg.itch.io), CC0
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [All KayKit packs on itch.io](https://kaylousberg.itch.io/)
- [Dungeon Pack Remastered](https://kaylousberg.itch.io/kaykit-dungeon-remastered)
- [Medieval Hexagon Pack](https://kaylousberg.itch.io/kaykit-medieval-hexagon)
- [Character Pack: Adventurers](https://kaylousberg.itch.io/kaykit-adventurers)
- [GitHub mirrors](https://github.com/KayKit-Game-Assets)

## How to search

Each itch.io page shows the free tier contents and the paid tiers. For scripted downloads, several packs are
mirrored in the KayKit-Game-Assets GitHub organisation (the Adventurers, Skeletons and City Builder Bits repos
state CC0 1.0 in LICENSE.txt; GitHub 1.0 releases can contain fewer items than the current itch.io tiers).

## Import into Godot 4

- Import GLB; KayKit characters come rigged and animated, so enable animation import and check clip names.
- Hex tiles: build a GridMap MeshLibrary from the tile scenes (Scene > Export As > MeshLibrary).

## Import into Blender

- `bpy.ops.import_scene.gltf(filepath=...)`; source `.blend` files are only in the paid Source tier.

## Pitfalls

- Do not resell unmodified copies or present them as your own work (author's request alongside CC0).
- Record which tier you downloaded; Extra and Source tier files are paid.
- Do not mix KayKit gradient-atlas textures with VRAM compression on low-res atlases; use lossless if banding appears.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "kaykit-dungeon-remastered",
  "title": "KayKit Dungeon Pack Remastered",
  "creator": "Kay Lousberg",
  "source_url": "https://kaylousberg.itch.io/kaykit-dungeon-remastered",
  "licence": "CC0-1.0",
  "licence_url": "https://creativecommons.org/publicdomain/zero/1.0/deed.en",
  "attribution": "KayKit Dungeon Pack Remastered by Kay Lousberg, CC0",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "zip",
  "intended_use": [
    "3D maze and dungeon set"
  ],
  "restrictions": [
    "Do not resell unmodified copies (author request)."
  ],
  "fetch": {
    "method": "manual-page",
    "status": "to-fetch"
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
