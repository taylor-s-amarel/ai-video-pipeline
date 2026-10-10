# Directional motion blur

Numpy linear motion blur at any angle with sub-pixel shifts, a whip-pan blur profile for transition frames and a normalised line kernel.

## Use

```python
import directional_motion_blur
```

Placed by `baltor_catalog.py place directional_motion_blur <step-dir>` under `.baltor/lib/directional-motion-blur/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
