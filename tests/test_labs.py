"""Smoke test: every lab script runs to completion (select with ``-m lab``)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.lab

ROOT = Path(__file__).resolve().parent.parent
LABS = sorted((ROOT / "labs").glob("lab*.py"))


def test_all_labs_present():
    assert len(LABS) == 22


@pytest.mark.parametrize("lab", LABS, ids=lambda p: p.stem)
def test_lab_runs(lab, tmp_path):
    env = {**os.environ, "PYTHONPATH": str(ROOT), "MPLBACKEND": "Agg", "CFMAT_OUTPUT_DIR": str(tmp_path)}
    env.setdefault("OMP_NUM_THREADS", "2")   # OpenMP busy-waits badly when CPUs are oversubscribed
    env.pop("ANTHROPIC_API_KEY", None)       # keep the LLM step offline in tests
    result = subprocess.run([sys.executable, str(lab)], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=900)
    assert result.returncode == 0, result.stderr[-3000:]
