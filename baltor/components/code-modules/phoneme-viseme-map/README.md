# Phoneme to viseme mapping

Maps every ARPAbet phoneme to Rhubarb-style mouth letters (A-H, X) and turns timed phones into merged, flicker-free mouth cues for lip-sync animation.

## Use

```python
import phoneme_viseme_map
```

Placed by `baltor_catalog.py place phoneme_viseme_map <step-dir>` under `.baltor/lib/phoneme-viseme-map/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## References

- https://github.com/DanielSWolf/rhubarb-lip-sync

## Licence

MIT. Original work for the Baltor public-good collection.
