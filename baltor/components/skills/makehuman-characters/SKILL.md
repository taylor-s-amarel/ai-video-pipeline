---
name: "makehuman-characters"
description: "Use when a realistic or semi-realistic human base mesh is needed. MakeHuman's code is AGPL but its bundled assets and exports from official builds (1.2.0+) are CC0; third-party community assets keep their own licences. Covers export settings, Blender and Godot import, and licence evidence."
---

# MakeHuman characters (CC0 exports)

Use when a realistic or semi-realistic human base mesh is needed. MakeHuman's code is AGPL but its bundled assets and exports from official builds (1.2.0+) are CC0; third-party community assets keep their own licences. Covers export settings, Blender and Godot import, and licence evidence.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

MakeHuman source is AGPL; the bundled assets (base mesh, targets, textures, clothes, poses, expressions) are CC0, and since 1.2.0 exports from official, unmodified builds are CC0. Third-party assets keep their own licences.

- `CC0-1.0`: bundled assets and exports - <https://static.makehumancommunity.org/about/license.html>
- `AGPL-3.0`: MakeHuman code - <https://github.com/makehumancommunity/makehuman/blob/master/LICENSE.md>

Attribution: **optional**. Redistribution of the files: **allowed**.
Commercial use: **allowed**. Automated downloading: **unspecified**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required (CC0 or equivalent). A courtesy credit, if you give one:

```
Character base mesh made with MakeHuman (CC0)
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Licence](https://static.makehumancommunity.org/about/license.html)
- [Asset packs](https://static.makehumancommunity.org/assets/assetpacks.html)
- [FAQ: are MakeHuman files free?](https://static.makehumancommunity.org/makehuman/faq/are_makehuman_files_free.html)

## How to search

Use an official 1.2.x build, apply only bundled or CC0 assets, export FBX or Collada with a game-ready skeleton,
and keep a note of every third-party asset in the manifest.

## Import into Godot 4

- Import the FBX; map the skeleton with BoneMap + SkeletonProfileHumanoid to reuse humanoid animations.

## Import into Blender

- `bpy.ops.import_scene.fbx(filepath=...)`; apply scale and rotation before rigging tweaks.

## Pitfalls

- Community clothes/hair packs can be CC-BY; record each one.
- Exports made with versions before 1.2.0 were under AGPL terms.
- Photoreal humans in faceless videos can read as real people; avoid implying they are real individuals.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "makehuman-narrator",
  "title": "Narrator base mesh",
  "creator": "Made with MakeHuman",
  "source_url": "https://static.makehumancommunity.org/about/license.html",
  "licence": "CC0-1.0",
  "licence_url": "https://static.makehumancommunity.org/about/license.html",
  "attribution": "Character made with MakeHuman (CC0)",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "fbx",
  "intended_use": [
    "3D narrator stand-in"
  ],
  "fetch": {
    "method": "manual-page",
    "status": "manual"
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
