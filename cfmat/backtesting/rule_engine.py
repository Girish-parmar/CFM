"""Bar-by-bar execution of a ``StrategySpec`` with trade-level accounting (M12).

Execution model: rules are evaluated at each bar's close; orders fill at the
next bar's open (with slippage); protective stops and targets fill intrabar at
the stop/target price, or at the open if price gaps through them. When a stop
and a target are both touched in the same bar, the stop is assumed first.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..analytics import indicators as ind
from ..analytics.metrics import equity_curve
from ..strategies.rules import Evaluator
from ..strategies.spec import StrategySpec


@dataclass
class BacktestResult:
    """Outcome of a rule-engine backtest: daily returns, positions and the trade list."""
    spec: StrategySpec
    returns: pd.Series
    position: pd.Series
    trades: pd.DataFrame

    @property
    def equity(self) -> pd.Series:
        return equity_curve(self.returns)

    def stats(self) -> pd.Series:
        """Summary statistics of the backtest (see ``cfmat.backtesting.report.backtest_stats``)."""
        from .report import backtest_stats
        return backtest_stats(self)


def signals(bars: pd.DataFrame, spec: StrategySpec) -> pd.DataFrame:
    """Evaluate the four rule lists (AND within each list) at every close."""
    ev = Evaluator(bars)

    def all_of(rules):
        if not rules:
            return pd.Series(False, index=bars.index)
        out = ev.boolean(rules[0])
        for r in rules[1:]:
            out &= ev.boolean(r)
        return out

    return pd.DataFrame({"long_entry": all_of(spec.long_entry), "long_exit": all_of(spec.long_exit),
                         "short_entry": all_of(spec.short_entry), "short_exit": all_of(spec.short_exit)})


def backtest(
    bars: pd.DataFrame,
    spec: StrategySpec,
    cost_bps: float = 5.0,
    slippage_bps: float = 2.0,
    size: float = 1.0,
    allow_reverse: bool = True,
) -> BacktestResult:
    """Run ``spec`` bar by bar. Returns daily returns (fraction of capital, with
    ``size`` × capital notional per position), positions and a trade list."""
    spec = spec.resolve()
    sig = signals(bars, spec)
    le, lx = sig["long_entry"].to_numpy(), sig["long_exit"].to_numpy()
    se, sx = sig["short_entry"].to_numpy(), sig["short_exit"].to_numpy()
    o, h, l, c = (bars[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    a = ind.atr(bars, spec.atr_period).to_numpy()
    idx = bars.index
    n = len(bars)
    cost, slip = cost_bps / 1e4, slippage_bps / 1e4
    stop_dist = spec.stop_atr if spec.stop_atr is not None else spec.trail_atr

    ret = np.zeros(n)
    held = np.zeros(n)
    trades = []
    pos, entry_px, entry_i, stop, target = 0, 0.0, 0, None, None
    pending = None

    def close_trade(i, px, reason):
        trades.append({"side": "long" if pos == 1 else "short", "entry_time": idx[entry_i], "entry_price": entry_px,
                       "exit_time": idx[i], "exit_price": px, "bars": i - entry_i + 1,
                       "return": pos * (px / entry_px - 1) - 2 * cost, "reason": reason})

    for i in range(n):
        ref = c[i - 1] if i > 0 else o[i]
        day = 0.0
        if pending is not None:
            kind, arg = pending
            pending = None
            if pos != 0:                                   # exit (or first leg of a reversal) at the open
                px = o[i] * (1 - slip * pos)
                day += pos * (px / ref - 1) - cost
                close_trade(i, px, arg if kind == "exit" else "reverse")
                pos = 0
            if kind in ("enter", "reverse"):
                side = arg if kind == "enter" else -held[i - 1]
                px = o[i] * (1 + slip * side)
                pos, entry_px, entry_i, ref = int(side), px, i, px
                day -= cost
                atr_then = a[i - 1] if i > 0 else np.nan
                stop = px - side * stop_dist * atr_then if stop_dist is not None and not np.isnan(atr_then) else None
                target = (px + side * spec.target_atr * atr_then
                          if spec.target_atr is not None and not np.isnan(atr_then) else None)
        if pos != 0:
            hit_stop = stop is not None and ((pos == 1 and l[i] <= stop) or (pos == -1 and h[i] >= stop))
            hit_target = target is not None and ((pos == 1 and h[i] >= target) or (pos == -1 and l[i] <= target))
            if hit_stop or hit_target:
                if hit_stop:
                    level, reason = stop, "stop"
                    px = min(o[i], level) if pos == 1 else max(o[i], level)
                else:
                    level, reason = target, "target"
                    px = max(o[i], level) if pos == 1 else min(o[i], level)
                if i == entry_i:                           # entered at this open: can't fill beyond it
                    px = level
                px *= 1 - slip * pos
                day += pos * (px / ref - 1) - cost
                close_trade(i, px, reason)
                pos, stop, target = 0, None, None
        if pos != 0:
            day += pos * (c[i] / ref - 1)
            if spec.trail_atr is not None and not np.isnan(a[i]):
                trail = c[i] - pos * spec.trail_atr * a[i]
                stop = trail if stop is None else (max(stop, trail) if pos == 1 else min(stop, trail))
        ret[i] = day * size
        held[i] = pos
        if i == n - 1:
            break
        if pos == 1:
            if allow_reverse and se[i]:
                pending = ("reverse", None)
            elif lx[i]:
                pending = ("exit", "signal")
            elif spec.max_bars and i - entry_i + 1 >= spec.max_bars:
                pending = ("exit", "time")
        elif pos == -1:
            if allow_reverse and le[i]:
                pending = ("reverse", None)
            elif sx[i]:
                pending = ("exit", "signal")
            elif spec.max_bars and i - entry_i + 1 >= spec.max_bars:
                pending = ("exit", "time")
        elif le[i] != se[i]:
            pending = ("enter", 1 if le[i] else -1)
    if pos != 0:
        close_trade(n - 1, c[-1], "end of data")
    trade_cols = ["side", "entry_time", "entry_price", "exit_time", "exit_price", "bars", "return", "reason"]
    return BacktestResult(spec, pd.Series(ret, index=idx, name="strategy_return"),
                          pd.Series(held, index=idx, name="position"), pd.DataFrame(trades, columns=trade_cols))
