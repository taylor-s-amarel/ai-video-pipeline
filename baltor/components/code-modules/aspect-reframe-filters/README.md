# Aspect-ratio reframe filters

ffmpeg filter builders that reframe to any aspect ratio by cover-crop (with focus point), contain-pad, or blur-pad (sharp foreground over a blurred, darkened fill) with even sizes.

## Use

```python
import aspect_reframe_filters
```

Placed by `baltor_catalog.py place aspect_reframe_filters <step-dir>` under `.baltor/lib/aspect-reframe-filters/`.
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
