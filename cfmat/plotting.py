"""Chart helper for the labs: saves figures under labs/output/."""

from __future__ import annotations

from pathlib import Path

import matplotlib

if matplotlib.get_backend().lower() not in ("module://matplotlib_inline.backend_inline", "nbagg", "widget"):
    matplotlib.use("Agg")  # scripts and CI render off-screen; notebooks keep inline plots

import matplotlib.pyplot as plt  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "labs" / "output"


def savefig(fig: "plt.Figure", name: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{name}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
