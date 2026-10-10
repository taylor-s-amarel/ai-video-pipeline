---
name: "palette-pixel-retro"
description: "Use when choosing colours for a short ('Pixel retro'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Pixel retro

Pixel-art and game-style stories; pairs with nearest-neighbour scaling. Mode: dark. Frosted panels use `#14142A` at 70%.

## Colours

| Role | Hex |
|---|---|
| background | `#1B1B2F` |
| surface | `#2C2C4A` |
| panel_tint | `#14142A` |
| text | `#F4F4F4` |
| title | `#FFC85C` |
| keyword | `#9CEB6B` |
| accent | `#4AA8F0` |
| accent_2 | `#E05A6D` |
| stroke | `#0B0B18` |
| light | `#FFC85C` |
| particle | `#F4F4F4` |

Gradient: `#1B1B2F` -> `#2C2C4A`. Five-stop ramp for recolouring procedural backgrounds:
`#0B0B18`, `#1B1B2F`, `#3B5DC9`, `#4AA8F0`, `#F4F4F4` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#F4F4F4` | panel_tint@panel `#14142A` at 70% | 6.10:1 | any-size |
| title `#FFC85C` | panel_tint@panel `#14142A` at 70% | 4.37:1 | large-bold-only |
| keyword `#9CEB6B` | panel_tint@panel `#14142A` at 70% | 4.64:1 | any-size |
| text `#F4F4F4` | background `#1B1B2F` | 15.34:1 | any-size |
| title `#FFC85C` | background `#1B1B2F` | 10.98:1 | any-size |
| keyword `#9CEB6B` | background `#1B1B2F` | 11.65:1 | any-size |
| accent `#4AA8F0` | background `#1B1B2F` | 6.54:1 | any-size |
| text `#F4F4F4` | surface `#2C2C4A` | 12.19:1 | any-size |
| keyword `#9CEB6B` | surface `#2C2C4A` | 9.26:1 | any-size |
| text `#F4F4F4` | stroke `#0B0B18` | 17.75:1 | any-size |
| title `#FFC85C` | stroke `#0B0B18` | 12.71:1 | any-size |
| background `#1B1B2F` | keyword@card95 `#9CEB6B` at 95% | 10.47:1 | any-size |
| background `#1B1B2F` | title@card95 `#FFC85C` at 95% | 9.87:1 | any-size |
| background `#1B1B2F` | accent@card95 `#4AA8F0` at 95% | 5.93:1 | any-size |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
0 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0xF4F4F4` for captions, `fontcolor=0xFFC85C` for titles;
  frosted panels: `drawbox=...:color=0x14142A@0.7:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#F4F4F4")`; `kit.frosted_panel(frame, box, "#14142A", 0.7)`.
- Backgrounds: the `bg_layer_*_in_pixel_retro` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#F4F4F4", "#14142A", 0.7))
print(round(kit.contrast_ratio("#F4F4F4", "#1B1B2F"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
