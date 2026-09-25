"""Interest rates: bond maths and the Nelson-Siegel yield curve (M02, M09).

    bond_price           price of a fixed-coupon bond from its yield to maturity
    bond_risk            price, Macaulay and modified duration, convexity and DV01
    nelson_siegel        yields from level, slope and curvature factors and the decay tau
    nelson_siegel_fit    fit one curve; tau estimated (grid, then refined) or fixed
    nelson_siegel_tau    the single tau that fits a whole panel of curves best
    nelson_siegel_panel  one fit per date; with a fixed tau each date is a single
                         least-squares solve (Diebold and Li, 2006)
    inversion_episodes   runs where a spread (for example 10y - 3m) stays below zero

Yields and spreads are in percent (7.25 means 7.25%), maturities in years.

Nelson-Siegel: y(m) = b0 + b1 (1 - e^-x)/x + b2 ((1 - e^-x)/x - e^-x), x = m / tau.
b0 is the long end (level), b0 + b1 the short end, so b1 = short - long (negative for an
upward-sloping curve), and b2 the hump in the middle (curvature), largest near m = 1.8 tau.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def bond_price(ytm: float, coupon: float, maturity: float, freq: int = 2, face: float = 100.0) -> float:
    """Price of a bond paying ``coupon`` (% a year) ``freq`` times a year, at yield ``ytm`` (%).

    G-secs pay semi-annually (``freq=2``). The next coupon is one full period away
    (no accrued interest): a clean price on a coupon date.
    """
    periods = max(round(maturity * freq), 1)
    y, c = ytm / 100 / freq, coupon / 100 / freq * face
    t = np.arange(1, periods + 1)
    return float(np.sum(c / (1 + y) ** t) + face / (1 + y) ** periods)


def bond_risk(ytm: float, coupon: float, maturity: float, freq: int = 2, face: float = 100.0) -> dict:
    """Price and interest-rate risk of a fixed-coupon bond.

    ``modified`` duration and ``convexity`` are per unit of yield (so a 0.5% rise changes the
    price by about -modified x 0.005 + 0.5 x convexity x 0.005^2, as a fraction); ``dv01`` is the
    price change for a one-basis-point fall in yield, per ``face``.
    """
    periods = max(round(maturity * freq), 1)
    y, c = ytm / 100 / freq, coupon / 100 / freq * face
    t = np.arange(1, periods + 1)
    cash = np.full(periods, c)
    cash[-1] += face
    pv = cash / (1 + y) ** t
    price = pv.sum()
    macaulay = float((t * pv).sum() / price / freq)
    modified = macaulay / (1 + y)
    convexity = float((pv * t * (t + 1)).sum() / price / (1 + y) ** 2 / freq**2)
    return {"price": float(price), "macaulay": macaulay, "modified": float(modified), "convexity": convexity,
            "dv01": float(modified * price * 1e-4)}


def _loadings(maturities, tau: float) -> np.ndarray:
    m = np.asarray(maturities, dtype=float)
    x = np.maximum(m, 1e-9) / tau
    slope = (1 - np.exp(-x)) / x
    return np.column_stack([np.ones_like(m), slope, slope - np.exp(-x)])


def nelson_siegel(maturities, beta0: float, beta1: float, beta2: float, tau: float) -> np.ndarray:
    """Yields (%) at ``maturities`` (years) for the given factors."""
    return _loadings(maturities, tau) @ np.array([beta0, beta1, beta2], dtype=float)


@dataclass(frozen=True)
class NelsonSiegel:
    """A fitted curve: level ``beta0``, ``beta1`` = short - long, curvature ``beta2``, decay
    ``tau`` (years) and the root-mean-square fitting error ``rmse`` (percentage points)."""

    beta0: float
    beta1: float
    beta2: float
    tau: float
    rmse: float

    def yields(self, maturities) -> np.ndarray:
        """Fitted yields (%) at ``maturities`` (years)."""
        return nelson_siegel(maturities, self.beta0, self.beta1, self.beta2, self.tau)

    @property
    def short_rate(self) -> float:
        """The curve's limit at zero maturity, ``beta0 + beta1``."""
        return self.beta0 + self.beta1


def _tau_grid(bounds: tuple[float, float]) -> np.ndarray:
    return np.geomspace(bounds[0], bounds[1], 121)


def _solve(maturities, yields, tau: float) -> tuple[np.ndarray, float]:
    X = _loadings(maturities, tau)
    beta, *_ = np.linalg.lstsq(X, yields, rcond=None)
    return beta, float(np.sum((yields - X @ beta) ** 2))


