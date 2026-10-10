# Frosted-glass panel filtergraph

Builds an ffmpeg filter_complex for a live frosted-glass panel (crop, gblur/boxblur, 55-75% colour tint, feathered rounded alpha, opacity capped at 0.98) behind titles and captions.

## Use

```python
import frosted_glass_filter
```

Placed by `baltor_catalog.py place frosted_glass_filter <step-dir>` under `.baltor/lib/frosted-glass-filter/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `ffmpeg`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## Licence

MIT. Original work for the Baltor public-good collection.
