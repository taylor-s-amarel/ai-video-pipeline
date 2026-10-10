---
name: "avatar-generators-for-faceless-video"
description: "Use when a faceless channel needs a consistent narrator or 'commenter' avatars without photos of real people. DiceBear (MIT code, per-style artwork licences), Boring Avatars (MIT, abstract), and Notion Avatar (MIT code, CC0 assets) generate SVG avatars deterministically. Warns about the NC xkcd font."
---

# Avatar generators for faceless narrators (DiceBear, Boring Avatars, Notion Avatar)

Use when a faceless channel needs a consistent narrator or 'commenter' avatars without photos of real people. DiceBear (MIT code, per-style artwork licences), Boring Avatars (MIT, abstract), and Notion Avatar (MIT code, CC0 assets) generate SVG avatars deterministically. Warns about the NC xkcd font.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

DiceBear code is MIT and each avatar style keeps its creator's licence (many need attribution). Boring Avatars is MIT. Notion Avatar code is MIT and its assets CC0. The xkcd font (ipython/xkcd-font) is CC BY-NC 3.0 and not for monetised work.

- `MIT`: DiceBear code - <https://github.com/dicebear/dicebear>
- `MIT`: Boring Avatars - <https://github.com/boringdesigners/boring-avatars>
- `CC0-1.0`: Notion Avatar assets - <https://github.com/Mayandev/notion-avatar>

Attribution: **per-asset**. Redistribution of the files: **per-asset**.
Commercial use: **per-asset**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Depends on each asset's licence. When the asset requires credit, use:

```
Avatar style "{style}" by {artist} via DiceBear ({licence})
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [DiceBear](https://github.com/dicebear/dicebear)
- [Boring Avatars](https://github.com/boringdesigners/boring-avatars)
- [Notion Avatar](https://github.com/Mayandev/notion-avatar)

## How to search

Seed avatars with a stable string (channel or character name) so they stay identical across videos; export SVG
and render to PNG at 4x for crisp scaling.

## Import into Godot 4

- Import SVG with `ui-lossless` and a high svg/scale; animate with Tween (bob, blink by swapping frames).

## Import into Blender

- Import SVG as curves for a 2.5D narrator card.

## Pitfalls

- Check the licence of the specific DiceBear style before using it on screen.
- Avoid the xkcd font for monetised stick-figure videos (CC BY-NC 3.0).
- Do not generate avatars that resemble real, identifiable people.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "notion-narrator",
  "title": "Narrator avatar (Notion Avatar)",
  "creator": "Notion Avatar assets",
  "source_url": "https://github.com/Mayandev/notion-avatar",
  "licence": "CC0-1.0",
  "licence_url": "https://github.com/Mayandev/notion-avatar",
  "attribution": "Narrator avatar made with Notion Avatar (assets CC0)",
  "attribution_required": false,
  "redistribution": "allowed",
  "format": "svg",
  "intended_use": [
    "faceless narrator portrait"
  ],
  "fetch": {
    "method": "manual-page",
    "status": "to-fetch"
  },
  "import_hints": {
    "godot": {
      "importer": "texture",
      "preset": "ui-lossless"
    },
    "video": {
      "role": "character"
    }
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
