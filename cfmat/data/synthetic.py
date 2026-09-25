"""Synthetic market data with known, documented properties (M03-M23).

Every generator is reproducible with ``seed`` and runs offline. Several plant a
specific effect (momentum, mean reversion, regimes, calendar effects, trend
archetypes) so a lab can show a method working when the effect exists. Real
markets are noisier and effects are smaller: always re-test on real data.

Generators that add noise to an existing series (``ohlcv_from_close``,
``implied_vol_series``) draw from a *salted* random stream. Labs often pass the
same seed to a price generator and to ``ohlcv_from_close``; with an unsalted
stream the open-price noise would equal the next day's return shock, planting
a look-ahead that makes candlestick patterns look predictive.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..analytics.metrics import TRADING_DAYS


def _derived_rng(seed: int | None, salt: int) -> np.random.Generator:
    """A random stream independent of ``default_rng(seed)`` for derived series."""
    return np.random.default_rng(None if seed is None else [salt, seed])


_OHLC_SALT = 0x4F484C43   # "OHLC"
_IV_SALT = 0x49565331     # "IVS1"
_VOL_SALT = 0x564F4C53    # "VOLS"


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
    """Build plausible open/high/low/volume columns around a close series.

    The noise comes from a stream independent of any price generator given the
    same ``seed``, so open, high and low carry no information about future closes.
    """
    rng = _derived_rng(seed, _OHLC_SALT)
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
    idio_vol: float | tuple[float, float] = 0.20,
    seed: int | None = None,
    start: str = "2022-01-03",
) -> pd.DataFrame:
    """Closes for ``n_assets`` stocks driven by one market factor plus noise.

    Betas are drawn from U(0.6, 1.4) and annual drifts from N(8%, 6%).
    ``idio_vol`` is one idiosyncratic volatility for every stock, or a
    ``(low, high)`` range from which each stock draws its own.
    Columns are named SYN01, SYN02, ...
    """
    rng = np.random.default_rng(seed)
    dt = 1.0 / TRADING_DAYS
    market = rng.normal(0.0, market_vol * np.sqrt(dt), size=(n_days - 1, 1))
    betas = rng.uniform(0.6, 1.4, size=n_assets)
    drifts = rng.normal(0.08, 0.06, size=n_assets)
    idio = rng.normal(0.0, np.sqrt(dt), size=(n_days - 1, n_assets))
    if isinstance(idio_vol, tuple):
        idio *= _derived_rng(seed, _VOL_SALT).uniform(*idio_vol, size=n_assets)
    else:
        idio *= idio_vol
    rets = drifts * dt + market * betas + idio
    paths = 100.0 * np.exp(np.vstack([np.zeros(n_assets), np.cumsum(rets, axis=0)]))
    cols = [f"SYN{i + 1:02d}" for i in range(n_assets)]
    return pd.DataFrame(paths, index=trading_days(n_days, start), columns=cols)


def factor_panel(
    n_stocks: int = 200,
    n_months: int = 120,
    premia: dict[str, float] | None = None,
    premium_vol: float = 1.5,
    outlier_share: float = 0.02,
    seed: int | None = None,
    start: str = "2015-01-31",
) -> pd.DataFrame:
    """Monthly (date, stock) panel of characteristics and next-month returns.

    Characteristics follow persistent AR(1) processes: ``earnings_yield``, ``roe``,
    ``debt_equity``, ``momentum_12_1`` and ``log_mcap``. Next-month returns
    (``fwd_ret``) load on standardised *sector-relative* value, quality and
    momentum. Each premium has a long-run mean (``premia``, per month per unit
    z-score) but drifts over time (AR(1) multiplier with volatility
    ``premium_vol``), so every factor has dry spells. Sectors differ in their
    typical earnings yield, so a raw value score is partly a sector bet, and
    ``outlier_share`` of reported earnings yields are distorted (one-off gains,
    data errors) without affecting returns, which is what winsorising is for.
    All numbers are fictional.
    """
    rng = np.random.default_rng(seed)
    premia = {"value": 0.0015, "quality": 0.0012, "momentum": 0.0015, **(premia or {})}
    sectors = np.array(["Banks", "IT", "Pharma", "Auto", "FMCG", "Energy", "Metals", "Infra"])
    sector_ey = dict(zip(sectors, [0.09, 0.035, 0.045, 0.06, 0.025, 0.08, 0.10, 0.07]))
    sector = rng.choice(sectors, n_stocks)
    names = [f"STK{i + 1:03d}" for i in range(n_stocks)]
    dates = pd.date_range(start, periods=n_months, freq="ME")

    def ar1(mean, sd, phi=0.9, shape=(n_months, n_stocks)):
        x = np.empty(shape)
        x[0] = mean + rng.normal(0, sd, shape[1])
        for t in range(1, shape[0]):
            x[t] = mean + phi * (x[t - 1] - mean) + rng.normal(0, sd * np.sqrt(1 - phi**2), shape[1])
        return x

    base_ey = np.array([sector_ey[s] for s in sector])
    ey = ar1(base_ey, 0.02)
    roe = ar1(0.15, 0.06)
    de = np.exp(ar1(-0.7, 0.5))
    mom = ar1(0.0, 0.25, phi=0.8)
    size = ar1(10.0, 1.2, phi=0.98)

    def z(x):
        return (x - x.mean(axis=1, keepdims=True)) / x.std(axis=1, keepdims=True)

    loadings = {"value": z(ey - base_ey), "quality": z(z(roe) - 0.5 * z(np.log(de))), "momentum": z(mom)}
    drift = ar1(1.0, premium_vol, phi=0.9, shape=(n_months, len(loadings)))
    sector_ret = {s: rng.normal(0, 0.03, n_months) for s in sectors}
    fwd = (0.008 + np.column_stack([sector_ret[s] for s in sector]) + rng.normal(0, 0.08, (n_months, n_stocks)))
    for j, (name, load) in enumerate(loadings.items()):
        fwd += premia[name] * drift[:, [j]] * load
    reported_ey = ey.copy()
    hit = rng.random(ey.shape) < outlier_share
    reported_ey[hit] *= rng.choice([-2.0, 4.0, 8.0], size=int(hit.sum()))
    index = pd.MultiIndex.from_product([dates, names], names=["date", "stock"])
    return pd.DataFrame({
        "sector": np.tile(sector, n_months),
        "earnings_yield": reported_ey.ravel(),
        "roe": roe.ravel(),
        "debt_equity": de.ravel(),
        "momentum_12_1": mom.ravel(),
        "log_mcap": size.ravel(),
        "fwd_ret": fwd.ravel(),
    }, index=index)


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


def seasonal_prices(
    n: int = 3000,
    base_drift: float = 0.06,
    sigma: tuple[float, float] = (0.12, 0.30),
    phi: tuple[float, float] = (0.2, -0.2),
    p_stay: tuple[float, float] = (0.98, 0.98),
    weekday_effect: dict[int, float] | None = None,
    turn_of_month: float = 0.0015,
    tom_days: tuple[int, int] = (1, 3),
    streak_len: int = 3,
    streak_bounce: float = 0.0020,
    seed: int | None = None,
    start: str = "2014-01-01",
) -> pd.DataFrame:
    """Daily OHLCV with *planted* calendar, regime and pattern effects.

    Daily return r_t = base drift
        + ``weekday_effect[weekday of t]`` (default: Monday −12 bp, Friday +12 bp)
        + ``turn_of_month`` if t is among the last ``tom_days[0]`` or first
          ``tom_days[1]`` trading days of a month
        + ``streak_bounce`` if the previous ``streak_len`` days all closed down
        + phi[k] · r_{t−1} (momentum in the calm regime, reversal in the turbulent one)
        + noise with the regime's volatility ``sigma[k]``.
    Month-of-year and the other weekdays carry no effect, so they are useful
    decoys for multiple-testing exercises. Column ``regime`` is the hidden
    state (for grading only). Real calendar effects are smaller and less stable.
    """
    effects = {0: -0.0012, 4: 0.0012} if weekday_effect is None else weekday_effect
    rng = np.random.default_rng(seed)
    idx = trading_days(n, start)
    months = idx.to_period("M")
    pos_from_start = pd.Series(1, index=idx).groupby(months).cumsum().to_numpy()
    pos_from_end = pd.Series(1, index=idx).iloc[::-1].groupby(months[::-1]).cumsum().iloc[::-1].to_numpy()
    tom = (pos_from_end <= tom_days[0]) | (pos_from_start <= tom_days[1])
    weekday = idx.weekday.to_numpy()
    dt = 1.0 / TRADING_DAYS
    states = np.zeros(n, dtype=int)
    for t in range(1, n):
        states[t] = states[t - 1] if rng.random() < p_stay[states[t - 1]] else 1 - states[t - 1]
    r = np.zeros(n)
    base = base_drift * dt
    for t in range(1, n):
        k = states[t]
        streak = t > streak_len and np.all(r[t - streak_len : t] < 0)
        r[t] = (base + effects.get(int(weekday[t]), 0.0) + turn_of_month * tom[t] + streak_bounce * streak
                + phi[k] * (r[t - 1] - base) + sigma[k] * np.sqrt(dt) * rng.normal())
    close = pd.Series(100.0 * np.exp(np.cumsum(r)), index=idx, name="close")
    bars = ohlcv_from_close(close, seed=None if seed is None else seed + 1)
    bars["regime"] = states
    return bars


ARCHETYPES = ("uptrend", "downtrend", "range", "volatile", "squeeze")


SECTORS = ("BANK", "TECH", "PHRM", "AUTO", "ENRG", "FMCG", "METL", "INFR")


def instrument_universe(
    n: int = 40, n_days: int = 756, seed: int | None = None, start: str = "2023-01-02"
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """A universe of fictional instruments with known behaviour, for screeners.

    Each instrument is one of ``ARCHETYPES``: steady uptrend, steady downtrend,
    range-bound (mean-reverting price), volatile (large swings, no drift) or
    squeeze (range-bound, with volatility collapsing over the last ~60 days).
    Prices start between ₹50 and ₹3,000 and daily turnover varies from under
    ₹1 crore to several hundred crore. Returns ({symbol: OHLCV}, metadata);
    metadata holds the true archetype for grading only.
    """
    rng = np.random.default_rng(seed)
    universe, meta = {}, []
    idx = trading_days(n_days, start)
    for i in range(n):
        kind = ARCHETYPES[i % len(ARCHETYPES)]
        sector = SECTORS[int(rng.integers(len(SECTORS)))]
        symbol = f"{sector}{i + 1:02d}"
        s0 = float(np.exp(rng.uniform(np.log(50), np.log(3000))))
        dt = 1.0 / TRADING_DAYS
        if kind in ("uptrend", "downtrend"):
            mu = rng.uniform(0.30, 0.50) * (1 if kind == "uptrend" else -1)
            sigma = rng.uniform(0.18, 0.28)
            r = rng.normal(mu * dt, sigma * np.sqrt(dt), n_days)
            logp = np.log(s0) + np.cumsum(r)
        elif kind == "volatile":
            r = rng.normal(0.0, rng.uniform(0.50, 0.70) * np.sqrt(dt), n_days)
            logp = np.log(s0) + np.cumsum(r)
        else:
            sigma = np.full(n_days, rng.uniform(0.20, 0.30) * np.sqrt(dt))
            if kind == "squeeze":
                sigma[-60:] *= np.linspace(1.0, 0.2, 60)
            theta = rng.uniform(0.05, 0.10)
            logp = np.empty(n_days)
            logp[0] = np.log(s0)
            for t in range(1, n_days):
                logp[t] = logp[t - 1] + theta * (np.log(s0) - logp[t - 1]) + sigma[t] * rng.normal()
        close = pd.Series(np.exp(logp), index=idx, name="close")
        bars = ohlcv_from_close(close, seed=int(rng.integers(1_000_000)))
        if kind == "squeeze":   # keep the day ranges consistent with the collapsing volatility
            scale = pd.Series(np.r_[np.ones(n_days - 60), np.linspace(1.0, 0.2, 60)], index=idx)
            for col in ("open", "high", "low"):
                bars[col] = bars["close"] + (bars[col] - bars["close"]) * scale
        turnover_cr = float(np.exp(rng.normal(np.log(20), 1.5)))
        bars["volume"] = (turnover_cr * 1e7 / bars["close"] * np.exp(rng.normal(0, 0.3, n_days))).round()
        universe[symbol] = bars
        meta.append({"symbol": symbol, "sector": sector, "archetype": kind, "turnover_cr": turnover_cr})
    return universe, pd.DataFrame(meta).set_index("symbol")


def implied_vol_series(
    close: pd.Series,
    premium: float = 0.15,
    noise_vol_pts: float = 1.5,
    floor: float = 0.08,
    seed: int | None = None,
) -> pd.Series:
    """A synthetic at-the-money implied-volatility index for ``close``.

    IV = EWMA realised volatility × (1 + ``premium``) + mean-reverting noise.
    The premium makes option selling profitable on average (the volatility risk
    premium) while IV still jumps when the market turns turbulent. Uses data
    up to each bar only.
    """
    rng = _derived_rng(seed, _IV_SALT)
    r = np.log(close).diff().fillna(0.0).to_numpy()
    var = np.empty(len(r))
    var[0] = r[1:60].var() if len(r) > 60 else 0.0001
    for t in range(1, len(r)):
        var[t] = 0.94 * var[t - 1] + 0.06 * r[t] ** 2
    noise = np.zeros(len(r))
    for t in range(1, len(r)):
        noise[t] = 0.9 * noise[t - 1] + rng.normal(0, noise_vol_pts / 100)
    iv = np.sqrt(var * TRADING_DAYS) * (1 + premium) + noise
    return pd.Series(np.maximum(iv, floor), index=close.index, name="iv")


def intraday_volume_profile(n_buckets: int = 25) -> np.ndarray:
    """U-shaped share of daily volume per bucket (sums to 1).

    25 buckets of 15 minutes cover the NSE cash session 09:15–15:30.
    """
    u = np.linspace(-1.0, 1.0, n_buckets)
    weights = 1.0 + 1.5 * u**2
    weights[-1] *= 1.3  # closing auction / last-hour rush
    return weights / weights.sum()


def brownian_ohlc(
    n_days: int = 504,
    sigma: float | np.ndarray = 0.25,
    mu: float = 0.0,
    overnight_share: float = 0.2,
    steps_per_day: int = 375,
    s0: float = 100.0,
    seed: int | None = None,
    start: str = "2022-01-03",
) -> pd.DataFrame:
    """Daily OHLC bars built from a simulated intraday path, with the true volatility known.

    Each day's variance σ²/252 is split between an overnight gap
    (``overnight_share``) and a Brownian intraday session of ``steps_per_day``
    one-minute steps (375 = NSE 09:15–15:30); high and low are the extremes of
    that path. ``sigma`` is annualised, either one number or one value per day
    (for volatility regimes). The ``true_vol`` column holds it, so estimators can
    be graded against the truth.
    """
    if not 0 <= overnight_share < 1:
        raise ValueError("overnight_share must be in [0, 1)")
    rng = np.random.default_rng(seed)
    vol = np.broadcast_to(np.asarray(sigma, dtype=float), (n_days,)).copy()
    daily_var = vol**2 / TRADING_DAYS
    drift = (mu - 0.5 * vol**2) / TRADING_DAYS
    gap = rng.normal(overnight_share * drift, np.sqrt(overnight_share * daily_var))
    steps = rng.normal(0.0, 1.0, size=(n_days, steps_per_day))
    steps *= np.sqrt((1 - overnight_share) * daily_var / steps_per_day)[:, None]
    steps += ((1 - overnight_share) * drift / steps_per_day)[:, None]
    session = np.cumsum(steps, axis=1)
    prev_close = np.log(s0)
    rows = np.empty((n_days, 4))
    for d in range(n_days):
        open_ = prev_close + gap[d]
        path = open_ + session[d]
        rows[d] = open_, max(open_, path.max()), min(open_, path.min()), path[-1]
        prev_close = path[-1]
    frame = pd.DataFrame(np.exp(rows), columns=["open", "high", "low", "close"], index=trading_days(n_days, start))
    frame["true_vol"] = vol
    return frame


NSE_SESSION = ("09:15", "15:30")


def _session_seconds(session: tuple[str, str]) -> tuple[pd.Timedelta, float]:
    open_, close = (pd.Timedelta(f"{t}:00") for t in session)
    return open_, (close - open_).total_seconds()


def tick_stream(
    n_days: int = 1,
    seed: int | None = None,
    symbol: str = "DEMO",
    s0: float = 2000.0,
    sigma: float = 0.25,
    ticks_per_second: float = 1.0,
    tick_size: float = 0.05,
    start: str = "2026-01-05",
    session: tuple[str, str] = NSE_SESSION,
    faults: bool = True,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Trades as a feed delivers them (arrival order), with planted faults and the answer key.

    Columns: ``ts`` (exchange time), ``seq`` (feed sequence number), ``symbol``,
    ``price`` (on the tick grid) and ``qty``. Prices follow a random walk with
    annual volatility ``sigma``; arrivals are Poisson at ``ticks_per_second``.
    With ``faults``, each day gets 10 duplicated messages, 8 ticks delivered
    late (out of order), 6 bad prints (2–4% spikes), a 45-second frozen price
    and a 90-second outage. Returns ``(ticks, truth)``: ``truth["flags"]`` has
    one boolean column per tick-level fault aligned with ``ticks``, and
    ``truth["periods"]`` lists the outage and stale windows.
    """
    rng = np.random.default_rng(seed)
    open_, seconds = _session_seconds(session)
    per_tick_sd = sigma / np.sqrt(TRADING_DAYS * seconds * ticks_per_second)
    days = trading_days(n_days, start)
    frames, flag_frames, periods, seq0, log_p = [], [], [], 0, np.log(s0)
    for day in days:
        n = int(rng.poisson(ticks_per_second * seconds))
        offsets = np.sort(rng.uniform(0, seconds, n))
        log_p += rng.normal(0, 0.004)                                           # overnight gap
        path = log_p + np.cumsum(rng.normal(0, per_tick_sd, n))
        log_p = path[-1]
        price = (np.round(np.exp(path) / tick_size) * tick_size).round(4)
        qty = np.maximum(1, rng.lognormal(3.0, 1.0, n)).round().astype(int)
        ts = day + open_ + pd.to_timedelta(np.round(offsets, 3), unit="s")
        day_ticks = pd.DataFrame({"ts": ts, "seq": np.arange(seq0 + 1, seq0 + n + 1), "symbol": symbol,
                                  "price": price, "qty": qty})
        seq0 += n
        flags = pd.DataFrame(False, index=day_ticks.index, columns=["duplicate", "out_of_order", "spike"])
        if faults:
            day_ticks, flags, day_periods = _plant_faults(day_ticks, flags, day + open_, seconds, tick_size, rng)
            periods += day_periods
        frames.append(day_ticks)
        flag_frames.append(flags)
    ticks = pd.concat(frames, ignore_index=True)
    flags = pd.concat(flag_frames, ignore_index=True)
    periods_frame = pd.DataFrame(periods, columns=["kind", "start", "end"])
    return ticks, {"flags": flags, "periods": periods_frame}


