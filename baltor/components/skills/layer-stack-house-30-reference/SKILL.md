---
name: "layer-stack-house-30-reference"
description: "Use when composing a short's layers in the 'House 30-layer reference stack' arrangement: every layer with source, opacity (max 98%), blend mode and motion, plus a ready ffmpeg graph for the procedural background layers."
---

# House 30-layer reference stack

The full 30-layer reference for house-style shorts; every layer under 98% opacity, a moving background throughout, the photo at 90% width with a feathered edge. Theme `ocean`, palette `palette_ocean_deep`, 1080x1920 at 30 fps.

## Layers (bottom to top)

| z | Layer | Role | Source | Opacity | Blend | Motion | Details |
|---|---|---|---|---|---|---|---|
| 1 | base_gradient | base | `bg_layer_gradient_drift` | 0.98 | normal | drift |  |
| 2 | footage_primary | background-video | `bg_layer_ocean_waves` | 0.92 | normal | loop |  |
| 3 | footage_secondary | background-video | `bg_layer_sunlit_water` | 0.35 | soft-light | loop |  |
| 4 | motion_grid | grid-2x2 | `grid_2x2_even_feathered (bg_layer_ocean_waves, bg_layer_meadow_wind, bg_layer_sunlit_water, bg_layer_coastal_aerial)` | 0.35 | screen | loop |  |
| 5 | haze | haze | `bg_layer_atmospheric_haze` | 0.22 | screen | drift |  |
| 6 | light_leaks | light | `bg_layer_light_leaks` | 0.28 | screen | drift |  |
| 7 | bokeh_far | particles | `bg_layer_bokeh_drift` | 0.22 | screen | rise |  |
| 8 | dust | particles | `bg_layer_dust_particles` | 0.3 | screen | rise |  |
| 9 | light_rays | light | `bg_layer_underwater_rays` | 0.18 | screen | sway |  |
| 10 | colour_wash | overlay | `accent` | 0.12 | soft-light | pulse | opacity keyframes 0s:0.08 4s:0.14 8s:0.08 |
| 11 | vignette | vignette | `bg_layer_vignette_breathe` | 0.5 | multiply | pulse |  |
| 12 | photo_shadow | shadow | `fx:photo_shadow` | 0.45 | multiply | follow | follows: photo; blur_px: 40; offset_px: [0, 18] |
| 13 | photo | photo | `photo` | 0.98 | normal | ken-burns | rect x0.05 y0.16 w0.9 h0.52; feather 48 px; camera: camera_ken_burns_in_upper_third |
| 14 | photo_rim_light | light | `fx:rim_light` | 0.2 | screen | follow | follows: photo |
| 15 | photo_grain | grain | `bg_layer_film_grain` | 0.08 | overlay | loop | rect x0.05 y0.16 w0.9 h0.52 |
| 16 | bokeh_near | particles | `bg_layer_bokeh_drift` | 0.16 | screen | parallax | speed: 1.4; scale: 1.6 |
| 17 | title_shadow | shadow | `fx:panel_shadow` | 0.3 | multiply | static | follows: title_panel |
| 18 | title_panel | panel | `panel:title` | 0.62 | normal | static | backing: frosted-glass |
| 19 | title_text | title | `title_house_yellow_hook` | 0.98 | normal | keyframed | animation: text_anim_settle_in; visible_from_s: 0.0 |
| 20 | title_light_sweep | light | `fx:light_sweep` | 0.25 | add | keyframed | window_s: [0.3, 0.9] |
| 21 | label_panel | panel | `panel:label` | 0.62 | normal | keyframed | animation: text_anim_springy_pop_overshoot |
| 22 | label_text | label | `title_fact_number_label` | 0.98 | normal | keyframed | animation: text_anim_springy_pop_overshoot |
| 23 | key_number | number | `text_anim_count_up_number` | 0.98 | normal | keyframed |  |
| 24 | caption_panel | panel | `panel:caption` | 0.62 | normal | static | backing: frosted-glass |
| 25 | caption_text | caption | `caption_frosted_keyword_pop` | 0.98 | normal | keyframed | animation: text_anim_fade_up_soft |
| 26 | caption_keyword | caption | `text_anim_keyword_pop_house` | 0.98 | normal | keyframed |  |
| 27 | global_grain | grain | `bg_layer_film_grain` | 0.08 | overlay | loop |  |
| 28 | edge_feather | vignette | `fx:edge_feather` | 0.3 | multiply | static |  |
| 29 | transition_flash | transition | `bg_layer_light_leaks` | 0.6 | screen | keyframed | opacity keyframes 0s:0.0 0.16s:0.6 0.32s:0.0; at: each cut |
| 30 | colour_grade | grade | `palette_ocean_deep` | 0.4 | soft-light | static |  |

Every opacity is at most 0.98 (house rule), at least one background layer moves at all times, and the photo
keeps at least 80% of the frame width with a feathered edge. Components named in the Source column are
other presets from this library (`bg_layer_*`, `grid_2x2_*`, `title_*`, `caption_*`, `text_anim_*`, `camera_*`).

Effects used:
- `fx:photo_shadow`: Blurred copy of the photo's alpha mask, filled with the palette background colour, offset and multiplied under the photo.
- `fx:rim_light`: The photo's feathered mask, blurred 24-40 px and filled with the palette light colour, screened behind the photo edge.
- `fx:panel_shadow`: The panel's mask blurred 20 px, offset 8 px down, multiplied.
- `fx:light_sweep`: A 30-degree soft white band (gaussian, 120 px wide) crossing the title once, added at low opacity.
- `fx:edge_feather`: A rounded-rectangle mask with a 60 px feather at the frame edge, multiplied to soften the borders.

## Render it

1. Background loop: `background_filtergraph.txt` composites the full-frame procedural layers
   (base_gradient, footage_primary, footage_secondary, motion_grid, haze, light_leaks, bokeh_far, dust, light_rays, vignette, bokeh_near, global_grain, colour_grade) in z order with their blend modes and opacities.

   ```bash
   ffmpeg -y -filter_complex "$(cat background_filtergraph.txt)" -map "[out]" -t 8 -r 30 \
     -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart layer-stack-house-30-reference-bg.mp4
   ffmpeg -y -stream_loop -1 -i layer-stack-house-30-reference-bg.mp4 -t 64 -c copy layer-stack-house-30-reference-bg-64s.mp4
   ```

2. Photo pass: render each photo with its camera move preset (see the `camera` detail on the photo layer) and
   overlay it at the photo rectangle with its feather, shadow and rim effects.
3. Text pass: titles, labels and captions from their presets, as RGBA frames or drawtext filters, in z order.
4. Cut-timed layers (colour_wash, photo_shadow, photo, photo_rim_light, photo_grain, title_shadow, title_panel, title_text, title_light_sweep, label_panel, label_text, key_number, caption_panel, caption_text, caption_keyword, edge_feather, transition_flash) are added around each cut or inside the photo rectangle.

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
