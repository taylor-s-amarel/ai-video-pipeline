# Damped follow camera

Critically damped (smooth-damp) 2D follow camera with dead zone, look-ahead and world bounds for top-down, side-on and map-flyover footage.

## Use

```python
import damped_follow_camera
```

Placed by `baltor_catalog.py place damped_follow_camera <step-dir>` under `.baltor/lib/damped-follow-camera/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
