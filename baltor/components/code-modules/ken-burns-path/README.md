# Ken Burns pan/zoom path generator

Per-frame crop rectangles for pan and zoom moves over a still, kept inside the image, log-space zoom, eased, with named presets and an upscale-risk measure.

## Use

```python
import ken_burns_path
```

Placed by `baltor_catalog.py place ken_burns_path <step-dir>` under `.baltor/lib/ken-burns-path/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
