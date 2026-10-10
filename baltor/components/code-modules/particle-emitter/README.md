# Deterministic particle emitter

Seeded 2D particle emitter with closed-form gravity and drag (random access to any frame), life-based size and opacity capped at 98%, and Pillow rendering for dust, sparks and embers.

## Use

```python
import particle_emitter
```

Placed by `baltor_catalog.py place particle_emitter <step-dir>` under `.baltor/lib/particle-emitter/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
