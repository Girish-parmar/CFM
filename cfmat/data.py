"""Market data for the labs.

Synthetic generators let every lab run offline and reproducibly (fix ``seed``).
``download_prices`` fetches real data through yfinance when it is installed,
e.g. ``download_prices("RELIANCE.NS")`` or ``download_prices("^NSEI")``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TRADING_DAYS = 252
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def trading_days(n: int, start: str = "2022-01-03") -> pd.DatetimeIndex:
    """``n`` business days starting at ``start`` (exchange holidays ignored)."""
    return pd.bdate_range(start=start, periods=n, name="date")


def gbm_prices(
    n: int = 756,
    s0: float = 100.0,
    mu: float = 0.10,
    sigma: float = 0.20,
    seed: int | None = None,
    start: str = "2022-01-03",
) -> pd.Series:
    """Daily closes from geometric Brownian motion.

    ``mu`` and ``sigma`` are annualised drift and volatility.
    """
    rng = np.random.default_rng(seed)
    dt = 1.0 / TRADING_DAYS
    shocks = rng.normal((mu - 0.5 * sigma**2) * dt, sigma * np.sqrt(dt), size=n - 1)
    path = s0 * np.exp(np.concatenate([[0.0], np.cumsum(shocks)]))
    return pd.Series(path, index=trading_days(n, start), name="close")


def ar1_prices(
    n: int = 1500,
    s0: float = 100.0,
    phi: float = 0.08,
    sigma: float = 0.20,
    drift: float = 0.05,
    seed: int | None = None,
    start: str = "2019-01-01",
) -> pd.Series:
    """Closes whose daily returns follow AR(1): r_t = phi * r_{t-1} + e_t.

    A small positive ``phi`` plants a weak momentum effect, which gives the
    machine-learning labs something real (but modest) to find.
    """
    rng = np.random.default_rng(seed)
    daily_sigma = sigma / np.sqrt(TRADING_DAYS)
    eps = rng.normal(0.0, daily_sigma * np.sqrt(1 - phi**2), size=n - 1)
    r = np.empty(n - 1)
    r[0] = eps[0]
    for t in range(1, n - 1):
        r[t] = phi * r[t - 1] + eps[t]
    r += drift / TRADING_DAYS
    path = s0 * np.exp(np.concatenate([[0.0], np.cumsum(r)]))
    return pd.Series(path, index=trading_days(n, start), name="close")


def ohlcv_from_close(close: pd.Series, seed: int | None = None, base_volume: float = 1e6) -> pd.DataFrame:
    """Build plausible open/high/low/volume columns around a close series."""
    rng = np.random.default_rng(seed)
    c = close.to_numpy(dtype=float)
    rets = np.diff(np.log(c), prepend=np.log(c[0]))
    daily_vol = max(float(np.std(rets[1:])) if len(c) > 2 else 0.01, 1e-4)
    prev_close = np.concatenate([[c[0]], c[:-1]])
    open_ = prev_close * np.exp(rng.normal(0, daily_vol * 0.3, size=len(c)))
    upper = np.maximum(open_, c) * np.exp(np.abs(rng.normal(0, daily_vol * 0.5, size=len(c))))
    lower = np.minimum(open_, c) * np.exp(-np.abs(rng.normal(0, daily_vol * 0.5, size=len(c))))
    volume = base_volume * np.exp(rng.normal(0, 0.3, size=len(c))) * (1 + 20 * np.abs(rets))
    return pd.DataFrame(
        {"open": open_, "high": upper, "low": lower, "close": c, "volume": volume.round()},
        index=close.index,
    )


def ohlcv(
    n: int = 756,
    s0: float = 100.0,
    mu: float = 0.10,
    sigma: float = 0.20,
    seed: int | None = None,
    start: str = "2022-01-03",
) -> pd.DataFrame:
    """Daily OHLCV bars built on a GBM close path."""
    close = gbm_prices(n, s0, mu, sigma, seed, start)
    return ohlcv_from_close(close, seed=None if seed is None else seed + 1)


def cointegrated_pair(
    n: int = 756,
    beta: float = 1.5,
    half_life: float = 10.0,
    spread_sigma: float = 1.5,
    seed: int | None = None,
    start: str = "2022-01-03",
) -> pd.DataFrame:
    """Two price series with y = 20 + beta * x + OU spread.

    The spread mean-reverts with the given half-life (in days), so a pairs
    strategy has a genuine edge before costs.
    """
    rng = np.random.default_rng(seed)
    x = gbm_prices(n, 100.0, 0.08, 0.25, seed=int(rng.integers(1_000_000)), start=start)
    theta = np.log(2) / half_life
    s = np.zeros(n)
    for t in range(1, n):
        s[t] = s[t - 1] - theta * s[t - 1] + rng.normal(0, spread_sigma)
    y = 20.0 + beta * x.to_numpy() + s
    return pd.DataFrame({"y": y, "x": x.to_numpy()}, index=x.index)


def universe(
    n_assets: int = 10,
    n_days: int = 756,
    market_vol: float = 0.18,
    idio_vol: float = 0.20,
    seed: int | None = None,
    start: str = "2022-01-03",
) -> pd.DataFrame:
    """Closes for ``n_assets`` stocks driven by one market factor plus noise.

    Betas are drawn from U(0.6, 1.4) and annual drifts from N(8%, 6%).
    Columns are named SYN01, SYN02, ...
    """
    rng = np.random.default_rng(seed)
    dt = 1.0 / TRADING_DAYS
    market = rng.normal(0.0, market_vol * np.sqrt(dt), size=(n_days - 1, 1))
    betas = rng.uniform(0.6, 1.4, size=n_assets)
    drifts = rng.normal(0.08, 0.06, size=n_assets)
    idio = rng.normal(0.0, idio_vol * np.sqrt(dt), size=(n_days - 1, n_assets))
    rets = drifts * dt + market * betas + idio
    paths = 100.0 * np.exp(np.vstack([np.zeros(n_assets), np.cumsum(rets, axis=0)]))
    cols = [f"SYN{i + 1:02d}" for i in range(n_assets)]
    return pd.DataFrame(paths, index=trading_days(n_days, start), columns=cols)


def regime_prices(
    n: int = 2500,
    mu: tuple[float, float] = (0.15, -0.25),
    sigma: tuple[float, float] = (0.12, 0.35),
    phi: tuple[float, float] = (0.0, 0.0),
    p_stay: tuple[float, float] = (0.985, 0.95),
    seed: int | None = None,
    start: str = "2016-01-01",
) -> pd.DataFrame:
    """Prices from a two-state Markov-switching model.

    State 0 is "calm", state 1 "turbulent". Each state has its own annual drift
    ``mu``, annual volatility ``sigma`` and AR(1) coefficient ``phi`` on daily
    returns; ``p_stay`` is the daily probability of staying in each state.
    Returns columns ``close`` and ``regime`` (the true hidden state, for grading
    only: a strategy must never use it).

    With different ``phi`` per state, whether momentum or reversal works depends
    on the regime, an interaction that tree ensembles can learn and linear
    models cannot.
    """
    rng = np.random.default_rng(seed)
    dt = 1.0 / TRADING_DAYS
    states = np.zeros(n, dtype=int)
    for t in range(1, n):
        stay = p_stay[states[t - 1]]
        states[t] = states[t - 1] if rng.random() < stay else 1 - states[t - 1]
    r = np.zeros(n)
    for t in range(1, n):
        k = states[t]
        r[t] = mu[k] * dt + phi[k] * (r[t - 1] - mu[states[t - 1]] * dt) + sigma[k] * np.sqrt(dt) * rng.normal()
    close = 100.0 * np.exp(np.cumsum(r))
    return pd.DataFrame({"close": close, "regime": states}, index=trading_days(n, start))


def garch_prices(
    n: int = 2500,
    omega: float = 2e-6,
    alpha: float = 0.08,
    beta: float = 0.90,
    mu: float = 0.08,
    seed: int | None = None,
    start: str = "2016-01-01",
) -> pd.DataFrame:
    """Prices whose daily returns follow GARCH(1,1): volatility clusters.

    σ²_t = omega + alpha·ε²_{t−1} + beta·σ²_{t−1}. Returns ``close`` and the true
    conditional volatility ``sigma`` (daily).
    """
    rng = np.random.default_rng(seed)
    var = np.empty(n)
    eps = np.empty(n)
    var[0] = omega / (1 - alpha - beta)
    eps[0] = np.sqrt(var[0]) * rng.normal()
    for t in range(1, n):
        var[t] = omega + alpha * eps[t - 1] ** 2 + beta * var[t - 1]
        eps[t] = np.sqrt(var[t]) * rng.normal()
    r = mu / TRADING_DAYS + eps
    r[0] = 0.0
    close = 100.0 * np.exp(np.cumsum(r))
    return pd.DataFrame({"close": close, "sigma": np.sqrt(var)}, index=trading_days(n, start))


def drifting_pair(
    n: int = 1500,
    beta_start: float = 1.2,
    beta_end: float = 1.9,
    half_life: float = 8.0,
    spread_sigma: float = 1.5,
    seed: int | None = None,
    start: str = "2019-01-01",
) -> pd.DataFrame:
    """A pair whose hedge ratio drifts from ``beta_start`` to ``beta_end``.

    y = 20 + beta_t · x + OU spread. A hedge ratio fixed in a formation window
    goes stale; an adaptive (Kalman) estimate keeps up. Column ``true_beta`` is
    for grading only.
    """
    rng = np.random.default_rng(seed)
    x = gbm_prices(n, 100.0, 0.06, 0.22, seed=int(rng.integers(1_000_000)), start=start).to_numpy()
    beta = np.linspace(beta_start, beta_end, n)
    theta = np.log(2) / half_life
    s = np.zeros(n)
    for t in range(1, n):
        s[t] = s[t - 1] * (1 - theta) + rng.normal(0, spread_sigma)
    y = 20.0 + beta * x + s
    return pd.DataFrame({"y": y, "x": x, "true_beta": beta}, index=trading_days(n, start))


def intraday_volume_profile(n_buckets: int = 25) -> np.ndarray:
    """U-shaped share of daily volume per bucket (sums to 1).

    25 buckets of 15 minutes cover the NSE cash session 09:15–15:30.
    """
    u = np.linspace(-1.0, 1.0, n_buckets)
    weights = 1.0 + 1.5 * u**2
    weights[-1] *= 1.3  # closing auction / last-hour rush
    return weights / weights.sum()


def load_ohlcv_csv(path: str | Path) -> pd.DataFrame:
    """Read a CSV with a date column and OHLCV columns (any capitalisation)."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    date_col = "date" if "date" in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col])
    return df.set_index(date_col).sort_index()


def download_prices(ticker: str, start: str = "2018-01-01", end: str | None = None) -> pd.DataFrame:
    """Download split/dividend-adjusted daily OHLCV with yfinance.

    NSE symbols take a ``.NS`` suffix (``TCS.NS``), BSE ``.BO``; indices use
    ``^NSEI`` (Nifty 50) and ``^NSEBANK`` (Bank Nifty). Free data is fine for
    learning; licensed exchange data is needed for anything commercial.
    """
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError("Install the data extra: pip install yfinance") from exc

    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if df is None or df.empty:
        raise ValueError(f"No data returned for {ticker!r}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    df.index.name = "date"
    return df[["open", "high", "low", "close", "volume"]]
