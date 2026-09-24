"""Performance analysis: tearsheet, drawdown periods, rolling metrics, calendar tables (M11).

Everything takes periodic simple returns (daily by default). Drawdowns are
measured from the starting capital as well as later peaks, so a strategy that
loses from day one shows that loss (``metrics.drawdown_series`` on an equity
curve starts from the first close instead).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as sps

from .metrics import (
    MONTHS,
    TRADING_DAYS,
    annualized_volatility,
    cagr,
    sharpe_ratio,
    sortino_ratio,
)
from .relative import capm


def underwater(returns: pd.Series) -> pd.Series:
    """Drawdown at each date as a negative fraction of the running peak, starting capital included."""
    wealth = (1.0 + returns.fillna(0.0)).cumprod()
    peak = wealth.cummax().clip(lower=1.0)
    return wealth / peak - 1.0


def drawdown_periods(returns: pd.Series, top: int = 5) -> pd.DataFrame:
    """The ``top`` deepest drawdowns: peak, trough, recovery, depth and durations in bars.

    ``peak`` is the last date at the high-water mark (the first date when the
    loss starts on day one). ``recovery`` and ``recovery_bars`` are missing
    while a drawdown is still open.
    """
    dd = underwater(returns)
    values, dates, n = dd.to_numpy(), dd.index, len(dd)
    rows, i = [], 0
    while i < n:
        if values[i] >= 0:
            i += 1
            continue
        start = i
        while i < n and values[i] < 0:
            i += 1
        trough = start + int(np.argmin(values[start:i]))
        peak = max(start - 1, 0)
        recovered = i < n
        rows.append({
            "peak": dates[peak],
            "trough": dates[trough],
            "recovery": dates[i] if recovered else pd.NaT,
            "depth": float(values[trough]),
            "bars_to_trough": trough - peak,
            "recovery_bars": i - trough if recovered else np.nan,
            "total_bars": (i if recovered else n - 1) - peak,
        })
    table = pd.DataFrame(rows, columns=["peak", "trough", "recovery", "depth", "bars_to_trough",
                                        "recovery_bars", "total_bars"])
    return table.sort_values("depth", kind="stable").head(top).reset_index(drop=True)


def ulcer_index(returns: pd.Series) -> float:
    """Root-mean-square drawdown in percent: punishes deep and long drawdowns."""
    return float(np.sqrt((100 * underwater(returns)).pow(2).mean()))


def omega_ratio(returns: pd.Series, threshold: float = 0.0) -> float:
    """Sum of gains above ``threshold`` over the sum of losses below it (uses the whole distribution)."""
    excess = returns.dropna() - threshold
    losses = -excess[excess < 0].sum()
    return float(excess[excess > 0].sum() / losses) if losses > 0 else float("inf")


def tail_ratio(returns: pd.Series, q: float = 0.95) -> float:
    """|q-quantile| / |(1 − q)-quantile|: above 1 means the right tail is fatter than the left."""
    r = returns.dropna()
    left = abs(float(r.quantile(1 - q)))
    return abs(float(r.quantile(q))) / left if left > 0 else float("inf")


def gain_to_pain(returns: pd.Series) -> float:
    """Sum of returns over the absolute sum of negative returns (Schwager; usually on monthly returns)."""
    r = returns.dropna()
    pain = -r[r < 0].sum()
    return float(r.sum() / pain) if pain > 0 else float("inf")


def monthly_returns(returns: pd.Series) -> pd.DataFrame:
    """Compounded return (%) per calendar month, years as rows, plus the year's total."""
    returns = returns.dropna()
    monthly = (1 + returns).groupby([returns.index.year, returns.index.month]).prod() - 1
    table = monthly.unstack() * 100
    table.columns = [MONTHS[m - 1] for m in table.columns]
    table.index.name = "year"
    table["Year"] = annual_returns(returns).reindex(table.index).to_numpy() * 100
    return table


def annual_returns(returns: pd.Series) -> pd.Series:
    """Compounded return per calendar year (fraction)."""
    returns = returns.dropna()
    return (1 + returns).groupby(returns.index.year).prod() - 1


