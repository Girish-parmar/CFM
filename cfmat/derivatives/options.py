"""Option pricing (M08, M09): Black–Scholes–Merton, Greeks, implied volatility,
binomial trees, futures fair value and multi-leg payoffs.

Conventions: ``T`` in years, ``r`` and ``q`` continuously compounded annual
rates, ``sigma`` annualised volatility, ``kind`` is "call" or "put".
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm


def _d1_d2(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> tuple[float, float]:
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return d1, d1 - sigma * np.sqrt(T)


def _check_kind(kind: str) -> str:
    kind = kind.lower()
    if kind not in ("call", "put"):
        raise ValueError("kind must be 'call' or 'put'")
    return kind


def bs_price(S: float, K: float, T: float, r: float, sigma: float, kind: str = "call", q: float = 0.0) -> float:
    """Black–Scholes–Merton price of a European option."""
    kind = _check_kind(kind)
    if T <= 0 or sigma <= 0:
        intrinsic = max(S - K, 0.0) if kind == "call" else max(K - S, 0.0)
        return float(intrinsic)
    d1, d2 = _d1_d2(S, K, T, r, sigma, q)
    if kind == "call":
        return float(S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))
    return float(K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1))


@dataclass(frozen=True)
class Greeks:
    """First-order Greeks: vega per 1 volatility point, theta per calendar day, rho per 1% rate move."""
    delta: float
    gamma: float
    vega: float   # price change for +1 volatility point (1%)
    theta: float  # price change per calendar day
    rho: float    # price change for +1% in rates


def bs_greeks(S: float, K: float, T: float, r: float, sigma: float, kind: str = "call", q: float = 0.0) -> Greeks:
    """Black–Scholes–Merton Greeks for a European option with continuous dividend yield ``q``."""
    kind = _check_kind(kind)
    d1, d2 = _d1_d2(S, K, T, r, sigma, q)
    disc_q, disc_r = np.exp(-q * T), np.exp(-r * T)
    pdf = norm.pdf(d1)
    gamma = disc_q * pdf / (S * sigma * np.sqrt(T))
    vega = S * disc_q * pdf * np.sqrt(T)
    decay = -S * disc_q * pdf * sigma / (2 * np.sqrt(T))
    if kind == "call":
        delta = disc_q * norm.cdf(d1)
        theta = decay - r * K * disc_r * norm.cdf(d2) + q * S * disc_q * norm.cdf(d1)
        rho = K * T * disc_r * norm.cdf(d2)
    else:
        delta = disc_q * (norm.cdf(d1) - 1.0)
        theta = decay + r * K * disc_r * norm.cdf(-d2) - q * S * disc_q * norm.cdf(-d1)
        rho = -K * T * disc_r * norm.cdf(-d2)
    return Greeks(float(delta), float(gamma), float(vega / 100), float(theta / 365), float(rho / 100))


def implied_volatility(
    price: float, S: float, K: float, T: float, r: float, kind: str = "call", q: float = 0.0
) -> float:
    """Volatility that makes the Black–Scholes price equal the market ``price``."""
    kind = _check_kind(kind)
    lower = max(S * np.exp(-q * T) - K * np.exp(-r * T), 0.0) if kind == "call" else max(
        K * np.exp(-r * T) - S * np.exp(-q * T), 0.0
    )
    upper = S * np.exp(-q * T) if kind == "call" else K * np.exp(-r * T)
    if not lower < price < upper:
        raise ValueError(f"price {price:.4f} is outside no-arbitrage bounds ({lower:.4f}, {upper:.4f})")
    return float(brentq(lambda s: bs_price(S, K, T, r, s, kind, q) - price, 1e-6, 5.0, xtol=1e-10))


def binomial_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    kind: str = "call",
    steps: int = 200,
    american: bool = False,
    q: float = 0.0,
) -> float:
    """Cox–Ross–Rubinstein tree. Set ``american=True`` for early exercise."""
    kind = _check_kind(kind)
    dt = T / steps
    u = np.exp(sigma * np.sqrt(dt))
    d = 1.0 / u
    p = (np.exp((r - q) * dt) - d) / (u - d)
    disc = np.exp(-r * dt)
    j = np.arange(steps + 1)
    prices = S * u**j * d ** (steps - j)
    values = np.maximum(prices - K, 0.0) if kind == "call" else np.maximum(K - prices, 0.0)
    for step in range(steps - 1, -1, -1):
        values = disc * (p * values[1:] + (1 - p) * values[:-1])
        if american:
            prices = S * u ** np.arange(step + 1) * d ** (step - np.arange(step + 1))
            exercise = np.maximum(prices - K, 0.0) if kind == "call" else np.maximum(K - prices, 0.0)
            values = np.maximum(values, exercise)
    return float(values[0])


def put_call_parity_gap(call: float, put: float, S: float, K: float, T: float, r: float, q: float = 0.0) -> float:
    """C − P − (S·e^(−qT) − K·e^(−rT)). Near zero when prices are consistent."""
    return float(call - put - (S * np.exp(-q * T) - K * np.exp(-r * T)))


def futures_fair_value(spot: float, T: float, r: float, q: float = 0.0) -> float:
    """Cost-of-carry fair value F = S·e^((r−q)T)."""
    return float(spot * np.exp((r - q) * T))


def strategy_payoff(legs: list[dict], spot: np.ndarray, lot_size: int = 1) -> np.ndarray:
    """Profit at expiry of a multi-leg position across a range of spot prices.

    Each leg is ``{"kind": "call"|"put"|"future", "strike": K, "qty": ±n,
    "premium": p}``. For futures, ``strike`` is the entry price and premium 0.
    Positive ``qty`` is long, negative is short.
    """
    spot = np.asarray(spot, dtype=float)
    total = np.zeros_like(spot)
    for leg in legs:
        kind, k, qty, prem = leg["kind"], leg["strike"], leg["qty"], leg.get("premium", 0.0)
        if kind == "call":
            value = np.maximum(spot - k, 0.0)
        elif kind == "put":
            value = np.maximum(k - spot, 0.0)
        elif kind == "future":
            value = spot - k
        else:
            raise ValueError(f"unknown leg kind {kind!r}")
        total += qty * (value - prem)
    return total * lot_size


@dataclass(frozen=True)
class SecondOrderGreeks:
    """Second-order Greeks in the same units as ``Greeks`` (volatility points, calendar days).

    vanna  change in delta for +1 volatility point (= change in vega per unit of spot)
    volga  change in vega (per point) for +1 volatility point; also called vomma
    charm  change in delta per calendar day (delta decay)
    speed  change in gamma per unit of spot
    zomma  change in gamma for +1 volatility point
    color  change in gamma per calendar day
    """
    vanna: float
    volga: float
    charm: float
    speed: float
    zomma: float
    color: float


def bs_second_order_greeks(
    S: float, K: float, T: float, r: float, sigma: float, kind: str = "call", q: float = 0.0
) -> SecondOrderGreeks:
    """Closed-form second-order Greeks under Black–Scholes–Merton with dividend yield ``q``.

    Vanna, volga, speed, zomma and color are the same for calls and puts; charm differs by
    the dividend term. Time derivatives are for calendar time passing (T shrinking).
    """
    kind = _check_kind(kind)
    d1, d2 = _d1_d2(S, K, T, r, sigma, q)
    rt = sigma * np.sqrt(T)
    disc_q = np.exp(-q * T)
    pdf = norm.pdf(d1)
    gamma = disc_q * pdf / (S * rt)
    vanna = -disc_q * pdf * d2 / sigma
    volga = S * disc_q * pdf * np.sqrt(T) * d1 * d2 / sigma
    shape = (2 * (r - q) * T - d2 * rt) / (2 * T * rt)
    charm = (q * disc_q * norm.cdf(d1) if kind == "call" else -q * disc_q * norm.cdf(-d1)) - disc_q * pdf * shape
    speed = -gamma / S * (d1 / rt + 1)
    zomma = gamma * (d1 * d2 - 1) / sigma
    color = disc_q * pdf / (2 * S * T * rt) * (2 * q * T + 1 + (2 * (r - q) * T - d2 * rt) / rt * d1)
    return SecondOrderGreeks(vanna=float(vanna / 100), volga=float(volga / 1e4), charm=float(charm / 365),
                             speed=float(speed), zomma=float(zomma / 100), color=float(color / 365))


def greek_pnl_attribution(legs: list[dict], path: pd.DataFrame, r: float = 0.065, q: float = 0.0) -> pd.DataFrame:
    """Explain an option position's P&L, step by step, with its Greeks.

    ``legs``: ``{"kind": "call"|"put", "strike": K, "qty": ±units, "expiry": date}``.
    ``path``: a DataFrame indexed by date with ``spot`` and ``iv`` (annualised, one level for
    all legs, e.g. ATM). For each step the Greeks at the start explain the move:
    delta·dS + ½gamma·dS² + vega·dσ + theta·days + vanna·dS·dσ + ½volga·dσ² + charm·days·dS
    (+ speed·dS³/6), with dσ in volatility points. ``actual`` is the full repricing;
    ``residual`` is what the terms miss. Returns one row per step.
    """
    rows = []
    for d0, d1 in pairwise(path.index):
        s0, s1 = float(path.at[d0, "spot"]), float(path.at[d1, "spot"])
        v0, v1 = float(path.at[d0, "iv"]), float(path.at[d1, "iv"])
        ds, dv, days = s1 - s0, (v1 - v0) * 100, (d1 - d0).days
        terms = dict.fromkeys(("delta", "gamma", "vega", "theta", "vanna", "volga", "charm", "speed", "actual"), 0.0)
        for leg in legs:
            t0 = (pd.Timestamp(leg["expiry"]) - d0).days / 365
            t1 = (pd.Timestamp(leg["expiry"]) - d1).days / 365
            if t0 <= 0:
                continue
            k, qty, kind = leg["strike"], leg["qty"], leg["kind"]
            g1 = bs_greeks(s0, k, t0, r, v0, kind, q)
            g2 = bs_second_order_greeks(s0, k, t0, r, v0, kind, q)
            terms["delta"] += qty * g1.delta * ds
            terms["gamma"] += qty * 0.5 * g1.gamma * ds**2
            terms["vega"] += qty * g1.vega * dv
            terms["theta"] += qty * g1.theta * days
            terms["vanna"] += qty * g2.vanna * ds * dv
            terms["volga"] += qty * 0.5 * g2.volga * dv**2
            terms["charm"] += qty * g2.charm * days * ds
            terms["speed"] += qty * g2.speed * ds**3 / 6
            terms["actual"] += qty * (bs_price(s1, k, t1, r, v1, kind, q) - bs_price(s0, k, t0, r, v0, kind, q))
        explained = sum(v for k, v in terms.items() if k != "actual")
        rows.append({"date": d1, **terms, "explained": explained, "residual": terms["actual"] - explained})
    return pd.DataFrame(rows).set_index("date")
