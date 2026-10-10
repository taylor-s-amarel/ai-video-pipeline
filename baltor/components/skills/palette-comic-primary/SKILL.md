---
name: "palette-comic-primary"
description: "Use when choosing colours for a short ('Comic primary (light)'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Comic primary (light)

Ridiculous stories, cartoons and comic panels. Mode: light. Frosted panels use `#FFFFFF` at 86%.

## Colours

| Role | Hex |
|---|---|
| background | `#FFF4D6` |
| surface | `#FFFFFF` |
| panel_tint | `#FFFFFF` |
| text | `#111111` |
| title | `#8E0B16` |
| keyword | `#1D4ED8` |
| accent | `#E63946` |
| accent_2 | `#FFD21F` |
| stroke | `#111111` |
| light | `#FFFFFF` |
| particle | `#FFFFFF` |

Gradient: `#FFE9A8` -> `#FFF4D6`. Five-stop ramp for recolouring procedural backgrounds:
`#111111`, `#E63946`, `#FF9F1C`, `#FFD21F`, `#FFF4D6` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#111111` | panel_tint@panel `#FFFFFF` at 86% | 13.67:1 | any-size |
| title `#8E0B16` | panel_tint@panel `#FFFFFF` at 86% | 6.88:1 | any-size |
| keyword `#1D4ED8` | panel_tint@panel `#FFFFFF` at 86% | 4.85:1 | any-size |
| text `#111111` | background `#FFF4D6` | 17.23:1 | any-size |
| title `#8E0B16` | background `#FFF4D6` | 8.67:1 | any-size |
| keyword `#1D4ED8` | background `#FFF4D6` | 6.11:1 | any-size |
| accent `#E63946` | background `#FFF4D6` | 3.80:1 | large-bold-only |
| text `#111111` | surface `#FFFFFF` | 18.88:1 | any-size |
| keyword `#1D4ED8` | surface `#FFFFFF` | 6.70:1 | any-size |
| background `#FFF4D6` | keyword@card95 `#1D4ED8` at 95% | 5.53:1 | any-size |
| background `#FFF4D6` | title@card95 `#8E0B16` at 95% | 7.98:1 | any-size |
| background `#FFF4D6` | accent@card95 `#E63946` at 95% | 3.60:1 | large-bold-only |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
1 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0x111111` for captions, `fontcolor=0x8E0B16` for titles;
  frosted panels: `drawbox=...:color=0xFFFFFF@0.86:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#111111")`; `kit.frosted_panel(frame, box, "#FFFFFF", 0.86)`.
- Backgrounds: the `bg_layer_*_in_comic_primary` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#111111", "#FFFFFF", 0.86))
print(round(kit.contrast_ratio("#111111", "#FFF4D6"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
