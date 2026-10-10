---
name: "mocap-dataset-licences"
description: "Use before pulling motion capture into a short or a game. Many free mocap sets are research or non-commercial (Bandai Namco: CC BY-NC; a CMU FBX conversion: CC BY-NC), Mixamo forbids redistribution, and Quaternius offers CC0 humanoid clips. Explains choosing and recording them."
---

# Motion-capture datasets and their licences (CC0 alternatives first)

Use before pulling motion capture into a short or a game. Many free mocap sets are research or non-commercial (Bandai Namco: CC BY-NC; a CMU FBX conversion: CC BY-NC), Mixamo forbids redistribution, and Quaternius offers CC0 humanoid clips. Explains choosing and recording them.

Checked on 2026-10-10. Machine-readable profile: `source.json` (schema `asset_source_profile`).

## Licence in one paragraph

Bandai Namco Research Motion Dataset: CC BY-NC 4.0 per its README (press reports say BY-NC-ND). The 4TU FBX conversion of CMU mocap is labelled CC BY-NC 4.0. Quaternius Universal Animation Library is CC0.

- `CC-BY-NC-4.0`: Bandai Namco BVH datasets - <https://github.com/BandaiNamcoResearchInc/Bandai-Namco-Research-Motiondataset>
- `CC-BY-NC-4.0`: 4TU FBX conversion of CMU mocap - <https://data.4tu.nl/datasets/0448aab2-3332-449f-a8e2-d208cb58c7df>
- `CC0-1.0`: Quaternius Universal Animation Library - <https://quaternius.com/packs/universalanimationlibrary.html>

Attribution: **per-asset**. Redistribution of the files: **per-asset**.
Commercial use: **per-asset**. Automated downloading: **allowed**.
Fair use is a defence, not a licence: if the terms above do not cover your use, do not use the asset.

## Exact credit line

Depends on each asset's licence. When the asset requires credit, use:

```
Motion data: {dataset} ({licence})
```

The `media_pack_fetcher` module writes `CREDITS.md` from the manifest; copy required lines into the video
description or end card.

## Where to look

- [Bandai Namco motion dataset](https://github.com/BandaiNamcoResearchInc/Bandai-Namco-Research-Motiondataset)
- [CMU mocap FBX conversion (4TU)](https://data.4tu.nl/datasets/0448aab2-3332-449f-a8e2-d208cb58c7df)
- [Quaternius Universal Animation Library (CC0)](https://quaternius.com/packs/universalanimationlibrary.html)

## How to search

Decide the use first (monetised video, open-source game, research). For monetised or redistributed work use CC0
clips; record research datasets with commercial_use non-commercial-only so the licence checker blocks misuse.

## Import into Godot 4

- Import BVH via Blender (Godot does not import BVH directly), export GLB, then retarget with SkeletonProfileHumanoid.

## Import into Blender

- File > Import > Motion Capture (.bvh); retarget onto your rig, then export GLB.

## Pitfalls

- Non-commercial datasets cannot appear in monetised shorts.
- Read each dataset's LICENSE file; converters can add their own terms.
- A non-commercial clip baked into a commercial video is still a licence breach.

## Manifest entry template

Add one entry per asset to the project's media pack manifest (`agent_media_pack_manifest` schema):

```json
{
  "id": "bandai-dataset-1",
  "title": "Bandai Namco Research Motion Dataset 1",
  "creator": "Bandai Namco Research Inc.",
  "source_url": "https://github.com/BandaiNamcoResearchInc/Bandai-Namco-Research-Motiondataset",
  "licence": "CC-BY-NC-4.0",
  "licence_url": "https://github.com/BandaiNamcoResearchInc/Bandai-Namco-Research-Motiondataset",
  "attribution": "Motion: Bandai Namco Research Motion Dataset (CC BY-NC 4.0)",
  "attribution_required": true,
  "redistribution": "allowed-with-licence",
  "commercial_use": "non-commercial-only",
  "format": "bvh",
  "intended_use": [
    "non-commercial motion study"
  ],
  "fetch": {
    "method": "git",
    "status": "to-fetch"
  },
  "verification": {
    "on": "2026-10-10",
    "how": "manual"
  }
}
```

Then run `python asset_licence_checker.py pack.json --use monetised-video` before rendering.
