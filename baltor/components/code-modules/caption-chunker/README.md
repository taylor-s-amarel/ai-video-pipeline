# Phrase-aware caption chunker

Splits narration into single-line caption chunks of at most 7 words using dynamic programming that prefers punctuation and pauses, avoids function-word endings and keeps numbers with units.

## Use

```python
import caption_chunker
```

Placed by `baltor_catalog.py place caption_chunker <step-dir>` under `.baltor/lib/caption-chunker/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