def _plant_faults(ticks, flags, day_open, seconds, tick_size, rng):
    """Outage and frozen window first, then single-tick faults well apart from each other and from the windows."""
    def window(length, avoid=None):
        while True:
            start = day_open + pd.Timedelta(seconds=float(rng.uniform(0.2 * seconds, 0.8 * seconds - length)))
            end = start + pd.Timedelta(seconds=length)
            if avoid is None or end + pd.Timedelta(minutes=10) < avoid[0] or start > avoid[1] + pd.Timedelta(minutes=10):
                return start, end

    outage = window(90)
    stale = window(45, avoid=outage)
    ticks = ticks[~ticks["ts"].between(*outage, inclusive="neither")].reset_index(drop=True)
    in_stale = ticks["ts"].between(*stale, inclusive="left").to_numpy()
    first = int(np.argmax(in_stale))
    ticks.loc[in_stale, "price"] = ticks.loc[first - 1, "price"]           # the feed repeats the last price
    flags = pd.DataFrame(False, index=ticks.index, columns=flags.columns)
    busy = np.zeros(len(ticks), bool)
    busy[max(first - 60, 0): first + int(in_stale.sum()) + 60] = True
    chosen = []
    candidates = rng.permutation(np.arange(100, len(ticks) - 100))
    for pos in candidates:
        if len(chosen) == 24:
            break
        if not busy[pos - 40: pos + 40].any():
            chosen.append(int(pos))
            busy[pos - 40: pos + 40] = True
    spikes, late, dups = chosen[:6], chosen[6:14], chosen[14:24]
    for pos in spikes:
        move = rng.uniform(0.02, 0.04) * rng.choice([-1, 1])
        ticks.loc[pos, "price"] = round(round(ticks.loc[pos, "price"] * (1 + move) / tick_size) * tick_size, 4)
    rows = ticks.to_dict("records")
    marks = [{"duplicate": False, "out_of_order": False, "spike": i in spikes} for i in range(len(rows))]
    order = list(range(len(rows)))
    for pos in late:                                                        # delivered 3-10 messages later
        order.remove(pos)
        order.insert(order.index(pos + int(rng.integers(3, 11))) + 1, pos)
        marks[pos]["out_of_order"] = True
    out_rows, out_marks = [], []
    for i in order:
        out_rows.append(rows[i])
        out_marks.append(marks[i])
        if i in dups:                                                       # the same message sent twice
            out_rows.append(dict(rows[i]))
            out_marks.append({"duplicate": True, "out_of_order": False, "spike": False})
    periods = [("outage", *outage), ("stale", *stale)]
    return pd.DataFrame(out_rows), pd.DataFrame(out_marks), periods


