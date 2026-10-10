# Seamless loop motion

Exactly periodic motion functions (orbit, breathe, wrapping drift, circle-sampled noise) plus a loop checker, for background layers that loop without a seam.

## Use

```python
import seamless_loop_motion
```

Placed by `baltor_catalog.py place seamless_loop_motion <step-dir>` under `.baltor/lib/seamless-loop-motion/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
