"""Return and performance statistics.

All functions take periodic (usually daily) simple returns as a pandas Series
unless stated otherwise. ``periods`` is the number of periods per year.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

TRADING_DAYS = 252
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
EULER_GAMMA = 0.5772156649015329


def simple_returns(prices: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    return prices.pct_change().dropna(how="all")


def log_returns(prices: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    return np.log(prices / prices.shift(1)).dropna(how="all")


def equity_curve(returns: pd.Series, start_value: float = 1.0) -> pd.Series:
    return start_value * (1.0 + returns).cumprod()


def cagr(returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    """Compound annual growth rate."""
    returns = returns.dropna()
    if len(returns) == 0:
        return 0.0
    growth = float((1.0 + returns).prod())
    if growth <= 0:
        return -1.0
    return growth ** (periods / len(returns)) - 1.0


def annualized_volatility(returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    return float(returns.std(ddof=1) * np.sqrt(periods))


def sharpe_ratio(returns: pd.Series, rf: float = 0.0, periods: int = TRADING_DAYS) -> float:
    """Annualised Sharpe ratio. ``rf`` is an annual risk-free rate."""
    excess = returns - rf / periods
    sd = excess.std(ddof=1)
    if np.isnan(sd) or sd < 1e-12:
        return 0.0
    return float(excess.mean() / sd * np.sqrt(periods))


def sortino_ratio(returns: pd.Series, rf: float = 0.0, periods: int = TRADING_DAYS) -> float:
    """Like Sharpe, but only downside deviation counts as risk."""
    excess = returns - rf / periods
    downside = np.sqrt(np.mean(np.minimum(excess, 0.0) ** 2))
    if downside < 1e-12:
        return 0.0
    return float(excess.mean() / downside * np.sqrt(periods))


def drawdown_series(equity: pd.Series) -> pd.Series:
    """Fractional distance below the running peak (0 at new highs, negative otherwise)."""
    return equity / equity.cummax() - 1.0


def max_drawdown(equity: pd.Series) -> float:
    """Worst peak-to-trough loss as a negative fraction, e.g. -0.25 for 25%."""
    return float(drawdown_series(equity).min())


def calmar_ratio(returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    mdd = max_drawdown(equity_curve(returns))
    return 0.0 if mdd == 0 else float(cagr(returns, periods) / abs(mdd))


def hit_rate(returns: pd.Series) -> float:
    """Share of non-zero periods that were profitable."""
    active = returns[returns != 0]
    return float((active > 0).mean()) if len(active) else 0.0


def profit_factor(returns: pd.Series) -> float:
    gains = returns[returns > 0].sum()
    losses = -returns[returns < 0].sum()
    return float(gains / losses) if losses > 0 else float("inf")


def performance_summary(returns: pd.Series, rf: float = 0.0, periods: int = TRADING_DAYS) -> pd.Series:
    """One-line tear sheet used throughout the course."""
    returns = returns.dropna()
    eq = equity_curve(returns)
    return pd.Series(
        {
            "total_return": float(eq.iloc[-1] - 1.0) if len(eq) else 0.0,
            "cagr": cagr(returns, periods),
            "volatility": annualized_volatility(returns, periods),
            "sharpe": sharpe_ratio(returns, rf, periods),
            "sortino": sortino_ratio(returns, rf, periods),
            "max_drawdown": max_drawdown(eq) if len(eq) else 0.0,
            "calmar": calmar_ratio(returns, periods),
            "hit_rate": hit_rate(returns),
            "profit_factor": profit_factor(returns),
            "skew": float(stats.skew(returns)) if len(returns) > 2 else 0.0,
            "excess_kurtosis": float(stats.kurtosis(returns)) if len(returns) > 3 else 0.0,
        }
    )


def probabilistic_sharpe_ratio(returns: pd.Series, sr_benchmark: float = 0.0) -> float:
    """Probability that the true (per-period) Sharpe exceeds ``sr_benchmark``.

    Bailey & López de Prado (2012). Accounts for sample length, skew and fat
    tails. ``sr_benchmark`` is per period, not annualised.
    """
    r = returns.dropna().to_numpy()
    n = len(r)
    if n < 3 or r.std(ddof=1) == 0:
        return 0.0
    sr = r.mean() / r.std(ddof=1)
    g3 = stats.skew(r)
    g4 = stats.kurtosis(r, fisher=False)
    denom = np.sqrt(max(1e-12, 1 - g3 * sr + (g4 - 1) / 4 * sr**2))
    return float(stats.norm.cdf((sr - sr_benchmark) * np.sqrt(n - 1) / denom))


def expected_max_sharpe(n_trials: int, sr_variance: float) -> float:
    """Expected maximum per-period Sharpe among ``n_trials`` skill-less strategies."""
    if n_trials < 2:
        return 0.0
    z1 = stats.norm.ppf(1 - 1.0 / n_trials)
    z2 = stats.norm.ppf(1 - 1.0 / (n_trials * np.e))
    return float(np.sqrt(sr_variance) * ((1 - EULER_GAMMA) * z1 + EULER_GAMMA * z2))


def deflated_sharpe_ratio(returns: pd.Series, n_trials: int, sr_variance: float) -> float:
    """PSR against the Sharpe you would expect from the best of ``n_trials`` random tries.

    Bailey & López de Prado (2014). ``sr_variance`` is the variance of the
    per-period Sharpe ratios across all the trials you ran. Values near 1 mean
    the result is unlikely to be a multiple-testing artefact.
    """
    return probabilistic_sharpe_ratio(returns, expected_max_sharpe(n_trials, sr_variance))
