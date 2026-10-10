---
name: "open-emoji-sets"
description: "Use when a caption or reaction overlay needs emoji drawn consistently on every platform. Twemoji graphics are CC-BY 4.0, Noto Emoji images Apache-2.0 (fonts OFL), OpenMoji CC BY-SA 4.0 and Microsoft Fluent Emoji MIT. Explains credits, share-alike and trademark limits."
---

# Open emoji artwork (Twemoji, Noto, OpenMoji, Fluent)

Use when a caption or reaction overlay needs emoji drawn consistently on every platform. Twemoji graphics are CC-BY 4.0, Noto Emoji images Apache-2.0 (fonts OFL), OpenMoji CC BY-SA 4.0 and Microsoft Fluent Emoji MIT. Explains credits, share-alike and trademark limits.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Twemoji (jdecked fork): graphics CC-BY 4.0, code MIT. Noto Emoji: fonts OFL 1.1, images and tools Apache 2.0, flags public domain. OpenMoji: graphics CC BY-SA 4.0. Fluent UI Emoji: repository MIT.

- `CC-BY-4.0`: Twemoji graphics - <https://github.com/jdecked/twemoji>
- `Apache-2.0`: Noto Emoji images - <https://github.com/googlefonts/noto-emoji>
- `CC-BY-SA-4.0`: OpenMoji graphics - <https://github.com/hfg-gmuend/openmoji>
- `MIT`: Fluent UI Emoji - <https://github.com/microsoft/fluentui-emoji>

Attribution: **per-asset**. Redistribution of the files: **allowed-with-licence**.
Commercial use: **allowed**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Depends on each asset's licence. When the asset requires credit, use:

```
Emoji: {set} ({licence})
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Twemoji](https://github.com/jdecked/twemoji)
- [Noto Emoji](https://github.com/googlefonts/noto-emoji)
- [OpenMoji](https://github.com/hfg-gmuend/openmoji)
- [Fluent UI Emoji](https://github.com/microsoft/fluentui-emoji)

## How to search

Pick one set per channel for a consistent look; Twemoji credit can go in the description; Noto images need only the
Apache notice if you redistribute files.

## Import into Godot 4

- Import SVG/PNG with `ui-lossless`; for text with emoji, use a colour emoji font as a fallback in the Theme.

## Import into Blender

- Use PNG renders as Images as Planes for floating reaction stickers.

## Pitfalls

- Emoji depicting brands or flags carry trademark/flag-use limits beyond the artwork licence.
- OpenMoji is share-alike: modified emoji must stay CC BY-SA 4.0.
- Platform emoji (Apple, Samsung) are not openly licensed; never screenshot them for overlays.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "twemoji-fire",
  "title": "Fire emoji (Twemoji)",
  "creator": "Twemoji contributors",
  "source_url": "https://github.com/jdecked/twemoji",
  "licence": "CC-BY-4.0",
  "licence_url": "https://creativecommons.org/licenses/by/4.0/deed.en",
  "attribution": "Emoji graphics: Twemoji, CC-BY 4.0",
  "attribution_required": true,
  "redistribution": "allowed-with-licence",
  "format": "svg",
  "intended_use": [
    "reaction sticker overlay"
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
