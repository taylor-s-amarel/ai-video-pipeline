# TTS text normaliser

Rewrites money, percentages, ranges, ordinals, years, clock times, temperatures, units, abbreviations and symbols into words so TTS voices read narration correctly.

## Use

```python
import tts_text_normaliser
```

Placed by `baltor_catalog.py place tts_text_normaliser <step-dir>` under `.baltor/lib/tts-text-normaliser/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
