"""Library of ready-made strategies expressed as ``StrategySpec`` rules (M12).

Categories: trend_up, trend_down, trend_both, range, either_way, pattern.
"""

from __future__ import annotations

from .spec import StrategySpec

TEMPLATES: dict[str, StrategySpec] = {
    "trend_up_breakout": StrategySpec(
        name="Trend up: Donchian breakout (long only)", category="trend_up",
        long_entry=["close > prev(highest(high, {entry}), 1)", "adx(14) > {adx_min}", "close > sma({trend})"],
        long_exit=["close < prev(lowest(low, {exit}), 1)"],
        trail_atr="{trail}", params={"entry": 20, "exit": 10, "adx_min": 20, "trend": 100, "trail": 3.0},
        description="Buy a 20-day high in an established uptrend; exit on a 10-day low or a 3-ATR trailing stop."),
    "trend_down_breakdown": StrategySpec(
        name="Trend down: Donchian breakdown (short only)", category="trend_down",
        short_entry=["close < prev(lowest(low, {entry}), 1)", "adx(14) > {adx_min}", "close < sma({trend})"],
        short_exit=["close > prev(highest(high, {exit}), 1)"],
        trail_atr="{trail}", params={"entry": 20, "exit": 10, "adx_min": 20, "trend": 100, "trail": 3.0},
        description="Short a 20-day low in an established downtrend (futures or F&O stocks); mirror of the breakout."),
    "trend_supertrend": StrategySpec(
        name="Trend both ways: Supertrend", category="trend_both",
        long_entry=["supertrend_dir({period}, {mult}) == 1", "adx(14) > {adx_min}"],
        long_exit=["supertrend_dir({period}, {mult}) == -1"],
        short_entry=["supertrend_dir({period}, {mult}) == -1", "adx(14) > {adx_min}"],
        short_exit=["supertrend_dir({period}, {mult}) == 1"],
        params={"period": 10, "mult": 3.0, "adx_min": 20},
        description="Long above the Supertrend line, short below it, only when ADX confirms a trend."),
    "trend_ema_cross": StrategySpec(
        name="Trend both ways: EMA crossover", category="trend_both",
        long_entry=["ema({fast}) > ema({slow})", "recent(cross_above(ema({fast}), ema({slow})), 3)"],
        long_exit=["cross_below(ema({fast}), ema({slow}))"],
        short_entry=["ema({fast}) < ema({slow})", "recent(cross_below(ema({fast}), ema({slow})), 3)"],
        short_exit=["cross_above(ema({fast}), ema({slow}))"],
        stop_atr=3.0, params={"fast": 20, "slow": 50}),
    "range_bollinger_rsi": StrategySpec(
        name="Range-bound: Bollinger + RSI reversion", category="range",
        long_entry=["adx(14) < {adx_max}", "close < bb_lower({n}, {k})", "rsi(14) < {rsi_low}"],
        long_exit=["close > bb_mid({n})"],
        short_entry=["adx(14) < {adx_max}", "close > bb_upper({n}, {k})", "rsi(14) > 100 - {rsi_low}"],
        short_exit=["close < bb_mid({n})"],
        stop_atr=2.0, max_bars=15, params={"n": 20, "k": 2.0, "adx_max": 20, "rsi_low": 35},
        description="Fade band extremes only when ADX says there is no trend."),
    "range_box": StrategySpec(
        name="Range-bound: buy support, sell resistance", category="range",
        long_entry=["er(20) < 0.3", "low <= lowest(low, {n}) * 1.005", "rsi(5) < 30"],
        long_exit=["high >= highest(high, {n}) * 0.99 or rsi(5) > 70"],
        short_entry=["er(20) < 0.3", "high >= highest(high, {n}) * 0.995", "rsi(5) > 70"],
        short_exit=["low <= lowest(low, {n}) * 1.01 or rsi(5) < 30"],
        stop_atr=1.5, max_bars=10, params={"n": 30}),
    "either_way_squeeze": StrategySpec(
        name="Either way: squeeze breakout", category="either_way",
        long_entry=["recent(squeeze({n}, {lookback}), {window})", "close > prev(highest(high, {n}), 1)"],
        short_entry=["recent(squeeze({n}, {lookback}), {window})", "close < prev(lowest(low, {n}), 1)"],
        stop_atr="{stop}", target_atr="{target}", max_bars=30,
        params={"n": 20, "lookback": 120, "window": 10, "stop": 1.5, "target": 4.0},
        description="After volatility compresses, trade the breakout in whichever direction it comes."),
    "either_way_atr_breakout": StrategySpec(
        name="Either way: ATR volatility breakout", category="either_way",
        long_entry=["close > prev(close, 1) + {k} * prev(atr(14), 1)"],
        short_entry=["close < prev(close, 1) - {k} * prev(atr(14), 1)"],
        trail_atr="{trail}", max_bars=20, params={"k": 1.5, "trail": 2.5}),
    "pattern_reversal": StrategySpec(
        name="Pattern: bullish candles at oversold levels", category="pattern",
        long_entry=["bullish_engulfing or hammer or morning_star or piercing_line", "rsi(14) < {rsi_max}", "close > sma(200)"],
        long_exit=["rsi(14) > 60"],
        stop_atr=1.5, max_bars=10, params={"rsi_max": 45}),
    "rsi2_pullback": StrategySpec(
        name="Pullback: RSI-2 in an uptrend", category="pattern",
        long_entry=["close > sma(200)", "rsi(2) < {oversold}"],
        long_exit=["close > sma(5)"],
        stop_atr=3.0, max_bars=10, params={"oversold": 10}),
}


def templates(category: str | None = None) -> dict[str, StrategySpec]:
    """Template strategies, optionally only one category."""
    return {k: v for k, v in TEMPLATES.items() if category is None or v.category == category}
