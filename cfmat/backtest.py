"""Vectorised backtesting (Module 8).

The one rule that matters most: a signal computed from bar t's close can only
earn bar t+1's return. ``vectorized_backtest`` enforces this by shifting the
position one bar before multiplying by returns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Callable

import numpy as np
import pandas as pd

from .metrics import equity_curve, sharpe_ratio


def vectorized_backtest(close: pd.Series, signal: pd.Series, cost_bps: float = 0.0) -> pd.DataFrame:
    """Backtest a single-instrument target-position series.

    ``signal`` is the desired exposure (e.g. −1, 0, +1 or fractional) decided at
    each close. ``cost_bps`` is charged on every unit of turnover (one side).
    """
    signal = signal.reindex(close.index).fillna(0.0)
    asset_ret = close.pct_change().fillna(0.0)
    held = signal.shift(1).fillna(0.0)
    turnover = held.diff().abs()
    turnover.iloc[0] = abs(held.iloc[0])
    cost = turnover * cost_bps / 1e4
    strat = held * asset_ret - cost
    return pd.DataFrame(
        {
            "close": close,
            "signal": signal,
            "position": held,
            "asset_return": asset_ret,
            "turnover": turnover,
            "cost": cost,
            "strategy_return": strat,
            "equity": equity_curve(strat),
        }
    )


def portfolio_backtest(prices: pd.DataFrame, weights: pd.DataFrame, cost_bps: float = 0.0) -> pd.DataFrame:
    """Backtest target weights across many instruments (weights decided at close)."""
    weights = weights.reindex(prices.index).fillna(0.0)
    rets = prices.pct_change().fillna(0.0)
    held = weights.shift(1).fillna(0.0)
    turnover = held.diff().abs().sum(axis=1)
    turnover.iloc[0] = held.iloc[0].abs().sum()
    cost = turnover * cost_bps / 1e4
    strat = (held * rets).sum(axis=1) - cost
    return pd.DataFrame({"turnover": turnover, "cost": cost, "strategy_return": strat, "equity": equity_curve(strat)})


def pairs_backtest(
    y: pd.Series, x: pd.Series, legs: pd.DataFrame, capital: float = 1_000_000.0, cost_bps: float = 0.0
) -> pd.DataFrame:
    """Rupee P&L of a pair where ``legs`` holds unit positions from ``pairs_signals``.

    Each spread unit (1 share of y against beta shares of x) is sized so that
    gross notional ≈ ``capital``.
    """
    gross_per_unit = y + legs["beta"].abs() * x
    units = (capital / gross_per_unit).fillna(0.0)
    shares_y = (legs["y"] * units).round()
    shares_x = (legs["x"] * units).round()
    held_y, held_x = shares_y.shift(1).fillna(0.0), shares_x.shift(1).fillna(0.0)
    pnl = held_y * y.diff().fillna(0.0) + held_x * x.diff().fillna(0.0)
    traded_value = held_y.diff().abs().fillna(held_y.abs()) * y + held_x.diff().abs().fillna(held_x.abs()) * x
    cost = traded_value * cost_bps / 1e4
    net = pnl - cost
    ret = net / capital
    return pd.DataFrame(
        {"shares_y": held_y, "shares_x": held_x, "pnl": pnl, "cost": cost, "net_pnl": net,
         "strategy_return": ret, "equity": equity_curve(ret)}
    )


# ---------------------------------------------------------------------------
# Indian transaction costs
# ---------------------------------------------------------------------------

@dataclass
class SegmentRates:
    brokerage_pct: float      # fraction of turnover (inf = always the flat cap)
    brokerage_cap: float      # max rupees per executed order (inf = no cap)
    stt_buy: float
    stt_sell: float
    exchange_txn: float
    stamp_buy: float


@dataclass
class IndianCostModel:
    """Statutory and broker charges for NSE trades.

    The default rates are illustrative, modelled on a typical discount-broker
    charge sheet. STT, exchange and stamp-duty rates change with Union Budgets
    and exchange circulars — check your broker's current sheet before relying
    on the numbers. For options, ``price`` means the option premium.
    """

    segments: dict[str, SegmentRates] = field(
        default_factory=lambda: {
            "equity_delivery": SegmentRates(0.0, np.inf, 0.001, 0.001, 0.0000297, 0.00015),
            "equity_intraday": SegmentRates(0.0003, 20.0, 0.0, 0.00025, 0.0000297, 0.00003),
            "futures": SegmentRates(0.0003, 20.0, 0.0, 0.0002, 0.0000173, 0.00002),
            "options": SegmentRates(np.inf, 20.0, 0.0, 0.001, 0.0003503, 0.00003),
        }
    )
    sebi_fee: float = 10 / 1e7   # ₹10 per crore of turnover
    gst: float = 0.18            # on brokerage + exchange + SEBI fees

    def charges(self, side: str, qty: float, price: float, segment: str = "equity_intraday") -> dict[str, float]:
        if side not in ("buy", "sell"):
            raise ValueError("side must be 'buy' or 'sell'")
        rates = self.segments[segment]
        turnover = abs(qty) * price
        brokerage = min(turnover * rates.brokerage_pct, rates.brokerage_cap) if turnover > 0 else 0.0
        stt = turnover * (rates.stt_buy if side == "buy" else rates.stt_sell)
        exchange = turnover * rates.exchange_txn
        sebi = turnover * self.sebi_fee
        stamp = turnover * rates.stamp_buy if side == "buy" else 0.0
        gst = self.gst * (brokerage + exchange + sebi)
        total = brokerage + stt + exchange + sebi + stamp + gst
        return {"turnover": turnover, "brokerage": brokerage, "stt": stt, "exchange": exchange,
                "sebi": sebi, "stamp": stamp, "gst": gst, "total": total}

    def round_trip_bps(self, qty: float, price: float, segment: str = "equity_intraday") -> float:
        """Total buy + sell charges as basis points of one side's turnover."""
        cost = self.charges("buy", qty, price, segment)["total"] + self.charges("sell", qty, price, segment)["total"]
        return 1e4 * cost / (abs(qty) * price)


