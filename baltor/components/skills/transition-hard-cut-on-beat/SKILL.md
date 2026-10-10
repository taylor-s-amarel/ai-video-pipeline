---
name: "transition-hard-cut-on-beat"
description: "Use when joining two shots of a short with the 'Hard cut on the beat' transition: exact ffmpeg xfade or concat command with the right offset, duration and tempo, and when not to use it."
---

# Hard cut on the beat

Hard cut, 0 ms, tempo standard.

## When to use
- Default between shots
- Every 1.5-3 s in fast edits
- On a music beat or a sentence break

## Avoid when
- Two shots that are nearly identical (looks like a glitch)

## Render it

```bash
ffmpeg -y -i A.mp4 -i B.mp4 -filter_complex \
  "[0:v]settb=AVTB,fps=30,format=yuv420p,setsar=1[a];[1:v]settb=AVTB,fps=30,format=yuv420p,setsar=1[b];[a][b]concat=n=2:v=1:a=0[v]" \
  -map "[v]" -c:v libx264 -crf 18 -pix_fmt yuv420p cut.mp4
```

A hard cut is a concatenation; cut on a beat or a sentence break.

For many clips, `short_style_preset_kit.xfade_chain(durations, transitions)` writes the whole graph with correct offsets:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
graph, total = kit.xfade_chain([4.0, 3.5, 5.0], [{"xfade": "fade", "duration_ms": 40}, {"cut": True}])
print(total)   # seconds after joining
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `transition_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- ffmpeg xfade and concat filters: https://ffmpeg.org/ffmpeg-filters.html
