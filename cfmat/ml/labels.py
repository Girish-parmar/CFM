"""Labels for financial ML: triple-barrier and meta-labels (M19, M23).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def triple_barrier_labels(
    close: pd.Series,
    horizon: int = 10,
    pt_mult: float = 1.0,
    sl_mult: float = 1.0,
    vol_window: int = 20,
    vertical: str = "sign",
) -> pd.DataFrame:
    """Label each bar by which barrier the price path touches first.

    Barrier width = volatility over the horizon (daily vol · sqrt(horizon)),
    scaled by ``pt_mult`` / ``sl_mult``. Returns columns ``label`` (+1 / −1,
    or 0 on the time barrier when ``vertical="zero"``), ``exit_pos`` (integer
    position of the exit bar) and ``ret`` (log return to exit).
    """
    logp = np.log(close.to_numpy(dtype=float))
    daily_vol = pd.Series(logp, index=close.index).diff().rolling(vol_window).std().to_numpy()
    n = len(close)
    labels = np.full(n, np.nan)
    exits = np.full(n, np.nan)
    rets = np.full(n, np.nan)
    for i in range(n - horizon):
        if np.isnan(daily_vol[i]):
            continue
        width = daily_vol[i] * np.sqrt(horizon)
        path = logp[i + 1 : i + horizon + 1] - logp[i]
        up = np.nonzero(path >= pt_mult * width)[0]
        down = np.nonzero(path <= -sl_mult * width)[0]
        first_up = up[0] if len(up) else horizon
        first_down = down[0] if len(down) else horizon
        if first_up < first_down:
            labels[i], j = 1, first_up
        elif first_down < first_up:
            labels[i], j = -1, first_down
        else:
            j = horizon - 1
            labels[i] = np.sign(path[j]) if vertical == "sign" else 0
        exits[i] = i + 1 + j
        rets[i] = path[j]
    return pd.DataFrame({"label": labels, "exit_pos": exits, "ret": rets}, index=close.index)


def meta_labels(
    close: pd.Series,
    side: pd.Series,
    horizon: int = 10,
    pt_mult: float = 1.0,
    sl_mult: float = 1.0,
    vol_window: int = 20,
) -> pd.DataFrame:
    """Meta-labels (López de Prado, 2018, ch. 3.6).

    A primary model decides the *side* (+1 long, −1 short, 0 no trade). For each
    bar with a side, label 1 if a trade in that direction would reach its profit
    target before its stop-loss (or finish positive at the time barrier), else 0.
    A secondary model trained on these labels learns *when to trust* the primary
    model, and its probability can size the bet.
    """
    logp = np.log(close.to_numpy(dtype=float))
    s = side.reindex(close.index).fillna(0.0).to_numpy()
    daily_vol = pd.Series(logp, index=close.index).diff().rolling(vol_window).std().to_numpy()
    n = len(close)
    labels = np.full(n, np.nan)
    rets = np.full(n, np.nan)
    for i in range(n - horizon):
        if s[i] == 0 or np.isnan(daily_vol[i]):
            continue
        width = daily_vol[i] * np.sqrt(horizon)
        path = s[i] * (logp[i + 1 : i + horizon + 1] - logp[i])       # P&L path of the trade
        up = np.nonzero(path >= pt_mult * width)[0]
        down = np.nonzero(path <= -sl_mult * width)[0]
        first_up = up[0] if len(up) else horizon
        first_down = down[0] if len(down) else horizon
        j = min(first_up, first_down, horizon - 1)
        labels[i] = 1.0 if first_up < first_down or (first_up == first_down and path[j] > 0) else 0.0
        rets[i] = path[j]
    return pd.DataFrame({"label": labels, "ret": rets, "side": s}, index=close.index)
