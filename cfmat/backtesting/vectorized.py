"""Vectorised backtesting and parameter search for signal functions (M11).

The one rule that matters most: a signal computed from bar t's close can only
earn bar t+1's return. ``vectorized_backtest`` enforces this by shifting the
position one bar before multiplying by returns.
"""

from __future__ import annotations

from collections.abc import Callable
from itertools import product

import numpy as np
import pandas as pd

from ..analytics.metrics import equity_curve, sharpe_ratio


def vectorized_backtest(close: pd.Series, signal: pd.Series, cost_bps: float = 0.0) -> pd.DataFrame:
    """Backtest a single-instrument target-position series.

    ``signal`` is the desired exposure (e.g. −1, 0, +1 or fractional) decided at
    each close. ``cost_bps`` is charged on every unit of turnover (one side).
    """
    signal = signal.reindex(close.index).fillna(0.0)
    asset_ret = close.pct_change().fillna(0.0)
    held = signal.shift(1).fillna(0.0)
    turnover = held.diff().abs()
    turnover.iloc[0] = abs(held.iloc[0])
    cost = turnover * cost_bps / 1e4
    strat = held * asset_ret - cost
    return pd.DataFrame(
        {
            "close": close,
            "signal": signal,
            "position": held,
            "asset_return": asset_ret,
            "turnover": turnover,
            "cost": cost,
            "strategy_return": strat,
            "equity": equity_curve(strat),
        }
    )


def portfolio_backtest(prices: pd.DataFrame, weights: pd.DataFrame, cost_bps: float = 0.0) -> pd.DataFrame:
    """Backtest target weights across many instruments (weights decided at close)."""
    weights = weights.reindex(prices.index).fillna(0.0)
    rets = prices.pct_change().fillna(0.0)
    held = weights.shift(1).fillna(0.0)
    turnover = held.diff().abs().sum(axis=1)
    turnover.iloc[0] = held.iloc[0].abs().sum()
    cost = turnover * cost_bps / 1e4
    strat = (held * rets).sum(axis=1) - cost
    return pd.DataFrame({"turnover": turnover, "cost": cost, "strategy_return": strat, "equity": equity_curve(strat)})


def pairs_backtest(
    y: pd.Series, x: pd.Series, legs: pd.DataFrame, capital: float = 1_000_000.0, cost_bps: float = 0.0
) -> pd.DataFrame:
    """Rupee P&L of a pair where ``legs`` holds unit positions from ``pairs_signals``.

    Each spread unit (1 share of y against beta shares of x) is sized so that
    gross notional ≈ ``capital``.
    """
    gross_per_unit = y + legs["beta"].abs() * x
    units = (capital / gross_per_unit).fillna(0.0)
    shares_y = (legs["y"] * units).round()
    shares_x = (legs["x"] * units).round()
    held_y, held_x = shares_y.shift(1).fillna(0.0), shares_x.shift(1).fillna(0.0)
    pnl = held_y * y.diff().fillna(0.0) + held_x * x.diff().fillna(0.0)
    # the change in holdings at bar t was traded at bar t-1's close, so cost it at that price
    traded_y = held_y.diff().fillna(held_y).abs()
    traded_x = held_x.diff().fillna(held_x).abs()
    traded_value = (traded_y * y.shift(1) + traded_x * x.shift(1)).fillna(0.0)
    cost = traded_value * cost_bps / 1e4
    net = pnl - cost
    ret = net / capital
    return pd.DataFrame(
        {"shares_y": held_y, "shares_x": held_x, "pnl": pnl, "cost": cost, "net_pnl": net,
         "strategy_return": ret, "equity": equity_curve(ret)}
    )


def grid_search(
    close: pd.Series,
    strategy: Callable[..., pd.Series],
    grid: dict[str, list],
    cost_bps: float = 0.0,
) -> pd.DataFrame:
    """In-sample Sharpe for every parameter combination (the overfitting trap)."""
    keys = list(grid)
    rows = []
    for values in product(*(grid[k] for k in keys)):
        params = dict(zip(keys, values))
        try:
            bt = vectorized_backtest(close, strategy(close, **params), cost_bps)
        except ValueError:
            continue
        rows.append({**params, "sharpe": sharpe_ratio(bt["strategy_return"])})
    return pd.DataFrame(rows).sort_values("sharpe", ascending=False, ignore_index=True)


def walk_forward(
    close: pd.Series,
    strategy: Callable[..., pd.Series],
    grid: dict[str, list],
    train: int = 504,
    test: int = 126,
    cost_bps: float = 0.0,
) -> tuple[pd.Series, pd.DataFrame]:
    """Re-optimise on each training window and trade the next test window.

    Returns the stitched out-of-sample returns and a table of chosen parameters.
    Only data up to the end of each window is ever passed to ``strategy``.
    """
    keys = list(grid)
    combos = [dict(zip(keys, v)) for v in product(*(grid[k] for k in keys))]
    oos, chosen = [], []
    for start in range(0, len(close) - train - test + 1, test):
        train_end, test_end = start + train, start + train + test
        best, best_score = None, -np.inf
        for params in combos:
            try:
                sig = strategy(close.iloc[:train_end], **params)
            except ValueError:
                continue
            bt = vectorized_backtest(close.iloc[:train_end], sig, cost_bps)
            score = sharpe_ratio(bt["strategy_return"].iloc[start:train_end])
            if score > best_score:
                best, best_score = params, score
        if best is None:
            continue
        sig = strategy(close.iloc[:test_end], **best)
        bt = vectorized_backtest(close.iloc[:test_end], sig, cost_bps)
        oos.append(bt["strategy_return"].iloc[train_end:test_end])
        chosen.append({"test_start": close.index[train_end], **best, "train_sharpe": best_score})
    if not oos:
        raise ValueError("series too short for the requested train/test windows")
    return pd.concat(oos), pd.DataFrame(chosen)
