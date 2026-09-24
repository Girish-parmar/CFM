# %% [markdown]
# # Lab 21 — Strategy Creator, Backtesting and Parallel Optimisation (Module 17)
#
# **Goals**
# 1. Browse the strategy library: trend up, trend down, both-way trend,
#    range-bound, either-way breakout and candlestick-pattern strategies.
# 2. Create your own strategy from indicators, parameters and patterns, save it
#    as JSON, and backtest it with a full trade-level report.
# 3. Optimise parameters in parallel (threads vs processes) and search smarter
#    (coarse-to-fine) instead of brute force.
# 4. Validate walk-forward and charge the result for the trials you ran.

# %%
import time

import pandas as pd

from cfmat import data, studio
from cfmat.analytics import metrics
from cfmat.backtesting import report
from cfmat.infra import parallel
from cfmat.infra.plotting import output_dir, savefig

pd.set_option("display.width", 180)
pd.set_option("display.max_columns", 14)
WORKERS = min(4, parallel.available_workers())

universe, meta = data.instrument_universe(40, n_days=1500, seed=7, start="2019-01-01")
trend_name = meta.index[meta["archetype"] == "uptrend"][0]
range_name = meta.index[meta["archetype"] == "range"][0]
bars = universe[trend_name]
print(f"Working instrument: {trend_name} ({len(bars)} bars); range example: {range_name}")

# %% [markdown]
# ## 1. The strategy library

# %%
for key, spec in studio.TEMPLATES.items():
    print(f"[{spec.category:<10}] {key:<24} {spec.name}")
spec = studio.TEMPLATES["range_bollinger_rsi"]
print("\nExample — range_bollinger_rsi rules:")
print("  long entry :", spec.long_entry)
print("  long exit  :", spec.long_exit)
print("  short entry:", spec.short_entry)
print("  stop / time:", spec.stop_atr, "ATR,", spec.max_bars, "bars;  parameters:", spec.params)
names = studio.available_functions()
print(f"\nThe rule language knows {len(names)} names, e.g.:", ", ".join(names[:20]), "…")

# %% [markdown]
# ## 2. Create a strategy: trend filter + pullback + candlestick confirmation

# %%
my_strategy = studio.StrategySpec(
    name="Uptrend pullback with bullish candle",
    category="custom",
    long_entry=[
        "close > sma({trend}) and sma(50) > sma({trend})",               # trend filter
        "recent(rsi({rsi_len}) < {oversold}, 3)",                         # a pullback in the last 3 bars
        "close > prev(high, 1) or bullish_engulfing or hammer",           # buyers are back
    ],
    # rules in a list are ANDed; use "or" inside one rule for either-or exits
    long_exit=["rsi({rsi_len}) > {overbought} or close > prev(highest(high, 10), 1)"],
    stop_atr="{stop}", max_bars=15,
    params={"trend": 100, "rsi_len": 5, "oversold": 35, "overbought": 70, "stop": 2.0},
    description="Buy short pullbacks in an established uptrend once buyers show up.",
)
path = output_dir() / "my_strategy.json"
my_strategy.to_json(path)
loaded = studio.StrategySpec.from_json(path)
print("Saved and reloaded:", loaded == my_strategy)

result = studio.backtest(bars, loaded, cost_bps=5, slippage_bps=2)
print(result.stats()[["cagr", "sharpe", "max_drawdown", "trades", "win_rate", "payoff_ratio",
                      "expectancy", "exposure", "max_consecutive_losses", "avg_bars"]].round(3).to_string())
