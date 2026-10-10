# Constant-speed Bezier motion path

Chains of cubic Bezier segments with an arc-length table so objects move at constant speed, plus heading angles and smooth paths through waypoints.

## Use

```python
import bezier_motion_path
```

Placed by `baltor_catalog.py place bezier_motion_path <step-dir>` under `.baltor/lib/bezier-motion-path/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
