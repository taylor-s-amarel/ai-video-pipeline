---
name: "palette-meadow-morning"
description: "Use when choosing colours for a short ('Meadow morning (light)'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Meadow morning (light)

Light frosted panels with dark green text. Use for gentle nature and pet topics. Mode: light. Frosted panels use `#FFFFFF` at 80%.

## Colours

| Role | Hex |
|---|---|
| background | `#EEF6E2` |
| surface | `#FFFFFF` |
| panel_tint | `#FFFFFF` |
| text | `#10230F` |
| title | `#1F5E14` |
| keyword | `#1E5E12` |
| accent | `#6BA539` |
| accent_2 | `#E8A33D` |
| stroke | `#FFFFFF` |
| light | `#FFF3C4` |
| particle | `#FFFFFF` |

Gradient: `#CFE8B4` -> `#EEF6E2`. Five-stop ramp for recolouring procedural backgrounds:
`#173A12`, `#3F7A22`, `#9CCB4A`, `#DDEEB0`, `#F7FBEF` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#10230F` | panel_tint@panel `#FFFFFF` at 80% | 10.30:1 | any-size |
| title `#1F5E14` | panel_tint@panel `#FFFFFF` at 80% | 4.89:1 | any-size |
| keyword `#1E5E12` | panel_tint@panel `#FFFFFF` at 80% | 4.90:1 | any-size |
| text `#10230F` | background `#EEF6E2` | 14.90:1 | any-size |
| title `#1F5E14` | background `#EEF6E2` | 7.08:1 | any-size |
| keyword `#1E5E12` | background `#EEF6E2` | 7.09:1 | any-size |
| text `#10230F` | surface `#FFFFFF` | 16.54:1 | any-size |
| keyword `#1E5E12` | surface `#FFFFFF` | 7.87:1 | any-size |
| text `#10230F` | stroke `#FFFFFF` | 16.54:1 | any-size |
| title `#1F5E14` | stroke `#FFFFFF` | 7.86:1 | any-size |
| background `#EEF6E2` | keyword@card95 `#1E5E12` at 95% | 6.27:1 | any-size |
| background `#EEF6E2` | title@card95 `#1F5E14` at 95% | 6.25:1 | any-size |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
2 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0x10230F` for captions, `fontcolor=0x1F5E14` for titles;
  frosted panels: `drawbox=...:color=0xFFFFFF@0.8:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#10230F")`; `kit.frosted_panel(frame, box, "#FFFFFF", 0.8)`.
- Backgrounds: the `bg_layer_*_in_meadow_morning` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#10230F", "#FFFFFF", 0.8))
print(round(kit.contrast_ratio("#10230F", "#EEF6E2"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
