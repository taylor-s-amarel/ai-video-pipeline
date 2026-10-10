# TTS sentence chunker

Splits narration into TTS-sized chunks of whole sentences (abbreviation, decimal and initial aware), splitting over-long sentences at clause marks and tagging paragraph boundaries for pauses.

## Use

```python
import tts_sentence_chunker
```

Placed by `baltor_catalog.py place tts_sentence_chunker <step-dir>` under `.baltor/lib/tts-sentence-chunker/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
