# Two-bone inverse kinematics

Analytic 2D two-bone IK for arms and legs with bend direction, unreachable-target handling and exact bone-length preservation, for stick figures and cut-out rigs.

## Use

```python
import two_bone_ik
```

Placed by `baltor_catalog.py place two_bone_ik <step-dir>` under `.baltor/lib/two-bone-ik/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
