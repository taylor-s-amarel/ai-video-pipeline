# Stick-figure rig

Forward-kinematics stick-figure rig with relative joint angles, seven named poses (stand, wave, cheer, walk, think, shrug) and Pillow rendering capped at 98% opacity.

## Use

```python
import stick_figure_rig
```

Placed by `baltor_catalog.py place stick_figure_rig <step-dir>` under `.baltor/lib/stick-figure-rig/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
