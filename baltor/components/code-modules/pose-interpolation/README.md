# Pose interpolation and walk cycles

Shortest-arc joint-angle pose blending with easing, looping pose cycles, a procedural walk cycle and pelvis bob, using stick_figure_rig joint names.

## Use

```python
import pose_interpolation
```

Placed by `baltor_catalog.py place pose_interpolation <step-dir>` under `.baltor/lib/pose-interpolation/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
