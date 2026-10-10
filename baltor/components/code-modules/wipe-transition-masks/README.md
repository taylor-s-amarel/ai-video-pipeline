# Wipe transition masks

Soft-edged numpy alpha masks for linear (any angle), radial, clock, diamond and blinds wipes that go exactly from clip A to clip B, plus a frame blender.

## Use

```python
import wipe_transition_masks
```

Placed by `baltor_catalog.py place wipe_transition_masks <step-dir>` under `.baltor/lib/wipe-transition-masks/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
