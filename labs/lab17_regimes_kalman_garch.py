# %% [markdown]
# # Lab 17 — Regime Switching, Kalman-Filter Pairs and GARCH Volatility (Module 16)
#
# **Goals**
# 1. Detect market regimes with a Markov-switching model and trade on them,
#    using the *filtered* probability (no look-ahead) rather than the smoothed one.
# 2. Forecast volatility with GARCH(1,1) and run a volatility-managed strategy.
# 3. Trade a pair whose hedge ratio drifts, with a Kalman filter instead of a
#    fixed or rolling regression.

# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cfmat import advanced as adv
from cfmat import backtest as bt
from cfmat import data, metrics, risk, strategies
from cfmat.plotting import savefig

pd.set_option("display.width", 160)
COST_BPS = 5


def summary(returns: pd.Series) -> dict:
    s = metrics.performance_summary(returns)
    return {"cagr": s["cagr"], "vol": s["volatility"], "sharpe": s["sharpe"], "max_dd": s["max_drawdown"]}


# %% [markdown]
# ## 1. Markov-switching regimes
# A calm, rising regime alternates with a turbulent, falling one. Fit the model on
# the first half, then run the filter through everything.

# %%
market = data.regime_prices(2500, seed=5)             # 'regime' column = truth, for grading only
rets = metrics.simple_returns(market["close"])
train_end = 1250
params = adv.fit_markov_regimes(rets.iloc[:train_end])
filtered = adv.markov_regime_probabilities(rets, params)
smoothed = adv.markov_regime_probabilities(rets, params, smoothed=True)
truth = market["regime"].reindex(filtered.index)
print(f"Estimated volatility: calm {filtered['vol_calm'].iloc[0]:.1%}, turbulent {filtered['vol_turbulent'].iloc[0]:.1%} "
      "(true 12% / 35%)")
print(f"Regime accuracy — filtered: {((filtered.p_turbulent > 0.5) == truth).mean():.1%}, "
      f"smoothed: {((smoothed.p_turbulent > 0.5) == truth).mean():.1%}")

test = filtered.index[train_end:]
close = market["close"].reindex(filtered.index)
risk_off_filtered = (filtered.p_turbulent < 0.5).astype(float)
risk_off_smoothed = (smoothed.p_turbulent < 0.5).astype(float)
table = pd.DataFrame({
    "buy & hold": summary(bt.vectorized_backtest(close, pd.Series(1.0, index=close.index), COST_BPS)["strategy_return"].loc[test]),
    "regime filter (filtered, honest)": summary(bt.vectorized_backtest(close, risk_off_filtered, COST_BPS)["strategy_return"].loc[test]),
    "regime filter (smoothed, LOOK-AHEAD)": summary(bt.vectorized_backtest(close, risk_off_smoothed, COST_BPS)["strategy_return"].loc[test]),
}).T
print(table.round(3))
print("The smoothed row is what a careless backtest reports. It uses future returns to label today.")

fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
close.plot(ax=axes[0], title="Price", logy=True)
filtered["p_turbulent"].plot(ax=axes[1], label="filtered (tradable)")
smoothed["p_turbulent"].plot(ax=axes[1], label="smoothed (look-ahead)", alpha=0.6)
axes[1].set_title("Probability of the turbulent regime")
axes[1].legend()
print("Chart saved to", savefig(fig, "lab17_regimes"))

# %% [markdown]
# ## 2. GARCH(1,1): does the estimator recover known parameters?

# %%
g = data.garch_prices(3000, omega=2e-6, alpha=0.08, beta=0.90, seed=7)
g_rets = metrics.simple_returns(g["close"])
fit = adv.garch11_fit(g_rets)
print(f"alpha {fit['alpha']:.3f} (true 0.080), beta {fit['beta']:.3f} (true 0.900), "
      f"long-run vol {fit['long_run_vol']:.1%} (true {np.sqrt(2e-6 / 0.02 * 252):.1%})")
