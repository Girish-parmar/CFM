"""Portfolio construction (Module 9): mean–variance, risk parity and
Hierarchical Risk Parity. Inputs are annualised ``mu`` (expected returns) and
``cov`` (covariance) as numpy arrays or pandas objects.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.optimize import minimize
from scipy.spatial.distance import squareform


def _as_array(x) -> np.ndarray:
    return x.to_numpy(dtype=float) if isinstance(x, (pd.Series, pd.DataFrame)) else np.asarray(x, dtype=float)


def _labels(obj, n: int) -> list:
    if isinstance(obj, pd.DataFrame):
        return list(obj.columns)
    if isinstance(obj, pd.Series):
        return list(obj.index)
    return list(range(n))


def portfolio_stats(weights, mu, cov, rf: float = 0.0) -> dict[str, float]:
    w, m, c = _as_array(weights), _as_array(mu), _as_array(cov)
    ret = float(w @ m)
    vol = float(np.sqrt(w @ c @ w))
    return {"return": ret, "volatility": vol, "sharpe": (ret - rf) / vol if vol > 0 else 0.0}


def risk_contributions(weights, cov) -> np.ndarray:
    """Share of total variance contributed by each asset (sums to 1)."""
    w, c = _as_array(weights), _as_array(cov)
    marginal = c @ w
    return w * marginal / (w @ marginal)


def _solve(objective, n: int, long_only: bool, extra_constraints=()) -> np.ndarray:
    bounds = [(0.0, 1.0)] * n if long_only else [(-1.0, 1.0)] * n
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}, *extra_constraints]
    res = minimize(objective, np.full(n, 1.0 / n), method="SLSQP", bounds=bounds, constraints=cons,
                   options={"maxiter": 500, "ftol": 1e-12})
    if not res.success:
        raise RuntimeError(f"optimiser failed: {res.message}")
    return res.x


def min_variance_weights(cov, long_only: bool = True) -> pd.Series:
    c = _as_array(cov)
    n = len(c)
    if long_only:
        w = _solve(lambda w: w @ c @ w, n, True)
    else:
        inv = np.linalg.solve(c, np.ones(n))
        w = inv / inv.sum()
    return pd.Series(w, index=_labels(cov, n))


def max_sharpe_weights(mu, cov, rf: float = 0.0, long_only: bool = True) -> pd.Series:
    m, c = _as_array(mu), _as_array(cov)
    n = len(m)
    w = _solve(lambda w: -(w @ m - rf) / np.sqrt(w @ c @ w), n, long_only)
    return pd.Series(w, index=_labels(cov, n))


def risk_parity_weights(cov) -> pd.Series:
    """Equal risk contribution via the convex log-barrier formulation."""
    c = _as_array(cov)
    n = len(c)
    res = minimize(lambda y: 0.5 * y @ c @ y - np.log(y).sum() / n, np.full(n, 1.0 / n),
                   method="L-BFGS-B", bounds=[(1e-9, None)] * n)
    w = res.x / res.x.sum()
    return pd.Series(w, index=_labels(cov, n))


def efficient_frontier(mu, cov, n_points: int = 30, long_only: bool = True) -> pd.DataFrame:
    m, c = _as_array(mu), _as_array(cov)
    n = len(m)
    targets = np.linspace(m.min(), m.max(), n_points)
    rows = []
    for target in targets:
        cons = ({"type": "eq", "fun": lambda w, t=target: w @ m - t},)
        try:
            w = _solve(lambda w: w @ c @ w, n, long_only, cons)
        except RuntimeError:
            continue
        rows.append({"target": target, **portfolio_stats(w, m, c)})
    return pd.DataFrame(rows)


def hrp_weights(returns: pd.DataFrame) -> pd.Series:
    """Hierarchical Risk Parity (López de Prado, 2016).

    1. Cluster assets on correlation distance.
    2. Re-order the covariance matrix so similar assets sit together.
    3. Split capital top-down between clusters in inverse proportion to risk.
    No matrix inversion, so it stays stable when assets are highly correlated.
    """
    cov = returns.cov().to_numpy()
    corr = returns.corr().to_numpy()
    dist = np.sqrt(np.clip(0.5 * (1.0 - corr), 0.0, None))
    np.fill_diagonal(dist, 0.0)
    order = list(leaves_list(linkage(squareform(dist, checks=False), method="single")))

    def cluster_var(idx: list[int]) -> float:
        sub = cov[np.ix_(idx, idx)]
        ivp = 1.0 / np.diag(sub)
        ivp /= ivp.sum()
        return float(ivp @ sub @ ivp)

    weights = np.ones(len(order))
    clusters = [order]
    while clusters:
        nxt = []
        for cluster in clusters:
            if len(cluster) < 2:
                continue
            half = len(cluster) // 2
            left, right = cluster[:half], cluster[half:]
            v_left, v_right = cluster_var(left), cluster_var(right)
            alpha = 1.0 - v_left / (v_left + v_right)
            weights[left] *= alpha
            weights[right] *= 1.0 - alpha
            nxt += [left, right]
        clusters = nxt
    return pd.Series(weights, index=returns.columns)
