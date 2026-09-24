"""Smoke test: every lab script runs to completion."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LABS = sorted((ROOT / "labs").glob("lab*.py"))


def test_all_labs_present():
    assert len(LABS) == 18


@pytest.mark.parametrize("lab", LABS, ids=lambda p: p.stem)
def test_lab_runs(lab):
    env = {**os.environ, "PYTHONPATH": str(ROOT), "MPLBACKEND": "Agg"}
    env.pop("ANTHROPIC_API_KEY", None)  # keep the LLM step offline in tests
    result = subprocess.run([sys.executable, str(lab)], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stderr[-3000:]
