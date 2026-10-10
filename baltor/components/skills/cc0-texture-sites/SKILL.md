---
name: "cc0-texture-sites"
description: "Use when Poly Haven and ambientCG lack a material. cgbookcase and 3DTextures.me publish CC0 PBR textures; ShareTextures uses a custom CC0-based licence that forbids automated downloads and redistribution. Explains which to script, which to download by hand, and how to credit."
---

# Smaller CC0 texture libraries (cgbookcase, 3DTextures.me) and ShareTextures' limits

Use when Poly Haven and ambientCG lack a material. cgbookcase and 3DTextures.me publish CC0 PBR textures; ShareTextures uses a custom CC0-based licence that forbids automated downloads and redistribution. Explains which to script, which to download by hand, and how to credit.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

cgbookcase: CC0, 100% free. 3DTextures.me: recent pages state CC0 for the free resolutions (higher resolutions on Patreon). ShareTextures: custom CC0 with restrictions (no automated downloads, no embedding in apps/add-ons, no redistribution without permission).

- `CC0-1.0`: cgbookcase textures - <https://www.cgbookcase.com/>
- `CC0-1.0`: 3DTextures.me free textures - <https://3dtextures.me/about/>
- `ShareTextures-custom`: ShareTextures assets - <https://www.sharetextures.com/p/license>

Attribution: **optional**. Redistribution of the files: **per-asset**.
Commercial use: **allowed**. Automated downloading: **forbidden**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required (CC0 or equivalent). A courtesy credit, if you give one:

```
Texture: {title} from {site}
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [cgbookcase textures](https://www.cgbookcase.com/textures)
- [3DTextures.me](https://3dtextures.me/)
- [ShareTextures licence](https://www.sharetextures.com/p/license)

## How to search

Use these as fall-backs. Download by hand, record the page URL and licence in the manifest, and import with the
same map wiring as ambientCG.

## Import into Godot 4

- Albedo/roughness with `texture-3d`, normal with `normal-map-3d`; check whether a site ships GL or DX normals.

## Import into Blender

- Principled BSDF wiring as for ambientCG; set non-colour maps to Non-Color.

## Pitfalls

- ShareTextures: an agent must not bulk-download or script downloads; fetch by hand only.
- 3DTextures.me Patreon-only resolutions are not covered by the free CC0 statement.
- Automating ShareTextures downloads violates its licence even though it calls itself CC0.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "cgbookcase-wood-10",
  "title": "Wood 10",
  "creator": "cgbookcase",
  "source_url": "https://www.cgbookcase.com/textures/wood-10",
  "licence": "CC0-1.0",
  "licence_url": "https://www.cgbookcase.com/",
  "attribution": "Wood 10 from cgbookcase.com, CC0",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "zip",
  "intended_use": [
    "wooden sign material"
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
