---
name: "layer-stack-multi-view-grid-12"
description: "Use when composing a short's layers in the 'Multi-view grid 12-layer stack' arrangement: every layer with source, opacity (max 98%), blend mode and motion, plus a ready ffmpeg graph for the procedural background layers."
---

# Multi-view grid 12-layer stack

Four synced viewpoints in a 2x2 grid as the main content, with view labels and captions. Theme `clouds`, palette `palette_okabe_ito_safe`, 1080x1920 at 30 fps.

## Layers (bottom to top)

| z | Layer | Role | Source | Opacity | Blend | Motion | Details |
|---|---|---|---|---|---|---|---|
| 1 | base_gradient | base | `bg_layer_gradient_drift` | 0.98 | normal | drift |  |
| 2 | blueprint | texture | `bg_layer_blueprint_grid` | 0.35 | soft-light | loop |  |
| 3 | haze | haze | `bg_layer_atmospheric_haze` | 0.15 | screen | drift |  |
| 4 | views | grid-2x2 | `grid_2x2_multi_viewpoint_split (asset:view_top, asset:view_front, asset:view_side, asset:view_3d)` | 0.96 | normal | loop |  |
| 5 | view_labels | label | `fx:view_labels` | 0.95 | normal | static |  |
| 6 | vignette | vignette | `bg_layer_vignette_breathe` | 0.3 | multiply | pulse |  |
| 7 | title_panel | panel | `panel:title` | 0.66 | normal | static | backing: frosted-glass |
| 8 | title_text | title | `title_step_card_center` | 0.98 | normal | keyframed | animation: text_anim_springy_pop_overshoot |
| 9 | caption_panel | panel | `panel:caption` | 0.66 | normal | static | backing: frosted-glass |
| 10 | caption_text | caption | `caption_two_tone_emphasis` | 0.98 | normal | keyframed | animation: text_anim_fade_up_soft |
| 11 | highlight_ring | overlay | `fx:callout_ring` | 0.9 | normal | keyframed | at: when a part is named |
| 12 | global_grain | grain | `bg_layer_film_grain` | 0.05 | overlay | loop |  |

Every opacity is at most 0.98 (house rule), at least one background layer moves at all times, and the photo
keeps at least 80% of the frame width with a feathered edge. Components named in the Source column are
other presets from this library (`bg_layer_*`, `grid_2x2_*`, `title_*`, `caption_*`, `text_anim_*`, `camera_*`).

Effects used:
- `fx:view_labels`: TOP / FRONT / SIDE / 3D labels in each grid cell's top-left corner.
- `fx:callout_ring`: A 6 px ring in the palette keyword colour drawn around the part being named.

## Render it

1. Background loop: `background_filtergraph.txt` composites the full-frame procedural layers
   (base_gradient, blueprint, haze, vignette, global_grain) in z order with their blend modes and opacities.

   ```bash
   ffmpeg -y -filter_complex "$(cat background_filtergraph.txt)" -map "[out]" -t 8 -r 30 \
     -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart layer-stack-multi-view-grid-12-bg.mp4
   ffmpeg -y -stream_loop -1 -i layer-stack-multi-view-grid-12-bg.mp4 -t 64 -c copy layer-stack-multi-view-grid-12-bg-64s.mp4
   ```

2. Photo pass: render each photo with its camera move preset (see the `camera` detail on the photo layer) and
   overlay it at the photo rectangle with its feather, shadow and rim effects.
3. Text pass: titles, labels and captions from their presets, as RGBA frames or drawtext filters, in z order.
4. Cut-timed layers (views, view_labels, title_panel, title_text, caption_panel, caption_text, highlight_ring) are added around each cut or inside the photo rectangle.

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
