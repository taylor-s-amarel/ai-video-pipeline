# Isometric and dimetric projection

True isometric and 2:1 pixel-art dimetric projection with ground unprojection, diamond tile picking and painter's-order depth sorting for 2.5D and top-down scenes.

## Use

```python
import isometric_projection
```

Placed by `baltor_catalog.py place isometric_projection <step-dir>` under `.baltor/lib/isometric-projection/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
