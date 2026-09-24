"""Futures strategies: contract calendar, rollover, lots, margin and basis trades (Module 17).

A futures position is not a stock position: it is sized in lots, needs margin,
expires every month and must be rolled into the next contract, paying charges
and crossing the calendar spread each time. ``backtest_futures`` handles all of
that; ``basis_trade`` implements the classic cash-and-carry arbitrage.

Expiry weekday, lot size and margin rates are set by exchange and broker
circulars and change over time: pass the current values as parameters.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..microstructure.costs import IndianCostModel


def monthly_expiries(index: pd.DatetimeIndex, weekday: int) -> pd.DatetimeIndex:
    """Last trading day of each month that falls on ``weekday`` (0 = Monday);
    if that weekday is a holiday, the trading day before it."""
    idx = pd.DatetimeIndex(index)
    out = []
    for _, days in pd.Series(idx, index=idx).groupby(idx.to_period("M")):
        days = pd.DatetimeIndex(days.to_numpy())
        month_end = days.max().to_period("M").to_timestamp(how="end").normalize()
        target = month_end - pd.Timedelta(days=(month_end.weekday() - weekday) % 7)
        eligible = days[days <= target]
        out.append(eligible.max() if len(eligible) else days.max())
    return pd.DatetimeIndex(out)


def weekly_expiries(index: pd.DatetimeIndex, weekday: int) -> pd.DatetimeIndex:
    """Every ``weekday`` in ``index`` (or the trading day before it, if a holiday)."""
    idx = pd.DatetimeIndex(index)
    weeks = idx.to_period("W-SUN")
    out = []
    for _, days in pd.Series(idx, index=idx).groupby(weeks):
        days = pd.DatetimeIndex(days.to_numpy())
        target = days.min() + pd.Timedelta(days=(weekday - days.min().weekday()) % 7)
        eligible = days[days <= target]
        out.append(eligible.max() if len(eligible) else days.max())
    return pd.DatetimeIndex(out)


def futures_curve(
    spot: pd.Series,
    r: float = 0.065,
    q: float = 0.012,
    expiry_weekday: int = 3,
    basis_noise_bps: float = 8.0,
    seed: int | None = None,
) -> pd.DataFrame:
    """Near- and next-month futures prices around a spot series.

    Fair value is S·e^((r−q)·days/365); a mean-reverting mispricing (in bp) is
    added so the basis trade has something to capture. The near contract
    converges to spot on its expiry day.
    """
    rng = np.random.default_rng(seed)
    idx = spot.index
    expiries = monthly_expiries(idx, expiry_weekday)
    pos = np.searchsorted(expiries.values, idx.values, side="left")
    last = expiries[-1]
    near = pd.DatetimeIndex([expiries[p] if p < len(expiries) else last + pd.DateOffset(months=1) for p in pos])
    nxt = pd.DatetimeIndex([expiries[p + 1] if p + 1 < len(expiries) else near[i] + pd.DateOffset(months=1)
                            for i, p in enumerate(pos)])
    dte_near = (near - idx).days.to_numpy()
    dte_next = (nxt - idx).days.to_numpy()
    noise = np.zeros((len(idx), 2))
    for t in range(1, len(idx)):
        noise[t] = 0.7 * noise[t - 1] + rng.normal(0, basis_noise_bps, 2)
    noise[dte_near == 0, 0] = 0.0
    s = spot.to_numpy(dtype=float)
    carry = r - q
    return pd.DataFrame({
        "spot": s,
        "near": s * np.exp(carry * dte_near / 365) * (1 + noise[:, 0] / 1e4),
        "next": s * np.exp(carry * dte_next / 365) * (1 + noise[:, 1] / 1e4),
        "near_expiry": near, "dte": dte_near, "is_expiry": dte_near == 0,
    }, index=idx)


def lots_for_capital(capital: float, price: float, lot_size: int, margin_rate: float, max_margin_use: float = 0.5) -> int:
    """Whole lots whose margin uses at most ``max_margin_use`` of capital."""
    return int(capital * max_margin_use // (price * lot_size * margin_rate))


def backtest_futures(
    curve: pd.DataFrame,
    target_lots: pd.Series,
    lot_size: int = 75,
    capital: float = 1_000_000.0,
    margin_rate: float = 0.12,
    cost_model: IndianCostModel | None = None,
    slippage_bps: float = 1.0,
) -> tuple[pd.DataFrame, dict]:
    """Hold ``target_lots`` (signed; decided and traded at each close) in the
    near contract, rolling open positions into the next contract on expiry day.

    Returns a daily table (lots, P&L, charges, equity, margin) and a summary.
    """
    cost_model = cost_model or IndianCostModel()
    target = target_lots.reindex(curve.index).fillna(0).round().astype(int).to_numpy()
    near, nxt, expiry = curve["near"].to_numpy(), curve["next"].to_numpy(), curve["is_expiry"].to_numpy()
    slip = slippage_bps / 1e4
    n = len(curve)
    lots, ref = 0, np.nan
    rows, rolls, total_charges, equity = [], 0, 0.0, capital

    def trade_cost(delta_lots: int, price: float) -> float:
        if delta_lots == 0:
            return 0.0
        side = "buy" if delta_lots > 0 else "sell"
        qty = abs(delta_lots) * lot_size
        return cost_model.charges(side, qty, price, "futures")["total"] + qty * price * slip

    for t in range(n):
        pnl = lots * lot_size * (near[t] - ref) if lots and not np.isnan(ref) else 0.0
        charges = 0.0
        price_now = near[t]
        if expiry[t] and lots:                           # roll: close expiring, reopen in next month
            charges += trade_cost(-lots, near[t]) + trade_cost(lots, nxt[t])
            rolls += 1
        if expiry[t]:
            price_now = nxt[t]                           # from here on we hold (or trade) the next contract
        charges += trade_cost(target[t] - lots, price_now)
        lots = int(target[t])
        ref = price_now
        equity += pnl - charges
        total_charges += charges
        margin = abs(lots) * lot_size * price_now * margin_rate
        rows.append({"lots": lots, "pnl": pnl, "charges": charges, "equity": equity, "margin": margin,
                     "margin_util": margin / equity if equity > 0 else np.inf})
    daily = pd.DataFrame(rows, index=curve.index)
    daily["return"] = daily["equity"].pct_change().fillna(daily["equity"].iloc[0] / capital - 1)
    summary = {"net_pnl": float(equity - capital), "return_on_capital": float(equity / capital - 1), "rolls": rolls,
               "charges": float(total_charges),
               "max_margin_util": float(daily["margin_util"].replace(np.inf, np.nan).max()),
               "margin_call_days": int((daily["margin_util"] > 1).sum())}
    return daily, summary


def basis_trade(
    curve: pd.DataFrame,
    r: float = 0.065,
    q: float = 0.012,
    lots: int = 1,
    lot_size: int = 75,
    entry_bps: float = 15.0,
    exit_bps: float = 3.0,
    allow_reverse: bool = False,
    cost_model: IndianCostModel | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cash-and-carry arbitrage on the near contract.

    When the future trades ``entry_bps`` above fair value, buy the underlying
    and sell the future; unwind when the mispricing falls below ``exit_bps`` or
    at expiry (convergence). ``allow_reverse`` also trades the opposite side
    (sell underlying, buy future), which needs stock borrowing in practice.
    Funding at ``r`` and dividends at ``q`` are charged on the cash leg.
    Returns (daily P&L table, trade list).
    """
    cost_model = cost_model or IndianCostModel()
    s, f, dte, expiry = (curve[c].to_numpy() for c in ("spot", "near", "dte", "is_expiry"))
    fair = s * np.exp((r - q) * dte / 365)
    mis = (f / fair - 1) * 1e4
    qty = lots * lot_size
    side, entry_i, trade_pnl = 0, 0, 0.0
    trades, rows = [], []
    for t in range(len(curve)):
        pnl = 0.0
        if side and t > 0:
            pnl = side * qty * ((s[t] - s[t - 1]) - (f[t] - f[t - 1]))          # long cash / short future when side = +1
            pnl -= side * qty * s[t - 1] * (r - q) / 365                         # funding minus dividends on the cash leg
        charges = 0.0
        if side and (abs(mis[t]) < exit_bps or expiry[t] or t == len(curve) - 1):
            charges += cost_model.charges("sell" if side > 0 else "buy", qty, s[t], "equity_delivery")["total"]
            charges += cost_model.charges("buy" if side > 0 else "sell", qty, f[t], "futures")["total"]
            trade_pnl += pnl - charges
            trades[-1].update({"exit_time": curve.index[t], "exit_bps": mis[t], "days": t - entry_i,
                               "reason": "expiry" if expiry[t] else "converged" if abs(mis[t]) < exit_bps else "end",
                               "pnl": trade_pnl})
            side = 0
        elif side:
            trade_pnl += pnl
        elif not expiry[t] and (mis[t] > entry_bps or (allow_reverse and mis[t] < -entry_bps)):
            side = 1 if mis[t] > 0 else -1
            entry_i = t
            charges += cost_model.charges("buy" if side > 0 else "sell", qty, s[t], "equity_delivery")["total"]
            charges += cost_model.charges("sell" if side > 0 else "buy", qty, f[t], "futures")["total"]
            trade_pnl = -charges
            trades.append({"entry_time": curve.index[t], "side": "cash-and-carry" if side > 0 else "reverse",
                           "entry_bps": mis[t], "notional": qty * s[t]})
        rows.append({"mispricing_bps": mis[t], "position": side, "pnl": pnl - charges, "charges": charges})
    return pd.DataFrame(rows, index=curve.index), pd.DataFrame(trades)
