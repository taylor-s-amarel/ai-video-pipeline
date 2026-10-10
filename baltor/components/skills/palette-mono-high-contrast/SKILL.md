---
name: "palette-mono-high-contrast"
description: "Use when choosing colours for a short ('Monochrome high contrast'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Monochrome high contrast

Maximum legibility; one yellow keyword colour. Mode: dark. Frosted panels use `#000000` at 75%.

## Colours

| Role | Hex |
|---|---|
| background | `#000000` |
| surface | `#161616` |
| panel_tint | `#000000` |
| text | `#FFFFFF` |
| title | `#FFFFFF` |
| keyword | `#FFE600` |
| accent | `#BDBDBD` |
| accent_2 | `#FFFFFF` |
| stroke | `#000000` |
| light | `#FFFFFF` |
| particle | `#FFFFFF` |

Gradient: `#000000` -> `#262626`. Five-stop ramp for recolouring procedural backgrounds:
`#000000`, `#161616`, `#3A3A3A`, `#9E9E9E`, `#FFFFFF` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#FFFFFF` | panel_tint@panel `#000000` at 75% | 10.40:1 | any-size |
| title `#FFFFFF` | panel_tint@panel `#000000` at 75% | 10.40:1 | any-size |
| keyword `#FFE600` | panel_tint@panel `#000000` at 75% | 8.21:1 | any-size |
| text `#FFFFFF` | background `#000000` | 21.00:1 | any-size |
| title `#FFFFFF` | background `#000000` | 21.00:1 | any-size |
| keyword `#FFE600` | background `#000000` | 16.57:1 | any-size |
| accent `#BDBDBD` | background `#000000` | 11.17:1 | any-size |
| text `#FFFFFF` | surface `#161616` | 18.09:1 | any-size |
| keyword `#FFE600` | surface `#161616` | 14.27:1 | any-size |
| text `#FFFFFF` | stroke `#000000` | 21.00:1 | any-size |
| title `#FFFFFF` | stroke `#000000` | 21.00:1 | any-size |
| background `#000000` | keyword@card95 `#FFE600` at 95% | 14.86:1 | any-size |
| background `#000000` | title@card95 `#FFFFFF` at 95% | 18.80:1 | any-size |
| background `#000000` | accent@card95 `#BDBDBD` at 95% | 10.07:1 | any-size |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
0 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0xFFFFFF` for captions, `fontcolor=0xFFFFFF` for titles;
  frosted panels: `drawbox=...:color=0x000000@0.75:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#FFFFFF")`; `kit.frosted_panel(frame, box, "#000000", 0.75)`.
- Backgrounds: the `bg_layer_*_in_mono_high_contrast` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#FFFFFF", "#000000", 0.75))
print(round(kit.contrast_ratio("#FFFFFF", "#000000"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
