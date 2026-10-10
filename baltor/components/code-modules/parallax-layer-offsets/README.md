# Parallax layer offsets (2.5D camera)

Pinhole-camera parallax for flat layers: per-layer screen shift and dolly scale from depth, focal picking for a target shift, and overscan needed so edges never show.

## Use

```python
import parallax_layer_offsets
```

Placed by `baltor_catalog.py place parallax_layer_offsets <step-dir>` under `.baltor/lib/parallax-layer-offsets/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
