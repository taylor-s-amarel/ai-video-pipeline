---
name: "layer-stack-comic-panel-14"
description: "Use when composing a short's layers in the 'Comic panel 14-layer stack' arrangement: every layer with source, opacity (max 98%), blend mode and motion, plus a ready ffmpeg graph for the procedural background layers."
---

# Comic panel 14-layer stack

Sunburst, halftone and sticker lettering for ridiculous stories and cartoons. Theme `meadow`, palette `palette_comic_primary`, 1080x1920 at 30 fps.

## Layers (bottom to top)

| z | Layer | Role | Source | Opacity | Blend | Motion | Details |
|---|---|---|---|---|---|---|---|
| 1 | sunburst | background-video | `bg_layer_comic_sunburst` | 0.92 | normal | rotate |  |
| 2 | halftone | texture | `bg_layer_halftone_drift` | 0.25 | multiply | loop |  |
| 3 | light_leaks | light | `bg_layer_light_leaks` | 0.18 | screen | drift |  |
| 4 | vignette | vignette | `bg_layer_vignette_breathe` | 0.35 | multiply | pulse |  |
| 5 | panel_shadow | shadow | `fx:photo_shadow` | 0.5 | multiply | follow | follows: photo; blur_px: 0; offset_px: [14, 14] |
| 6 | panel_border | overlay | `fx:ink_border` | 0.98 | normal | follow | follows: photo; border_px: 10 |
| 7 | photo | photo | `photo` | 0.98 | normal | punch-in | rect x0.05 y0.16 w0.9 h0.52; camera: camera_impact_punch_in |
| 8 | photo_halftone | texture | `bg_layer_halftone_drift` | 0.12 | multiply | loop | rect x0.05 y0.16 w0.9 h0.52 |
| 9 | title_sticker | panel | `panel:title` | 0.95 | normal | keyframed | backing: sticker |
| 10 | title_text | title | `title_comic_burst_hook` | 0.98 | normal | keyframed | animation: text_anim_springy_pop_overshoot |
| 11 | caption_sticker | panel | `panel:caption` | 0.95 | normal | keyframed | backing: sticker |
| 12 | caption_text | caption | `caption_sticker_label` | 0.98 | normal | keyframed | animation: text_anim_bounce_in_from_below |
| 13 | impact_lines | overlay | `fx:speed_lines` | 0.4 | normal | keyframed | at: punchlines |
| 14 | global_grain | grain | `bg_layer_film_grain` | 0.06 | overlay | loop |  |

Every opacity is at most 0.98 (house rule), at least one background layer moves at all times, and the photo
keeps at least 80% of the frame width with a feathered edge. Components named in the Source column are
other presets from this library (`bg_layer_*`, `grid_2x2_*`, `title_*`, `caption_*`, `text_anim_*`, `camera_*`).

Effects used:
- `fx:photo_shadow`: Blurred copy of the photo's alpha mask, filled with the palette background colour, offset and multiplied under the photo.
- `fx:ink_border`: A black border of 10 px around the comic panel.
- `fx:speed_lines`: Radial white lines from the frame centre, shown for 6-10 frames on a punchline.

## Render it

1. Background loop: `background_filtergraph.txt` composites the full-frame procedural layers
   (sunburst, halftone, light_leaks, vignette, global_grain) in z order with their blend modes and opacities.

   ```bash
   ffmpeg -y -filter_complex "$(cat background_filtergraph.txt)" -map "[out]" -t 8 -r 30 \
     -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart layer-stack-comic-panel-14-bg.mp4
   ffmpeg -y -stream_loop -1 -i layer-stack-comic-panel-14-bg.mp4 -t 64 -c copy layer-stack-comic-panel-14-bg-64s.mp4
   ```

2. Photo pass: render each photo with its camera move preset (see the `camera` detail on the photo layer) and
   overlay it at the photo rectangle with its feather, shadow and rim effects.
3. Text pass: titles, labels and captions from their presets, as RGBA frames or drawtext filters, in z order.
4. Cut-timed layers (panel_shadow, panel_border, photo, photo_halftone, title_sticker, title_text, caption_sticker, caption_text, impact_lines) are added around each cut or inside the photo rectangle.

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
