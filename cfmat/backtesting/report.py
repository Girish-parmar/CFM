"""Backtest reports: trade statistics, summary tables and charts (M11, M12)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..analytics.metrics import MONTHS, drawdown_series, equity_curve, performance_summary


def trade_stats(trades: pd.DataFrame) -> dict[str, float]:
    """Win rate, payoff, expectancy and streaks from a trade list with a ``return`` column."""
    if trades is None or len(trades) == 0:
        return {"trades": 0, "win_rate": 0.0, "avg_win": 0.0, "avg_loss": 0.0, "payoff_ratio": 0.0,
                "expectancy": 0.0, "trade_profit_factor": 0.0, "max_consecutive_losses": 0, "avg_bars": 0.0}
    r = trades["return"]
    wins, losses = r[r > 0], r[r <= 0]
    streak = longest = 0
    for x in r:
        streak = streak + 1 if x <= 0 else 0
        longest = max(longest, streak)
    avg_loss = losses.mean() if len(losses) else 0.0
    return {
        "trades": len(r),
        "win_rate": float((r > 0).mean()),
        "avg_win": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss": float(avg_loss),
        "payoff_ratio": float(wins.mean() / -avg_loss) if len(wins) and avg_loss < 0 else float("inf"),
        "expectancy": float(r.mean()),
        "trade_profit_factor": float(wins.sum() / -losses.sum()) if losses.sum() < 0 else float("inf"),
        "max_consecutive_losses": int(longest),
        "avg_bars": float(trades["bars"].mean()) if "bars" in trades else float("nan"),
    }


def backtest_stats(result) -> pd.Series:
    """One-line report for a ``strategy_builder.BacktestResult``."""
    perf = performance_summary(result.returns)
    trades = result.trades
    extra = {
        "exposure": float((result.position != 0).mean()),
        "long_trades": int((trades["side"] == "long").sum()) if len(trades) else 0,
        "short_trades": int((trades["side"] == "short").sum()) if len(trades) else 0,
        "exits_by_stop": int((trades["reason"] == "stop").sum()) if len(trades) else 0,
    }
    return pd.concat([perf, pd.Series(trade_stats(trades)), pd.Series(extra)])


def monthly_returns_table(returns: pd.Series) -> pd.DataFrame:
    """Compounded return (%) per calendar month, years as rows, plus a yearly total."""
    monthly = (1 + returns).groupby([returns.index.year, returns.index.month]).prod() - 1
    table = monthly.unstack() * 100
    table.columns = [MONTHS[m - 1] for m in table.columns]
    table.index.name = "year"
    yearly = (1 + returns).groupby(returns.index.year).prod() - 1
    table["Year"] = yearly.to_numpy() * 100
    return table


def compare(results: dict) -> pd.DataFrame:
    """Side-by-side stats for several backtest results."""
    keep = ["cagr", "volatility", "sharpe", "max_drawdown", "trades", "win_rate", "payoff_ratio",
            "expectancy", "exposure", "max_consecutive_losses"]
    return pd.DataFrame({name: backtest_stats(r)[keep] for name, r in results.items()}).T


def plot_backtest(bars: pd.DataFrame, result, title: str = ""):
    """Price with entries/exits, equity curve and drawdown. Returns the figure."""
    from ..infra.plotting import plt

    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True, gridspec_kw={"height_ratios": [3, 2, 1]})
    axes[0].plot(bars.index, bars["close"], lw=1, color="black")
    t = result.trades
    if len(t):
        for side, marker, colour in (("long", "^", "tab:green"), ("short", "v", "tab:red")):
            sub = t[t["side"] == side]
            axes[0].scatter(sub["entry_time"], sub["entry_price"], marker=marker, color=colour, s=30, label=f"{side} entry")
        axes[0].scatter(t["exit_time"], t["exit_price"], marker="x", color="grey", s=20, label="exit")
        axes[0].legend(loc="upper left", fontsize=8)
    axes[0].set_title(title or result.spec.name)
    eq = equity_curve(result.returns)
    axes[1].plot(eq.index, eq, color="tab:blue")
    axes[1].set_ylabel("equity")
    dd = drawdown_series(eq)
    axes[2].fill_between(dd.index, dd.to_numpy(), 0, color="tab:red", alpha=0.4)
    axes[2].set_ylabel("drawdown")
    return fig


__all__ = ["backtest_stats", "compare", "monthly_returns_table", "np", "plot_backtest", "trade_stats"]
