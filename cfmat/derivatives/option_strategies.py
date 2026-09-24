"""Option strategy backtester (Module 17).

Each cycle opens a multi-leg position on an entry date, re-prices every leg
daily with Black–Scholes at that day's implied volatility, tracks position
Greeks, and exits at a profit target, a stop-loss or expiry (cash-settled at
intrinsic value).

Strikes are placed in units of the *expected move* (IV × √T × spot) and
rounded to the strike step, so the same template works at any volatility level.

This is a teaching model: real backtests need historical option-chain prices
(bid/ask, skew, liquidity by strike). Margins here are rough approximations,
not exchange SPAN figures.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..microstructure.costs import IndianCostModel
from .options import bs_greeks, bs_price

# (kind, strike offset in expected moves, quantity per lot): negative quantity = short
OPTION_STRATEGIES: dict[str, list[tuple[str, float, int]]] = {
    "short_straddle": [("call", 0.0, -1), ("put", 0.0, -1)],
    "short_strangle": [("call", 1.0, -1), ("put", -1.0, -1)],
    "iron_condor": [("call", 1.0, -1), ("call", 1.6, 1), ("put", -1.0, -1), ("put", -1.6, 1)],
    "long_straddle": [("call", 0.0, 1), ("put", 0.0, 1)],
    "long_strangle": [("call", 0.8, 1), ("put", -0.8, 1)],
    "bull_call_spread": [("call", 0.0, 1), ("call", 1.0, -1)],
    "bear_put_spread": [("put", 0.0, 1), ("put", -1.0, -1)],
}

VIEW = {
    "short_straddle": "range-bound, falling volatility", "short_strangle": "range-bound, wide",
    "iron_condor": "range-bound, defined risk", "long_straddle": "big move either way / rising volatility",
    "long_strangle": "very big move either way", "bull_call_spread": "moderately bullish, defined risk",
    "bear_put_spread": "moderately bearish, defined risk",
}


@dataclass
class OptionsResult:
    trades: pd.DataFrame
    daily: pd.DataFrame

    def summary(self) -> dict[str, float]:
        t = self.trades
        if len(t) == 0:
            return {"trades": 0}
        pnl = t["pnl"]
        losses = pnl[pnl <= 0]
        return {
            "trades": len(t), "win_rate": float((pnl > 0).mean()), "total_pnl": float(pnl.sum()),
            "avg_pnl": float(pnl.mean()), "worst_trade": float(pnl.min()), "best_trade": float(pnl.max()),
            "profit_factor": float(pnl[pnl > 0].sum() / -losses.sum()) if losses.sum() < 0 else float("inf"),
            "avg_return_on_margin": float(t["return_on_margin"].mean()), "charges": float(t["charges"].sum()),
        }


def _strikes(legs, spot, iv, T, step):
    move = iv * np.sqrt(T)
    return [float(np.round(spot * np.exp(off * move) / step) * step) for _, off, _ in legs]


def _leg_iv(iv, spot, strike, skew):
    """Simple skew: implied vol rises as strikes fall (per unit of log-moneyness)."""
    return max(0.03, iv - skew * np.log(strike / spot))


def _value(kind, s, k, T, r, sigma, q):
    if T <= 0:
        return max(s - k, 0.0) if kind == "call" else max(k - s, 0.0)
    return bs_price(s, k, T, r, sigma, kind, q)


def backtest_options(
    spot: pd.Series,
    iv: pd.Series,
    strategy: str | list[tuple[str, float, int]],
    expiries: pd.DatetimeIndex,
    lot_size: int = 75,
    strike_step: float = 50.0,
    r: float = 0.065,
    q: float = 0.012,
    skew: float = 0.10,
    entry_days_before: int | None = None,
    entry_filter: pd.Series | None = None,
    profit_take: float | None = None,
    stop_loss: float | None = None,
    slippage_pct: float = 0.01,
    margin_rate: float = 0.12,
    cost_model: IndianCostModel | None = None,
) -> OptionsResult:
    """Backtest one option structure, one position per expiry cycle.

    Entry: the first trading day after the previous expiry, or the first day
    within ``entry_days_before`` calendar days of expiry. ``entry_filter`` (a
    boolean Series) must be True on the entry day. For credit trades
    ``profit_take`` / ``stop_loss`` are fractions / multiples of the credit; for
    debit trades, of the debit paid.
    """
    legs = OPTION_STRATEGIES[strategy] if isinstance(strategy, str) else strategy
    cost_model = cost_model or IndianCostModel()
    dates = spot.index
    s_arr, iv_arr = spot.to_numpy(float), iv.reindex(dates).ffill().to_numpy(float)
    expiries = pd.DatetimeIndex([e for e in expiries if dates[0] < e <= dates[-1]])
    trades, daily_rows = [], {}
    prev_exp = dates[0] - pd.Timedelta(days=1)

    def leg_charges(side, premium):
        return cost_model.charges(side, lot_size, max(premium, 0.05), "options")["total"]

    for expiry in expiries:
        window = dates[(dates > prev_exp) & (dates <= expiry)]
        prev_exp = expiry
        if entry_days_before is not None:
            window = window[(expiry - window).days <= entry_days_before]
        if len(window) < 2:
            continue
        entry = window[0]
        if entry_filter is not None and not bool(entry_filter.reindex([entry]).fillna(False).iloc[0]):
            continue
        i0 = dates.get_loc(entry)
        T0 = (expiry - entry).days / 365
        strikes = _strikes(legs, s_arr[i0], iv_arr[i0], T0, strike_step)
        entry_px = [_value(kind, s_arr[i0], k, T0, r, _leg_iv(iv_arr[i0], s_arr[i0], k, skew), q)
                    for (kind, _, _), k in zip(legs, strikes)]
        # pay the spread: buy a little higher, sell a little lower
        fills = [p * (1 + slippage_pct * np.sign(qty)) for p, (_, _, qty) in zip(entry_px, legs)]
        net = sum(qty * p for p, (_, _, qty) in zip(fills, legs)) * lot_size   # > 0 debit paid, < 0 credit received
        charges = sum(leg_charges("buy" if qty > 0 else "sell", p) for p, (_, _, qty) in zip(fills, legs))
        credit = -net if net < 0 else 0.0
        debit = net if net > 0 else 0.0
        max_loss = _max_loss(legs, strikes, net, lot_size)
        # Defined risk: block the worst-case loss. Undefined risk: a SPAN-like proxy of one
        # naked leg's margin (a short straddle or strangle loses on one side at a time) plus
        # the premium received, which the exchange also blocks.
        margin = max_loss if np.isfinite(max_loss) else margin_rate * s_arr[i0] * lot_size + credit
        reason, pnl, exit_date = "expiry", 0.0, expiry
        for j in range(i0, dates.get_loc(window[-1]) + 1):
            d = dates[j]
            T = max((expiry - d).days, 0) / 365
            vals, greeks = [], np.zeros(4)
            for (kind, _, qty), k in zip(legs, strikes):
                sig = _leg_iv(iv_arr[j], s_arr[j], k, skew)
                vals.append(_value(kind, s_arr[j], k, T, r, sig, q))
                if T > 0:
                    g = bs_greeks(s_arr[j], k, T, r, sig, kind, q)
                    greeks += qty * lot_size * np.array([g.delta, g.gamma, g.vega, g.theta])
            value = sum(qty * v for v, (_, _, qty) in zip(vals, legs)) * lot_size
            pnl = value - net
            row = daily_rows.setdefault(d, {"open_pnl": 0.0, "delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0})
            row["open_pnl"] += pnl
            for name, gv in zip(("delta", "gamma", "vega", "theta"), greeks):
                row[name] += gv
            if j == i0 or T == 0:
                continue
            basis = credit if credit else debit
            if profit_take is not None and pnl >= profit_take * basis:
                reason, exit_date = "profit target", d
                break
            if stop_loss is not None and pnl <= -stop_loss * basis:
                reason, exit_date = "stop loss", d
                break
        # closing trades pay the spread again; expiring options settle at intrinsic with no order
        if reason != "expiry":
            j = dates.get_loc(exit_date)
            T = (expiry - exit_date).days / 365
            exit_vals = [_value(kind, s_arr[j], k, T, r, _leg_iv(iv_arr[j], s_arr[j], k, skew), q)
                         for (kind, _, _), k in zip(legs, strikes)]
            exit_fills = [v * (1 - slippage_pct * np.sign(qty)) for v, (_, _, qty) in zip(exit_vals, legs)]
            pnl = sum(qty * v for v, (_, _, qty) in zip(exit_fills, legs)) * lot_size - net
            charges += sum(leg_charges("sell" if qty > 0 else "buy", v) for v, (_, _, qty) in zip(exit_fills, legs))
        pnl -= charges
        trades.append({
            "entry": entry, "expiry": expiry, "exit": exit_date, "reason": reason,
            "spot_entry": s_arr[i0], "iv_entry": iv_arr[i0], "strikes": "/".join(f"{k:.0f}" for k in strikes),
            "net_premium": -net, "margin": margin, "charges": charges, "pnl": pnl,
            "return_on_margin": pnl / margin if margin > 0 else np.nan,
        })
    trades_df = pd.DataFrame(trades)
    daily = pd.DataFrame.from_dict(daily_rows, orient="index").reindex(dates).fillna(0.0)
    if len(trades_df):
        realised = trades_df.set_index("exit")["pnl"].groupby(level=0).sum().reindex(dates).fillna(0.0).cumsum()
        daily["realised_pnl"] = realised
    return OptionsResult(trades_df, daily)


def _max_loss(legs, strikes, net, lot_size) -> float:
    """Worst-case loss at expiry across a wide grid of prices (inf if unbounded)."""
    grid = np.linspace(min(strikes) * 0.5, max(strikes) * 1.5, 2001)
    payoff = np.zeros_like(grid)
    for (kind, _, qty), k in zip(legs, strikes):
        payoff += qty * (np.maximum(grid - k, 0) if kind == "call" else np.maximum(k - grid, 0))
    pnl = payoff * lot_size - net
    edge_slope = (pnl[-1] - pnl[-2], pnl[1] - pnl[0])
    if edge_slope[0] < -1e-9 or edge_slope[1] > 1e-9:
        return float("inf")
    return float(max(0.0, -pnl.min()))


def _run_task(item: tuple[str, dict]) -> tuple[str, OptionsResult]:
    from ..infra.parallel import shared

    name, kwargs = item
    return name, backtest_options(shared("spot"), shared("iv"), **kwargs)


def run_many(
    spot: pd.Series, iv: pd.Series, configs: dict[str, dict], workers: int = 1, backend: str = "process"
) -> dict[str, OptionsResult]:
    """Backtest several option configurations in parallel.

    ``configs`` maps a label to keyword arguments for ``backtest_options``
    (``strategy``, ``expiries``, ``profit_take``…).
    """
    from ..infra.parallel import parallel_map

    out = parallel_map(_run_task, list(configs.items()), workers=workers, backend=backend,
                       shared={"spot": spot, "iv": iv})
    return dict(out)
