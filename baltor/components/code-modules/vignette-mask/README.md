# Vignette masks and filter

Aspect-aware smooth vignette multiplier masks in numpy with an apply helper, plus a validated ffmpeg vignette filter builder (lens angle, centre, per-frame evaluation).

## Use

```python
import vignette_mask
```

Placed by `baltor_catalog.py place vignette_mask <step-dir>` under `.baltor/lib/vignette-mask/`.
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
