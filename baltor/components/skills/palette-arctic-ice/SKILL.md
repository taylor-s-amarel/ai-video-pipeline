---
name: "palette-arctic-ice"
description: "Use when choosing colours for a short ('Arctic ice (light)'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Arctic ice (light)

Clean science and weather topics on a bright base. Mode: light. Frosted panels use `#FFFFFF` at 74%.

## Colours

| Role | Hex |
|---|---|
| background | `#E8F4FA` |
| surface | `#FFFFFF` |
| panel_tint | `#FFFFFF` |
| text | `#0B2537` |
| title | `#0B4F75` |
| keyword | `#005A8C` |
| accent | `#4CB5E0` |
| accent_2 | `#9C6ADE` |
| stroke | `#FFFFFF` |
| light | `#FFFFFF` |
| particle | `#FFFFFF` |

Gradient: `#CDE7F3` -> `#F4FAFD`. Five-stop ramp for recolouring procedural backgrounds:
`#0B2537`, `#1F5F86`, `#7FC1E3`, `#CDE7F3`, `#FFFFFF` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#0B2537` | panel_tint@panel `#FFFFFF` at 74% | 8.35:1 | any-size |
| title `#0B4F75` | panel_tint@panel `#FFFFFF` at 74% | 4.66:1 | any-size |
| keyword `#005A8C` | panel_tint@panel `#FFFFFF` at 74% | 3.92:1 | large-bold-only |
| text `#0B2537` | background `#E8F4FA` | 14.05:1 | any-size |
| title `#0B4F75` | background `#E8F4FA` | 7.84:1 | any-size |
| keyword `#005A8C` | background `#E8F4FA` | 6.60:1 | any-size |
| text `#0B2537` | surface `#FFFFFF` | 15.74:1 | any-size |
| keyword `#005A8C` | surface `#FFFFFF` | 7.39:1 | any-size |
| text `#0B2537` | stroke `#FFFFFF` | 15.74:1 | any-size |
| title `#0B4F75` | stroke `#FFFFFF` | 8.78:1 | any-size |
| background `#E8F4FA` | keyword@card95 `#005A8C` at 95% | 5.88:1 | any-size |
| background `#E8F4FA` | title@card95 `#0B4F75` at 95% | 6.90:1 | any-size |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
2 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0x0B2537` for captions, `fontcolor=0x0B4F75` for titles;
  frosted panels: `drawbox=...:color=0xFFFFFF@0.74:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#0B2537")`; `kit.frosted_panel(frame, box, "#FFFFFF", 0.74)`.
- Backgrounds: the `bg_layer_*_in_arctic_ice` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#0B2537", "#FFFFFF", 0.74))
print(round(kit.contrast_ratio("#0B2537", "#E8F4FA"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
