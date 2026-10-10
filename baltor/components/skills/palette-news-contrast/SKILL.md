---
name: "palette-news-contrast"
description: "Use when choosing colours for a short ('News high contrast'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# News high contrast

Briefings and explainers where text must read at a glance. Red is for bars and accents, not small text. Mode: dark. Frosted panels use `#000000` at 74%.

## Colours

| Role | Hex |
|---|---|
| background | `#0E0E10` |
| surface | `#1C1C20` |
| panel_tint | `#000000` |
| text | `#FFFFFF` |
| title | `#FFFFFF` |
| keyword | `#FFCC00` |
| accent | `#E03A3E` |
| accent_2 | `#3A7BD5` |
| stroke | `#000000` |
| light | `#FFFFFF` |
| particle | `#FFFFFF` |

Gradient: `#0E0E10` -> `#2A2A30`. Five-stop ramp for recolouring procedural backgrounds:
`#000000`, `#0E0E10`, `#2A2A30`, `#8A8A96`, `#FFFFFF` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#FFFFFF` | panel_tint@panel `#000000` at 74% | 10.00:1 | any-size |
| title `#FFFFFF` | panel_tint@panel `#000000` at 74% | 10.00:1 | any-size |
| keyword `#FFCC00` | panel_tint@panel `#000000` at 74% | 6.61:1 | any-size |
| text `#FFFFFF` | background `#0E0E10` | 19.28:1 | any-size |
| title `#FFFFFF` | background `#0E0E10` | 19.28:1 | any-size |
| keyword `#FFCC00` | background `#0E0E10` | 12.75:1 | any-size |
| accent `#E03A3E` | background `#0E0E10` | 4.44:1 | large-bold-only |
| text `#FFFFFF` | surface `#1C1C20` | 16.98:1 | any-size |
| keyword `#FFCC00` | surface `#1C1C20` | 11.23:1 | any-size |
| text `#FFFFFF` | stroke `#000000` | 21.00:1 | any-size |
| title `#FFFFFF` | stroke `#000000` | 21.00:1 | any-size |
| background `#0E0E10` | keyword@card95 `#FFCC00` at 95% | 11.46:1 | any-size |
| background `#0E0E10` | title@card95 `#FFFFFF` at 95% | 17.26:1 | any-size |
| background `#0E0E10` | accent@card95 `#E03A3E` at 95% | 4.07:1 | large-bold-only |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
0 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0xFFFFFF` for captions, `fontcolor=0xFFFFFF` for titles;
  frosted panels: `drawbox=...:color=0x000000@0.74:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#FFFFFF")`; `kit.frosted_panel(frame, box, "#000000", 0.74)`.
- Backgrounds: the `bg_layer_*_in_news_contrast` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#FFFFFF", "#000000", 0.74))
print(round(kit.contrast_ratio("#FFFFFF", "#0E0E10"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
