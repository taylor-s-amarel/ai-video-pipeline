---
name: "palette-okabe-ito-safe"
description: "Use when choosing colours for a short ('Okabe-Ito colour-vision-friendly'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Okabe-Ito colour-vision-friendly

Accent hues from the Okabe-Ito set, which is designed to stay distinguishable for common colour-vision deficiencies. Use when colour carries meaning. Mode: dark. Frosted panels use `#000000` at 66%.

## Colours

| Role | Hex |
|---|---|
| background | `#101010` |
| surface | `#1E1E1E` |
| panel_tint | `#000000` |
| text | `#FFFFFF` |
| title | `#F0E442` |
| keyword | `#56B4E9` |
| accent | `#E69F00` |
| accent_2 | `#009E73` |
| stroke | `#000000` |
| light | `#E69F00` |
| particle | `#FFFFFF` |

Gradient: `#101010` -> `#1E1E1E`. Five-stop ramp for recolouring procedural backgrounds:
`#000000`, `#101010`, `#0072B2`, `#56B4E9`, `#F0E442` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#FFFFFF` | panel_tint@panel `#000000` at 66% | 7.25:1 | any-size |
| title `#F0E442` | panel_tint@panel `#000000` at 66% | 5.49:1 | any-size |
| keyword `#56B4E9` | panel_tint@panel `#000000` at 66% | 3.14:1 | large-bold-only |
| text `#FFFFFF` | background `#101010` | 19.02:1 | any-size |
| title `#F0E442` | background `#101010` | 14.38:1 | any-size |
| keyword `#56B4E9` | background `#101010` | 8.24:1 | any-size |
| accent `#E69F00` | background `#101010` | 8.44:1 | any-size |
| text `#FFFFFF` | surface `#1E1E1E` | 16.67:1 | any-size |
| keyword `#56B4E9` | surface `#1E1E1E` | 7.22:1 | any-size |
| text `#FFFFFF` | stroke `#000000` | 21.00:1 | any-size |
| title `#F0E442` | stroke `#000000` | 15.88:1 | any-size |
| background `#101010` | keyword@card95 `#56B4E9` at 95% | 7.45:1 | any-size |
| background `#101010` | title@card95 `#F0E442` at 95% | 12.91:1 | any-size |
| background `#101010` | accent@card95 `#E69F00` at 95% | 7.63:1 | any-size |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
0 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0xFFFFFF` for captions, `fontcolor=0xF0E442` for titles;
  frosted panels: `drawbox=...:color=0x000000@0.66:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#FFFFFF")`; `kit.frosted_panel(frame, box, "#000000", 0.66)`.
- Backgrounds: the `bg_layer_*_in_okabe_ito_safe` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#FFFFFF", "#000000", 0.66))
print(round(kit.contrast_ratio("#FFFFFF", "#101010"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
- Palette source: Okabe-Ito palette hex values (lab reference table), https://siegal.bio.nyu.edu/color-palette/
