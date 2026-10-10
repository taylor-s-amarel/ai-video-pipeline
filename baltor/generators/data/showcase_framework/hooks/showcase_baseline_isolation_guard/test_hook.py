import json
import subprocess
import sys
from pathlib import Path

import hook

HOOK = Path(__file__).resolve().parent / "hook.py"


def call(event, arm):
    return subprocess.run([sys.executable, str(HOOK), "--arm", arm], input=json.dumps(event), capture_output=True,
                          text=True, timeout=30)


def test_baseline_blocks_catalogue_access():
    for ev in [{"tool_name": "mcp__baltor__intelligence_search", "tool_input": {"query": "x"}},
               {"tool_name": "Bash", "tool_input": {"command": "python3 ../../baltor/tools/baltor_catalog.py search dedupe"}},
               {"tool_name": "Bash", "tool_input": {"command": "baltor read some_skill --out vendor"}},
               {"tool_name": "Read", "tool_input": {"file_path": "/repo/baltor/components/skills/x/SKILL.md"}},
               {"tool_name": "Bash", "tool_input": {"command": "cat .baltor/step.lock.json"}},
               {"tool_name": "WebFetch", "tool_input": {"url": "https://baltor.ai/mcp"}}]:
        assert hook.blocked(ev, "baseline"), ev
        assert hook.blocked(ev, "baltor") is None


def test_ordinary_work_passes():
    for ev in [{"tool_name": "Bash", "tool_input": {"command": "python3 dedupe.py contacts.csv clusters.csv"}},
               {"tool_name": "Write", "tool_input": {"file_path": "NOTES.md", "content": "Baltimore office"}},
               {"tool_name": "Read", "tool_input": {"file_path": "contacts.csv"}}]:
        assert hook.blocked(ev, "baseline") is None, ev


def test_exit_codes():
    bad = {"tool_name": "mcp__baltor__provisioning_read", "tool_input": {"identity": "x"}}
    proc = call(bad, "baseline")
    assert proc.returncode == 2 and "baseline arm" in proc.stderr
    assert call(bad, "baltor").returncode == 0
    assert subprocess.run([sys.executable, str(HOOK), "--arm", "baseline"], input="not json", capture_output=True,
                          text=True, timeout=30).returncode == 0
