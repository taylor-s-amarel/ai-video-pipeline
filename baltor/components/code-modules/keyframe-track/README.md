# Keyframe track interpolator

Keyframe tracks for scalar or vector properties with per-segment easing (hold, linear, quad, cubic, sine, back), frame sampling and JSON round-trip.

## Use

```python
import keyframe_track
```

Placed by `baltor_catalog.py place keyframe_track <step-dir>` under `.baltor/lib/keyframe-track/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
