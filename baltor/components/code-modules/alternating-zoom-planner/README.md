# Alternating zoom planner

Assigns a camera move to every shot so zooms alternate in/out, pans break up runs, strength scales with shot length and very short shots get a punch-in.

## Use

```python
import alternating_zoom_planner
```

Placed by `baltor_catalog.py place alternating_zoom_planner <step-dir>` under `.baltor/lib/alternating-zoom-planner/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
