---
name: "layer-stack-dreamy-soft-18"
description: "Use when composing a short's layers in the 'Dreamy soft 18-layer stack' arrangement: every layer with source, opacity (max 98%), blend mode and motion, plus a ready ffmpeg graph for the procedural background layers."
---

# Dreamy soft 18-layer stack

Silk, bokeh, haze and warm leaks for relationship and feelings topics. Theme `meadow`, palette `palette_relationship_blush`, 1080x1920 at 30 fps.

## Layers (bottom to top)

| z | Layer | Role | Source | Opacity | Blend | Motion | Details |
|---|---|---|---|---|---|---|---|
| 1 | base_gradient | base | `bg_layer_gradient_drift` | 0.98 | normal | drift |  |
| 2 | silk | background-video | `bg_layer_silk_waves` | 0.8 | normal | loop |  |
| 3 | clouds | background-video | `bg_layer_cloud_timelapse` | 0.25 | soft-light | loop |  |
| 4 | motion_grid | grid-2x2 | `grid_2x2_soft_vignette_grid (bg_layer_cloud_timelapse, bg_layer_silk_waves, bg_layer_atmospheric_haze, bg_layer_underwater_rays)` | 0.3 | screen | loop |  |
| 5 | haze | haze | `bg_layer_atmospheric_haze` | 0.25 | screen | drift |  |
| 6 | light_leaks | light | `bg_layer_light_leaks` | 0.32 | screen | drift |  |
| 7 | bokeh_far | particles | `bg_layer_bokeh_drift` | 0.28 | screen | rise |  |
| 8 | fireflies | particles | `bg_layer_fireflies` | 0.2 | screen | drift |  |
| 9 | vignette | vignette | `bg_layer_vignette_breathe` | 0.35 | multiply | pulse |  |
| 10 | photo_shadow | shadow | `fx:photo_shadow` | 0.35 | multiply | follow | follows: photo; blur_px: 50; offset_px: [0, 20] |
| 11 | photo | photo | `photo` | 0.98 | normal | rotate | rect x0.05 y0.16 w0.9 h0.52; feather 64 px; camera: camera_slow_rotate_drift |
| 12 | bokeh_near | particles | `bg_layer_bokeh_drift` | 0.14 | screen | parallax | speed: 1.4; scale: 1.6 |
| 13 | title_panel | panel | `panel:title` | 0.74 | normal | static | backing: frosted-glass |
| 14 | title_text | title | `title_minimal_serif_white` | 0.98 | normal | keyframed | animation: text_anim_blur_in_focus |
| 15 | caption_panel | panel | `panel:caption` | 0.74 | normal | static | backing: pill |
| 16 | caption_text | caption | `caption_pill_per_line` | 0.98 | normal | keyframed | animation: text_anim_springy_pop_overshoot |
| 17 | global_grain | grain | `bg_layer_film_grain` | 0.06 | overlay | loop |  |
| 18 | colour_grade | grade | `palette_relationship_blush` | 0.35 | soft-light | static |  |

Every opacity is at most 0.98 (house rule), at least one background layer moves at all times, and the photo
keeps at least 80% of the frame width with a feathered edge. Components named in the Source column are
other presets from this library (`bg_layer_*`, `grid_2x2_*`, `title_*`, `caption_*`, `text_anim_*`, `camera_*`).

Effects used:
- `fx:photo_shadow`: Blurred copy of the photo's alpha mask, filled with the palette background colour, offset and multiplied under the photo.

## Render it

1. Background loop: `background_filtergraph.txt` composites the full-frame procedural layers
   (base_gradient, silk, clouds, motion_grid, haze, light_leaks, bokeh_far, fireflies, vignette, bokeh_near, global_grain, colour_grade) in z order with their blend modes and opacities.

   ```bash
   ffmpeg -y -filter_complex "$(cat background_filtergraph.txt)" -map "[out]" -t 8 -r 30 \
     -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart layer-stack-dreamy-soft-18-bg.mp4
   ffmpeg -y -stream_loop -1 -i layer-stack-dreamy-soft-18-bg.mp4 -t 64 -c copy layer-stack-dreamy-soft-18-bg-64s.mp4
   ```

2. Photo pass: render each photo with its camera move preset (see the `camera` detail on the photo layer) and
   overlay it at the photo rectangle with its feather, shadow and rim effects.
3. Text pass: titles, labels and captions from their presets, as RGBA frames or drawtext filters, in z order.
4. Cut-timed layers (photo_shadow, photo, title_panel, title_text, caption_panel, caption_text) are added around each cut or inside the photo rectangle.

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
