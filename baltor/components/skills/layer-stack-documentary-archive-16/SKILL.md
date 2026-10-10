---
name: "layer-stack-documentary-archive-16"
description: "Use when composing a short's layers in the 'Documentary archive 16-layer stack' arrangement: every layer with source, opacity (max 98%), blend mode and motion, plus a ready ffmpeg graph for the procedural background layers."
---

# Documentary archive 16-layer stack

Paper, smoke and grain around an archive photo with a date stamp; for today-in-history and biographies. Theme `clouds`, palette `palette_history_archive`, 1080x1920 at 30 fps.

## Layers (bottom to top)

| z | Layer | Role | Source | Opacity | Blend | Motion | Details |
|---|---|---|---|---|---|---|---|
| 1 | base_gradient | base | `bg_layer_gradient_drift` | 0.98 | normal | drift |  |
| 2 | paper | texture | `bg_layer_warm_paper` | 0.85 | normal | drift |  |
| 3 | contours | texture | `bg_layer_topographic_lines` | 0.18 | multiply | loop |  |
| 4 | smoke | haze | `bg_layer_smoke_wisps` | 0.25 | screen | rise |  |
| 5 | dust | particles | `bg_layer_dust_particles` | 0.3 | screen | rise |  |
| 6 | light_leaks | light | `bg_layer_light_leaks` | 0.22 | screen | drift |  |
| 7 | vignette | vignette | `bg_layer_vignette_breathe` | 0.55 | multiply | pulse |  |
| 8 | photo_shadow | shadow | `fx:photo_shadow` | 0.45 | multiply | follow | follows: photo; blur_px: 30; offset_px: [8, 14] |
| 9 | photo_border | overlay | `fx:paper_border` | 0.95 | normal | follow | follows: photo; border_px: 18 |
| 10 | photo | photo | `photo` | 0.96 | normal | ken-burns | rect x0.05 y0.16 w0.9 h0.52; feather 6 px; camera: camera_diagonal_drift |
| 11 | photo_grain | grain | `bg_layer_film_grain` | 0.14 | overlay | loop | rect x0.05 y0.16 w0.9 h0.52 |
| 12 | date_stamp | title | `title_date_stamp_history` | 0.98 | normal | keyframed | animation: text_anim_typewriter |
| 13 | caption_panel | panel | `panel:caption` | 0.78 | normal | static | backing: solid |
| 14 | caption_text | caption | `caption_typewriter_mono` | 0.98 | normal | keyframed | animation: text_anim_typewriter |
| 15 | global_grain | grain | `bg_layer_film_grain` | 0.12 | overlay | loop |  |
| 16 | colour_grade | grade | `palette_history_archive` | 0.45 | soft-light | static |  |

Every opacity is at most 0.98 (house rule), at least one background layer moves at all times, and the photo
keeps at least 80% of the frame width with a feathered edge. Components named in the Source column are
other presets from this library (`bg_layer_*`, `grid_2x2_*`, `title_*`, `caption_*`, `text_anim_*`, `camera_*`).

Effects used:
- `fx:photo_shadow`: Blurred copy of the photo's alpha mask, filled with the palette background colour, offset and multiplied under the photo.
- `fx:paper_border`: A paper-coloured border around the photo, slightly rotated (0.5-1.5 degrees).

## Render it

1. Background loop: `background_filtergraph.txt` composites the full-frame procedural layers
   (base_gradient, paper, contours, smoke, dust, light_leaks, vignette, global_grain, colour_grade) in z order with their blend modes and opacities.

   ```bash
   ffmpeg -y -filter_complex "$(cat background_filtergraph.txt)" -map "[out]" -t 8 -r 30 \
     -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart layer-stack-documentary-archive-16-bg.mp4
   ffmpeg -y -stream_loop -1 -i layer-stack-documentary-archive-16-bg.mp4 -t 64 -c copy layer-stack-documentary-archive-16-bg-64s.mp4
   ```

2. Photo pass: render each photo with its camera move preset (see the `camera` detail on the photo layer) and
   overlay it at the photo rectangle with its feather, shadow and rim effects.
3. Text pass: titles, labels and captions from their presets, as RGBA frames or drawtext filters, in z order.
4. Cut-timed layers (photo_shadow, photo_border, photo, photo_grain, date_stamp, caption_panel, caption_text) are added around each cut or inside the photo rectangle.

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
