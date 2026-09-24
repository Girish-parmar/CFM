"""From model probabilities to positions and bet sizes (M19, M23).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def proba_to_position(proba: pd.Series, threshold: float = 0.55) -> pd.Series:
    """Long above ``threshold``, short below 1 − threshold, flat otherwise."""
    pos = pd.Series(0.0, index=proba.index)
    pos[proba > threshold] = 1.0
    pos[proba < 1 - threshold] = -1.0
    return pos


def bet_size(proba: pd.Series) -> pd.Series:
    """Map the probability that a trade succeeds to a size in [0, 1].

    Size = 2·Φ(z) − 1 with z = (p − 0.5) / sqrt(p(1 − p)), floored at 0, so
    trades the model doubts get no capital and confident ones approach full size
    (López de Prado, 2018, ch. 10).
    """
    from scipy.stats import norm

    p = proba.clip(1e-6, 1 - 1e-6)
    z = (p - 0.5) / np.sqrt(p * (1 - p))
    size = pd.Series(2 * norm.cdf(z) - 1, index=proba.index).clip(lower=0.0)
    return size.where(proba.notna(), 0.0)
