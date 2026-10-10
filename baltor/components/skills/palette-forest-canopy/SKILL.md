---
name: "palette-forest-canopy"
description: "Use when choosing colours for a short ('Forest canopy'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Forest canopy

Woods, wildlife and calm nature facts. Mode: dark. Frosted panels use `#0A1A0F` at 64%.

## Colours

| Role | Hex |
|---|---|
| background | `#0D1F12` |
| surface | `#173322` |
| panel_tint | `#0A1A0F` |
| text | `#F4FBEF` |
| title | `#E9F5A1` |
| keyword | `#A7E163` |
| accent | `#3E8E41` |
| accent_2 | `#F3E3A0` |
| stroke | `#06110A` |
| light | `#F3E3A0` |
| particle | `#EAF7C9` |

Gradient: `#0D1F12` -> `#20402A`. Five-stop ramp for recolouring procedural backgrounds:
`#0B1A0E`, `#20402A`, `#3E6B2F`, `#A7E163`, `#F6F9E8` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#F4FBEF` | panel_tint@panel `#0A1A0F` at 64% | 5.13:1 | any-size |
| title `#E9F5A1` | panel_tint@panel `#0A1A0F` at 64% | 4.65:1 | any-size |
| keyword `#A7E163` | panel_tint@panel `#0A1A0F` at 64% | 3.50:1 | large-bold-only |
| text `#F4FBEF` | background `#0D1F12` | 16.28:1 | any-size |
| title `#E9F5A1` | background `#0D1F12` | 14.76:1 | any-size |
| keyword `#A7E163` | background `#0D1F12` | 11.12:1 | any-size |
| accent `#3E8E41` | background `#0D1F12` | 4.21:1 | large-bold-only |
| text `#F4FBEF` | surface `#173322` | 12.97:1 | any-size |
| keyword `#A7E163` | surface `#173322` | 8.86:1 | any-size |
| text `#F4FBEF` | stroke `#06110A` | 18.21:1 | any-size |
| title `#E9F5A1` | stroke `#06110A` | 16.51:1 | any-size |
| background `#0D1F12` | keyword@card95 `#A7E163` at 95% | 10.00:1 | any-size |
| background `#0D1F12` | title@card95 `#E9F5A1` at 95% | 13.23:1 | any-size |
| background `#0D1F12` | accent@card95 `#3E8E41` at 95% | 3.85:1 | large-bold-only |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
0 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0xF4FBEF` for captions, `fontcolor=0xE9F5A1` for titles;
  frosted panels: `drawbox=...:color=0x0A1A0F@0.64:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#F4FBEF")`; `kit.frosted_panel(frame, box, "#0A1A0F", 0.64)`.
- Backgrounds: the `bg_layer_*_in_forest_canopy` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#F4FBEF", "#0A1A0F", 0.64))
print(round(kit.contrast_ratio("#F4FBEF", "#0D1F12"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
