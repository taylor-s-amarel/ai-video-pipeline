---
name: "gdquest-open-source-demos"
description: "Use when borrowing GDQuest's Godot 4 controllers, shaders or premade characters. Code is MIT, but several art sets (godot-4-3D-Characters, third-person controller models) are CC-BY-NC-SA 4.0 and cannot appear in monetised work. Explains reusing code while swapping art."
---

# GDQuest open-source Godot demos (MIT code, some NC art)

Use when borrowing GDQuest's Godot 4 controllers, shaders or premade characters. Code is MIT, but several art sets (godot-4-3D-Characters, third-person controller models) are CC-BY-NC-SA 4.0 and cannot appear in monetised work. Explains reusing code while swapping art.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

GDQuest demo code is MIT. Art in godot-4-3D-Characters and godot-4-3d-third-person-controller is CC-BY-NC-SA 4.0 (non-commercial, share-alike, credit GDQuest).

- `MIT`: code - <https://github.com/gdquest-demos/godot-4-3d-third-person-controller>
- `CC-BY-NC-SA-4.0`: 3D character art - <https://raw.githubusercontent.com/gdquest-demos/godot-4-3D-Characters/main/LICENSE>

Attribution: **per-asset**. Redistribution of the files: **per-asset**.
Commercial use: **per-asset**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Depends on each asset's licence. When the asset requires credit, use:

```
Character art by GDQuest (CC BY-NC-SA 4.0)
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [GDQuest demos](https://github.com/gdquest-demos)
- [Premade 3D characters](https://github.com/gdquest-demos/godot-4-3D-Characters)
- [Third-person controller](https://github.com/gdquest-demos/godot-4-3d-third-person-controller)

## How to search

Copy controllers and scripts (MIT) into your project and swap the characters for CC0 Quaternius or KayKit models.

## Import into Godot 4

- Retarget CC0 characters onto the controller's AnimationTree by matching animation names.

## Import into Blender

- Not needed unless you rebuild characters.

## Pitfalls

- Do not use the GDQuest characters (Sophia, Gobot, GDbot ...) in monetised videos or commercial games.
- Third parties have asked about the art licence changing over time; read the LICENSE at the commit you use.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "gdquest-controller-code",
  "title": "Third-person controller code",
  "creator": "GDQuest",
  "source_url": "https://github.com/gdquest-demos/godot-4-3d-third-person-controller",
  "licence": "MIT",
  "licence_url": "https://github.com/gdquest-demos/godot-4-3d-third-person-controller",
  "attribution": "Controller code by GDQuest (MIT)",
  "attribution_required": false,
  "redistribution": "allowed-with-licence",
  "format": "zip",
  "intended_use": [
    "controller logic only",
    "art replaced"
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
