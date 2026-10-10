# Saliency crop window

Chooses the crop window of a target aspect that keeps the most salient content (edges plus colour distinctness via integral images) and smooths it over time for jitter-free reframing.

## Use

```python
import saliency_crop_window
```

Placed by `baltor_catalog.py place saliency_crop_window <step-dir>` under `.baltor/lib/saliency-crop-window/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