def futures_chain(
    spot: pd.Series,
    underlying: str = "DEMOIDX",
    listed: int = 3,
    expiry_weekday: int = 1,
    lot_size: int = 50,
    tick_size: float = 0.05,
    r: float = 0.065,
    q: float = 0.012,
    basis_noise_bps: float = 5.0,
    seed: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Daily closes for a chain of monthly futures on ``spot``, and their instrument master.

    Each contract expires on the last ``expiry_weekday`` of its month (0 =
    Monday; set it to the exchange's current rule) and trades for ``listed``
    months before expiry at cost of carry, S·e^((r−q)·days/365), plus noise.
    Returns ``(prices, master)``: one price column per contract (missing
    outside its life) and a table of symbol, underlying, segment, lot size,
    tick size and expiry. Symbols follow the NSE pattern, e.g. ``DEMOIDX26JANFUT``.
    """
    rng = _derived_rng(seed, 0x46555453)   # "FUTS"
    idx = spot.index
    months = pd.period_range(idx[0], idx[-1] + pd.DateOffset(months=listed), freq="M")
    rows, prices = [], {}
    for month in months:
        last = month.to_timestamp(how="end").normalize()
        expiry = last - pd.Timedelta(days=(last.weekday() - expiry_weekday) % 7)
        first_day = (month - listed).to_timestamp()
        live = (idx >= first_day) & (idx <= expiry)
        if not live.any():
            continue
        symbol = f"{underlying}{expiry:%y}{expiry:%b}".upper() + "FUT"
        days_left = (expiry - idx[live]).days.to_numpy()
        noise = rng.normal(0, basis_noise_bps / 1e4, live.sum())
        fair = spot[live].to_numpy() * np.exp((r - q) * days_left / 365) * (1 + noise)
        prices[symbol] = pd.Series((np.round(fair / tick_size) * tick_size).round(4), index=idx[live])
        rows.append({"symbol": symbol, "underlying": underlying, "segment": "FUT", "lot_size": lot_size,
                     "tick_size": tick_size, "expiry": expiry})
    master = pd.DataFrame(rows).set_index("symbol")
    return pd.DataFrame(prices).reindex(idx), master
