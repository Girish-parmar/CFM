"""Filesystem locations used by the library, in one place.

``SAMPLE_DATA_DIR``  fictional sample data shipped inside the package
``user_data_dir()``  the learner's own price files (``CFMAT_DATA_DIR``, default ``<repo>/data``)
``output_dir()``     where labs write charts and files (``CFMAT_OUTPUT_DIR``,
                     default ``<repo>/build/lab-output``)

The repository root is detected from the package location for an editable
install; for a normal install it falls back to the current working directory.
"""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DATA_DIR = PACKAGE_DIR / "data" / "samples"


def repo_root() -> Path:
    candidate = PACKAGE_DIR.parent
    return candidate if (candidate / "pyproject.toml").exists() else Path.cwd()


def user_data_dir() -> Path:
    return Path(os.environ.get("CFMAT_DATA_DIR") or repo_root() / "data")


def output_dir(create: bool = True) -> Path:
    path = Path(os.environ.get("CFMAT_OUTPUT_DIR") or repo_root() / "build" / "lab-output")
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path
