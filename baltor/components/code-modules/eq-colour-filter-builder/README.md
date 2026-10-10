# Colour grade filter builder (eq, colorbalance, curves)

Builds range-checked ffmpeg colour chains from eq (brightness, contrast, saturation, gamma), colorbalance by tonal range, hue and built-in curves presets.

## Use

```python
import eq_colour_filter_builder
```

Placed by `baltor_catalog.py place eq_colour_filter_builder <step-dir>` under `.baltor/lib/eq-colour-filter-builder/`.
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
