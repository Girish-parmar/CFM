"""Market microstructure and execution (Module 10).

Contents: a price–time-priority limit order book, TWAP / VWAP / POV
schedules, the Almgren–Chriss optimal trajectory, the square-root impact rule
and implementation-shortfall accounting.
"""

from __future__ import annotations

import itertools
from collections import deque

import numpy as np
import pandas as pd


class OrderBook:
    """Continuous double auction with price–time priority (like NSE's matching engine).

    >>> book = OrderBook()
    >>> _ = book.add_limit("SELL", 101.0, 50)
    >>> _, trades = book.add_limit("BUY", 101.0, 20)
    >>> trades[0]["qty"], book.best_ask()
    (20, 101.0)
    """

    def __init__(self) -> None:
        self.bids: dict[float, deque] = {}
        self.asks: dict[float, deque] = {}
        self._where: dict[int, tuple[str, float]] = {}
        self._ids = itertools.count(1)
        self.trades: list[dict] = []

    # -- queries -------------------------------------------------------------
    def best_bid(self) -> float | None:
        return max(self.bids) if self.bids else None

    def best_ask(self) -> float | None:
        return min(self.asks) if self.asks else None

    def spread(self) -> float | None:
        bid, ask = self.best_bid(), self.best_ask()
        return None if bid is None or ask is None else ask - bid

    def resting_order_ids(self) -> list[int]:
        return list(self._where)

    def mid(self) -> float | None:
        bid, ask = self.best_bid(), self.best_ask()
        return None if bid is None or ask is None else (bid + ask) / 2

    def depth(self, levels: int = 5) -> pd.DataFrame:
        bids = sorted(self.bids, reverse=True)[:levels]
        asks = sorted(self.asks)[:levels]
        rows = []
        for i in range(max(len(bids), len(asks))):
            rows.append({
                "bid_qty": sum(q for _, q in self.bids[bids[i]]) if i < len(bids) else None,
                "bid": bids[i] if i < len(bids) else None,
                "ask": asks[i] if i < len(asks) else None,
                "ask_qty": sum(q for _, q in self.asks[asks[i]]) if i < len(asks) else None,
            })
        return pd.DataFrame(rows)

    # -- order entry ---------------------------------------------------------------
    def add_limit(self, side: str, price: float, qty: int) -> tuple[int, list[dict]]:
        order_id = next(self._ids)
        remaining, trades = self._match(side, qty, order_id, limit=price)
        if remaining > 0:
            book = self.bids if side == "BUY" else self.asks
            book.setdefault(price, deque()).append([order_id, remaining])
            self._where[order_id] = (side, price)
        return order_id, trades

    def add_market(self, side: str, qty: int) -> list[dict]:
        _, trades = self._match(side, qty, next(self._ids), limit=None)
        return trades

    def cancel(self, order_id: int) -> bool:
        loc = self._where.pop(order_id, None)
        if loc is None:
            return False
        side, price = loc
        book = self.bids if side == "BUY" else self.asks
        queue = book[price]
        for entry in queue:
            if entry[0] == order_id:
                queue.remove(entry)
                break
        if not queue:
            del book[price]
        return True

    def _match(self, side: str, qty: int, taker_id: int, limit: float | None) -> tuple[int, list[dict]]:
        if side not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")
        opposite = self.asks if side == "BUY" else self.bids
        trades = []
        while qty > 0 and opposite:
            best = min(opposite) if side == "BUY" else max(opposite)
            if limit is not None and ((side == "BUY" and best > limit) or (side == "SELL" and best < limit)):
                break
            queue = opposite[best]
            maker = queue[0]
            traded = min(qty, maker[1])
            trade = {"price": best, "qty": traded, "aggressor": side, "maker_id": maker[0], "taker_id": taker_id}
            trades.append(trade)
            self.trades.append(trade)
            qty -= traded
            maker[1] -= traded
            if maker[1] == 0:
                queue.popleft()
                self._where.pop(maker[0], None)
            if not queue:
                del opposite[best]
        return qty, trades


# ---------------------------------------------------------------------------
# Execution schedules
# ---------------------------------------------------------------------------

def _integer_split(total: int, weights: np.ndarray) -> np.ndarray:
    """Split ``total`` shares by ``weights`` into integers that sum exactly (largest remainder)."""
    weights = np.asarray(weights, dtype=float)
    raw = total * weights / weights.sum()
    base = np.floor(raw).astype(int)
    shortfall = total - base.sum()
    base[np.argsort(raw - base)[::-1][:shortfall]] += 1
    return base


def twap_schedule(total_qty: int, n_slices: int) -> np.ndarray:
    return _integer_split(total_qty, np.ones(n_slices))


def vwap_schedule(total_qty: int, volume_profile: np.ndarray) -> np.ndarray:
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


def square_root_impact_bps(qty: float, adv: float, daily_vol: float, y: float = 1.0) -> float:
    """Empirical square-root law: impact ≈ Y · σ_daily · sqrt(Q / ADV)."""
    return float(y * daily_vol * np.sqrt(qty / adv) * 1e4)


def implementation_shortfall(
    side: str, decision_price: float, fills: list[tuple[int, float]], target_qty: int, final_price: float
) -> dict[str, float]:
    """Perold (1988) shortfall versus the price when the decision was made.

    ``fills`` is a list of (qty, price). Unfilled shares are charged the move
    from decision to ``final_price`` as opportunity cost. Positive = cost.
    """
    sign = 1 if side == "BUY" else -1
    filled = sum(q for q, _ in fills)
    avg = sum(q * p for q, p in fills) / filled if filled else decision_price
    execution = sign * (avg - decision_price) * filled
    opportunity = sign * (final_price - decision_price) * (target_qty - filled)
    notional = decision_price * target_qty
    return {
        "filled_qty": filled,
        "avg_price": avg,
        "execution_cost": execution,
        "opportunity_cost": opportunity,
        "total_cost": execution + opportunity,
        "total_bps": 1e4 * (execution + opportunity) / notional,
    }
