# ASS karaoke tags from word times

Converts word timestamps into ASS karaoke tags (\k, \kf, \ko) with a lead-in tag and rounding carried forward so highlight timing never drifts from the voice.

## Use

```python
import ass_karaoke_tags
```

Placed by `baltor_catalog.py place ass_karaoke_tags <step-dir>` under `.baltor/lib/ass-karaoke-tags/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