def nelson_siegel_fit(
    maturities, yields, tau: float | None = None, tau_bounds: tuple[float, float] = (0.1, 10.0),
) -> NelsonSiegel:
    """Least-squares Nelson-Siegel fit to one curve.

    For a given ``tau`` the model is linear in the betas, so the fit is ordinary least squares.
    With ``tau=None`` it is chosen by a grid search inside ``tau_bounds`` and refined with a
    bounded one-dimensional search. Needs at least four maturities.
    """
    from scipy.optimize import minimize_scalar

    m = np.asarray(maturities, dtype=float)
    y = np.asarray(yields, dtype=float)
    keep = ~np.isnan(y)
    m, y = m[keep], y[keep]
    if len(m) < 4:
        raise ValueError("need at least four maturities with yields")
    if tau is None:
        grid = _tau_grid(tau_bounds)
        sse = np.array([_solve(m, y, t)[1] for t in grid])
        i = int(np.argmin(sse))
        lo, hi = np.log(grid[max(i - 1, 0)]), np.log(grid[min(i + 1, len(grid) - 1)])
        best = minimize_scalar(lambda z: _solve(m, y, float(np.exp(z)))[1], bounds=(lo, hi), method="bounded",
                               options={"xatol": 1e-6})
        tau = float(np.exp(best.x)) if best.fun <= sse[i] else float(grid[i])
    beta, sse = _solve(m, y, tau)
    return NelsonSiegel(float(beta[0]), float(beta[1]), float(beta[2]), float(tau), float(np.sqrt(sse / len(m))))


def nelson_siegel_tau(curves: pd.DataFrame, tau_bounds: tuple[float, float] = (0.1, 10.0)) -> float:
    """The ``tau`` minimising the pooled squared error of fixed-tau fits to every row of ``curves``.

    More stable than the median of per-date free fits, whose taus are noisy and trade off
    against the betas. Rows with missing yields are ignored.
    """
    from scipy.optimize import minimize_scalar

    maturities = np.asarray(curves.columns, dtype=float)
    Y = curves.dropna().to_numpy(dtype=float).T

    def sse(tau: float) -> float:
        X = _loadings(maturities, tau)
        beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
        return float(np.sum((Y - X @ beta) ** 2))

    grid = _tau_grid(tau_bounds)
    errors = np.array([sse(t) for t in grid])
    i = int(np.argmin(errors))
    lo, hi = np.log(grid[max(i - 1, 0)]), np.log(grid[min(i + 1, len(grid) - 1)])
    best = minimize_scalar(lambda z: sse(float(np.exp(z))), bounds=(lo, hi), method="bounded", options={"xatol": 1e-6})
    return float(np.exp(best.x)) if best.fun <= errors[i] else float(grid[i])


def nelson_siegel_panel(curves: pd.DataFrame, tau: float | None = None) -> pd.DataFrame:
    """Fit every row of ``curves`` (index = dates, columns = maturities in years).

    Returns ``beta0``, ``beta1``, ``beta2``, ``tau`` and ``rmse`` per date. With a fixed
    ``tau`` (Diebold-Li) the factors are comparable from day to day and the whole panel is
    one least-squares solve; with ``tau=None`` each date is fitted on its own and the
    factors are noisier, because tau and the betas trade off against each other.
    """
    maturities = np.asarray(curves.columns, dtype=float)
    if tau is None:
        fits = [nelson_siegel_fit(maturities, row) for row in curves.to_numpy()]
        return pd.DataFrame([f.__dict__ for f in fits], index=curves.index)
    if curves.isna().any().any():
        rows = [nelson_siegel_fit(maturities, row, tau=tau).__dict__ for row in curves.to_numpy()]
        return pd.DataFrame(rows, index=curves.index)
    X = _loadings(maturities, tau)
    Y = curves.to_numpy(dtype=float).T
    beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
    rmse = np.sqrt(np.mean((Y - X @ beta) ** 2, axis=0))
    return pd.DataFrame({"beta0": beta[0], "beta1": beta[1], "beta2": beta[2], "tau": float(tau), "rmse": rmse},
                        index=curves.index)


def inversion_episodes(spread: pd.Series, min_days: int = 5, merge_gap: int = 5) -> pd.DataFrame:
    """Runs where ``spread`` is below zero: ``start``, ``end``, ``days`` and the ``deepest`` value.

    Runs separated by at most ``merge_gap`` observations are merged (noise makes a spread
    near zero flicker), then runs shorter than ``min_days`` observations are dropped.
    """
    s = spread.dropna()
    below = (s < 0).to_numpy()
    runs, start = [], None
    for i, flag in enumerate(below):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            runs.append([start, i - 1])
            start = None
    if start is not None:
        runs.append([start, len(below) - 1])
    merged: list[list[int]] = []
    for run in runs:
        if merged and run[0] - merged[-1][1] - 1 <= merge_gap:
            merged[-1][1] = run[1]
        else:
            merged.append(run)
    rows = [{"start": s.index[a], "end": s.index[b], "days": b - a + 1, "deepest": float(s.iloc[a:b + 1].min())}
            for a, b in merged if b - a + 1 >= min_days]
    return pd.DataFrame(rows, columns=["start", "end", "days", "deepest"])
