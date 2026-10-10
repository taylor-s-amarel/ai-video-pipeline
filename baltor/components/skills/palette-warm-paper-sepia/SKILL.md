---
name: "palette-warm-paper-sepia"
description: "Use when choosing colours for a short ('Warm paper sepia (light)'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Warm paper sepia (light)

Archive and today-in-history looks on paper textures. Mode: light. Frosted panels use `#FFF8EC` at 78%.

## Colours

| Role | Hex |
|---|---|
| background | `#F3EBDD` |
| surface | `#FFF8EC` |
| panel_tint | `#FFF8EC` |
| text | `#2B1D12` |
| title | `#7A2E0E` |
| keyword | `#9E3510` |
| accent | `#8C6239` |
| accent_2 | `#3E5C76` |
| stroke | `#FFF8EC` |
| light | `#FFE7B0` |
| particle | `#FFFFFF` |

Gradient: `#E9DCC3` -> `#F3EBDD`. Five-stop ramp for recolouring procedural backgrounds:
`#5B4636`, `#8C6239`, `#CDB792`, `#EFE3CC`, `#FFF9EE` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#2B1D12` | panel_tint@panel `#FFF8EC` at 78% | 9.15:1 | any-size |
| title `#7A2E0E` | panel_tint@panel `#FFF8EC` at 78% | 5.29:1 | any-size |
| keyword `#9E3510` | panel_tint@panel `#FFF8EC` at 78% | 3.96:1 | large-bold-only |
| text `#2B1D12` | background `#F3EBDD` | 13.78:1 | any-size |
| title `#7A2E0E` | background `#F3EBDD` | 7.97:1 | any-size |
| keyword `#9E3510` | background `#F3EBDD` | 5.97:1 | any-size |
| accent `#8C6239` | background `#F3EBDD` | 4.52:1 | any-size |
| text `#2B1D12` | surface `#FFF8EC` | 15.45:1 | any-size |
| keyword `#9E3510` | surface `#FFF8EC` | 6.69:1 | any-size |
| text `#2B1D12` | stroke `#FFF8EC` | 15.45:1 | any-size |
| title `#7A2E0E` | stroke `#FFF8EC` | 8.94:1 | any-size |
| background `#F3EBDD` | keyword@card95 `#9E3510` at 95% | 5.40:1 | any-size |
| background `#F3EBDD` | title@card95 `#7A2E0E` at 95% | 7.04:1 | any-size |
| background `#F3EBDD` | accent@card95 `#8C6239` at 95% | 4.07:1 | large-bold-only |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
0 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0x2B1D12` for captions, `fontcolor=0x7A2E0E` for titles;
  frosted panels: `drawbox=...:color=0xFFF8EC@0.78:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#2B1D12")`; `kit.frosted_panel(frame, box, "#FFF8EC", 0.78)`.
- Backgrounds: the `bg_layer_*_in_warm_paper_sepia` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#2B1D12", "#FFF8EC", 0.78))
print(round(kit.contrast_ratio("#2B1D12", "#F3EBDD"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