def _absolute(returns: pd.Series, rf: float, periods: int) -> dict[str, float]:
    r = returns.dropna()
    dd = underwater(r)
    episodes = drawdown_periods(r, top=len(r))
    monthly = (1 + r).resample("ME").prod() - 1 if isinstance(r.index, pd.DatetimeIndex) else pd.Series(dtype=float)
    var95 = -float(r.quantile(0.05))
    return {
        "total_return": float((1 + r).prod() - 1),
        "cagr": cagr(r, periods),
        "volatility": annualized_volatility(r, periods),
        "sharpe": sharpe_ratio(r, rf, periods),
        "sortino": sortino_ratio(r, rf, periods),
        "max_drawdown": float(dd.min()),
        "calmar": cagr(r, periods) / -float(dd.min()) if dd.min() < 0 else float("inf"),
        "longest_drawdown_bars": float(episodes["total_bars"].max()) if len(episodes) else 0.0,
        "ulcer_index": ulcer_index(r),
        "skew": float(sps.skew(r)),
        "excess_kurtosis": float(sps.kurtosis(r)),
        "var_95": var95,
        "cvar_95": -float(r[r <= -var95].mean()),
        "best_period": float(r.max()),
        "worst_period": float(r.min()),
        "positive_periods": float((r > 0).mean()),
        "positive_months": float((monthly > 0).mean()) if len(monthly) else float("nan"),
        "tail_ratio": tail_ratio(r),
        "omega": omega_ratio(r),
        "gain_to_pain": gain_to_pain(monthly) if len(monthly) else float("nan"),
    }


def tearsheet(returns: pd.Series, benchmark: pd.Series | None = None, rf: float = 0.0,
              periods: int = TRADING_DAYS) -> pd.DataFrame:
    """Full performance report: returns, risk, drawdown, distribution and, with a benchmark, CAPM statistics.

    One column for the strategy (and one for the benchmark when given); the
    relative rows (alpha, beta, information ratio, capture) appear in the
    strategy column only. VaR and CVaR are historical, one period, as positive
    loss fractions. ``gain_to_pain`` uses monthly returns.
    """
    if benchmark is None:
        return pd.DataFrame({"strategy": _absolute(returns, rf, periods)})
    common = returns.dropna().index.intersection(benchmark.dropna().index)
    r, b = returns.loc[common], benchmark.loc[common]
    table = pd.DataFrame({"strategy": _absolute(r, rf, periods), "benchmark": _absolute(b, rf, periods)})
    return pd.concat([table, pd.DataFrame({"strategy": capm(r, b, rf, periods)})])


def rolling_metrics(returns: pd.Series, window: int = 63, benchmark: pd.Series | None = None,
                    periods: int = TRADING_DAYS) -> pd.DataFrame:
    """Annualised return, volatility, Sharpe, Sortino and worst drawdown over a moving window.

    With a benchmark, adds rolling beta and correlation. Overlapping windows are
    strongly autocorrelated: read the lines as a description, not as independent evidence.
    """
    r = returns.astype(float)
    mean, std = r.rolling(window).mean(), r.rolling(window).std()
    downside = np.sqrt((r.clip(upper=0) ** 2).rolling(window).mean())
    log_wealth = np.log1p(r).cumsum()

    def worst_drawdown(x: np.ndarray) -> float:
        wealth = np.exp(np.concatenate([[0.0], np.cumsum(np.log1p(x))]))
        return float((wealth / np.maximum.accumulate(wealth) - 1.0).min())

    out = pd.DataFrame({
        "return": np.expm1((log_wealth - log_wealth.shift(window)) * periods / window),
        "volatility": std * np.sqrt(periods),
        "sharpe": mean / std * np.sqrt(periods),
        "sortino": mean / downside * np.sqrt(periods),
        "max_drawdown": r.rolling(window).apply(worst_drawdown, raw=True),
    })
    if benchmark is not None:
        b = benchmark.reindex(r.index)
        out["beta"] = r.rolling(window).cov(b) / b.rolling(window).var()
        out["correlation"] = r.rolling(window).corr(b)
    return out
