"""Smoke test: every ready lab in course/course.yaml runs to completion (select with ``-m lab``)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.course_tools import load_route_manager

pytestmark = pytest.mark.lab

ROOT = Path(__file__).resolve().parent.parent
LABS = [lab.path for lab in load_route_manager().Course.load().labs() if lab.status == "ready"]


def test_every_lab_file_is_a_ready_lab_in_the_manifest():
    assert sorted(LABS) == sorted((ROOT / "curriculum").glob("m*/lab_*.py"))


@pytest.mark.parametrize("lab", LABS, ids=lambda p: p.stem.removeprefix("lab_"))
def test_lab_runs(lab, tmp_path):
    env = {**os.environ, "PYTHONPATH": str(ROOT), "MPLBACKEND": "Agg", "CFMAT_OUTPUT_DIR": str(tmp_path)}
    env.setdefault("OMP_NUM_THREADS", "2")   # OpenMP busy-waits badly when CPUs are oversubscribed
    env.pop("ANTHROPIC_API_KEY", None)       # keep the LLM step offline in tests
    result = subprocess.run([sys.executable, str(lab)], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=900)
    assert result.returncode == 0, result.stderr[-3000:]
