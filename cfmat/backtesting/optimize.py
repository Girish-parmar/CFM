"""Parameter search for Strategy Creator specs: parallel sweeps, coarse-to-fine
search, walk-forward and strategy x instrument matrices (Module 12).
"""

from __future__ import annotations

from itertools import product

import numpy as np
import pandas as pd

from ..analytics.metrics import equity_curve, max_drawdown, performance_summary, sharpe_ratio
from ..infra.parallel import parallel_map, shared
from ..strategies.spec import StrategySpec
from .rule_engine import BacktestResult, backtest


def expand_grid(grid: dict[str, list]) -> list[dict]:
    keys = list(grid)
    return [dict(zip(keys, values)) for values in product(*(grid[k] for k in keys))]


def _score(result: BacktestResult, rows: slice | None) -> dict:
    r = result.returns if rows is None else result.returns.iloc[rows]
    t = result.trades
    if rows is not None and len(t):
        start, end = result.returns.index[rows][[0, -1]]
        t = t[(t["exit_time"] >= start) & (t["exit_time"] <= end)]
    return {"sharpe": sharpe_ratio(r), "cagr": performance_summary(r)["cagr"],
            "max_dd": max_drawdown(equity_curve(r)), "trades": len(t),
            "win_rate": float((t["return"] > 0).mean()) if len(t) else 0.0}


def _sweep_task(params: dict) -> dict:
    bars, spec, kwargs, rows = shared("bars"), shared("spec"), shared("kwargs"), shared("rows")
    try:
        result = backtest(bars, spec.resolve(**params), **kwargs)
        return {**params, **_score(result, rows)}
    except ValueError as exc:
        return {**params, "sharpe": np.nan, "error": str(exc)}


def sweep(
    bars: pd.DataFrame,
    spec: StrategySpec,
    grid: dict[str, list] | list[dict],
    workers: int = 1,
    backend: str = "process",
    rows: slice | None = None,
    **backtest_kwargs,
) -> pd.DataFrame:
    """Backtest every parameter combination; results sorted by Sharpe.

    ``rows`` restricts scoring to a slice of bars (e.g. a training window);
    pass bars that end at the window so no later data is ever touched.
    """
    combos = expand_grid(grid) if isinstance(grid, dict) else list(grid)
    out = parallel_map(_sweep_task, combos, workers=workers, backend=backend,
                       shared={"bars": bars, "spec": spec, "kwargs": backtest_kwargs, "rows": rows})
    return pd.DataFrame(out).sort_values("sharpe", ascending=False, ignore_index=True)


def coarse_to_fine(
    bars: pd.DataFrame,
    spec: StrategySpec,
    grid: dict[str, list],
    top_k: int = 3,
    workers: int = 1,
    backend: str = "process",
    rows: slice | None = None,
    **backtest_kwargs,
) -> tuple[pd.DataFrame, int]:
    """Smarter search: test every other value of each parameter first, then only
    the neighbours of the ``top_k`` coarse winners. Returns (results, evaluations)."""
    coarse_grid = {k: v[::2] if len(v) > 2 else v for k, v in grid.items()}
    first = sweep(bars, spec, coarse_grid, workers, backend, rows, **backtest_kwargs)
    tried = {tuple(sorted(r.items())) for r in expand_grid(coarse_grid)}
    neighbours = []
    for _, row in first.dropna(subset=["sharpe"]).head(top_k).iterrows():
        axes = {}
        for k, values in grid.items():
            i = values.index(row[k])
            axes[k] = values[max(0, i - 1): i + 2]
        for combo in expand_grid(axes):
            key = tuple(sorted(combo.items()))
            if key not in tried:
                tried.add(key)
                neighbours.append(combo)
    second = sweep(bars, spec, neighbours, workers, backend, rows, **backtest_kwargs) if neighbours else first.iloc[:0]
    results = pd.concat([first, second], ignore_index=True).sort_values("sharpe", ascending=False, ignore_index=True)
    return results, len(results)


def _like(values: list, v):
    """Cast a value read back from a results table to the type used in the grid."""
    if all(isinstance(x, (int, np.integer)) and not isinstance(x, bool) for x in values):
        return int(v)
    if all(isinstance(x, (float, int)) for x in values):
        return float(v)
    return v


def walk_forward(
    bars: pd.DataFrame,
    spec: StrategySpec,
    grid: dict[str, list],
    train: int = 750,
    test: int = 250,
    workers: int = 1,
    backend: str = "process",
    **backtest_kwargs,
) -> tuple[pd.Series, pd.DataFrame]:
    """Re-optimise on each training window, trade the next test window."""
    oos, chosen = [], []
    for start in range(0, len(bars) - train - test + 1, test):
        train_end, test_end = start + train, start + train + test
        table = sweep(bars.iloc[:train_end], spec, grid, workers, backend, slice(start, train_end), **backtest_kwargs)
        best = {k: _like(grid[k], table.iloc[0][k]) for k in grid}
        result = backtest(bars.iloc[:test_end], spec.resolve(**best), **backtest_kwargs)
        oos.append(result.returns.iloc[train_end:test_end])
        chosen.append({"test_start": bars.index[train_end], **best, "train_sharpe": table.iloc[0]["sharpe"]})
    if not oos:
        raise ValueError("not enough bars for the requested train/test windows")
    return pd.concat(oos), pd.DataFrame(chosen)


def _matrix_task(task: tuple[str, str]) -> dict:
    symbol, name = task
    result = backtest(shared("universe")[symbol], shared("specs")[name], **shared("kwargs"))
    return {"symbol": symbol, "strategy": name, **_score(result, None)}


def strategy_matrix(
    universe: dict[str, pd.DataFrame],
    specs: dict[str, StrategySpec],
    workers: int = 1,
    backend: str = "process",
    **backtest_kwargs,
) -> pd.DataFrame:
    """Backtest every strategy on every instrument (long format: one row per pair)."""
    tasks = [(s, n) for s in universe for n in specs]
    rows = parallel_map(_matrix_task, tasks, workers=workers, backend=backend,
                        shared={"universe": universe, "specs": specs, "kwargs": backtest_kwargs})
    return pd.DataFrame(rows)