forecast = adv.garch11_forecast(g_rets, fit)
true_next = g["sigma"].reindex(g_rets.index).shift(-1)
print(f"Correlation of the GARCH forecast with the true next-day volatility: {forecast.corr(true_next):.3f}")

# %% [markdown]
# ### Volatility-managed exposure on the regime market
# Scale exposure to a 12% volatility target using (a) 20-day realised volatility
# and (b) a GARCH forecast fitted on the training half only.

# %%
garch_params = adv.garch11_fit(rets.iloc[:train_end])
w_garch = adv.vol_target_weights(adv.garch11_forecast(rets, garch_params), target_vol=0.12)
w_real = risk.volatility_target_leverage(rets, target_vol=0.12, lookback=20)
vol_table = pd.DataFrame({
    "buy & hold": table.loc["buy & hold"],
    "realised-vol target": summary(bt.vectorized_backtest(close, w_real, COST_BPS)["strategy_return"].loc[test]),
    "GARCH vol target": summary(bt.vectorized_backtest(close, w_garch, COST_BPS)["strategy_return"].loc[test]),
    "GARCH vol target × regime filter": summary(
        bt.vectorized_backtest(close, w_garch * risk_off_filtered, COST_BPS)["strategy_return"].loc[test]),
}).T
print(vol_table.round(3))
print("Vol management pays when high volatility comes with poor returns (as here, and often in real markets).")

# %% [markdown]
# ## 3. Kalman-filter pairs trading with a drifting hedge ratio

# %%
pair = data.drifting_pair(1500, beta_start=1.2, beta_end=1.9, seed=2)
static = strategies.pairs_signals(pair["y"], pair["x"], formation=250, window=30)
rolling_beta = strategies.rolling_hedge_ratio(pair["y"], pair["x"], 120)
kal = adv.kalman_pairs_signals(pair["y"], pair["x"], delta=1e-6, obs_var=10.0, entry_z=1.5)
after = pair.index[250:]
print("Mean absolute hedge-ratio error after the formation year:")
print(f"  fixed OLS {(static['beta'] - pair['true_beta']).abs().loc[after].mean():.3f} | "
      f"rolling 120d OLS {(rolling_beta - pair['true_beta']).abs().loc[after].mean():.3f} | "
      f"Kalman {(kal['beta'] - pair['true_beta']).abs().loc[after].mean():.3f}")

x_rets = pair["x"].pct_change()
rows = {}
for name, legs in {"fixed-beta pair": static, "Kalman pair": kal}.items():
    res = bt.pairs_backtest(pair["y"], pair["x"], legs, capital=1_000_000, cost_bps=COST_BPS)
    r = res["strategy_return"].loc[after]
    exposure = np.polyfit(x_rets.loc[after].fillna(0), r, 1)[0]
    rows[name] = {**summary(r), "exposure_to_x": exposure, "net_pnl_lakh": res["net_pnl"].loc[after].sum() / 1e5}
print(pd.DataFrame(rows).T.round(3))
print("A good hedge leaves little exposure to x: the P&L should come from the spread, not the market.")

fig, ax = plt.subplots(figsize=(9, 4))
pair["true_beta"].plot(ax=ax, label="true", lw=2, c="black")
static["beta"].plot(ax=ax, label="fixed OLS (formation year)")
rolling_beta.plot(ax=ax, label="rolling 120d OLS", alpha=0.6)
kal["beta"].plot(ax=ax, label="Kalman")
ax.set(title="Hedge-ratio estimates", ylim=(0.5, 2.5))
ax.legend()
print("Chart saved to", savefig(fig, "lab17_kalman_beta"))

# %% [markdown]
# ## Exercises
# 1. Add a third regime to the Markov model. Does the BIC justify it?
# 2. Replace GARCH(1,1) with GJR-GARCH (asymmetric response to negative returns)
#    and compare forecast accuracy on real Nifty data.
# 3. Tune the Kalman `delta` by walk-forward rather than by eye, and report how many
#    values you tried.
