---
name: "rive-community-files"
description: "Use when an interactive or state-machine animation from the Rive community would fit a scene or UI. Community and Marketplace files are shared under CC BY, so they need credit; runtimes are MIT. Covers remixing, credit, exporting .riv and playing it on the web or rendering to video."
---

# Rive community and marketplace files (CC BY)

Use when an interactive or state-machine animation from the Rive community would fit a scene or UI. Community and Marketplace files are shared under CC BY, so they need credit; runtimes are MIT. Covers remixing, credit, exporting .riv and playing it on the web or rendering to video.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Rive docs: community files and marketplace files are shared under a CC BY licence (record the version shown on the file page). The Rive runtimes (rive-runtime, rive-wasm) are MIT.

- `CC-BY`: community files - <https://rive.app/docs/community/community-overview>
- `MIT`: web runtime - <https://github.com/rive-app/rive-wasm>

Attribution: **required**. Redistribution of the files: **allowed-with-licence**.
Commercial use: **allowed**. Automated downloading: **unspecified**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Required. Fill in the braces from each asset page and use the line verbatim:

```
Animation: "{title}" by {creator}, Rive community (CC BY)
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Community overview](https://rive.app/docs/community/community-overview)
- [Marketplace overview](https://www.rive.app/docs/community/marketplace-overview)
- [rive-wasm runtime](https://github.com/rive-app/rive-wasm)

## How to search

Remix a community file into your account, adjust it, export .riv, and record the original author and URL in the manifest.

## Import into Godot 4

- Render to a PNG sequence through the web runtime for video, or evaluate a maintained Godot Rive integration
  (check its licence) for interactive use.

## Import into Blender

- Use a rendered PNG sequence on a plane.

## Pitfalls

- Credit the original author of every remixed file.
- The overview pages say 'CC BY' without a version; record what the file page states.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "rive-button",
  "title": "Animated button (fill in)",
  "creator": "Rive community author (fill in)",
  "source_url": "https://rive.app/docs/community/community-overview",
  "licence": "CC BY (version as shown on the file page)",
  "licence_url": "https://rive.app/docs/community/community-overview",
  "attribution": "Animation by Author, Rive community (CC BY)",
  "attribution_required": true,
  "redistribution": "allowed-with-licence",
  "format": "riv",
  "intended_use": [
    "animated call-to-action"
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
