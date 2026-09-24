"""Execution schedules: TWAP, VWAP, POV and the Almgren-Chriss optimal trajectory (M15).
"""

from __future__ import annotations

import numpy as np


def _integer_split(total: int, weights: np.ndarray) -> np.ndarray:
    """Split ``total`` shares by ``weights`` into integers that sum exactly (largest remainder)."""
    weights = np.asarray(weights, dtype=float)
    raw = total * weights / weights.sum()
    base = np.floor(raw).astype(int)
    shortfall = total - base.sum()
    base[np.argsort(raw - base)[::-1][:shortfall]] += 1
    return base


def twap_schedule(total_qty: int, n_slices: int) -> np.ndarray:
    """Split ``total_qty`` into ``n_slices`` near-equal integer child orders."""
    return _integer_split(total_qty, np.ones(n_slices))


def vwap_schedule(total_qty: int, volume_profile: np.ndarray) -> np.ndarray:
    """Split ``total_qty`` in proportion to an intraday volume profile, as integers that sum exactly."""
    return _integer_split(total_qty, volume_profile)


def pov_schedule(total_qty: int, forecast_volume: np.ndarray, participation: float = 0.10) -> np.ndarray:
    """Trade a fixed share of market volume until done (may finish early or not at all)."""
    remaining = total_qty
    out = np.zeros(len(forecast_volume), dtype=int)
    for i, vol in enumerate(forecast_volume):
        take = min(remaining, int(participation * vol))
        out[i] = take
        remaining -= take
    return out


def almgren_chriss_trajectory(
    total_qty: float, horizon: float, n_steps: int, sigma: float, eta: float, gamma: float = 0.0,
    risk_aversion: float = 1e-6,
) -> np.ndarray:
    """Holdings x_0..x_N under the Almgren–Chriss (2000) optimal liquidation.

    ``sigma``: price volatility per unit time; ``eta``: temporary impact;
    ``gamma``: permanent impact; ``risk_aversion``: lambda. lambda → 0 gives
    TWAP; larger lambda front-loads selling to cut timing risk.
    """
    tau = horizon / n_steps
    t = np.arange(n_steps + 1) * tau
    if risk_aversion <= 0:
        return total_qty * (1.0 - t / horizon)
    eta_tilde = eta - 0.5 * gamma * tau
    kappa_tilde_sq = risk_aversion * sigma**2 / eta_tilde
    kappa = np.arccosh(0.5 * kappa_tilde_sq * tau**2 + 1.0) / tau
    return total_qty * np.sinh(kappa * (horizon - t)) / np.sinh(kappa * horizon)


def almgren_chriss_cost(holdings: np.ndarray, horizon: float, sigma: float, eta: float, gamma: float = 0.0) -> dict[str, float]:
    """Expected impact cost and variance of a liquidation trajectory."""
    n_steps = len(holdings) - 1
    tau = horizon / n_steps
    trades = -np.diff(holdings)
    eta_tilde = eta - 0.5 * gamma * tau
    expected = 0.5 * gamma * holdings[0] ** 2 + eta_tilde / tau * np.sum(trades**2)
    variance = sigma**2 * tau * np.sum(holdings[1:] ** 2)
    return {"expected_cost": float(expected), "variance": float(variance), "std": float(np.sqrt(variance))}
