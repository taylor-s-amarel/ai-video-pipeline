"""Score total.json against the expected total. Prints one JSON line."""
import json
import sys
from pathlib import Path

ws, expected = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text())["total"]
try:
    got = float(json.loads((ws / "total.json").read_text())["total"])
except Exception as exc:  # noqa: BLE001
    print(json.dumps({"value": 0.0, "passed": False, "details": {"error": str(exc)}}))
    sys.exit(0)
ok = abs(got - expected) <= 0.005
print(json.dumps({"value": 1.0 if ok else 0.0, "passed": ok, "details": {"reported": got, "expected": expected}}))
