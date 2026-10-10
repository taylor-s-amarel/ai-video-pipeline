---
name: "layer-stack-pixel-retro-10"
description: "Use when composing a short's layers in the 'Pixel retro 10-layer stack' arrangement: every layer with source, opacity (max 98%), blend mode and motion, plus a ready ffmpeg graph for the procedural background layers."
---

# Pixel retro 10-layer stack

Nearest-neighbour pixel sky, scanlines and pixel lettering for game-style stories. Theme `meadow`, palette `palette_pixel_retro`, 1080x1920 at 30 fps.

## Layers (bottom to top)

| z | Layer | Role | Source | Opacity | Blend | Motion | Details |
|---|---|---|---|---|---|---|---|
| 1 | pixel_sky | background-video | `bg_layer_pixel_sky_parallax` | 0.95 | normal | scroll |  |
| 2 | lava | texture | `bg_layer_lava_blobs` | 0.12 | soft-light | drift |  |
| 3 | vignette | vignette | `bg_layer_vignette_breathe` | 0.35 | multiply | pulse |  |
| 4 | sprite_scene | photo | `pixel_scene` | 0.98 | normal | static | rect x0.05 y0.16 w0.9 h0.52; scale_filter: neighbor |
| 5 | title_panel | panel | `panel:title` | 0.7 | normal | static | backing: solid |
| 6 | title_text | title | `title_kinetic_slam_hook` | 0.98 | normal | keyframed | animation: text_anim_kinetic_slam |
| 7 | caption_panel | panel | `panel:caption` | 0.7 | normal | static | backing: solid |
| 8 | caption_text | caption | `caption_outline_bold_center` | 0.98 | normal | keyframed | animation: text_anim_typewriter |
| 9 | scanlines | overlay | `bg_layer_crt_scanlines` | 0.15 | overlay | loop |  |
| 10 | transition_flash | transition | `bg_layer_light_leaks` | 0.4 | screen | keyframed | opacity keyframes 0s:0.0 0.1s:0.4 0.2s:0.0; at: each cut |

Every opacity is at most 0.98 (house rule), at least one background layer moves at all times, and the photo
keeps at least 80% of the frame width with a feathered edge. Components named in the Source column are
other presets from this library (`bg_layer_*`, `grid_2x2_*`, `title_*`, `caption_*`, `text_anim_*`, `camera_*`).

Effects used:
- none

## Render it

1. Background loop: `background_filtergraph.txt` composites the full-frame procedural layers
   (pixel_sky, lava, vignette, scanlines) in z order with their blend modes and opacities.

   ```bash
   ffmpeg -y -filter_complex "$(cat background_filtergraph.txt)" -map "[out]" -t 8 -r 30 \
     -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart layer-stack-pixel-retro-10-bg.mp4
   ffmpeg -y -stream_loop -1 -i layer-stack-pixel-retro-10-bg.mp4 -t 64 -c copy layer-stack-pixel-retro-10-bg-64s.mp4
   ```

2. Photo pass: render each photo with its camera move preset (see the `camera` detail on the photo layer) and
   overlay it at the photo rectangle with its feather, shadow and rim effects.
3. Text pass: titles, labels and captions from their presets, as RGBA frames or drawtext filters, in z order.
4. Cut-timed layers (sprite_scene, title_panel, title_text, caption_panel, caption_text, transition_flash) are added around each cut or inside the photo rectangle.

To build a graph for your own inputs, give each layer an ffmpeg input index and let the kit write it:

```python
import json, sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
stack = json.load(open("preset.json"))
print(kit.layer_stack_problems(stack))            # [] when the house rules hold
layers = [dict(l, input=i) for i, l in enumerate(stack["layers"]) if l["source"]["kind"] == "component"]
print(kit.layer_stack_filter(layers, 1080, 1920, 30))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `layer_stack_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- ffmpeg filters (blend, overlay, alphamerge): https://ffmpeg.org/ffmpeg-filters.html
