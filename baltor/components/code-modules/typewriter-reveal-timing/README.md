# Typewriter reveal timing

Character-by-character reveal schedule with punctuation pauses and ASS events that keep line layout stable by drawing the untyped remainder fully transparent.

## Use

```python
import typewriter_reveal_timing
```

Placed by `baltor_catalog.py place typewriter_reveal_timing <step-dir>` under `.baltor/lib/typewriter-reveal-timing/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
