---
name: "godot-asset-store-and-library"
description: "Use when a Godot 4 project needs an addon or a template project. The Asset Store (store.godotengine.org) replaces the legacy Asset Library, which is being deprecated; each listing carries its own licence. Covers searching, licence checks, the legacy REST API and installing safely."
---

# Godot Asset Store and legacy Asset Library

Use when a Godot 4 project needs an addon or a template project. The Asset Store (store.godotengine.org) replaces the legacy Asset Library, which is being deprecated; each listing carries its own licence. Covers searching, licence checks, the legacy REST API and installing safely.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Each asset declares its own licence (MIT is common). The Asset Store is the successor to the Asset Library; assets were not migrated automatically.

- `per-asset`: each listing - <https://docs.godotengine.org/en/stable/community/asset_store/what_is_asset_store.html>

Attribution: **per-asset**. Redistribution of the files: **per-asset**.
Commercial use: **per-asset**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Depends on each asset's licence. When the asset requires credit, use:

```
{addon} by {author} ({licence})
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Godot Asset Store](https://store.godotengine.org/)
- [About the Asset Store (docs)](https://docs.godotengine.org/en/stable/community/asset_store/what_is_asset_store.html)
- [Legacy Asset Library](https://godotengine.org/asset-library/asset)
- [Legacy API reference (API.md)](https://raw.githubusercontent.com/godotengine/godot-asset-library/master/API.md)

## API

<https://raw.githubusercontent.com/godotengine/godot-asset-library/master/API.md> (auth: none). GET /asset?type=any&godot_version=4.x&filter=...&max_results=50 ; GET /asset/{id}. Omitting godot_version lists only 2.1 assets.

## How to search

Search the store first; fall back to the legacy library API for older addons. Record the addon's repository URL,
licence and version in the manifest, and pin the version.

## Import into Godot 4

- Install from the editor's Asset Store tab (Godot 4.7+) or unzip into `res://addons/<name>/` and enable in
  Project Settings > Plugins.

## Import into Blender

- Not applicable; for Blender add-ons use extensions.blender.org (not covered here).

## Pitfalls

- Read an addon's code before enabling it: plugins run in the editor with full project access.
- Templates are standalone projects; addons go into res://addons/.
- Addon licences differ from the assets they bundle; demo art inside an addon can be NC.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "terrain3d",
  "title": "Terrain3D",
  "creator": "TokisanGames",
  "source_url": "https://github.com/TokisanGames/Terrain3D",
  "licence": "MIT",
  "licence_url": "https://github.com/TokisanGames/Terrain3D",
  "attribution": "Terrain3D by TokisanGames (MIT)",
  "attribution_required": false,
  "redistribution": "allowed-with-licence",
  "format": "zip",
  "intended_use": [
    "editable farm terrain"
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
