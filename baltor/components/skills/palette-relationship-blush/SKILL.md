---
name: "palette-relationship-blush"
description: "Use when choosing colours for a short ('Relationship blush (light)'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Relationship blush (light)

Soft looks for trust, communication and feelings topics. Mode: light. Frosted panels use `#FFFFFF` at 74%.

## Colours

| Role | Hex |
|---|---|
| background | `#FBEFF1` |
| surface | `#FFFFFF` |
| panel_tint | `#FFFFFF` |
| text | `#3A1E2B` |
| title | `#8E2450` |
| keyword | `#A3154C` |
| accent | `#E8B4C4` |
| accent_2 | `#6D8B74` |
| stroke | `#FFFFFF` |
| light | `#FFE0E8` |
| particle | `#FFFFFF` |

Gradient: `#F6D7DE` -> `#FBEFF1`. Five-stop ramp for recolouring procedural backgrounds:
`#3B1E2B`, `#9C4F6B`, `#E8B4C4`, `#F6D7DE`, `#FFF5F7` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#3A1E2B` | panel_tint@panel `#FFFFFF` at 74% | 7.95:1 | any-size |
| title `#8E2450` | panel_tint@panel `#FFFFFF` at 74% | 4.42:1 | large-bold-only |
| keyword `#A3154C` | panel_tint@panel `#FFFFFF` at 74% | 4.02:1 | large-bold-only |
| text `#3A1E2B` | background `#FBEFF1` | 13.36:1 | any-size |
| title `#8E2450` | background `#FBEFF1` | 7.43:1 | any-size |
| keyword `#A3154C` | background `#FBEFF1` | 6.76:1 | any-size |
| text `#3A1E2B` | surface `#FFFFFF` | 14.99:1 | any-size |
| keyword `#A3154C` | surface `#FFFFFF` | 7.58:1 | any-size |
| text `#3A1E2B` | stroke `#FFFFFF` | 14.99:1 | any-size |
| title `#8E2450` | stroke `#FFFFFF` | 8.33:1 | any-size |
| background `#FBEFF1` | keyword@card95 `#A3154C` at 95% | 6.23:1 | any-size |
| background `#FBEFF1` | title@card95 `#8E2450` at 95% | 6.68:1 | any-size |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
2 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0x3A1E2B` for captions, `fontcolor=0x8E2450` for titles;
  frosted panels: `drawbox=...:color=0xFFFFFF@0.74:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#3A1E2B")`; `kit.frosted_panel(frame, box, "#FFFFFF", 0.74)`.
- Backgrounds: the `bg_layer_*_in_relationship_blush` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#3A1E2B", "#FFFFFF", 0.74))
print(round(kit.contrast_ratio("#3A1E2B", "#FBEFF1"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
