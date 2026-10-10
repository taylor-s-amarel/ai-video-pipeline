---
name: "layer-stack-landscape-news-14"
description: "Use when composing a short's layers in the 'Landscape briefing 14-layer stack' arrangement: every layer with source, opacity (max 98%), blend mode and motion, plus a ready ffmpeg graph for the procedural background layers."
---

# Landscape briefing 14-layer stack

A 16:9 briefing layout with a lower-third bar and two-line subtitles. Theme `clouds`, palette `palette_news_contrast`, 1920x1080 at 30 fps.

## Layers (bottom to top)

| z | Layer | Role | Source | Opacity | Blend | Motion | Details |
|---|---|---|---|---|---|---|---|
| 1 | base_gradient | base | `bg_layer_gradient_drift` | 0.98 | normal | drift |  |
| 2 | footage | background-video | `bg_layer_city_night_bokeh` | 0.6 | normal | loop |  |
| 3 | haze | haze | `bg_layer_atmospheric_haze` | 0.2 | screen | drift |  |
| 4 | light_leaks | light | `bg_layer_light_leaks` | 0.15 | screen | drift |  |
| 5 | vignette | vignette | `bg_layer_vignette_breathe` | 0.5 | multiply | pulse |  |
| 6 | photo_shadow | shadow | `fx:photo_shadow` | 0.4 | multiply | follow | follows: photo; blur_px: 30; offset_px: [0, 12] |
| 7 | photo | photo | `photo` | 0.98 | normal | ken-burns | rect x0.1 y0.08 w0.8 h0.7; feather 12 px; camera: camera_handheld_micro_shake |
| 8 | kicker_bar | panel | `accent` | 0.95 | normal | keyframed | animation: text_anim_mask_reveal_up |
| 9 | lower_third_panel | panel | `panel:title` | 0.74 | normal | keyframed | backing: solid |
| 10 | lower_third_text | title | `title_news_lower_third` | 0.98 | normal | keyframed | animation: text_anim_mask_reveal_up |
| 11 | subtitle_panel | panel | `panel:caption` | 0.74 | normal | static | backing: solid |
| 12 | subtitle_text | caption | `caption_solid_band_lower` | 0.98 | normal | keyframed | animation: text_anim_fade_up_soft |
| 13 | global_grain | grain | `bg_layer_film_grain` | 0.05 | overlay | loop |  |
| 14 | colour_grade | grade | `palette_news_contrast` | 0.3 | soft-light | static |  |

Every opacity is at most 0.98 (house rule), at least one background layer moves at all times, and the photo
keeps at least 80% of the frame width with a feathered edge. Components named in the Source column are
other presets from this library (`bg_layer_*`, `grid_2x2_*`, `title_*`, `caption_*`, `text_anim_*`, `camera_*`).

Effects used:
- `fx:photo_shadow`: Blurred copy of the photo's alpha mask, filled with the palette background colour, offset and multiplied under the photo.

## Render it

1. Background loop: `background_filtergraph.txt` composites the full-frame procedural layers
   (base_gradient, footage, haze, light_leaks, vignette, kicker_bar, global_grain, colour_grade) in z order with their blend modes and opacities.

   ```bash
   ffmpeg -y -filter_complex "$(cat background_filtergraph.txt)" -map "[out]" -t 8 -r 30 \
     -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart layer-stack-landscape-news-14-bg.mp4
   ffmpeg -y -stream_loop -1 -i layer-stack-landscape-news-14-bg.mp4 -t 64 -c copy layer-stack-landscape-news-14-bg-64s.mp4
   ```

2. Photo pass: render each photo with its camera move preset (see the `camera` detail on the photo layer) and
   overlay it at the photo rectangle with its feather, shadow and rim effects.
3. Text pass: titles, labels and captions from their presets, as RGBA frames or drawtext filters, in z order.
4. Cut-timed layers (photo_shadow, photo, lower_third_panel, lower_third_text, subtitle_panel, subtitle_text) are added around each cut or inside the photo rectangle.

To build a graph for your own inputs, give each layer an ffmpeg input index and let the kit write it:

```python
import json, sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
stack = json.load(open("preset.json"))
print(kit.layer_stack_problems(stack))            # [] when the house rules hold
layers = [dict(l, input=i) for i, l in enumerate(stack["layers"]) if l["source"]["kind"] == "component"]
print(kit.layer_stack_filter(layers, 1920, 1080, 30))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `layer_stack_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- ffmpeg filters (blend, overlay, alphamerge): https://ffmpeg.org/ffmpeg-filters.html
