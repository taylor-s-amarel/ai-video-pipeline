# Scene change detector

Finds hard cuts with colour-histogram distance against an absolute and locally adaptive threshold (fades and motion ignored) and reports shot lengths for pacing checks.

## Use

```python
import scene_change_detector
```

Placed by `baltor_catalog.py place scene_change_detector <step-dir>` under `.baltor/lib/scene-change-detector/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
