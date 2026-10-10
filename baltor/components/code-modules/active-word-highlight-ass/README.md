# Active-word highlight ASS events

Emits ASS events that keep a whole caption line visible while recolouring (and optionally scaling) the word currently spoken, with contiguous, flicker-free timing.

## Use

```python
import active_word_highlight_ass
```

Placed by `baltor_catalog.py place active_word_highlight_ass <step-dir>` under `.baltor/lib/active-word-highlight-ass/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
