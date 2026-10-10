# Caption keyword picker

Chooses the word that pops in each caption, preferring numbers, topic terms and proper nouns over long content words, and avoids popping the same word twice in a row.

## Use

```python
import caption_keyword_picker
```

Placed by `baltor_catalog.py place caption_keyword_picker <step-dir>` under `.baltor/lib/caption-keyword-picker/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
