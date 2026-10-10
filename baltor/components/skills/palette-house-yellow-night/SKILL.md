---
name: "palette-house-yellow-night"
description: "Use when choosing colours for a short ('House yellow on night glass'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# House yellow on night glass

The house default. Bold yellow hook (#FFD21F) and keyword pops over a dark navy frosted panel. Mode: dark. Frosted panels use `#0B1220` at 62%.

## Colours

| Role | Hex |
|---|---|
| background | `#0B1220` |
| surface | `#162033` |
| panel_tint | `#0B1220` |
| text | `#FFFFFF` |
| title | `#FFD21F` |
| keyword | `#FFD21F` |
| accent | `#2EC4B6` |
| accent_2 | `#FF7A59` |
| stroke | `#000000` |
| light | `#FFB347` |
| particle | `#FFE8A3` |

Gradient: `#0B1220` -> `#1F4E79`. Five-stop ramp for recolouring procedural backgrounds:
`#060B14`, `#0B1220`, `#1F4E79`, `#2EC4B6`, `#E8F7FF` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#FFFFFF` | panel_tint@panel `#0B1220` at 62% | 5.26:1 | any-size |
| title `#FFD21F` | panel_tint@panel `#0B1220` at 62% | 3.63:1 | large-bold-only |
| keyword `#FFD21F` | panel_tint@panel `#0B1220` at 62% | 3.63:1 | large-bold-only |
| text `#FFFFFF` | background `#0B1220` | 18.72:1 | any-size |
| title `#FFD21F` | background `#0B1220` | 12.91:1 | any-size |
| keyword `#FFD21F` | background `#0B1220` | 12.91:1 | any-size |
| accent `#2EC4B6` | background `#0B1220` | 8.63:1 | any-size |
| text `#FFFFFF` | surface `#162033` | 16.29:1 | any-size |
| keyword `#FFD21F` | surface `#162033` | 11.24:1 | any-size |
| text `#FFFFFF` | stroke `#000000` | 21.00:1 | any-size |
| title `#FFD21F` | stroke `#000000` | 14.49:1 | any-size |
| background `#0B1220` | keyword@card95 `#FFD21F` at 95% | 11.60:1 | any-size |
| background `#0B1220` | title@card95 `#FFD21F` at 95% | 11.60:1 | any-size |
| background `#0B1220` | accent@card95 `#2EC4B6` at 95% | 7.80:1 | any-size |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
0 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0xFFFFFF` for captions, `fontcolor=0xFFD21F` for titles;
  frosted panels: `drawbox=...:color=0x0B1220@0.62:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#FFFFFF")`; `kit.frosted_panel(frame, box, "#0B1220", 0.62)`.
- Backgrounds: the `bg_layer_*_in_house_yellow_night` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#FFFFFF", "#0B1220", 0.62))
print(round(kit.contrast_ratio("#FFFFFF", "#0B1220"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
