# Overlay timeline filter

Schedules image/video overlays with time windows, alpha fade in/out shifted to each slot, opacity capped at 0.98 and a check for overlays that collide in space and time.

## Use

```python
import overlay_timeline_filter
```

Placed by `baltor_catalog.py place overlay_timeline_filter <step-dir>` under `.baltor/lib/overlay-timeline-filter/`.
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
