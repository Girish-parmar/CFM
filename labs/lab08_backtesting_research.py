# %% [markdown]
# # Lab 8 — Backtesting and Research Methodology (Module 8)
#
# **Goals**
# 1. Price realistic Indian transaction costs and see how they change a strategy.
# 2. Watch in-sample optimisation overfit, and fix it with walk-forward testing.
# 3. Quantify data-snooping with the Deflated Sharpe Ratio.
# 4. Re-run a strategy in the event-driven engine and reconcile it with the vectorised result.

# %%
import numpy as np
import pandas as pd

from cfmat import backtest as bt
from cfmat import data, metrics, strategies
from cfmat.engine import SmaCrossStrategy, run_event_backtest

# %% [markdown]
# ## 1. What does a trade really cost?

# %%
model = bt.IndianCostModel()
examples = [("equity_delivery", 200, 1_500.0), ("equity_intraday", 200, 1_500.0),
            ("futures", 75, 24_500.0), ("options", 75, 120.0)]
rows = []
for segment, qty, price in examples:
    buy, sell = model.charges("buy", qty, price, segment), model.charges("sell", qty, price, segment)
    rows.append({"segment": segment, "turnover_one_side": buy["turnover"],
                 "total_charges": buy["total"] + sell["total"],
                 "round_trip_bps": model.round_trip_bps(qty, price, segment),
                 "stt_share": (buy["stt"] + sell["stt"]) / (buy["total"] + sell["total"])})
print(pd.DataFrame(rows).round(2).to_string(index=False))
print("\nOptions: charges are measured against premium, so the bps look huge — that is the point.")

close = data.ar1_prices(2000, phi=0.06, seed=17)
signal = strategies.time_series_momentum(close, 5)    # a fast, high-turnover rule
turnover = bt.vectorized_backtest(close, signal, 0)["turnover"].mean() * 252
print(f"\nFast momentum rule turns its book over ~{turnover:.0f}x a year:")
for cost in (0, 2, 5, 10, 20):
    res = bt.vectorized_backtest(close, signal, cost)
    print(f"cost {cost:>2} bps → Sharpe {metrics.sharpe_ratio(res['strategy_return']):5.2f}")

# %% [markdown]
# ## 2. In-sample optimisation vs walk-forward
# Search 36 SMA parameter pairs on a series with a weak trend.

# %%
grid = {"fast": [5, 10, 20, 30, 40, 50], "slow": [60, 80, 100, 150, 200, 250]}
split = 1000
in_sample = bt.grid_search(close.iloc[:split], strategies.sma_crossover, grid, cost_bps=5)
best = in_sample.iloc[0]
print("Top 5 in-sample:\n", in_sample.head().round(2).to_string(index=False))

best_sig = strategies.sma_crossover(close, int(best.fast), int(best.slow))
full = bt.vectorized_backtest(close, best_sig, 5)
print(f"\nBest in-sample Sharpe {best.sharpe:.2f} → same parameters out of sample: "
      f"{metrics.sharpe_ratio(full['strategy_return'].iloc[split:]):.2f}")

oos, chosen = bt.walk_forward(close, strategies.sma_crossover, grid, train=750, test=250, cost_bps=5)
print(f"Walk-forward out-of-sample Sharpe: {metrics.sharpe_ratio(oos):.2f}")
print(chosen.round({"train_sharpe": 2}).to_string(index=False))

# %% [markdown]
# ## 3. The Deflated Sharpe Ratio
# Generate 300 random long/short strategies on a *driftless* random walk. Any
# positive Sharpe is pure luck, yet the best one looks great.

# %%
rng = np.random.default_rng(0)
walk = data.gbm_prices(1000, mu=0.0, sigma=0.2, seed=3)
trial_returns = []
for _ in range(300):
    random_signal = pd.Series(rng.choice([-1.0, 1.0], len(walk)), index=walk.index).rolling(5).mean().fillna(0).round()
    trial_returns.append(bt.vectorized_backtest(walk, random_signal, 0)["strategy_return"])
sharpes = np.array([r.mean() / r.std() for r in trial_returns])
best_i = int(np.argmax(sharpes))
best_r = trial_returns[best_i]
print(f"Best of 300 random strategies: annualised Sharpe {metrics.sharpe_ratio(best_r):.2f}")
print(f"Probabilistic Sharpe (vs 0)  : {metrics.probabilistic_sharpe_ratio(best_r):.1%}  ← looks convincing")
print(f"Deflated Sharpe (300 trials) : {metrics.deflated_sharpe_ratio(best_r, 300, sharpes.var()):.1%}  ← the honest number")

# %% [markdown]
# ## 4. Event-driven engine vs vectorised backtest

# %%
bars = data.ohlcv_from_close(close.iloc[:750], seed=2)
table, broker = run_event_backtest(bars, SmaCrossStrategy(20, 100, qty=500), cash=100_000,
                                   cost_model=bt.IndianCostModel(), segment="equity_delivery")
vec = bt.vectorized_backtest(bars["close"], strategies.sma_crossover(bars["close"], 20, 100), 0)
print(f"Event-driven : {len(broker.fills)} fills, charges ₹{broker.total_charges:,.0f}, "
      f"final equity ₹{table['equity'].iloc[-1]:,.0f}")
print(f"Vectorised   : total return {vec['equity'].iloc[-1] - 1:.2%} (no costs, trades at close)")
print("Differences come from fills at the next open, slippage, statutory charges and position sizing.")

# %% [markdown]
# ## Exercises
# 1. Add the cost model's round-trip bps to the vectorised backtest automatically.
# 2. Plot the walk-forward chosen parameters over time. Are they stable?
# 3. Write down, before looking at any data, the full list of strategies you will
#    test for your capstone. That list is your `n_trials`.