# ---------------------------------------------------------------------------
# Parameter search
# ---------------------------------------------------------------------------

def grid_search(
    close: pd.Series,
    strategy: Callable[..., pd.Series],
    grid: dict[str, list],
    cost_bps: float = 0.0,
) -> pd.DataFrame:
    """In-sample Sharpe for every parameter combination (the overfitting trap)."""
    keys = list(grid)
    rows = []
    for values in product(*(grid[k] for k in keys)):
        params = dict(zip(keys, values))
        try:
            bt = vectorized_backtest(close, strategy(close, **params), cost_bps)
        except ValueError:
            continue
        rows.append({**params, "sharpe": sharpe_ratio(bt["strategy_return"])})
    return pd.DataFrame(rows).sort_values("sharpe", ascending=False, ignore_index=True)


def walk_forward(
    close: pd.Series,
    strategy: Callable[..., pd.Series],
    grid: dict[str, list],
    train: int = 504,
    test: int = 126,
    cost_bps: float = 0.0,
) -> tuple[pd.Series, pd.DataFrame]:
    """Re-optimise on each training window and trade the next test window.

    Returns the stitched out-of-sample returns and a table of chosen parameters.
    Only data up to the end of each window is ever passed to ``strategy``.
    """
    keys = list(grid)
    combos = [dict(zip(keys, v)) for v in product(*(grid[k] for k in keys))]
    oos, chosen = [], []
    for start in range(0, len(close) - train - test + 1, test):
        train_end, test_end = start + train, start + train + test
        best, best_score = None, -np.inf
        for params in combos:
            try:
                sig = strategy(close.iloc[:train_end], **params)
            except ValueError:
                continue
            bt = vectorized_backtest(close.iloc[:train_end], sig, cost_bps)
            score = sharpe_ratio(bt["strategy_return"].iloc[start:train_end])
            if score > best_score:
                best, best_score = params, score
        if best is None:
            continue
        sig = strategy(close.iloc[:test_end], **best)
        bt = vectorized_backtest(close.iloc[:test_end], sig, cost_bps)
        oos.append(bt["strategy_return"].iloc[train_end:test_end])
        chosen.append({"test_start": close.index[train_end], **best, "train_sharpe": best_score})
    if not oos:
        raise ValueError("series too short for the requested train/test windows")
    return pd.concat(oos), pd.DataFrame(chosen)
