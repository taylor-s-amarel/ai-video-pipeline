# Looping rain and snow overlays

Deterministic, exactly looping rain streaks and swaying snow rendered as transparent Pillow overlays with depth-based size and opacity capped at 98%.

## Use

```python
import precipitation_overlay
```

Placed by `baltor_catalog.py place precipitation_overlay <step-dir>` under `.baltor/lib/precipitation-overlay/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
