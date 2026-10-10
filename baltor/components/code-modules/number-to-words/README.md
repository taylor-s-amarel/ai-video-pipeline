# Number to words for TTS

Spells cardinals, negatives, decimals, ordinals and years the way they are spoken ("nineteen seventy", "twenty-first", "three point one four") for text-to-speech input.

## Use

```python
import number_to_words
```

Placed by `baltor_catalog.py place number_to_words <step-dir>` under `.baltor/lib/number-to-words/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
