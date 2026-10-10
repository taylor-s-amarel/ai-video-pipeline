---
name: "palette-ocean-deep"
description: "Use when choosing colours for a short ('Ocean deep'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Ocean deep

Sea and underwater topics. Cyan keyword, house yellow title. Mode: dark. Frosted panels use `#041C2C` at 64%.

## Colours

| Role | Hex |
|---|---|
| background | `#03141F` |
| surface | `#082A3D` |
| panel_tint | `#041C2C` |
| text | `#FFFFFF` |
| title | `#FFD21F` |
| keyword | `#7FF0FF` |
| accent | `#18A0C8` |
| accent_2 | `#FFB703` |
| stroke | `#00111A` |
| light | `#9FE7F5` |
| particle | `#D8FBFF` |

Gradient: `#03141F` -> `#0B5E8A`. Five-stop ramp for recolouring procedural backgrounds:
`#021019`, `#04223F`, `#0B5E8A`, `#2FA4C8`, `#C8F1FF` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#FFFFFF` | panel_tint@panel `#041C2C` at 64% | 5.29:1 | any-size |
| title `#FFD21F` | panel_tint@panel `#041C2C` at 64% | 3.65:1 | large-bold-only |
| keyword `#7FF0FF` | panel_tint@panel `#041C2C` at 64% | 3.98:1 | large-bold-only |
| text `#FFFFFF` | background `#03141F` | 18.68:1 | any-size |
| title `#FFD21F` | background `#03141F` | 12.89:1 | any-size |
| keyword `#7FF0FF` | background `#03141F` | 14.06:1 | any-size |
| accent `#18A0C8` | background `#03141F` | 6.14:1 | any-size |
| text `#FFFFFF` | surface `#082A3D` | 14.90:1 | any-size |
| keyword `#7FF0FF` | surface `#082A3D` | 11.22:1 | any-size |
| text `#FFFFFF` | stroke `#00111A` | 19.17:1 | any-size |
| title `#FFD21F` | stroke `#00111A` | 13.23:1 | any-size |
| background `#03141F` | keyword@card95 `#7FF0FF` at 95% | 12.62:1 | any-size |
| background `#03141F` | title@card95 `#FFD21F` at 95% | 11.58:1 | any-size |
| background `#03141F` | accent@card95 `#18A0C8` at 95% | 5.58:1 | any-size |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
0 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0xFFFFFF` for captions, `fontcolor=0xFFD21F` for titles;
  frosted panels: `drawbox=...:color=0x041C2C@0.64:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#FFFFFF")`; `kit.frosted_panel(frame, box, "#041C2C", 0.64)`.
- Backgrounds: the `bg_layer_*_in_ocean_deep` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#FFFFFF", "#041C2C", 0.64))
print(round(kit.contrast_ratio("#FFFFFF", "#03141F"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
