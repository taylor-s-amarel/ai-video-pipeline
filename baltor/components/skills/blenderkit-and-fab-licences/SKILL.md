---
name: "blenderkit-and-fab-licences"
description: "Use when an asset comes from BlenderKit (Royalty Free or CC0) or Epic's Fab (Fab Standard License, formerly Megascans). These are not CC licences: use inside your work is broad, but redistributing the asset files is not allowed. Explains how to keep them out of repositories and Baltor packages."
---

# Royalty-free marketplaces (BlenderKit, Fab) - what you may not do

Use when an asset comes from BlenderKit (Royalty Free or CC0) or Epic's Fab (Fab Standard License, formerly Megascans). These are not CC licences: use inside your work is broad, but redistributing the asset files is not allowed. Explains how to keep them out of repositories and Baltor packages.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

BlenderKit Royalty Free: commercial use without credit, but no resale or redistribution of the asset itself (including inside asset packs or game levels sold on marketplaces); BlenderKit also hosts CC0 assets. Fab Standard License: use in any engine or tool under Epic's terms; files are licensed to the claiming account.

- `BlenderKit-Royalty-Free`: BlenderKit RF assets - <https://www.blenderkit.com/docs/licenses/>
- `Fab-Standard-License`: Fab/Megascans (read the current licence on fab.com) - <https://www.cgchannel.com/2024/10/epic-games-has-made-megascans-free-to-all-but-only-until-the-end-of-2024/>

Attribution: **never**. Redistribution of the files: **project-only**.
Commercial use: **allowed**. Automated downloading: **forbidden**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required by the terms. If you mention the source, keep it to:

```
Asset: {title} ({marketplace}), used under {licence}
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [BlenderKit licences](https://www.blenderkit.com/docs/licenses/)
- [Fab launch (Sketchfab blog)](https://sketchfab.com/blogs/community/epics-unified-marketplace-fab-launches-today)

## How to search

Prefer CC0 sources first. When a marketplace asset is the only option, record it with redistribution
`project-only`, keep the files in an ignored local folder, and render them into the final video only.

## Import into Godot 4

- Keep marketplace assets in a `.gitignore`d folder (for example `res://_licensed/`) and ship the project
  without them; the media pack manifest tells the next person what to download.

## Import into Blender

- Link or append from a local library outside the repository; pack textures only in local renders.

## Pitfalls

- Never commit Royalty Free or Fab files to a public repository or a Baltor package; ship a manifest entry with redistribution: project-only.
- Fab terms changed in 2024-2025; re-read the current Fab Standard License before each project.
- A downloaded .blend that embeds RF textures is still the RF asset; do not share it.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "blenderkit-rf-chair",
  "title": "Example BlenderKit Royalty Free chair (fill in)",
  "creator": "BlenderKit author (fill in)",
  "source_url": "https://www.blenderkit.com/docs/licenses/",
  "licence": "BlenderKit Royalty Free",
  "licence_url": "https://www.blenderkit.com/docs/licenses/",
  "attribution": "",
  "attribution_required": false,
  "redistribution": "project-only",
  "format": "blend",
  "intended_use": [
    "rendered prop only"
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
