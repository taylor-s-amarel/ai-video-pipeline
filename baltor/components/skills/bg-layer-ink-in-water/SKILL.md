---
name: "bg-layer-ink-in-water"
description: "Use when a short needs the 'Ink in water' moving background or overlay layer: a seamless 8-second procedural ffmpeg loop (no downloads), default opacity and blend, measured motion, and how to source licensed footage instead."
---

# Ink in water

Dark ink clouds curling through clear water. Category: footage; usual stack role: background-video.

## When to use
- Chemistry
- art history
- reflective openers

## Layer defaults

| Setting | Value |
|---|---|
| Opacity | 0.9 (house cap 0.98) |
| Blend | normal |
| Motion | drift, seamless every 8 s |
| Size | 1080x1920 at 30 fps |



## Render the loop (procedural, no downloads)

```bash
ffmpeg -y -filter_complex "$(cat filtergraph.txt)" -map "[out]" -t 8 -r 30 \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart bg-layer-ink-in-water.mp4
# stretch the loop under a full-length edit
ffmpeg -y -stream_loop -1 -i bg-layer-ink-in-water.mp4 -t 64 -c copy bg-layer-ink-in-water-64s.mp4
```

`filtergraph.txt` builds the image with ffmpeg's `geq` (per-pixel expressions), `scroll`, `blend`, `displace`
and a `lutrgb` gradient map, at reduced working resolution where the look is soft, then scales to 1080x1920.
Every time term repeats every 8 s and every scrolled texture moves a whole tile per loop,
so the file loops without a seam. Tested with FFmpeg 6.1.1.

Colour stops (gray value -> colour): 0 `#F5F2EA`, 120 `#C9CFE0`, 180 `#4B5D8C`, 255 `#0E1736`.

## Use real footage instead

This layer looks best with real footage. Search for: "ink in water macro", "ink drop water slow motion"; prefer white background.

| Source | Site | Terms | Notes |
|---|---|---|---|
| Wikimedia Commons | https://commons.wikimedia.org/ | see each item page | Each file page states its author and licence (often CC BY, CC BY-SA or public domain). Use the page's own credit line. |
| NASA Image and Video Library | https://images.nasa.gov/ | https://www.nasa.gov/nasa-brand-center/images-and-media/ | NASA's guidelines say its media is generally not subject to US copyright; logos and insignia are not public domain, endorsement may not be implied, and some items are third-party and marked. |
| Pexels | https://www.pexels.com/ | https://www.pexels.com/license/ | Pexels License: free to use and modify, attribution appreciated but not required; do not sell unaltered copies, imply endorsement or show identifiable people in a bad light. |
| Pixabay | https://pixabay.com/ | https://pixabay.com/en/service/license/ | Pixabay Content License: free to use without attribution; no standalone redistribution, and restrictions on trademarks and recognisable people. |

- Accept: CC0-1.0; Public domain (check the item page, e.g. US federal government works); CC-BY-4.0 (credit the author in the post text); Pexels License (see terms_url); Pixabay Content License (see terms_url).
- Reject: Any NC (non-commercial) licence; Any ND (no-derivatives) licence; No stated licence; CC-BY-SA unless you accept ShareAlike terms for the finished video.
- Record for every clip: item page URL, author or agency, licence name and version, retrieval date, credit line, if required. Keep the clip outside this package and list it in your
  project's rights manifest. "Fair use" is not a licence; do not rely on it for stock backgrounds.
- Trim to a loop: `ffmpeg -ss 3 -i clip.mp4 -t 8 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" -an -c:v libx264 -crf 18 -pix_fmt yuv420p bg-layer-ink-in-water-footage.mp4`
- Keep the procedural loop below as the fallback when no suitable licensed clip exists.

## Put it in a stack

```bash
# [base] is everything below this layer; ffmpeg's blend uses the first input as the base
ffmpeg -i base.mp4 -i bg-layer-ink-in-water.mp4 -filter_complex \
  "[0:v]format=gbrp[a];[1:v]format=gbrp[b];[a][b]blend=all_mode=normal:all_opacity=0.9:shortest=1,format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -crf 18 stacked.mp4
```

For `normal` blending put the layer first (`[b][a]blend=all_mode=normal`), because ffmpeg's normal mode weights
the first input by the opacity. The `short_style_preset_kit` module's `layer_stack_filter` handles both orders for whole stacks.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `background_layer_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- ffmpeg filters (geq, scroll, blend, displace, lutrgb): https://ffmpeg.org/ffmpeg-filters.html
