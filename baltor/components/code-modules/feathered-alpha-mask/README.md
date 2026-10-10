# Feathered alpha masks

Signed-distance rounded-rectangle and ellipse masks with even soft feathers, edge fades, mask combining and Pillow output, capped at 98% so no layer has a hard cutout or full opacity.

## Use

```python
import feathered_alpha_mask
```

Placed by `baltor_catalog.py place feathered_alpha_mask <step-dir>` under `.baltor/lib/feathered-alpha-mask/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
