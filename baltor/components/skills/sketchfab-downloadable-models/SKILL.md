---
name: "sketchfab-downloadable-models"
description: "Use when a scan, museum object or hero model is only available on Sketchfab. Downloadable models carry a per-model Creative Commons licence (CC0, BY, BY-SA, BY-ND, BY-NC); store purchases use Standard or Editorial licences. Covers filters, credit format, NC/ND pitfalls and import."
---

# Sketchfab downloadable models (per-model CC licences)

Use when a scan, museum object or hero model is only available on Sketchfab. Downloadable models carry a per-model Creative Commons licence (CC0, BY, BY-SA, BY-ND, BY-NC); store purchases use Standard or Editorial licences. Covers filters, credit format, NC/ND pitfalls and import.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Each downloadable model has a CC licence chosen by its author; CC BY requires credit, NC forbids commercial use, ND forbids modification. Store models use Standard or Editorial licences, and purchased models may never be offered for download to others.

- `per-asset`: downloadable models - <https://help.sketchfab.com/en/articles/16152221-choosing-your-model-s-license>
- `Sketchfab-Store`: store purchases - <https://help.sketchfab.com/en/articles/16152225-store-license-usage-faq>

Attribution: **per-asset**. Redistribution of the files: **per-asset**.
Commercial use: **per-asset**. Automated downloading: **unspecified**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Depends on each asset's licence. When the asset requires credit, use:

```
"{title}" by {creator} on Sketchfab, licensed {licence}
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Licence filters announcement](https://sketchfab.com/blogs/community/refine-downloadable-model-searches-with-new-license-filters)
- [Crediting creators](https://help.sketchfab.com/en/articles/16152215-crediting-users-for-3d-model-downloads)

## How to search

Filter downloadable models by licence (CC0 or CC BY for monetised work). Open the model, copy the title, author
and licence into the manifest, then download the glTF/GLB conversion.

## Import into Godot 4

- Import the GLB; scans are often huge: decimate in Blender first and check triangles with `gltf_glb_inspector`.

## Import into Blender

- `bpy.ops.import_scene.gltf(filepath=...)`; use Decimate and bake to reduce scan meshes before Godot.

## Pitfalls

- Editorial store licences cover news/public-interest use only, never promotion.
- BY-NC models cannot be used in monetised videos; BY-ND models cannot be re-textured, cropped into new models or re-rigged.
- Museum accounts often choose NC licences; check every object.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "sketchfab-scan",
  "title": "Example museum scan (fill in)",
  "creator": "Museum account (fill in)",
  "source_url": "https://help.sketchfab.com/en/articles/16152221-choosing-your-model-s-license",
  "licence": "CC-BY-4.0",
  "licence_url": "https://creativecommons.org/licenses/by/4.0/deed.en",
  "attribution": "\"Model title\" by Author on Sketchfab, CC BY 4.0",
  "attribution_required": true,
  "redistribution": "allowed-with-licence",
  "format": "glb",
  "intended_use": [
    "history short hero prop"
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
