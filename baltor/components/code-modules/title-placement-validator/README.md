# Title placement validator

Checks first-frame title boxes against house rules (centre in the upper 40%, overlaid on the photo, photo >= 80% width and never shrunk, inside margins, legible size) and suggests a compliant box.

## Use

```python
import title_placement_validator
```

Placed by `baltor_catalog.py place title_placement_validator <step-dir>` under `.baltor/lib/title-placement-validator/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
