---
name: "mixamo-characters-and-animations"
description: "Use when a humanoid needs quick rigging or mocap-style animations from Adobe Mixamo. Mixamo content is royalty free inside your projects, but raw character/animation files may not be redistributed or used to train ML models. Covers keeping files out of repos and packages, Godot retargeting and Blender."
---

# Mixamo characters and animations (use in work, never redistribute raw files)

Use when a humanoid needs quick rigging or mocap-style animations from Adobe Mixamo. Mixamo content is royalty free inside your projects, but raw character/animation files may not be redistributed or used to train ML models. Covers keeping files out of repos and packages, Godot retargeting and Blender.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Adobe's FAQ: Mixamo characters and animations are royalty free for personal, commercial and non-profit projects. The fuller licensing FAQ (reposted on Adobe's forum) says the raw files may not be distributed, including in asset packs or engine templates, and may not be used to train machine-learning models.

- `Adobe-Mixamo-terms`: all Mixamo characters and animations - <https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html>

Attribution: **never**. Redistribution of the files: **forbidden**.
Commercial use: **allowed**. Automated downloading: **forbidden**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Not required by the terms. If you mention the source, keep it to:

```
Animation: Adobe Mixamo
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Mixamo](https://www.mixamo.com/)
- [Animate characters (Adobe Help)](https://helpx.adobe.com/creative-cloud/help/animate-characters-mixamo.html)
- [Licensing FAQ repost](https://community.adobe.com/questions-696/mixamo-faq-licensing-royalties-ownership-eula-and-tos-589400)

## How to search

Sign in with an Adobe ID, upload or pick a character, search animations, set In Place for loops, and download FBX
(With Skin for the first clip, Without Skin for the rest). Store the files in a git-ignored folder and list each
clip in the media pack manifest with fetch.method manual-page. For redistributable projects use the CC0
Quaternius Universal Animation Library instead.

## Import into Godot 4

- Import the FBX (ufbx in Godot 4.3+). In Advanced Import Settings add a BoneMap with SkeletonProfileHumanoid so
  Mixamo bone names map and clips retarget; enable Fix Silhouette for A-pose rigs.
- Save clips into an AnimationLibrary resource that stays in the ignored folder.

## Import into Blender

- `bpy.ops.import_scene.fbx(filepath="Running.fbx")`; check the armature's scale after import (FBX files often
  arrive scaled for centimetre units) and apply scale before mixing with other rigs.

## Pitfalls

- Never commit Mixamo FBX/DAE files to a public repository, a template or a Baltor package; record them with redistribution: forbidden.
- Do not use Mixamo files as machine-learning training data.
- Bipedal humanoids only; the site keeps only the last uploaded character.
- A Godot or Blender project that embeds the raw Mixamo clips is a redistribution if you publish the project.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "mixamo-run-cycle",
  "title": "Running (Mixamo)",
  "creator": "Adobe Mixamo",
  "source_url": "https://www.mixamo.com/",
  "licence": "Adobe Mixamo terms",
  "licence_url": "https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html",
  "attribution": "",
  "attribution_required": false,
  "redistribution": "forbidden",
  "ai_training": "forbidden",
  "format": "fbx",
  "intended_use": [
    "character run cycle in a rendered short"
  ],
  "restrictions": [
    "Keep the FBX out of repositories and packages.",
    "Not for ML training."
  ],
  "fetch": {
    "method": "manual-page",
    "status": "manual"
  },
  "import_hints": {
    "godot": {
      "importer": "scene",
      "notes": "BoneMap + SkeletonProfileHumanoid"
    },
    "blender": {
      "operator": "bpy.ops.import_scene.fbx"
    }
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
