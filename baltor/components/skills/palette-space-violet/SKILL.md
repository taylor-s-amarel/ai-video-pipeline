---
name: "palette-space-violet"
description: "Use when choosing colours for a short ('Space violet'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Space violet

Space, astronomy and women-in-space facts with the house yellow hook. Mode: dark. Frosted panels use `#0B0820` at 72%.

## Colours

| Role | Hex |
|---|---|
| background | `#05040F` |
| surface | `#120F2B` |
| panel_tint | `#0B0820` |
| text | `#FFFFFF` |
| title | `#FFD21F` |
| keyword | `#CBB8FF` |
| accent | `#6C63FF` |
| accent_2 | `#4FD1C5` |
| stroke | `#03020A` |
| light | `#B69CFF` |
| particle | `#FFFFFF` |

Gradient: `#05040F` -> `#1C1645`. Five-stop ramp for recolouring procedural backgrounds:
`#02030A`, `#141B3A`, `#3B2F8F`, `#6C63FF`, `#E9E6FF` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#FFFFFF` | panel_tint@panel `#0B0820` at 72% | 8.18:1 | any-size |
| title `#FFD21F` | panel_tint@panel `#0B0820` at 72% | 5.65:1 | any-size |
| keyword `#CBB8FF` | panel_tint@panel `#0B0820` at 72% | 4.61:1 | any-size |
| text `#FFFFFF` | background `#05040F` | 20.37:1 | any-size |
| title `#FFD21F` | background `#05040F` | 14.05:1 | any-size |
| keyword `#CBB8FF` | background `#05040F` | 11.48:1 | any-size |
| accent `#6C63FF` | background `#05040F` | 4.72:1 | any-size |
| text `#FFFFFF` | surface `#120F2B` | 18.60:1 | any-size |
| keyword `#CBB8FF` | surface `#120F2B` | 10.48:1 | any-size |
| text `#FFFFFF` | stroke `#03020A` | 20.65:1 | any-size |
| title `#FFD21F` | stroke `#03020A` | 14.24:1 | any-size |
| background `#05040F` | keyword@card95 `#CBB8FF` at 95% | 10.34:1 | any-size |
| background `#05040F` | title@card95 `#FFD21F` at 95% | 12.62:1 | any-size |
| background `#05040F` | accent@card95 `#6C63FF` at 95% | 4.32:1 | large-bold-only |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
0 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0xFFFFFF` for captions, `fontcolor=0xFFD21F` for titles;
  frosted panels: `drawbox=...:color=0x0B0820@0.72:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#FFFFFF")`; `kit.frosted_panel(frame, box, "#0B0820", 0.72)`.
- Backgrounds: the `bg_layer_*_in_space_violet` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#FFFFFF", "#0B0820", 0.72))
print(round(kit.contrast_ratio("#FFFFFF", "#05040F"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
