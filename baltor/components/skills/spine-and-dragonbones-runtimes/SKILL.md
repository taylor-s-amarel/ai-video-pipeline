---
name: "spine-and-dragonbones-runtimes"
description: "Use before choosing a 2D skeletal animation format. Spine runtimes (including spine-godot) are source-available but need a Spine Editor licence; DragonBones runtimes are MIT; Godot's own Skeleton2D needs no runtime. Explains which to pick for redistributable projects and videos."
---

# Skeletal 2D animation runtimes (Spine licence vs DragonBones MIT)

Use before choosing a 2D skeletal animation format. Spine runtimes (including spine-godot) are source-available but need a Spine Editor licence; DragonBones runtimes are MIT; Godot's own Skeleton2D needs no runtime. Explains which to pick for redistributable projects and videos.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Spine Runtimes License: integrating the runtimes requires a valid Spine Editor licence (or every user needs one); the trial grants no runtime rights. DragonBonesJS is MIT.

- `Spine-Runtimes-License`: Spine runtimes incl. spine-godot - <https://eu.esotericsoftware.com/spine-runtimes-license>
- `MIT`: DragonBones JS runtime - <https://github.com/DragonBones/DragonBonesJS>

Attribution: **never**. Redistribution of the files: **per-asset**.
Commercial use: **check-terms**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required by the terms. If you mention the source, keep it to:

```
No credit line needed.
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Spine runtimes](https://github.com/EsotericSoftware/spine-runtimes)
- [Spine Editor licence](https://en.esotericsoftware.com/spine-editor-license)
- [DragonBonesJS](https://github.com/DragonBones/DragonBonesJS)

## How to search

For agent-built shorts, prefer Godot Skeleton2D/Polygon2D rigs (no runtime licence) or pre-rendered frames.
Use Spine only when the team already owns Spine Editor licences.

## Import into Godot 4

- Skeleton2D + Bone2D + Polygon2D with AnimationPlayer covers most cut-out characters without third-party runtimes.

## Import into Blender

- Grease Pencil or cut-out rigs rendered to PNG sequences avoid runtime licensing entirely.

## Pitfalls

- Do not ship spine-godot in a public template unless you hold a Spine Editor licence and follow its terms.
- Exported Spine JSON is your art, but the runtime that plays it is licensed separately.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "cutout-rig",
  "title": "Cut-out character rig (original)",
  "creator": "Your team",
  "source_url": "https://github.com/DragonBones/DragonBonesJS",
  "licence": "Original work",
  "licence_url": "https://github.com/DragonBones/DragonBonesJS",
  "attribution": "",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "png",
  "intended_use": [
    "Skeleton2D narrator"
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
