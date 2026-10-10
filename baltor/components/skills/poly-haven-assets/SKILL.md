---
name: "poly-haven-assets"
description: "Use when a render or Godot scene needs photoreal HDRI lighting/skies, PBR textures or models. Poly Haven assets are CC0 and its public JSON API lists every asset with download URLs and hashes. Covers API use, credit expectations, Godot sky/material setup and Blender world lighting."
---

# Poly Haven HDRIs, textures and models (CC0, with API)

Use when a render or Godot scene needs photoreal HDRI lighting/skies, PBR textures or models. Poly Haven assets are CC0 and its public JSON API lists every asset with download URLs and hashes. Covers API use, credit expectations, Godot sky/material setup and Blender world lighting.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

All Poly Haven assets are CC0. You may not claim to be the original author or re-license them as your own. The API is free for everyone including commercial use; Poly Haven asks API users to make clear to their users that the assets come from Poly Haven.

- `CC0-1.0`: all HDRIs, textures and models - <https://docs.polyhaven.com/en/faq>

Attribution: **optional**. Redistribution of the files: **allowed**.
Commercial use: **allowed**. Automated downloading: **api-only**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required (CC0 or equivalent). A courtesy credit, if you give one:

```
HDRI/texture: {title} from Poly Haven (polyhaven.com), CC0
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [HDRIs](https://polyhaven.com/hdris)
- [Textures](https://polyhaven.com/textures)
- [Models](https://polyhaven.com/models)
- [Sunrise/sunset HDRIs](https://polyhaven.com/hdris/sunrise-sunset)

## API

<https://polyhaven.com/our-api> (auth: none). Lists assets with categories, tags, authors, download URLs, hashes and sizes; e.g. api.polyhaven.com/assets?type=hdris.

## How to search

Filter HDRIs by category (Pure Skies, Fields & Countryside, Studio ...). A 2K or 4K HDRI is enough for lighting
and a blurred moving background; 8K+ is only needed when the sky is seen sharp. Use the API for scripted
pipelines (the `polydown` CLI or the `dcc-asset-polyhaven` agent skill wrap it) and verify each download against
the hash the API returns with the `media_pack_fetcher` module.

## Import into Godot 4

- HDRI sky: WorldEnvironment > Environment > Background: Sky > Sky Material: PanoramaSkyMaterial, panorama = the
  imported `.hdr`/`.exr`. Ambient light and reflections then come from the sky.
- Textures: albedo/roughness/AO with the `texture-3d` preset, the normal map with `normal-map-3d`.

## Import into Blender

- World shader: Environment Texture node -> Background; set the strength, rotate with a Mapping node.
- Models: `bpy.ops.import_scene.gltf(filepath=...)` or append from the `.blend`.

## Pitfalls

- CC0 does not clear trademarks or recognisable private places in scans.
- Download only what the project uses; bulk mirroring wastes donated bandwidth.
- Godot expects OpenGL-style normal maps (Y+); pick the GL variant when a site offers GL and DX.
- Very large EXRs slow imports; downscale for video backgrounds.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "polyhaven-grasslands-sunset",
  "title": "Grasslands Sunset HDRI",
  "creator": "Poly Haven",
  "source_url": "https://polyhaven.com/a/grasslands_sunset",
  "licence": "CC0-1.0",
  "licence_url": "https://docs.polyhaven.com/en/faq",
  "attribution": "Grasslands Sunset HDRI from Poly Haven, CC0",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "hdr",
  "intended_use": [
    "sky and lighting for a farm diorama"
  ],
  "fetch": {
    "method": "api",
    "status": "to-fetch"
  },
  "import_hints": {
    "godot": {
      "importer": "texture",
      "notes": "PanoramaSkyMaterial panorama"
    },
    "video": {
      "role": "hdri-lighting"
    }
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
