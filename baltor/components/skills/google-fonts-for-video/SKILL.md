---
name: "google-fonts-for-video"
description: "Use when picking caption, hook-title or pixel fonts for shorts and Godot UI. Most Google Fonts are SIL OFL 1.1 (a few Apache-2.0), Kenney Fonts are CC0. Covers verifying a family's licence in the google/fonts repo, what OFL allows in videos, and Godot/Blender font import."
---

# Google Fonts and Kenney fonts for captions and titles (OFL, Apache, CC0)

Use when picking caption, hook-title or pixel fonts for shorts and Godot UI. Most Google Fonts are SIL OFL 1.1 (a few Apache-2.0), Kenney Fonts are CC0. Covers verifying a family's licence in the google/fonts repo, what OFL allows in videos, and Godot/Blender font import.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

google/fonts groups files by licence folder (ofl/, apache/, ufl/); most families are SIL OFL 1.1. OFL fonts may be embedded and redistributed with software but not sold alone; documents (and renders) made with them are not bound by the licence. Kenney Fonts are CC0.

- `OFL-1.1`: families in ofl/ - <https://openfontlicense.org/open-font-license-official-text/>
- `Apache-2.0`: families in apache/ (e.g. Luckiest Guy) - <https://github.com/google/fonts/tree/main/apache>
- `CC0-1.0`: Kenney Fonts - <https://kenney.nl/assets/kenney-fonts>

Attribution: **never**. Redistribution of the files: **allowed-with-licence**.
Commercial use: **allowed**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required by the terms. If you mention the source, keep it to:

```
Font: {family} ({licence})
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [google/fonts repository](https://github.com/google/fonts)
- [Google Fonts FAQ](https://developers.google.com/fonts/faq?tid=311165647)
- [Bebas Neue](https://fonts.google.com/specimen/Bebas%2BNeue)
- [Montserrat licence tab](https://fonts.google.com/specimen/Montserrat/license)
- [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P)
- [Kenney Fonts](https://kenney.nl/assets/kenney-fonts)

## How to search

Pick on fonts.google.com, then confirm the licence by finding the family folder in google/fonts (ofl/<family> with
OFL.txt, or apache/<family>). Bold condensed faces (Bebas Neue, Anton) suit hook titles; Montserrat, Poppins and
Inter suit one-line captions; Press Start 2P, Pixelify Sans, Silkscreen and VT323 suit pixel scenes.

## Import into Godot 4

- Drop the TTF/OTF into the project; it imports as FontFile. For pixel fonts disable antialiasing and use
  integer sizes (Press Start 2P works best at multiples of 8 px).

## Import into Blender

- `bpy.data.fonts.load("/path/BebasNeue-Regular.ttf")`, then assign to a text object's data.font.

## Pitfalls

- Never sell or bundle a font file alone; keep OFL.txt next to any redistributed font.
- Check the folder: a family under apache/ is Apache-2.0, not OFL.
- Video tools that burn subtitles need the font installed or passed explicitly (FFmpeg subtitles filter fontsdir).

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "bebas-neue",
  "title": "Bebas Neue Regular",
  "creator": "Ryoichi Tsunekawa",
  "source_url": "https://fonts.google.com/specimen/Bebas%2BNeue",
  "licence": "OFL-1.1",
  "licence_url": "https://github.com/google/fonts/tree/main/ofl/bebasneue",
  "attribution": "Font: Bebas Neue by Ryoichi Tsunekawa (SIL OFL 1.1)",
  "attribution_required": false,
  "redistribution": "allowed-with-licence",
  "format": "ttf",
  "intended_use": [
    "bold hook title"
  ],
  "fetch": {
    "method": "manual-page",
    "status": "to-fetch"
  },
  "import_hints": {
    "godot": {
      "importer": "font"
    },
    "video": {
      "role": "font"
    }
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
