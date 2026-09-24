"""Option pricing for Module 6: Black–Scholes–Merton, Greeks, implied volatility,
binomial trees, futures fair value and multi-leg payoffs.

Conventions: ``T`` in years, ``r`` and ``q`` continuously compounded annual
rates, ``sigma`` annualised volatility, ``kind`` is "call" or "put".
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
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
    delta: float
    gamma: float
    vega: float   # price change for +1 volatility point (1%)
    theta: float  # price change per calendar day
    rho: float    # price change for +1% in rates


def bs_greeks(S: float, K: float, T: float, r: float, sigma: float, kind: str = "call", q: float = 0.0) -> Greeks:
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
