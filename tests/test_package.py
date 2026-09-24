"""Package layout: every subpackage imports on its own, sample data ships, versions agree."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

import cfmat
from cfmat.infra import paths

ROOT = Path(__file__).resolve().parent.parent
SUBPACKAGES = sorted(p.name for p in (ROOT / "cfmat").iterdir() if (p / "__init__.py").exists())


def test_expected_subpackages():
    assert SUBPACKAGES == ["analytics", "automation", "backtesting", "data", "derivatives", "econometrics", "infra",
                           "microstructure", "ml", "nlp", "portfolio", "research", "strategies", "trading"]


@pytest.mark.parametrize("name", [*SUBPACKAGES, "studio", "automation.signal_service", "infra.plotting"])
def test_each_module_imports_in_a_fresh_interpreter(name):
    # a fresh interpreter catches circular imports that pass when modules are already loaded
    result = subprocess.run([sys.executable, "-c", f"import cfmat.{name}"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-2000:]


def test_public_names_resolve():
    import importlib

    for name in SUBPACKAGES:
        module = importlib.import_module(f"cfmat.{name}")
        for attr in getattr(module, "__all__", []):
            assert hasattr(module, attr), f"cfmat.{name}.__all__ lists missing name {attr!r}"


def test_sample_data_ships_inside_the_package():
    assert (paths.SAMPLE_DATA_DIR / "sample_headlines.csv").exists()
    assert len(list((paths.SAMPLE_DATA_DIR / "filings").glob("*.md"))) == 3


def test_output_dir_honours_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("CFMAT_OUTPUT_DIR", str(tmp_path / "out"))
    assert paths.output_dir() == tmp_path / "out" and (tmp_path / "out").is_dir()


def test_version_matches_pyproject():
    text = (ROOT / "pyproject.toml").read_text()
    assert re.search(r'^version = "([^"]+)"', text, re.M).group(1) == cfmat.__version__
