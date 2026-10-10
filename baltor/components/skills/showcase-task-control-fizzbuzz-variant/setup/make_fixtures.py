#!/usr/bin/env python3
"""Create the workspace and hidden expected output for a negative-control task."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import controls_fixtures as cf  # noqa: E402
import showcase_eval as se  # noqa: E402


def make(task, workspace, hidden, seed, args):
    cf.MAKERS[task["params"]["kind"]](task["params"], workspace, hidden, seed)


if __name__ == "__main__":
    raise SystemExit(se.setup_cli(__file__, make))
