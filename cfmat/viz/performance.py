"""Performance charts: equity and drawdown, monthly heatmap, rolling metrics, return distribution, trades.

Every function takes periodic simple returns (or a round-trip table) and
returns a matplotlib figure; save it with ``cfmat.viz.savefig``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm
from scipy import stats as sps

from ..analytics.performance import drawdown_periods, monthly_returns, rolling_metrics, underwater
from ._common import ACCENT, DOWN, NEUTRAL, UP, figure


def equity_chart(returns: pd.Series, benchmark: pd.Series | None = None, log_scale: bool = False,
                 title: str = "Growth of 1 and drawdown"):
    """Growth of 1 (with an optional benchmark) above the underwater curve; the deepest drawdown is shaded."""
    fig, (ax, ax_dd) = figure(2, 1, figsize=(11, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1.2]})
    r = returns.dropna()
    wealth = (1 + r).cumprod()
    ax.plot(wealth.index, wealth, color=ACCENT[0], lw=1.3, label="strategy")
    if benchmark is not None:
        b = benchmark.reindex(r.index).fillna(0.0)
        ax.plot(b.index, (1 + b).cumprod(), color=NEUTRAL, lw=1.0, alpha=0.8, label="benchmark")
    worst = drawdown_periods(r, top=1)
    if len(worst):
        end = worst.loc[0, "recovery"] if pd.notna(worst.loc[0, "recovery"]) else r.index[-1]
        ax.axvspan(worst.loc[0, "peak"], end, color=DOWN, alpha=0.08, label=f"worst drawdown {worst.loc[0, 'depth']:.1%}")
    if log_scale:
        ax.set_yscale("log")
    ax.set_title(title)
    ax.legend(loc="upper left", fontsize=8)
    dd = underwater(r)
    ax_dd.fill_between(dd.index, 100 * dd.to_numpy(), 0, color=DOWN, alpha=0.4)
    ax_dd.set_ylabel("drawdown %")
    return fig


def monthly_heatmap(returns: pd.Series, title: str = "Monthly returns (%)"):
    """Calendar heatmap of compounded monthly returns with the yearly total in the last column."""
    table = monthly_returns(returns)
    values = table.to_numpy(dtype=float)
    fig, ax = figure(figsize=(11, 0.55 * len(table) + 1.8))
    ax.grid(False)
    finite = np.abs(values[np.isfinite(values)])
    limit = float(finite.max()) if finite.size else 1.0
    image = ax.imshow(values, cmap="RdYlGn", aspect="auto",
                      norm=TwoSlopeNorm(vcenter=0.0, vmin=-limit - 1e-9, vmax=limit + 1e-9))
    for (i, j), v in np.ndenumerate(values):
        if np.isfinite(v):
            ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=8,
                    fontweight="bold" if j == values.shape[1] - 1 else "normal")
    ax.set_xticks(range(len(table.columns)), table.columns, fontsize=8)
    ax.set_yticks(range(len(table)), table.index, fontsize=8)
    ax.axvline(values.shape[1] - 1.5, color="white", lw=2)
    ax.set_title(title)
    fig.colorbar(image, ax=ax, fraction=0.025, pad=0.01)
    return fig


def rolling_chart(returns: pd.Series, window: int = 63, benchmark: pd.Series | None = None,
                  title: str | None = None):
    """Rolling Sharpe, volatility and worst drawdown (and beta with a benchmark) over ``window`` bars."""
    roll = rolling_metrics(returns, window, benchmark)
    rows = ["sharpe", "volatility", "max_drawdown"] + (["beta"] if benchmark is not None else [])
    fig, axes = figure(len(rows), 1, figsize=(11, 2.2 * len(rows) + 0.6), sharex=True)
    for ax, col, colour in zip(np.atleast_1d(axes), rows, ACCENT, strict=False):
        ax.plot(roll.index, roll[col], color=colour, lw=1.1)
        ax.set_ylabel(col.replace("_", " "), fontsize=9)
        if col in ("sharpe", "beta"):
            ax.axhline(0 if col == "sharpe" else 1, color=NEUTRAL, lw=0.8, ls="--")
    np.atleast_1d(axes)[0].set_title(title or f"Rolling {window}-bar metrics")
    return fig


def distribution_chart(returns: pd.Series, bins: int = 60, title: str = "Return distribution"):
    """Histogram against a fitted normal (with 95% VaR and CVaR marked) and a normal Q-Q plot."""
    r = returns.dropna().to_numpy(dtype=float)
    fig, (ax, ax_qq) = figure(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.6, 1]})
    ax.hist(r, bins=bins, density=True, color=ACCENT[0], alpha=0.55, label="returns")
    grid = np.linspace(r.min(), r.max(), 300)
    ax.plot(grid, sps.norm.pdf(grid, r.mean(), r.std(ddof=1)), color=NEUTRAL, lw=1.2, label="normal fit")
    var = np.quantile(r, 0.05)
    cvar = r[r <= var].mean()
    ax.axvline(var, color=ACCENT[1], ls="--", lw=1.1, label=f"VaR 95% {-var:.2%}")
    ax.axvline(cvar, color=DOWN, ls="--", lw=1.1, label=f"CVaR 95% {-cvar:.2%}")
    ax.set_title(f"{title} (skew {sps.skew(r):.2f}, excess kurtosis {sps.kurtosis(r):.1f})")
    ax.legend(fontsize=8)
    (osm, osr), (slope, intercept, _) = sps.probplot(r, dist="norm")
    ax_qq.scatter(osm, osr, s=6, color=ACCENT[0], alpha=0.6)
    ax_qq.plot(osm, slope * osm + intercept, color=NEUTRAL, lw=1.0)
    ax_qq.set_xlabel("normal quantiles")
    ax_qq.set_ylabel("return quantiles")
    ax_qq.set_title("Q-Q: fat tails bend away from the line")
    return fig


def trade_chart(trips: pd.DataFrame, title: str = "Trade review"):
    """Four panels from a round-trip table: P&L per trade, cumulative P&L, R-multiples, MAE vs MFE.

    Without R-multiples the third panel shows net P&L; without MAE/MFE the
    fourth shows holding time against P&L.
    """
    t = trips[trips["status"] == "CLOSED"] if "status" in trips else trips
    fig, axes = figure(2, 2, figsize=(11, 7))
    (ax_bar, ax_cum), (ax_r, ax_ex) = axes
    pnl = t["net_pnl"].to_numpy(dtype=float)
    colours = np.where(pnl > 0, UP, DOWN)
    ax_bar.bar(np.arange(len(pnl)), pnl, color=colours)
    ax_bar.axhline(0, color=NEUTRAL, lw=0.8)
    ax_bar.set_title("net P&L per trade")
    ax_cum.plot(np.arange(len(pnl)), np.cumsum(pnl), color=ACCENT[0], lw=1.3)
    ax_cum.set_title("cumulative net P&L")
    r = t["r_multiple"].dropna() if "r_multiple" in t else pd.Series(dtype=float)
    series, label = (r, "R-multiple") if len(r) else (t["net_pnl"], "net P&L")
    ax_r.hist(series, bins=min(30, max(5, len(series) // 2)), color=ACCENT[2], alpha=0.7)
    ax_r.axvline(0, color=NEUTRAL, lw=0.8)
    ax_r.set_title(f"{label} distribution (mean {series.mean():.2f})" if len(series) else label)
    if "mae" in t and t["mae"].notna().any():
        ax_ex.scatter(-t["mae"], t["mfe"], c=colours, s=22)
        ax_ex.set_xlabel("adverse excursion (MAE, price)")
        ax_ex.set_ylabel("favourable excursion (MFE, price)")
        ax_ex.set_title("MAE vs MFE: winners (green), losers (red)")
    else:
        hours = t["holding"] / pd.Timedelta(hours=1)
        ax_ex.scatter(hours, pnl, c=colours, s=22)
        ax_ex.set_xlabel("holding (hours)")
        ax_ex.set_title("holding time vs net P&L")
    fig.suptitle(title)
    return fig
