# Damped spring motion

Closed-form damped spring (under, critical, over) with overshoot and settle-time measurement and per-frame sampling, for springy text pops and entrances.

## Use

```python
import spring_motion
```

Placed by `baltor_catalog.py place spring_motion <step-dir>` under `.baltor/lib/spring-motion/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
