"""Risk measurement and position sizing (M13).

VaR and expected shortfall are returned as positive loss fractions: 0.021
means "a 2.1% loss". Multiply by portfolio value for rupees.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm


def historical_var(returns: pd.Series, alpha: float = 0.99) -> float:
    """Historical VaR at ``alpha`` as a positive loss fraction."""
    return float(-np.quantile(returns.dropna(), 1 - alpha))


def parametric_var(returns: pd.Series, alpha: float = 0.99) -> float:
    """Gaussian (variance–covariance) VaR. Understates risk when tails are fat."""
    r = returns.dropna()
    return float(-(r.mean() + norm.ppf(1 - alpha) * r.std(ddof=1)))


def monte_carlo_var(returns: pd.Series, alpha: float = 0.99, n_sims: int = 100_000, seed: int | None = None) -> float:
    """Bootstrap VaR: resample historical returns with replacement."""
    rng = np.random.default_rng(seed)
    sims = rng.choice(returns.dropna().to_numpy(), size=n_sims, replace=True)
    return float(-np.quantile(sims, 1 - alpha))


def expected_shortfall(returns: pd.Series, alpha: float = 0.975) -> float:
    """Average loss on the days worse than VaR (a.k.a. CVaR)."""
    r = returns.dropna()
    cutoff = np.quantile(r, 1 - alpha)
    return float(-r[r <= cutoff].mean())


def scale_var(one_day_var: float, horizon_days: int) -> float:
    """Square-root-of-time rule (assumes i.i.d. returns)."""
    return float(one_day_var * np.sqrt(horizon_days))


def kupiec_test(breaches: pd.Series, alpha: float = 0.99) -> dict[str, float]:
    """Kupiec proportion-of-failures test of a VaR model.

    ``breaches`` is a boolean Series (loss worse than VaR). Under a correct
    ``alpha`` VaR the breach rate is ``1 - alpha``; the likelihood-ratio statistic
    is chi-squared with one degree of freedom.
    """
    from scipy.stats import chi2

    b = breaches.dropna().astype(bool)
    n, x = len(b), int(b.sum())
    p = 1.0 - alpha
    phat = x / n if n else 0.0

    def loglik(q: float) -> float:
        q = min(max(q, 1e-12), 1 - 1e-12)
        return (n - x) * np.log(1 - q) + x * np.log(q)

    lr = -2.0 * (loglik(p) - loglik(phat))
    return {"days": n, "breaches": x, "expected": n * p, "breach_rate": phat, "lr_stat": float(lr),
            "p_value": float(chi2.sf(lr, 1))}


def fixed_fractional_qty(capital: float, risk_fraction: float, entry: float, stop: float, lot_size: int = 1) -> int:
    """Shares (rounded down to whole lots) so that hitting ``stop`` loses
    ``risk_fraction`` of ``capital``."""
    per_share_risk = abs(entry - stop)
    if per_share_risk == 0:
        raise ValueError("entry and stop must differ")
    raw = capital * risk_fraction / per_share_risk
    return int(raw // lot_size * lot_size)


def atr_stop_qty(capital: float, risk_fraction: float, atr_value: float, atr_multiple: float = 2.0, lot_size: int = 1) -> int:
    """Volatility-based sizing: stop placed ``atr_multiple`` ATRs away."""
    per_share_risk = atr_value * atr_multiple
    return int(capital * risk_fraction / per_share_risk // lot_size * lot_size)


def kelly_fraction(returns: pd.Series) -> float:
    """Continuous-time Kelly leverage mu / sigma² (per-period moments).

    Full Kelly is far too aggressive once estimation error is considered;
    practitioners use a quarter to a half of it.
    """
    r = returns.dropna()
    var = r.var(ddof=1)
    return float(r.mean() / var) if var > 0 else 0.0


def volatility_target_leverage(
    returns: pd.Series, target_vol: float = 0.10, lookback: int = 20, max_leverage: float = 2.0, periods: int = 252
) -> pd.Series:
    """Leverage that scales exposure to hit ``target_vol``, using only past data."""
    realised = returns.rolling(lookback).std().shift(1) * np.sqrt(periods)
    return (target_vol / realised).clip(upper=max_leverage).fillna(0.0)


def portfolio_var(weights: np.ndarray, cov: np.ndarray, alpha: float = 0.99, value: float = 1.0) -> float:
    """Parametric VaR of a portfolio from a covariance matrix of returns."""
    sigma = float(np.sqrt(weights @ cov @ weights))
    return float(norm.ppf(alpha) * sigma * value)


def stress_test(positions: dict[str, float], shocks: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Rupee P&L of ``positions`` (symbol → exposure) under named scenarios
    (scenario → {symbol: return})."""
    rows = {
        name: {sym: exposure * shock.get(sym, 0.0) for sym, exposure in positions.items()}
        for name, shock in shocks.items()
    }
    table = pd.DataFrame(rows).T
    table["total"] = table.sum(axis=1)
    return table
