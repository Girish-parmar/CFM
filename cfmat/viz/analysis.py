"""Analysis charts: correlation heatmap, volatility estimators and cone, rankings, rotation graph, frontier."""

from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform

from ..analytics.metrics import TRADING_DAYS
from ..analytics.volatility import compare_estimators
from ..portfolio.construction import efficient_frontier, max_sharpe_weights, min_variance_weights, portfolio_stats
from ._common import ACCENT, DOWN, NEUTRAL, UP, figure


def correlation_heatmap(returns: pd.DataFrame, method: str = "pearson", cluster: bool = True,
                        title: str | None = None):
    """Correlation matrix, ordered by hierarchical clustering so related assets sit together."""
    corr = returns.corr(method=method)
    if cluster and len(corr) > 2:
        distance = np.sqrt(np.clip(0.5 * (1 - corr.to_numpy()), 0, None))
        np.fill_diagonal(distance, 0.0)
        order = leaves_list(linkage(squareform(distance, checks=False), method="average"))
        corr = corr.iloc[order, order]
    n = len(corr)
    fig, ax = figure(figsize=(1.0 + 0.5 * n, 0.8 + 0.45 * n))
    ax.grid(False)
    image = ax.imshow(corr.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
    if n <= 20:
        for (i, j), v in np.ndenumerate(corr.to_numpy()):
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7)
    ax.set_xticks(range(n), corr.columns, rotation=90, fontsize=8)
    ax.set_yticks(range(n), corr.index, fontsize=8)
    ax.set_title(title or f"{method.title()} correlation{' (clustered)' if cluster else ''}")
    fig.colorbar(image, ax=ax, fraction=0.04, pad=0.02)
    return fig


def volatility_chart(ohlc: pd.DataFrame, window: int = 21, true_vol: pd.Series | None = None,
                     title: str | None = None):
    """Every volatility estimator over time, against the true volatility when it is known."""
    table = compare_estimators(ohlc, window)
    fig, ax = figure(figsize=(11, 4.5))
    for colour, col in zip(ACCENT, table.columns, strict=False):
        ax.plot(table.index, table[col], lw=1.0, color=colour, label=col.replace("_", "-"), alpha=0.85)
    if true_vol is not None:
        ax.plot(true_vol.index, true_vol, color="black", lw=1.6, ls="--", label="true")
    ax.set_ylabel("annualised volatility")
    ax.set_title(title or f"Volatility estimators, {window}-day window")
    ax.legend(fontsize=8, ncol=3)
    return fig


def cone_chart(cone: pd.DataFrame, title: str = "Volatility cone"):
    """Plot the output of ``analytics.volatility.volatility_cone``: quantile bands and today's value."""
    fig, ax = figure(figsize=(9, 4.5))
    x = cone.index.to_numpy()
    if {"min", "max"} <= set(cone.columns):
        ax.fill_between(x, cone["min"], cone["max"], color=ACCENT[0], alpha=0.12, label="min–max")
    if {"q25", "q75"} <= set(cone.columns):
        ax.fill_between(x, cone["q25"], cone["q75"], color=ACCENT[0], alpha=0.25, label="25–75%")
    if "median" in cone:
        ax.plot(x, cone["median"], color=ACCENT[0], lw=1.4, label="median")
    ax.plot(x, cone["current"], color=DOWN, marker="o", lw=1.2, label="current")
    ax.set_xlabel("window (trading days)")
    ax.set_ylabel("annualised volatility")
    ax.set_xticks(x)
    ax.set_title(title)
    ax.legend(fontsize=8)
    return fig


def ranking_chart(scores: pd.Series, top: int | None = None, title: str = "Ranking", fmt: str = "{:.2f}"):
    """Horizontal bars, best at the top, green above zero and red below."""
    s = scores.dropna().sort_values(ascending=False)
    if top:
        s = s.head(top)
    s = s.iloc[::-1]
    fig, ax = figure(figsize=(8, 0.35 * len(s) + 1.2))
    ax.barh(range(len(s)), s.to_numpy(), color=np.where(s.to_numpy() >= 0, UP, DOWN), alpha=0.8)
    ax.set_yticks(range(len(s)), s.index, fontsize=8)
    for i, v in enumerate(s.to_numpy()):
        ax.text(v, i, " " + fmt.format(v), va="center", ha="left" if v >= 0 else "right", fontsize=7)
    ax.axvline(0, color=NEUTRAL, lw=0.8)
    ax.set_title(title)
    return fig


