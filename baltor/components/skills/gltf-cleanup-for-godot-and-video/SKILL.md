---
name: "gltf-cleanup-for-godot-and-video"
description: "Use after downloading any GLB/FBX/OBJ: inspect it, decode Draco or meshopt if needed, fix scale and units, reduce triangles and textures, validate, then import. Uses the gltf_glb_inspector module and open tools (glTF-Transform, gltfpack, glTF-Validator, obj2gltf, Blender)."
---

# Clean up downloaded 3D models for Godot, Blender and video

Use after downloading any GLB/FBX/OBJ: inspect it, decode Draco or meshopt if needed, fix scale and units, reduce triangles and textures, validate, then import. Uses the gltf_glb_inspector module and open tools (glTF-Transform, gltfpack, glTF-Validator, obj2gltf, Blender).

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Tools: glTF-Transform MIT, meshoptimizer/gltfpack MIT, glTF-Validator Apache-2.0, obj2gltf Apache-2.0. Tool licences do not change the model's own licence.

- `MIT`: glTF-Transform - <https://github.com/donmccurdy/glTF-Transform>
- `MIT`: meshoptimizer and gltfpack - <https://github.com/zeux/meshoptimizer>
- `Apache-2.0`: glTF-Validator - <https://github.com/KhronosGroup/glTF-Validator>
- `Apache-2.0`: obj2gltf - <https://github.com/CesiumGS/obj2gltf>

Attribution: **never**. Redistribution of the files: **allowed**.
Commercial use: **allowed**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required by the terms. If you mention the source, keep it to:

```
No credit line needed.
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [glTF-Transform](https://github.com/donmccurdy/glTF-Transform)
- [glTF-Validator](https://github.com/KhronosGroup/glTF-Validator)
- [meshoptimizer / gltfpack](https://github.com/zeux/meshoptimizer)
- [Godot: available 3D formats](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/available_formats.html)

## How to search

1. `python gltf_glb_inspector.py model.glb` - note extensionsRequired, triangles, bounds and copyright.
2. If Draco/meshopt is required and your importer lacks it, decode it (Blender import + GLB re-export works).
3. Scale: set the root scale so the largest dimension matches real size (inspector bounds).
4. Reduce: `gltf-transform resize in.glb out.glb --width 1024 --height 1024`; `gltf-transform optimize` for size.
5. Validate with glTF-Validator, then import.

## Import into Godot 4

- glTF 2.0 is Godot's recommended 3D format; `.blend` import needs Blender installed and FBX goes through ufbx.

## Import into Blender

- `bpy.ops.import_scene.gltf(filepath=...)` then File > Export > glTF 2.0 to write a cleaned GLB.

## Pitfalls

- Optimising never changes the licence: carry the source, licence and credit into the new file's manifest entry.
- OBJ carries no animation or PBR metadata; convert to glTF with obj2gltf or Blender.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "cleaned-model",
  "title": "Cleaned model (derived)",
  "creator": "Original creator (keep)",
  "source_url": "https://github.com/donmccurdy/glTF-Transform",
  "licence": "Same as the original model",
  "licence_url": "https://github.com/donmccurdy/glTF-Transform",
  "attribution": "Keep the original credit line",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "glb",
  "intended_use": [
    "optimised copy for Godot"
  ],
  "will_modify": true,
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