print("\nLast trades:\n", result.trades.tail(5).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print("\nMonthly returns (%):\n", report.monthly_returns_table(result.returns).round(1).tail(3))
print("Chart saved to", savefig(report.plot_backtest(bars, result), "lab21_my_strategy"))

# %% [markdown]
# ## 3. One instrument, many strategies

# %%
results = {k: studio.backtest(bars, studio.TEMPLATES[k]) for k in
           ("trend_up_breakout", "trend_supertrend", "trend_ema_cross", "rsi2_pullback", "range_bollinger_rsi")}
results["my_strategy"] = result
print(f"On the uptrend {trend_name}:")
print(report.compare(results).round(3))
range_results = {k: studio.backtest(universe[range_name], studio.TEMPLATES[k]) for k in
                 ("trend_up_breakout", "range_bollinger_rsi", "range_box")}
print(f"\nOn the range-bound {range_name}:")
print(report.compare(range_results).round(3)[["cagr", "sharpe", "max_drawdown", "trades", "win_rate"]])

# %% [markdown]
# ## 4. Parameter sweep: serial vs threads vs processes

# %%
grid = {"entry": [10, 15, 20, 30, 40, 55], "exit": [5, 10, 15, 20], "adx_min": [15, 20, 25], "trend": [50, 100, 200]}
n_combos = len(studio.expand_grid(grid))
if __name__ == "__main__":        # process pools need this guard on Windows/macOS
    timings = {}
    for backend, workers in (("serial", 1), ("thread", WORKERS), ("process", WORKERS)):
        t0 = time.perf_counter()
        table = studio.sweep(bars, studio.TEMPLATES["trend_up_breakout"], grid, workers=workers, backend=backend)
        timings[backend] = time.perf_counter() - t0
    print(f"{n_combos} backtests:", {k: f"{v:.1f}s" for k, v in timings.items()})
    print(f"Speed-up with {WORKERS} processes: {timings['serial'] / timings['process']:.1f}x; "
          f"threads: {timings['serial'] / timings['thread']:.1f}x (the backtest loop holds Python's GIL)")
    print(table.head(5).round(3).to_string(index=False))

# %% [markdown]
# ## 5. Smarter search: coarse-to-fine

# %%
if __name__ == "__main__":
    t0 = time.perf_counter()
    smart, evaluations = studio.coarse_to_fine(bars, studio.TEMPLATES["trend_up_breakout"], grid, top_k=3,
                                           workers=WORKERS, backend="process")
    print(f"Coarse-to-fine: {evaluations} of {n_combos} combinations in {time.perf_counter() - t0:.1f}s")
    print(f"Best Sharpe — full grid {table['sharpe'].iloc[0]:.2f}, coarse-to-fine {smart['sharpe'].iloc[0]:.2f} "
          f"(rank {int((table['sharpe'] > smart['sharpe'].iloc[0]).sum()) + 1} of {n_combos} in the full grid)")
    best = studio.backtest(bars, studio.TEMPLATES["trend_up_breakout"].resolve(**{k: table.iloc[0][k] for k in grid}))
    trial_sr = table["sharpe"] / (252 ** 0.5)
    print(f"Deflated Sharpe of the grid winner ({n_combos} trials): "
          f"{metrics.deflated_sharpe_ratio(best.returns, n_combos, trial_sr.var()):.1%}")

# %% [markdown]
# ## 6. Walk-forward: optimise on the past, trade the future

# %%
if __name__ == "__main__":
    small_grid = {"entry": [10, 20, 40], "exit": [5, 10, 20], "trend": [50, 100, 200]}
    oos, chosen = studio.walk_forward(bars, studio.TEMPLATES["trend_up_breakout"], small_grid, train=500, test=250,
                                  workers=WORKERS, backend="process")
    print(chosen.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    print(f"\nWalk-forward out-of-sample Sharpe {metrics.sharpe_ratio(oos):.2f} vs best in-sample "
          f"{table['sharpe'].iloc[0]:.2f} — the honest number is the first one.")

# %% [markdown]
# ## Exercises
# 1. Write a *short* version of `my_strategy` for downtrends and test it on the
#    downtrend instruments from Lab 20.
# 2. Add your own indicator to the language with `@studio.register("my_indicator")`.
# 3. Time the sweep with 1, 2, 4 and 8 processes. Where does the speed-up flatten, and why?
