---
name: "layer-stack-neon-explainer-20"
description: "Use when composing a short's layers in the 'Neon explainer 20-layer stack' arrangement: every layer with source, opacity (max 98%), blend mode and motion, plus a ready ffmpeg graph for the procedural background layers."
---

# Neon explainer 20-layer stack

Synthwave grid, scanlines and glow around a screen or photo for AI and tech explainers. Theme `night_city`, palette `palette_neon_night`, 1080x1920 at 30 fps.

## Layers (bottom to top)

| z | Layer | Role | Source | Opacity | Blend | Motion | Details |
|---|---|---|---|---|---|---|---|
| 1 | base_gradient | base | `bg_layer_gradient_drift` | 0.98 | normal | drift |  |
| 2 | neon_grid | background-video | `bg_layer_neon_grid` | 0.9 | normal | loop |  |
| 3 | facets | texture | `bg_layer_lowpoly_facets` | 0.2 | soft-light | drift |  |
| 4 | motion_grid | grid-2x2 | `grid_2x2_tight_mosaic (bg_layer_neon_grid, bg_layer_crt_scanlines, bg_layer_pixel_sky_parallax, bg_layer_lava_blobs)` | 0.25 | screen | loop |  |
| 5 | haze | haze | `bg_layer_atmospheric_haze` | 0.18 | screen | drift |  |
| 6 | light_leaks | light | `bg_layer_light_leaks` | 0.3 | screen | drift |  |
| 7 | bokeh | particles | `bg_layer_bokeh_drift` | 0.25 | screen | rise |  |
| 8 | vignette | vignette | `bg_layer_vignette_breathe` | 0.5 | multiply | pulse |  |
| 9 | photo_glow | light | `fx:rim_light` | 0.35 | screen | follow | follows: photo |
| 10 | photo | photo | `photo` | 0.98 | normal | ken-burns | rect x0.05 y0.16 w0.9 h0.52; feather 24 px; camera: camera_push_in_fast |
| 11 | photo_scanlines | overlay | `bg_layer_crt_scanlines` | 0.15 | overlay | loop | rect x0.05 y0.16 w0.9 h0.52 |
| 12 | title_panel | panel | `panel:title` | 0.66 | normal | static | backing: frosted-glass |
| 13 | title_text | title | `title_neon_sign_hook` | 0.98 | normal | keyframed | animation: text_anim_blur_in_focus |
| 14 | title_glow | light | `fx:text_glow` | 0.6 | screen | keyframed | follows: title_text |
| 15 | caption_panel | panel | `panel:caption` | 0.66 | normal | static | backing: frosted-glass |
| 16 | caption_text | caption | `caption_neon_glow` | 0.98 | normal | keyframed | animation: text_anim_blur_in_focus |
| 17 | caption_keyword | caption | `text_anim_keyword_pop_house` | 0.98 | normal | keyframed |  |
| 18 | scanlines | overlay | `bg_layer_crt_scanlines` | 0.12 | overlay | loop |  |
| 19 | global_grain | grain | `bg_layer_film_grain` | 0.06 | overlay | loop |  |
| 20 | transition_flash | transition | `bg_layer_light_leaks` | 0.5 | screen | keyframed | opacity keyframes 0s:0.0 0.15s:0.5 0.3s:0.0; at: each cut |

Every opacity is at most 0.98 (house rule), at least one background layer moves at all times, and the photo
keeps at least 80% of the frame width with a feathered edge. Components named in the Source column are
other presets from this library (`bg_layer_*`, `grid_2x2_*`, `title_*`, `caption_*`, `text_anim_*`, `camera_*`).

Effects used:
- `fx:rim_light`: The photo's feathered mask, blurred 24-40 px and filled with the palette light colour, screened behind the photo edge.
- `fx:text_glow`: The title's own alpha blurred 18 px and tinted with the palette accent.

## Render it

1. Background loop: `background_filtergraph.txt` composites the full-frame procedural layers
   (base_gradient, neon_grid, facets, motion_grid, haze, light_leaks, bokeh, vignette, scanlines, global_grain) in z order with their blend modes and opacities.

   ```bash
   ffmpeg -y -filter_complex "$(cat background_filtergraph.txt)" -map "[out]" -t 8 -r 30 \
     -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart layer-stack-neon-explainer-20-bg.mp4
   ffmpeg -y -stream_loop -1 -i layer-stack-neon-explainer-20-bg.mp4 -t 64 -c copy layer-stack-neon-explainer-20-bg-64s.mp4
   ```

2. Photo pass: render each photo with its camera move preset (see the `camera` detail on the photo layer) and
   overlay it at the photo rectangle with its feather, shadow and rim effects.
3. Text pass: titles, labels and captions from their presets, as RGBA frames or drawtext filters, in z order.
4. Cut-timed layers (photo_glow, photo, photo_scanlines, title_panel, title_text, title_glow, caption_panel, caption_text, caption_keyword, transition_flash) are added around each cut or inside the photo rectangle.

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
