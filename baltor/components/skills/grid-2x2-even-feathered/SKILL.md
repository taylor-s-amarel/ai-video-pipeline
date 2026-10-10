---
name: "grid-2x2-even-feathered"
description: "Use when you want four moving clips in a feathered 2x2 grid ('Even feathered 2x2') as a background layer or split-screen: exact cell geometry, opacities, mirroring and a ready ffmpeg graph."
---

# Even feathered 2x2

A 2x2 grid of moving sources for Vertical 9:16 (generic) (1080x1920), used as a background-layer with `screen` blending.

## When to use
- House stacks (layer 4)
- Any background that needs four kinds of motion

## Geometry

Gutter 24 px, margin 0 px, feather 32 px, corner radius 0 px.

| Cell | x | y | w | h | Source | Opacity | Mirror | Start offset s | Reveal s |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 0 | 528 | 948 | bg_layer_ocean_waves | 0.35 | - | 0 | 0 |
| 2 | 552 | 0 | 528 | 948 | bg_layer_meadow_wind | 0.35 | - | 0 | 0 |
| 3 | 0 | 972 | 528 | 948 | bg_layer_sunlit_water | 0.35 | - | 0 | 0 |
| 4 | 552 | 972 | 528 | 948 | bg_layer_coastal_aerial | 0.35 | - | 0 | 0 |

Each cell's alpha mask is a rounded rectangle whose edge fades linearly over the feather width, scaled by
the cell opacity (never above 0.98), so there are no hard rectangular cut-outs.

## Render it

```bash
ffmpeg -y -filter_complex "$(cat filtergraph.txt)" -map "[out]" -t 8 -r 30 \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart grid-2x2-even-feathered.mp4
```

The graph renders the four procedural cell loops and a base gradient itself, so it runs with no inputs. Masks are drawn once with `geq` and looped, then joined to each cell with `alphamerge` and placed
with `overlay`. A reveal delay fades a cell in over 0.4 s.

Hard-edged alternative (no gutter, no feather) with `xstack`:

```bash
ffmpeg -i a.mp4 -i b.mp4 -i c.mp4 -i d.mp4 -filter_complex \
  "[0:v]scale=540:960[a];[1:v]scale=540:960[b];[2:v]scale=540:960[c];[3:v]scale=540:960[d];[a][b][c][d]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[v]" \
  -map "[v]" -c:v libx264 -crf 18 -pix_fmt yuv420p grid-hard.mp4
```

In a stack, blend the grid at 35% or less with `screen` over the background
(`short_style_preset_kit.grid_2x2_filter` builds the same graph from `preset.json`).

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `grid_2x2_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- ffmpeg filters (alphamerge, overlay, xstack, geq): https://ffmpeg.org/ffmpeg-filters.html
