---
name: "khronos-gltf-sample-assets"
description: "Use when you need known-good glTF/GLB files to test an importer, a Godot scene loader, a Blender script or the glTF inspector. Each model folder documents its own licence and credit."
---

# Khronos glTF Sample Assets (test models)

Use when you need known-good glTF/GLB files to test an importer, a Godot scene loader, a Blender script or the glTF inspector. Each model folder documents its own licence and credit.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Licences are per model and stated in Models/<Name>/README.md (many CC-BY 4.0, some CC0); keep the credit with the file.

- `per-asset`: each model folder - <https://github.com/KhronosGroup/glTF-Sample-Assets>

Attribution: **per-asset**. Redistribution of the files: **per-asset**.
Commercial use: **per-asset**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Depends on each asset's licence. When the asset requires credit, use:

```
{title} from Khronos glTF Sample Assets, {licence}, {credit from README}
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Repository](https://github.com/KhronosGroup/glTF-Sample-Assets)
- [Duck GLB (raw)](https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Duck/glTF-Binary/Duck.glb)

## How to search

Use `Models/<Name>/glTF-Binary/<Name>.glb` for single-file tests. The repository's testing list highlights models
meant for exercising viewers and converters.

## Import into Godot 4

- Drop the GLB into a test project and compare node/mesh counts with `gltf_glb_inspector --json`.

## Import into Blender

- `bpy.ops.import_scene.gltf(filepath="Duck.glb")`, then compare object counts with the inspector.

## Pitfalls

- Do not ship sample models in a product without checking their individual licence.
- Some samples exercise extensions your importer may not support; that is their purpose.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "khronos-duck",
  "title": "Duck",
  "creator": "Khronos Group sample assets",
  "source_url": "https://github.com/KhronosGroup/glTF-Sample-Assets",
  "download_url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Duck/glTF-Binary/Duck.glb",
  "licence": "See Models/Duck/README.md",
  "licence_url": "https://github.com/KhronosGroup/glTF-Sample-Assets",
  "attribution": "Duck from Khronos glTF Sample Assets (see Models/Duck/README.md for licence and credit)",
  "attribution_required": true,
  "redistribution": "allowed-with-licence",
  "format": "glb",
  "file_name": "Duck.glb",
  "sha256": "65bf938f54d6073e619e76e007820bbf980cdc3dc0daec0d94830ffc4ae54ab5",
  "bytes": 120484,
  "intended_use": [
    "importer smoke test"
  ],
  "fetch": {
    "method": "direct",
    "status": "fetched",
    "fetched_on": "2026-10-10"
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
