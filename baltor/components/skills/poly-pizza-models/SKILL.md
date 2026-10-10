---
name: "poly-pizza-models"
description: "Use when you need one specific low-poly object fast (a pizza, a car, a cloud) from Poly Pizza's library, which mixes CC0 uploads with CC-BY models such as the archived Poly by Google set. Explains reading each model's licence, building the credit line, and importing the GLB."
---

# Poly Pizza low-poly models (per-model CC0 or CC-BY)

Use when you need one specific low-poly object fast (a pizza, a car, a cloud) from Poly Pizza's library, which mixes CC0 uploads with CC-BY models such as the archived Poly by Google set. Explains reading each model's licence, building the credit line, and importing the GLB.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Licence is per model: many are CC0 (Kenney, Quaternius uploads), many archived Poly by Google models are CC-BY and need credit.

- `CC0-1.0`: models marked CC0 - <https://creativecommons.org/publicdomain/zero/1.0/deed.en>
- `CC-BY`: models marked Creative Commons Attribution (check the version on the page) - <https://creativecommons.org/licenses/by/4.0/deed.en>

Attribution: **per-asset**. Redistribution of the files: **per-asset**.
Commercial use: **allowed**. Automated downloading: **unspecified**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Depends on each asset's licence. When the asset requires credit, use:

```
{title} by {creator} [CC-BY] via Poly Pizza (poly.pizza)
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Search](https://poly.pizza/search/Low%20Poly%20Art)
- [Example CC0 model (Kenney pizza)](https://poly.pizza/m/fJsz9IVM8f)
- [Example CC-BY model (Poly by Google forest)](https://poly.pizza/m/2_fv3tn3NG_)

## API

<https://poly.pizza/docs/press> (auth: key). The press page describes an API (free for hobby use, pay-as-you-go commercially); check current docs.

## How to search

Search by object name, open the model page, read the licence badge and creator, then download GLTF/GLB.
Put the credit line in the media pack manifest before you use the model.

## Import into Godot 4

- Import the GLB; Poly by Google models often have very different scales, so normalise with the
  `gltf_glb_inspector` bounds before placing them.

## Import into Blender

- `bpy.ops.import_scene.gltf(filepath=...)`; apply scale after normalising.

## Pitfalls

- Paid packs from other studios appear in search results; skip anything not free.
- Record the exact CC-BY version shown on each model page.
- Do not assume a whole search page shares one licence.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "poly-pizza-forest",
  "title": "Forest",
  "creator": "Poly by Google",
  "source_url": "https://poly.pizza/m/2_fv3tn3NG_",
  "licence": "CC-BY (version as shown on the model page)",
  "licence_url": "https://poly.pizza/m/2_fv3tn3NG_",
  "attribution": "Forest by Poly by Google [CC-BY] via Poly Pizza",
  "attribution_required": true,
  "redistribution": "allowed-with-licence",
  "format": "glb",
  "intended_use": [
    "background tree cluster"
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
