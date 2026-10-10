---
name: "layer-stack-lean-12-layer"
description: "Use when composing a short's layers in the 'Lean 12-layer stack' arrangement: every layer with source, opacity (max 98%), blend mode and motion, plus a ready ffmpeg graph for the procedural background layers."
---

# Lean 12-layer stack

Twelve layers that keep every house rule but render about three times faster than the 30-layer reference. Theme `ocean`, palette `palette_ocean_deep`, 1080x1920 at 30 fps.

## Layers (bottom to top)

| z | Layer | Role | Source | Opacity | Blend | Motion | Details |
|---|---|---|---|---|---|---|---|
| 1 | base_gradient | base | `bg_layer_gradient_drift` | 0.98 | normal | drift |  |
| 2 | footage_primary | background-video | `bg_layer_ocean_waves` | 0.92 | normal | loop |  |
| 3 | motion_grid | grid-2x2 | `grid_2x2_even_feathered (bg_layer_ocean_waves, bg_layer_meadow_wind, bg_layer_sunlit_water, bg_layer_coastal_aerial)` | 0.3 | screen | loop |  |
| 4 | light_leaks | light | `bg_layer_light_leaks` | 0.28 | screen | drift |  |
| 5 | dust | particles | `bg_layer_dust_particles` | 0.3 | screen | rise |  |
| 6 | vignette | vignette | `bg_layer_vignette_breathe` | 0.5 | multiply | pulse |  |
| 7 | photo | photo | `photo` | 0.98 | normal | ken-burns | rect x0.05 y0.16 w0.9 h0.52; feather 48 px; camera: camera_ken_burns_slow_in_center |
| 8 | title_panel | panel | `panel:title` | 0.62 | normal | static | backing: frosted-glass |
| 9 | title_text | title | `title_house_yellow_hook` | 0.98 | normal | keyframed | animation: text_anim_settle_in; visible_from_s: 0.0 |
| 10 | caption_panel | panel | `panel:caption` | 0.62 | normal | static | backing: frosted-glass |
| 11 | caption_text | caption | `caption_frosted_keyword_pop` | 0.98 | normal | keyframed | animation: text_anim_fade_up_soft |
| 12 | global_grain | grain | `bg_layer_film_grain` | 0.08 | overlay | loop |  |

Every opacity is at most 0.98 (house rule), at least one background layer moves at all times, and the photo
keeps at least 80% of the frame width with a feathered edge. Components named in the Source column are
other presets from this library (`bg_layer_*`, `grid_2x2_*`, `title_*`, `caption_*`, `text_anim_*`, `camera_*`).

Effects used:
- none

## Render it

1. Background loop: `background_filtergraph.txt` composites the full-frame procedural layers
   (base_gradient, footage_primary, motion_grid, light_leaks, dust, vignette, global_grain) in z order with their blend modes and opacities.

   ```bash
   ffmpeg -y -filter_complex "$(cat background_filtergraph.txt)" -map "[out]" -t 8 -r 30 \
     -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart layer-stack-lean-12-layer-bg.mp4
   ffmpeg -y -stream_loop -1 -i layer-stack-lean-12-layer-bg.mp4 -t 64 -c copy layer-stack-lean-12-layer-bg-64s.mp4
   ```

2. Photo pass: render each photo with its camera move preset (see the `camera` detail on the photo layer) and
   overlay it at the photo rectangle with its feather, shadow and rim effects.
3. Text pass: titles, labels and captions from their presets, as RGBA frames or drawtext filters, in z order.
4. Cut-timed layers (photo, title_panel, title_text, caption_panel, caption_text) are added around each cut or inside the photo rectangle.

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
