---
name: "palette-desert-dune"
description: "Use when choosing colours for a short ('Desert dune'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Desert dune

Ancient history, deserts, exploration. Mode: dark. Frosted panels use `#2A190D` at 70%.

## Colours

| Role | Hex |
|---|---|
| background | `#3B2414` |
| surface | `#5A3820` |
| panel_tint | `#2A190D` |
| text | `#FFF4E6` |
| title | `#FFD08A` |
| keyword | `#FFC27F` |
| accent | `#D9822B` |
| accent_2 | `#7FB7BE` |
| stroke | `#1C1007` |
| light | `#FFC97A` |
| particle | `#FFE9C7` |

Gradient: `#3B2414` -> `#8A5A2B`. Five-stop ramp for recolouring procedural backgrounds:
`#1C1007`, `#3B2414`, `#8A5A2B`, `#D9A15E`, `#FFF1DC` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#FFF4E6` | panel_tint@panel `#2A190D` at 70% | 5.77:1 | any-size |
| title `#FFD08A` | panel_tint@panel `#2A190D` at 70% | 4.37:1 | large-bold-only |
| keyword `#FFC27F` | panel_tint@panel `#2A190D` at 70% | 3.96:1 | large-bold-only |
| text `#FFF4E6` | background `#3B2414` | 13.34:1 | any-size |
| title `#FFD08A` | background `#3B2414` | 10.10:1 | any-size |
| keyword `#FFC27F` | background `#3B2414` | 9.16:1 | any-size |
| accent `#D9822B` | background `#3B2414` | 4.95:1 | any-size |
| text `#FFF4E6` | surface `#5A3820` | 9.56:1 | any-size |
| keyword `#FFC27F` | surface `#5A3820` | 6.56:1 | any-size |
| text `#FFF4E6` | stroke `#1C1007` | 17.16:1 | any-size |
| title `#FFD08A` | stroke `#1C1007` | 12.99:1 | any-size |
| background `#3B2414` | keyword@card95 `#FFC27F` at 95% | 8.24:1 | any-size |
| background `#3B2414` | title@card95 `#FFD08A` at 95% | 9.08:1 | any-size |
| background `#3B2414` | accent@card95 `#D9822B` at 95% | 4.50:1 | any-size |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
0 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0xFFF4E6` for captions, `fontcolor=0xFFD08A` for titles;
  frosted panels: `drawbox=...:color=0x2A190D@0.7:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#FFF4E6")`; `kit.frosted_panel(frame, box, "#2A190D", 0.7)`.
- Backgrounds: the `bg_layer_*_in_desert_dune` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#FFF4E6", "#2A190D", 0.7))
print(round(kit.contrast_ratio("#FFF4E6", "#3B2414"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
