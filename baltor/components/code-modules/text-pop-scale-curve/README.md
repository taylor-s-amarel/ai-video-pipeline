# Text pop scale curve

Key-word pop curve (1.0 -> 1.12 -> 1.0 over 180 ms by default) as per-frame scales, an ffmpeg time expression and ASS transform tags, with ease and spring shapes.

## Use

```python
import text_pop_scale_curve
```

Placed by `baltor_catalog.py place text_pop_scale_curve <step-dir>` under `.baltor/lib/text-pop-scale-curve/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
