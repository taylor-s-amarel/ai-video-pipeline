# Staggered word entrance timing

Per-word entrance windows (fixed stagger or TTS word times) and per-frame opacity/rise state, capped at 98% opacity, for kinetic caption and title reveals.

## Use

```python
import word_stagger_timing
```

Placed by `baltor_catalog.py place word_stagger_timing <step-dir>` under `.baltor/lib/word-stagger-timing/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
