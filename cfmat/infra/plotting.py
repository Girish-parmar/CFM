"""Chart helper for the labs: saves figures under ``build/lab-output/``.

Set ``CFMAT_OUTPUT_DIR`` to save somewhere else (see ``cfmat.infra.paths``).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

if matplotlib.get_backend().lower() not in ("module://matplotlib_inline.backend_inline", "nbagg", "widget"):
    matplotlib.use("Agg")  # scripts and CI render off-screen; notebooks keep inline plots

import matplotlib.pyplot as plt

from .paths import output_dir

__all__ = ["output_dir", "plt", "savefig"]


def savefig(fig: plt.Figure, name: str) -> Path:
    """Save ``fig`` as ``<output_dir>/<name>.png``, close it and return the path."""
    path = output_dir() / f"{name}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
