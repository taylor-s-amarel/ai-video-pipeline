---
name: "quaternius-low-poly-assets"
description: "Use when a scene needs free low-poly 3D models or humanoid animations (nature, farm, medieval, sci-fi, animals, characters, Universal Animation Library) under CC0. Explains free versus paid Source tiers, credit, glTF import into Godot 4 and Blender, and retargeting the animation library."
---

# Quaternius low-poly packs (CC0)

Use when a scene needs free low-poly 3D models or humanoid animations (nature, farm, medieval, sci-fi, animals, characters, Universal Animation Library) under CC0. Explains free versus paid Source tiers, credit, glTF import into Godot 4 and Blender, and retargeting the animation library.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Quaternius releases its free packs under CC0: commercial use allowed, no attribution required. Some MegaKits also sell a 'Source' tier with engine projects.

- `CC0-1.0`: free pack downloads - <https://quaternius.com/>

Attribution: **optional**. Redistribution of the files: **allowed**.
Commercial use: **allowed**. Automated downloading: **unspecified**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required (CC0 or equivalent). A courtesy credit, if you give one:

```
Models by Quaternius (quaternius.com), CC0
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [All packs](https://quaternius.com/)
- [Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html)
- [Universal Base Characters](https://quaternius.com/packs/universalbasecharacters.html)
- [Farm Buildings](https://quaternius.com/packs/farmbuildings.html)
- [Ultimate Space Kit](https://quaternius.com/packs/ultimatespacekit.html)

## How to search

Browse the home page by theme; each pack page lists model count, release date and formats. Prefer packs that
list glTF. For characters, pair Universal Base Characters with the Universal Animation Library (120+ animations
on one humanoid rig) instead of Mixamo when you need files you can redistribute.

## Import into Godot 4

- Import the `.glb`/`.gltf`; in the Import dock set Root Type as needed and enable animation import.
- For the Universal Animation Library, set up a BoneMap with `SkeletonProfileHumanoid` in Advanced Import
  Settings so the clips retarget onto other humanoids (see the Godot "Retargeting 3D Skeletons" guide).

## Import into Blender

- `bpy.ops.import_scene.gltf(filepath=...)`; `.blend` packs can be appended with File > Append.
- Check Object > Apply > Scale before export if you rescale; keep Y-up/+Z-forward glTF conventions on re-export.

## Pitfalls

- MegaKit 'Source' tiers (Unity/Unreal/Godot implementations) are paid; the free download is the model set.
- CC0 has no warranty: check scale, pivots and animation names after import.
- Older packs ship FBX/OBJ/Blend only; convert to GLB in Blender rather than using OBJ (no animation).

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "quaternius-farm-animals",
  "title": "Farm Animal Pack",
  "creator": "Quaternius",
  "source_url": "https://quaternius.com/packs/farmanimal.html",
  "licence": "CC0-1.0",
  "licence_url": "https://quaternius.com/packs/farmanimal.html",
  "attribution": "Farm Animal Pack by Quaternius, CC0",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "zip",
  "intended_use": [
    "animated farm animals for a diorama"
  ],
  "fetch": {
    "method": "manual-page",
    "status": "to-fetch"
  },
  "import_hints": {
    "godot": {
      "importer": "scene"
    },
    "blender": {
      "operator": "bpy.ops.import_scene.fbx"
    }
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
