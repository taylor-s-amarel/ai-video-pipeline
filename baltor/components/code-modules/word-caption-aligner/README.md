# Word-timestamp caption aligner with drift report

Retimes caption cues to spoken word timestamps (fuzzy token matching, interpolation for unrecognised cues, overlap repair) and reports per-cue drift against a 150 ms tolerance.

## Use

```python
import word_caption_aligner
```

Placed by `baltor_catalog.py place word_caption_aligner <step-dir>` under `.baltor/lib/word-caption-aligner/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