def rotation_chart(ratio: pd.DataFrame, momentum: pd.DataFrame, tail: int = 10, step: int = 5,
                   title: str = "Relative rotation graph"):
    """RRG from ``analytics.relative.relative_rotation``: each asset's recent path through the quadrants.

    ``tail`` points spaced ``step`` bars apart end at the latest date (the big dot).
    """
    fig, ax = figure(figsize=(8, 8))
    points = [(ratio[c].iloc[-1 - step * tail::step], momentum[c].iloc[-1 - step * tail::step]) for c in ratio]
    xs = np.concatenate([p[0].dropna().to_numpy() for p in points] + [np.array([100.0])])
    ys = np.concatenate([p[1].dropna().to_numpy() for p in points] + [np.array([100.0])])
    span = max(np.abs(xs - 100).max(), np.abs(ys - 100).max()) * 1.15 + 0.5
    quadrants = (("Leading", 100, 100, UP), ("Weakening", 100, 100 - span, ACCENT[0]),
                 ("Lagging", 100 - span, 100 - span, DOWN), ("Improving", 100 - span, 100, "#f9a825"))
    for name, x0, y0, colour in quadrants:
        ax.add_patch(Rectangle((x0, y0), span, span, color=colour, alpha=0.07))
        right, top = x0 >= 100, y0 >= 100
        ax.text(100 + (0.95 if right else -0.95) * span, 100 + (0.93 if top else -0.93) * span, name,
                ha="right" if right else "left", va="top" if top else "bottom", fontsize=10, color=colour,
                fontweight="bold")
    for i, (c, (x, y)) in enumerate(zip(ratio.columns, points, strict=True)):
        colour = ACCENT[i % len(ACCENT)]
        ax.plot(x.to_numpy(), y.to_numpy(), color=colour, lw=1.0, marker="o", markersize=3, alpha=0.8)
        ax.scatter(x.iloc[-1], y.iloc[-1], color=colour, s=60, zorder=5)
        ax.annotate(c, (x.iloc[-1], y.iloc[-1]), textcoords="offset points", xytext=(5, 5), fontsize=8)
    ax.axhline(100, color=NEUTRAL, lw=0.8)
    ax.axvline(100, color=NEUTRAL, lw=0.8)
    ax.set_xlim(100 - span, 100 + span)
    ax.set_ylim(100 - span, 100 + span)
    ax.set_xlabel("RS-ratio (trend of relative strength)")
    ax.set_ylabel("RS-momentum (its rate of change)")
    ax.set_title(title)
    return fig


def frontier_chart(returns: pd.DataFrame, n_points: int = 30, periods: int = TRADING_DAYS, rf: float = 0.0,
                   title: str = "Efficient frontier (in-sample)"):
    """Long-only efficient frontier with the assets, the minimum-variance and the maximum-Sharpe portfolios.

    Uses sample means and covariances, so it shows the frontier of the past,
    not a forecast; small changes in the means move the maximum-Sharpe point a lot.
    """
    mu, cov = returns.mean() * periods, returns.cov() * periods
    frontier = efficient_frontier(mu, cov, n_points)
    fig, ax = figure(figsize=(9, 6))
    ax.plot(frontier["volatility"], frontier["return"], color=ACCENT[0], lw=1.6, label="efficient frontier")
    vols = np.sqrt(np.diag(cov))
    ax.scatter(vols, mu, color=NEUTRAL, s=25)
    for name, x, y in zip(returns.columns, vols, mu, strict=True):
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(4, 3), fontsize=7)
    for label, w, colour in (("min variance", min_variance_weights(cov), UP),
                             ("max Sharpe", max_sharpe_weights(mu, cov, rf), DOWN)):
        stats = portfolio_stats(w, mu, cov, rf)
        ax.scatter(stats["volatility"], stats["return"], color=colour, s=90, marker="*", zorder=5,
                   label=f"{label} (Sharpe {stats['sharpe']:.2f})")
    ax.set_xlabel("annualised volatility")
    ax.set_ylabel("annualised return")
    ax.set_title(title)
    ax.legend(fontsize=8)
    return fig
