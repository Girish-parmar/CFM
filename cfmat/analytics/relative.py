"""Relative performance: beta, correlation, relative strength and rotation (M07, M11, M12).

    capm                  alpha, beta, R², tracking error, information ratio, up/down capture
    rolling_beta          beta to a benchmark over a moving window
    rolling_correlation   correlation with a benchmark over a moving window
    relative_strength     price ratio to a benchmark, rebased to 1
    mansfield_rs          relative strength versus its own moving average (0 = neutral)
    rs_rating             IBD-style 1–99 percentile of weighted 3/6/9/12-month performance
    relative_rotation     RS-ratio and RS-momentum for a relative rotation graph (RRG)
    rotation_quadrant     Leading / Weakening / Lagging / Improving
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics import TRADING_DAYS
from .stats import hac_tstat


def _aligned(returns: pd.Series, benchmark: pd.Series) -> pd.DataFrame:
    frame = pd.concat({"r": returns, "b": benchmark}, axis=1, join="inner").dropna()
    if len(frame) < 3:
        raise ValueError("need at least three overlapping observations")
    return frame


def capm(returns: pd.Series, benchmark: pd.Series, rf: float = 0.0, periods: int = TRADING_DAYS) -> dict[str, float]:
    """Regression of excess returns on benchmark excess returns, plus active-return statistics.

    ``alpha`` is annualised (periods × daily intercept) with a Newey–West
    t-statistic. Up/down capture compare mean returns on the benchmark's up and
    down days.
    """
    f = _aligned(returns, benchmark)
    r, b = f["r"] - rf / periods, f["b"] - rf / periods
    beta = float(np.cov(r, b, ddof=1)[0, 1] / np.var(b, ddof=1))
    resid = r - beta * b
    corr = float(np.corrcoef(r, b)[0, 1])
    active = f["r"] - f["b"]
    te = float(active.std(ddof=1) * np.sqrt(periods))
    up, down = f["b"] > 0, f["b"] < 0
    return {
        "alpha": float(resid.mean() * periods),
        "alpha_tstat": hac_tstat(resid),
        "beta": beta,
        "correlation": corr,
        "r_squared": corr**2,
        "tracking_error": te,
        "information_ratio": float(active.mean() * periods / te) if te > 0 else float("nan"),
        "up_capture": float(f.loc[up, "r"].mean() / f.loc[up, "b"].mean()) if up.any() else float("nan"),
        "down_capture": float(f.loc[down, "r"].mean() / f.loc[down, "b"].mean()) if down.any() else float("nan"),
    }


def rolling_beta(returns: pd.Series | pd.DataFrame, benchmark: pd.Series, window: int = 63) -> pd.Series | pd.DataFrame:
    """Beta to ``benchmark`` over a moving window (covariance / benchmark variance)."""
    var = benchmark.rolling(window).var()
    if isinstance(returns, pd.DataFrame):
        return returns.apply(lambda s: s.rolling(window).cov(benchmark) / var)
    return returns.rolling(window).cov(benchmark) / var


def rolling_correlation(returns: pd.Series | pd.DataFrame, benchmark: pd.Series,
                        window: int = 63) -> pd.Series | pd.DataFrame:
    """Correlation with ``benchmark`` over a moving window."""
    if isinstance(returns, pd.DataFrame):
        return returns.apply(lambda s: s.rolling(window).corr(benchmark))
    return returns.rolling(window).corr(benchmark)


def relative_strength(close: pd.Series | pd.DataFrame, benchmark_close: pd.Series) -> pd.Series | pd.DataFrame:
    """Price divided by the benchmark, rebased to 1 at the first date: rising = outperforming."""
    ratio = close.div(benchmark_close, axis=0)
    return ratio / ratio.bfill().iloc[0]


def mansfield_rs(close: pd.Series | pd.DataFrame, benchmark_close: pd.Series,
                 window: int = 200) -> pd.Series | pd.DataFrame:
    """Mansfield relative strength: 100 × (RS / moving average of RS − 1); above 0 = outperforming its norm."""
    rs = close.div(benchmark_close, axis=0)
    return 100.0 * (rs / rs.rolling(window).mean() - 1.0)


def rs_rating(
    close: pd.DataFrame,
    periods: tuple[int, ...] = (63, 126, 189, 252),
    weights: tuple[float, ...] = (0.4, 0.2, 0.2, 0.2),
) -> pd.DataFrame:
    """Relative-strength rating 1–99: percentile of weighted 3/6/9/12-month returns across the universe.

    The IBD convention weights the latest quarter double. The weakest asset
    rates 1 and the strongest 99; the rating is relative to whichever universe
    you pass in.
    """
    if len(periods) != len(weights):
        raise ValueError("periods and weights must have the same length")
    score = sum(w * (close / close.shift(p) - 1.0) for p, w in zip(periods, weights, strict=True))
    position = (score.rank(axis=1) - 1).div(score.notna().sum(axis=1) - 1, axis=0)   # 0 = weakest, 1 = strongest
    return (1 + (98 * position).round()).where(score.notna())


def relative_rotation(close: pd.DataFrame, benchmark_close: pd.Series, window: int = 63,
                      momentum_window: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    """RS-ratio and RS-momentum for a relative rotation graph; both centre on 100.

    RS-ratio = 100 × RS / its ``window``-day mean (trend of relative strength);
    RS-momentum = 100 × RS-ratio / RS-ratio ``momentum_window`` days ago (its
    rate of change). This is an open approximation of the JdK RRG, whose exact
    normalisation is proprietary.
    """
    rs = close.div(benchmark_close, axis=0)
    ratio = 100.0 * rs / rs.rolling(window).mean()
    momentum = 100.0 * ratio / ratio.shift(momentum_window)
    return ratio, momentum


def rotation_quadrant(ratio: pd.Series, momentum: pd.Series) -> pd.Series:
    """Quadrant of each asset: Leading (≥100, ≥100), Weakening, Lagging or Improving."""
    strong, rising = ratio >= 100, momentum >= 100
    labels = np.select([strong & rising, strong & ~rising, ~strong & ~rising], ["Leading", "Weakening", "Lagging"],
                       default="Improving")
    return pd.Series(labels, index=ratio.index).where(ratio.notna() & momentum.notna())
