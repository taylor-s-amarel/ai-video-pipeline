---
name: "nasa-3d-resources"
description: "Use for space and science shorts that need real spacecraft models (Apollo Lunar Module, Hubble, Curiosity, astronaut, Gateway). NASA's repository states the assets are free and without copyright, subject to NASA's media usage guidelines. Covers download from GitHub, Draco/WebP pitfalls and scale."
---

# NASA 3D Resources (spacecraft, rovers, suits)

Use for space and science shorts that need real spacecraft models (Apollo Lunar Module, Hubble, Curiosity, astronaut, Gateway). NASA's repository states the assets are free and without copyright, subject to NASA's media usage guidelines. Covers download from GitHub, Draco/WebP pitfalls and scale.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

The repository README says the assets are free and without copyright and points to NASA's usage guidelines. Do not use NASA insignia or imply NASA endorsement; some models come from outside contributors.

- `Public domain statement (NASA)`: repository assets, with NASA usage guidelines - <https://github.com/nasa/NASA-3D-Resources>

Attribution: **optional**. Redistribution of the files: **allowed**.
Commercial use: **allowed**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required (CC0 or equivalent). A courtesy credit, if you give one:

```
3D model: {title}, NASA 3D Resources (github.com/nasa/NASA-3D-Resources)
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [3D Models folder](https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models)
- [Apollo Lunar Module](https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/Apollo%20Lunar%20Module)
- [Astronaut](https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/Astronaut)

## How to search

Browse the `3D Models` folder; each model has a preview PNG plus GLB, BLEND or LWO. Download raw files from
`https://raw.githubusercontent.com/nasa/NASA-3D-Resources/master/3D%20Models/<folder>/<file>` with the
`media_pack_fetcher` module (raw.githubusercontent.com is on its default allow-list) and record the SHA-256.

## Import into Godot 4

- Decode Draco first (for example with glTF-Transform) if your Godot version does not import the file, then import
  the GLB and scale the root so the model matches your scene units (use the inspector's bounds).

## Import into Blender

- Blender's glTF importer reads Draco and WebP: `bpy.ops.import_scene.gltf(filepath="Apollo Lunar Module.glb")`.
  Re-export a decoded GLB for other tools if needed.

## Pitfalls

- Do not use NASA logos/insignia or imply endorsement; follow NASA's media usage guidelines.
- Several GLBs require KHR_draco_mesh_compression and use EXT_texture_webp (checked 2026-10-10 on the Apollo LM, Astronaut and Hubble files).
- Units vary: the Astronaut GLB is about 74 units tall and Hubble (A) about 525 units; normalise before placing.
- Curiosity is .blend only: export a GLB from Blender for Godot.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "nasa-apollo-lunar-module",
  "title": "Apollo Lunar Module",
  "creator": "NASA",
  "source_url": "https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/Apollo%20Lunar%20Module",
  "download_url": "https://raw.githubusercontent.com/nasa/NASA-3D-Resources/master/3D%20Models/Apollo%20Lunar%20Module/Apollo%20Lunar%20Module.glb",
  "licence": "Public domain statement (NASA) + NASA usage guidelines",
  "licence_url": "https://github.com/nasa/NASA-3D-Resources",
  "attribution": "Apollo Lunar Module 3D model, NASA 3D Resources",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "glb",
  "file_name": "Apollo Lunar Module.glb",
  "sha256": "379101dfcee399267addf771709107c35e826b0b9e5233272f123e4c8a585c4e",
  "bytes": 716840,
  "intended_use": [
    "Moon landing history short hero model"
  ],
  "restrictions": [
    "Requires KHR_draco_mesh_compression; textures are WebP with PNG fallbacks.",
    "No NASA insignia; no implied endorsement."
  ],
  "fetch": {
    "method": "direct",
    "status": "fetched",
    "fetched_on": "2026-10-10"
  },
  "import_hints": {
    "blender": {
      "operator": "bpy.ops.import_scene.gltf"
    },
    "video": {
      "role": "prop"
    }
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
