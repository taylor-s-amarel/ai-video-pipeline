---
name: "lottiefiles-animations"
description: "Use when a short needs vector motion overlays (confetti, arrows, icons, loaders) from LottieFiles. Free animations use the Lottie Simple License: commercial use allowed, modifications stay under the same licence, no compiling a competing library. Covers checks with the Lottie inspector and rendering."
---

# LottieFiles free animations (Lottie Simple License)

Use when a short needs vector motion overlays (confetti, arrows, icons, loaders) from LottieFiles. Free animations use the Lottie Simple License: commercial use allowed, modifications stay under the same licence, no compiling a competing library. Covers checks with the Lottie inspector and rendering.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Lottie Simple License: download, modify, publish and distribute public files including commercially; derivatives stay under the same licence; no collecting files to build a similar or competing service; attribution encouraged, not required. The help centre adds: do not resell or redistribute originals as standalone files.

- `Lottie-Simple-License`: free public animations - <https://lottiefiles.com/page/license>

Attribution: **optional**. Redistribution of the files: **project-only**.
Commercial use: **allowed**. Automated downloading: **forbidden**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required (CC0 or equivalent). A courtesy credit, if you give one:

```
Animation: "{title}" by {creator} on LottieFiles (Lottie Simple License)
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Lottie Simple License](https://lottiefiles.com/page/license)
- [Commercial use (help)](https://help.lottiefiles.com/hc/en-us/articles/900002438343-Can-I-use-a-free-animation-on-Lottiefiles-for-commercial-business-use)
- [lottie-web player](https://github.com/airbnb/lottie-web)
- [dotlottie-web player](https://github.com/LottieFiles/dotlottie-web)

## How to search

Download the Lottie JSON or .lottie by hand, run `lottie_json_inspector anim.json --target 1080x1920`, and fix
anything it flags (external images, fonts, expressions) before rendering.

## Import into Godot 4

- Godot's built-in vector support uses ThorVG for SVG; for Lottie, render frames to PNG (lottie-web in a headless
  browser) and play them as a SpriteFrames animation, or use a maintained addon after checking its licence.

## Import into Blender

- Render the Lottie to a PNG sequence and load it as an image sequence on a plane.

## Pitfalls

- Do not bulk-collect LottieFiles animations into a library, package or service.
- Creators can add restrictions on individual animations; read each page.
- Expressions and text layers often render differently across players; prefer shape-only animations.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "lottie-confetti",
  "title": "Confetti burst (fill in)",
  "creator": "LottieFiles creator (fill in)",
  "source_url": "https://lottiefiles.com/page/license",
  "licence": "Lottie Simple License",
  "licence_url": "https://lottiefiles.com/page/license",
  "attribution": "Animation by Creator on LottieFiles",
  "attribution_required": false,
  "redistribution": "project-only",
  "format": "json-lottie",
  "intended_use": [
    "celebration overlay at the reveal"
  ],
  "fetch": {
    "method": "manual-page",
    "status": "manual"
  },
  "import_hints": {
    "video": {
      "role": "overlay"
    }
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
