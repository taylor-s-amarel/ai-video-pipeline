# Caption retiming from anchors

Fixes steadily drifting captions with a linear time map solved from two anchors or fitted from several (with residual report), plus shifts and frame-rate scale factors.

## Use

```python
import caption_retime_anchors
```

Placed by `baltor_catalog.py place caption_retime_anchors <step-dir>` under `.baltor/lib/caption-retime-anchors/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
