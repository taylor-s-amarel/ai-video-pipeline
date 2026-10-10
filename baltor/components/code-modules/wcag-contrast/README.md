# WCAG contrast and readable text colour

WCAG 2.x relative luminance and contrast ratio with AA/AAA grading, worst-case readable text colour over moving backgrounds, and the minimum backing-panel opacity that reaches a target ratio.

## Use

```python
import wcag_contrast
```

Placed by `baltor_catalog.py place wcag_contrast <step-dir>` under `.baltor/lib/wcag-contrast/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## References

- https://www.w3.org/TR/WCAG21/#dfn-contrast-ratio

## Licence

MIT. Original work for the Baltor public-good collection.
