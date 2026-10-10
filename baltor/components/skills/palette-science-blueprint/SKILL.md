---
name: "palette-science-blueprint"
description: "Use when choosing colours for a short ('Science blueprint'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Science blueprint

Explainers, how-it-works and engineering topics. Mode: dark. Frosted panels use `#0A1F36` at 66%.

## Colours

| Role | Hex |
|---|---|
| background | `#0F2C4C` |
| surface | `#163A61` |
| panel_tint | `#0A1F36` |
| text | `#FFFFFF` |
| title | `#9FE7FF` |
| keyword | `#FFD21F` |
| accent | `#3D6A99` |
| accent_2 | `#FF8A5B` |
| stroke | `#06182B` |
| light | `#BFE9FF` |
| particle | `#E6F0FF` |

Gradient: `#0F2C4C` -> `#1F4E79`. Five-stop ramp for recolouring procedural backgrounds:
`#06182B`, `#0F2C4C`, `#3D6A99`, `#9FE7FF`, `#E6F0FF` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#FFFFFF` | panel_tint@panel `#0A1F36` at 66% | 5.43:1 | any-size |
| title `#9FE7FF` | panel_tint@panel `#0A1F36` at 66% | 3.97:1 | large-bold-only |
| keyword `#FFD21F` | panel_tint@panel `#0A1F36` at 66% | 3.75:1 | large-bold-only |
| text `#FFFFFF` | background `#0F2C4C` | 14.14:1 | any-size |
| title `#9FE7FF` | background `#0F2C4C` | 10.33:1 | any-size |
| keyword `#FFD21F` | background `#0F2C4C` | 9.75:1 | any-size |
| text `#FFFFFF` | surface `#163A61` | 11.58:1 | any-size |
| keyword `#FFD21F` | surface `#163A61` | 7.99:1 | any-size |
| text `#FFFFFF` | stroke `#06182B` | 17.89:1 | any-size |
| title `#9FE7FF` | stroke `#06182B` | 13.08:1 | any-size |
| background `#0F2C4C` | keyword@card95 `#FFD21F` at 95% | 8.76:1 | any-size |
| background `#0F2C4C` | title@card95 `#9FE7FF` at 95% | 9.28:1 | any-size |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
2 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0xFFFFFF` for captions, `fontcolor=0x9FE7FF` for titles;
  frosted panels: `drawbox=...:color=0x0A1F36@0.66:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#FFFFFF")`; `kit.frosted_panel(frame, box, "#0A1F36", 0.66)`.
- Backgrounds: the `bg_layer_*_in_science_blueprint` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#FFFFFF", "#0A1F36", 0.66))
print(round(kit.contrast_ratio("#FFFFFF", "#0F2C4C"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
