# %% [markdown]
# # Lab 7 — Algorithmic Trading Strategies (Module 7)
#
# **Goals**: implement and compare the main strategy families on the same data.
# 1. Trend following (SMA crossover, time-series momentum)
# 2. Mean reversion (Bollinger bands, RSI)
# 3. Cross-sectional momentum on a stock universe
# 4. Statistical arbitrage: a cointegrated pair
#
# Costs of 5 bps per unit turnover are applied throughout. Lab 8 shows why that
# number matters and how to avoid fooling yourself with parameter choices.

# %%
import matplotlib.pyplot as plt
import pandas as pd

from cfmat import backtest as bt
from cfmat import data, metrics, strategies
from cfmat.plotting import savefig

COST_BPS = 5
trend_series = data.ar1_prices(1500, phi=0.10, seed=5)     # has momentum
revert_series = data.ar1_prices(1500, phi=-0.15, seed=6)   # has short-term reversal

# %% [markdown]
# ## 1–2. Single-instrument strategies on two market "regimes"

# %%
candidates = {
    "buy & hold": lambda c: pd.Series(1.0, index=c.index),
    "SMA 20/100": lambda c: strategies.sma_crossover(c, 20, 100),
    "TS momentum 60d": lambda c: strategies.time_series_momentum(c, 60),
    "Bollinger MR": lambda c: strategies.bollinger_mean_reversion(c, 10, 1.5, 0.25),
    "RSI 2 reversal": lambda c: strategies.rsi_reversal(c, 2, 10, 90),
}
rows = []
curves = {}
for regime, close in (("trending", trend_series), ("mean-reverting", revert_series)):
    for name, fn in candidates.items():
        res = bt.vectorized_backtest(close, fn(close), COST_BPS)
        stats = metrics.performance_summary(res["strategy_return"])
        rows.append({"regime": regime, "strategy": name, "cagr": stats["cagr"], "sharpe": stats["sharpe"],
                     "max_dd": stats["max_drawdown"], "turnover/yr": res["turnover"].mean() * 252})
        if regime == "trending":
            curves[name] = res["equity"]
table = pd.DataFrame(rows).set_index(["regime", "strategy"])
print(table.round(2))
print("\nNo rule wins everywhere: reversal rules earn only when returns are negatively autocorrelated,")
print("momentum rules only when they are positively autocorrelated. Knowing your regime is the edge.")

fig, ax = plt.subplots(figsize=(10, 5))
pd.DataFrame(curves).plot(ax=ax, title="Equity curves — trending regime (after costs)")
print("Chart saved to", savefig(fig, "lab07_equity_curves"))

# %% [markdown]
# ## 3. Cross-sectional momentum on a 20-stock universe

# %%
universe = data.universe(20, 1500, seed=4)
weights = strategies.cross_sectional_momentum(universe, lookback=126, skip=21, top_n=5)
xs = bt.portfolio_backtest(universe, weights, COST_BPS)
equal = bt.portfolio_backtest(universe, pd.DataFrame(1 / 20, index=universe.index, columns=universe.columns), COST_BPS)
print(pd.DataFrame({
    "top-5 momentum": metrics.performance_summary(xs["strategy_return"].iloc[150:]),
    "equal weight": metrics.performance_summary(equal["strategy_return"].iloc[150:]),
}).loc[["cagr", "volatility", "sharpe", "max_drawdown"]].round(3))

# %% [markdown]
# ## 4. Pairs trading
# Formation period: estimate the hedge ratio. Trading period: fade z-score extremes.

# %%
pair = data.cointegrated_pair(1500, seed=8)
legs = strategies.pairs_signals(pair["y"], pair["x"], formation=250, window=30, entry_z=2.0, exit_z=0.5)
res = bt.pairs_backtest(pair["y"], pair["x"], legs, capital=1_000_000, cost_bps=COST_BPS)
trades = int((legs["y"].diff().abs() > 0).sum() // 2)
print(f"Hedge ratio {legs['beta'].iloc[0]:.3f}, ~{trades} round trips")
print(metrics.performance_summary(res["strategy_return"].iloc[250:])[["cagr", "sharpe", "max_drawdown", "hit_rate"]].round(3))
print(f"Net P&L ₹{res['net_pnl'].sum():,.0f} after ₹{res['cost'].sum():,.0f} of costs on ₹10 lakh gross")

fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
legs["zscore"].plot(ax=axes[0], title="Spread z-score")
for level in (-2, 2):
    axes[0].axhline(level, ls="--", c="grey")
res["equity"].plot(ax=axes[1], title="Pair equity")
print("Chart saved to", savefig(fig, "lab07_pairs"))

# %% [markdown]
# ## Exercises
# 1. Add a volatility filter: only trade the SMA strategy when 20-day vol < 30%.
# 2. Find two real NSE stocks from the same sector that pass the Engle–Granger test on
#    2019–2022 data and trade them on 2023–2025. Does the relationship survive?
# 3. Combine the trend and mean-reversion sleeves 50/50. What happens to drawdowns?
