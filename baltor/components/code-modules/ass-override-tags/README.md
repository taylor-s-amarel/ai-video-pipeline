# ASS override tag builders

Range-checked builders for ASS override tags (position, move, fades, colours, inverted alpha, scale, rotation, blur, clip, transforms) and a safe block joiner.

## Use

```python
import ass_override_tags
```

Placed by `baltor_catalog.py place ass_override_tags <step-dir>` under `.baltor/lib/ass-override-tags/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
