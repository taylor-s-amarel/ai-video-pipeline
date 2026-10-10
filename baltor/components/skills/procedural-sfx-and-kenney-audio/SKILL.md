---
name: "procedural-sfx-and-kenney-audio"
description: "Use when a short or Godot scene needs clicks, pops, whooshes, coins or impacts. Start with Kenney's CC0 audio packs, or synthesise original effects with ZzFX (MIT), jsfxr (Unlicense) or rFXGen (zlib) so no third-party sample is involved. Covers recording parameters as provenance and import."
---

# Sound effects - Kenney CC0 audio and procedural generators (ZzFX, jsfxr, rFXGen)

Use when a short or Godot scene needs clicks, pops, whooshes, coins or impacts. Start with Kenney's CC0 audio packs, or synthesise original effects with ZzFX (MIT), jsfxr (Unlicense) or rFXGen (zlib) so no third-party sample is involved. Covers recording parameters as provenance and import.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Kenney audio packs are CC0. ZzFX is MIT, jsfxr Unlicense, rFXGen zlib/libpng, Bfxr Apache-2.0; those licences cover the tools, and the sounds you synthesise from your own parameters are your own work (record the parameters).

- `CC0-1.0`: Kenney audio packs - <https://kenney.nl/support>
- `MIT`: ZzFX - <https://github.com/KilledByAPixel/ZzFX>
- `Unlicense`: jsfxr - <https://github.com/chr15m/jsfxr>
- `Zlib`: rFXGen - <https://github.com/raysan5/rfxgen>

Attribution: **optional**. Redistribution of the files: **allowed**.
Commercial use: **allowed**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required (CC0 or equivalent). A courtesy credit, if you give one:

```
Sound effects: Kenney (CC0) / generated with ZzFX
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Kenney audio packs](https://kenney.nl/assets/category:Audio)
- [Kenney Interface Sounds](https://kenney.nl/assets/interface-sounds)
- [ZzFX](https://github.com/KilledByAPixel/ZzFX)
- [rFXGen](https://github.com/raysan5/rfxgen)

## How to search

Use Kenney Interface Sounds for caption pops and UI clicks, RPG Audio for foley, Casino Audio for reveals.
For a unique sound, generate it (rFXGen CLI presets: coin, laser, explosion, powerup, hit, jump, blip) and save
the .rfx/parameter file next to the WAV.

## Import into Godot 4

- WAV for short effects (import as AudioStreamWAV), OGG for loops (enable Loop); play via AudioStreamPlayer.

## Import into Blender

- Add sounds as Sound strips in the Video Sequencer for animatics.

## Pitfalls

- Keep the generator name and parameter array in the manifest so the effect can be regenerated.
- Keep effects about 6-10 dB under narration peaks so captions stay audible.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "kenney-interface-sounds",
  "title": "Interface Sounds",
  "creator": "Kenney",
  "source_url": "https://kenney.nl/assets/interface-sounds",
  "licence": "CC0-1.0",
  "licence_url": "https://kenney.nl/support",
  "attribution": "Interface Sounds by Kenney (kenney.nl), CC0",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "zip",
  "intended_use": [
    "caption pop and click sounds"
  ],
  "fetch": {
    "method": "manual-page",
    "status": "to-fetch"
  },
  "import_hints": {
    "video": {
      "role": "sfx"
    }
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
