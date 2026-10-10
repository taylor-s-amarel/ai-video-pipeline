---
description: "Build a licence-checked media pack manifest for a project"
argument-hint: "<project idea, e.g. 'top-down maze short about one small adjustment'>"
---

Build an agent media pack manifest for: $ARGUMENTS

1. Decide the look (2D pixel, flat vector, low-poly 3D, photoreal HDRI) and the delivery (1080x1920 video, Godot 4 scene, Blender render).
2. Start from the closest starter-pack skill (stick-figure, low-poly diorama, top-down maze, platformer, isometric town,
   space/NASA, nature backgrounds, UI/caption, farm diorama, this-vs-that, history, animal crowd) and its `pack.json`.
3. Add or swap assets only from sources whose source skill lists a licence you can meet. Prefer CC0; record CC-BY credits.
4. Write `pack.json` that validates against the `agent_media_pack_manifest` schema: one entry per asset with source_url,
   licence, licence_url, exact attribution, redistribution, format, intended_use, fetch method and import hints.
5. Run `python3 asset_licence_checker.py pack.json --use monetised-video` and fix every error.
6. Run `python3 media_pack_fetcher.py pack.json --out assets/<pack> --dry-run`, then without --dry-run; download
   manual-page assets by hand and record their sha256.
7. Commit the manifest, lock file and CREDITS.md - never project-only files.
