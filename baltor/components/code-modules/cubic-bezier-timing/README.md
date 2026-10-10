# CSS cubic-bezier timing functions

Evaluates cubic-bezier(x1, y1, x2, y2) timing curves exactly like CSS (Newton + bisection), with the ease/ease-in/ease-out/ease-in-out presets and a CSS parser.

## Use

```python
import cubic_bezier_timing
```

Placed by `baltor_catalog.py place cubic_bezier_timing <step-dir>` under `.baltor/lib/cubic-bezier-timing/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## References

- https://www.w3.org/TR/css-easing-1/

## Licence

MIT. Original work for the Baltor public-good collection.
