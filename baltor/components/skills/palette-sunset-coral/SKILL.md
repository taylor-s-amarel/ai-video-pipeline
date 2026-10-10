---
name: "palette-sunset-coral"
description: "Use when choosing colours for a short ('Sunset coral'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Sunset coral

Warm evening tones for feelings and relationship topics. Mode: dark. Frosted panels use `#1E1230` at 70%.

## Colours

| Role | Hex |
|---|---|
| background | `#2B1B3D` |
| surface | `#3D2654` |
| panel_tint | `#1E1230` |
| text | `#FFFFFF` |
| title | `#FFC857` |
| keyword | `#FFB4B4` |
| accent | `#F9844A` |
| accent_2 | `#C05299` |
| stroke | `#1E1230` |
| light | `#FF9F45` |
| particle | `#FFD6A5` |

Gradient: `#2B1B3D` -> `#7A3B69`. Five-stop ramp for recolouring procedural backgrounds:
`#1E1230`, `#3D2654`, `#7A3B69`, `#F9844A`, `#FFE3C2` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#FFFFFF` | panel_tint@panel `#1E1230` at 70% | 6.62:1 | any-size |
| title `#FFC857` | panel_tint@panel `#1E1230` at 70% | 4.30:1 | large-bold-only |
| keyword `#FFB4B4` | panel_tint@panel `#1E1230` at 70% | 3.92:1 | large-bold-only |
| text `#FFFFFF` | background `#2B1B3D` | 15.82:1 | any-size |
| title `#FFC857` | background `#2B1B3D` | 10.28:1 | any-size |
| keyword `#FFB4B4` | background `#2B1B3D` | 9.37:1 | any-size |
| accent `#F9844A` | background `#2B1B3D` | 6.35:1 | any-size |
| text `#FFFFFF` | surface `#3D2654` | 13.09:1 | any-size |
| keyword `#FFB4B4` | surface `#3D2654` | 7.75:1 | any-size |
| text `#FFFFFF` | stroke `#1E1230` | 17.73:1 | any-size |
| title `#FFC857` | stroke `#1E1230` | 11.52:1 | any-size |
| background `#2B1B3D` | keyword@card95 `#FFB4B4` at 95% | 8.43:1 | any-size |
| background `#2B1B3D` | title@card95 `#FFC857` at 95% | 9.24:1 | any-size |
| background `#2B1B3D` | accent@card95 `#F9844A` at 95% | 5.74:1 | any-size |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
0 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0xFFFFFF` for captions, `fontcolor=0xFFC857` for titles;
  frosted panels: `drawbox=...:color=0x1E1230@0.7:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#FFFFFF")`; `kit.frosted_panel(frame, box, "#1E1230", 0.7)`.
- Backgrounds: the `bg_layer_*_in_sunset_coral` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#FFFFFF", "#1E1230", 0.7))
print(round(kit.contrast_ratio("#FFFFFF", "#2B1B3D"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
