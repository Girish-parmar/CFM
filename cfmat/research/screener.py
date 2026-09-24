"""Screeners and analytics for instrument selection (M12).

Workflow:

    table = screen(universe, workers=4)            # metrics for every instrument
    table.query(PRESETS["trend_up"])                # or any custom filter string
    ranked = rank(table, {"ret_6m": 1, "vol_60": -0.5})
    picks = diversify(returns, ranked.index, n=8, max_corr=0.6)

``classify`` labels each instrument's current regime (trending up / down,
range-bound, squeeze, volatile) and ``suggest_strategies`` maps the label to
strategy templates, so the screener feeds the Strategy Creator directly.

All metrics use data up to the last bar only. Filters are pandas ``query``
strings; they are meant for your own research notebook, not for text typed by
untrusted users.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..analytics import indicators as ind
from ..analytics import patterns as pat
from ..analytics.metrics import max_drawdown
from ..infra.parallel import parallel_map, shared

PRESETS: dict[str, str] = {
    "liquid": "turnover_cr >= 5",
    "trend_up": "trend_slope_1y > 0.15 and trend_r2_1y > 0.4 and close > sma_50 and vol_20 < 0.45",
    "trend_down": "trend_slope_1y < -0.15 and trend_r2_1y > 0.4 and close < sma_50 and vol_20 < 0.45",
    "range_bound": "trend_r2_1y < 0.25 and er_60 < 0.3 and bb_width_pctile > 0.10 and vol_20 < 0.45",
    "squeeze": "bb_width_pctile <= 0.10",
    "high_volatility": "vol_20 >= 0.45",
    "near_52w_high": "dist_52w_high >= -0.05",
    "oversold_in_uptrend": "close > sma_200 and rsi_14 < 35",
    "momentum_leaders": "ret_6m > 0.15 and close > sma_200",
}

STRATEGY_FIT = {
    "trending_up": ["trend_up_breakout", "rsi2_pullback", "trend_supertrend", "options: bull_call_spread"],
    "trending_down": ["trend_down_breakdown", "trend_supertrend", "options: bear_put_spread"],
    "range_bound": ["range_bollinger_rsi", "range_box", "options: iron_condor", "options: short_strangle"],
    "squeeze": ["either_way_squeeze", "options: long_straddle"],
    "volatile": ["either_way_atr_breakout", "reduce size / avoid"],
    "mixed": ["no clear edge: wait, or trade smaller"],
}


def trend_fit(close: pd.Series, window: int = 250) -> tuple[float, float]:
    """Annualised slope and R² of a straight line fitted to the last ``window``
    log prices. A high R² with a large slope is a persistent trend; a random walk
    can also produce a high R² by chance, so combine it with other evidence."""
    y = np.log(close.iloc[-window:].to_numpy(dtype=float))
    if len(y) < window // 2:
        return float("nan"), float("nan")
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    resid = y - (slope * x + intercept)
    r2 = 1 - resid.var() / y.var() if y.var() > 0 else 0.0
    return float(np.exp(slope * 252) - 1), float(r2)


def instrument_metrics(bars: pd.DataFrame, benchmark_returns: pd.Series | None = None) -> dict[str, float]:
    """Screening metrics for one instrument, as of its last bar."""
    close, high, low = bars["close"], bars["high"], bars["low"]
    rets = close.pct_change()
    last = lambda s: float(s.iloc[-1]) if len(s) and pd.notna(s.iloc[-1]) else float("nan")  # noqa: E731
    sma50, sma200 = close.rolling(50).mean(), close.rolling(200).mean()
    dmi = ind.adx(bars, 14)
    bw = ind.bollinger_bandwidth(close, 20)
    year = close.iloc[-252:]
    turnover = (close * bars["volume"]).rolling(20).mean() / 1e7 if "volume" in bars else pd.Series(np.nan, index=bars.index)
    out = {
        "close": last(close),
        "ret_1m": last(close.pct_change(21)), "ret_3m": last(close.pct_change(63)),
        "ret_6m": last(close.pct_change(126)), "ret_12m": last(close.pct_change(252)),
        "sma_50": last(sma50), "sma_200": last(sma200),
        "sma50_slope": last(sma50 / sma50.shift(20) - 1),
        "dist_52w_high": last(close / high.rolling(252, min_periods=20).max() - 1),
        "dist_52w_low": last(close / low.rolling(252, min_periods=20).min() - 1),
        "vol_20": last(rets.rolling(20).std() * np.sqrt(252)),
        "vol_60": last(rets.rolling(60).std() * np.sqrt(252)),
        "atr_pct": last(ind.atr(bars, 14) / close),
        "adx": last(dmi["adx"]), "plus_di": last(dmi["plus_di"]), "minus_di": last(dmi["minus_di"]),
        "rsi_14": last(ind.rsi(close, 14)),
        "er_60": last(ind.efficiency_ratio(close, 60)),
        "hurst": ind.hurst_exponent(np.log(year.to_numpy())) if len(year) > 100 else float("nan"),
        "bb_width_pctile": last(bw.rolling(252, min_periods=60).rank(pct=True)),
        "range_60": last((high.rolling(60).max() - low.rolling(60).min()) / close),
        "turnover_cr": last(turnover),
        "amihud": float((rets.abs() / turnover.replace(0, np.nan)).iloc[-60:].mean() * 1e4) if "volume" in bars else float("nan"),
        "max_dd_1y": max_drawdown(year / year.iloc[0]) if len(year) > 1 else float("nan"),
    }
    out["trend_slope_1y"], out["trend_r2_1y"] = trend_fit(close, 250)
    if benchmark_returns is not None:
        joined = pd.concat([rets, benchmark_returns], axis=1, join="inner").dropna().iloc[-252:]
        if len(joined) > 60:
            cov = np.cov(joined.iloc[:, 0], joined.iloc[:, 1])
            out["beta_1y"] = float(cov[0, 1] / cov[1, 1])
            out["corr_1y"] = float(joined.corr().iloc[0, 1])
    return out


def classify(row: pd.Series) -> str:
    """Current regime from screener metrics (a rule of thumb, not a forecast).

    Order matters: a volatility squeeze first, then very high volatility, then a
    persistent one-year trend, then range-bound behaviour.
    """
    if row["bb_width_pctile"] <= 0.10 and row["adx"] < 30:
        return "squeeze"
    if row["vol_20"] >= 0.45:
        return "volatile"
    if row["trend_r2_1y"] >= 0.4 and abs(row["trend_slope_1y"]) >= 0.15:
        if row["trend_slope_1y"] > 0 and row["close"] > row["sma_50"]:
            return "trending_up"
        if row["trend_slope_1y"] < 0 and row["close"] < row["sma_50"]:
            return "trending_down"
    if row["trend_r2_1y"] < 0.25 and row["er_60"] < 0.3:
        return "range_bound"
    return "mixed"


def _metrics_task(symbol: str) -> dict:
    universe, bench = shared("universe"), shared("benchmark")
    return {"symbol": symbol, **instrument_metrics(universe[symbol], bench)}


def equal_weight_index(universe: dict[str, pd.DataFrame]) -> pd.Series:
    """Daily returns of an equal-weight index of the universe (a benchmark proxy)."""
    return pd.DataFrame({s: b["close"].pct_change() for s, b in universe.items()}).mean(axis=1)


def screen(
    universe: dict[str, pd.DataFrame],
    benchmark_returns: pd.Series | None = None,
    workers: int = 1,
    backend: str = "process",
) -> pd.DataFrame:
    """Metrics, regime and suggested strategies for every instrument."""
    bench = equal_weight_index(universe) if benchmark_returns is None else benchmark_returns
    rows = parallel_map(_metrics_task, list(universe), workers=workers, backend=backend,
                        shared={"universe": universe, "benchmark": bench})
    table = pd.DataFrame(rows).set_index("symbol")
    table["regime"] = table.apply(classify, axis=1)
    table["suggested"] = table["regime"].map(lambda r: ", ".join(STRATEGY_FIT[r][:2]))
    return table


def apply_filters(table: pd.DataFrame, filters: list[str] | str) -> pd.DataFrame:
    """Keep rows that pass every filter (preset names or pandas query strings)."""
    out = table
    for f in [filters] if isinstance(filters, str) else filters:
        out = out.query(PRESETS.get(f, f), engine="python")
    return out


def rank(table: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """Composite score = Σ weight × z-score(column). Negative weight = lower is better."""
    score = pd.Series(0.0, index=table.index)
    for col, w in weights.items():
        x = table[col].astype(float)
        score += w * ((x - x.mean()) / x.std(ddof=0)).fillna(0.0)
    return table.assign(score=score).sort_values("score", ascending=False)


def pattern_scan(universe: dict[str, pd.DataFrame], names: list[str] | None = None, lookback: int = 1) -> pd.DataFrame:
    """Which patterns fired in the last ``lookback`` bars, per instrument."""
    rows = {}
    for symbol, bars in universe.items():
        found = pat.scan(bars, names).iloc[-lookback:].any()
        rows[symbol] = found
    table = pd.DataFrame(rows).T
    return table.loc[table.any(axis=1)]


def diversify(returns: pd.DataFrame, candidates: list[str] | pd.Index, n: int = 10, max_corr: float = 0.7,
              lookback: int = 252) -> list[str]:
    """Walk down a ranked candidate list and keep names whose correlation with
    every name already kept is below ``max_corr``."""
    corr = returns.iloc[-lookback:].corr()
    picked: list[str] = []
    for sym in candidates:
        if all(abs(corr.loc[sym, p]) < max_corr for p in picked):
            picked.append(sym)
        if len(picked) == n:
            break
    return picked
