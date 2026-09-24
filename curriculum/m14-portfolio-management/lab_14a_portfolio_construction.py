# %% [markdown]
# # Lab 14a — Portfolio Construction and Allocation Across Strategies (M14)
#
# **Goals**
# 1. Compare equal-weight, minimum-variance, max-Sharpe, risk-parity and HRP portfolios
#    *out of sample* with a rolling estimate-then-hold loop.
# 2. Reduce estimation error with Ledoit–Wolf covariance shrinkage.
# 3. Draw the efficient frontier and see how unstable its tangency point is.
# 4. Allocate capital across strategy sleeves (trend, reversal, pairs) with weights that use
#    only past data.

# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf

from cfmat import data, portfolio, strategies
from cfmat.analytics import metrics
from cfmat.backtesting import vectorized as bt
from cfmat.infra.plotting import savefig

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 12)

prices = data.universe(10, 1500, seed=30)
rets = metrics.simple_returns(prices)

# %% [markdown]
# ## 1. Portfolio construction, tested out of sample
# Estimate on 3 years, hold for the next year, roll forward.

# %%
def lw_cov(r: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(LedoitWolf().fit(r).covariance_ * 252, index=r.columns, columns=r.columns)


methods = {
    "equal weight": lambda r: pd.Series(1 / r.shape[1], index=r.columns),
    "min variance": lambda r: portfolio.min_variance_weights(r.cov() * 252),
    "min variance (Ledoit–Wolf)": lambda r: portfolio.min_variance_weights(lw_cov(r)),
    "max Sharpe": lambda r: portfolio.max_sharpe_weights(r.mean() * 252, r.cov() * 252, rf=0.065),
    "risk parity": lambda r: portfolio.risk_parity_weights(r.cov() * 252),
    "HRP": portfolio.hrp_weights,
}
train, test = 750, 250
oos = {name: [] for name in methods}
turnover = {name: [] for name in methods}
previous = {}
for start in range(0, len(rets) - train - test + 1, test):
    est = rets.iloc[start:start + train]
    hold = rets.iloc[start + train:start + train + test]
    for name, fn in methods.items():
        w = fn(est)
        oos[name].append(hold @ w)
        if name in previous:
            turnover[name].append((w - previous[name]).abs().sum())
        previous[name] = w
summary = pd.DataFrame({name: metrics.performance_summary(pd.concat(parts)) for name, parts in oos.items()}).T
summary["turnover_per_rebalance"] = [np.mean(turnover[n]) for n in summary.index]
print(summary[["cagr", "volatility", "sharpe", "max_drawdown", "turnover_per_rebalance"]].round(3))

w_hrp = portfolio.hrp_weights(rets)
w_mv = portfolio.min_variance_weights(rets.cov() * 252)
w_ms = portfolio.max_sharpe_weights(rets.mean() * 252, rets.cov() * 252, rf=0.065)
print("\nWeights (full sample):")
print(pd.DataFrame({"HRP": w_hrp, "min variance": w_mv, "max Sharpe": w_ms}).round(3).T)
print("\nMax-Sharpe weights depend on noisy mean estimates: watch how concentrated and unstable they are.")

# %% [markdown]
# ## 2. The efficient frontier and the instability of its tangency portfolio
# Re-estimate expected returns on two halves of the sample and compare the max-Sharpe weights.

# %%
frontier = portfolio.efficient_frontier(rets.mean() * 252, rets.cov() * 252, n_points=25)
half = len(rets) // 2
w_first = portfolio.max_sharpe_weights(rets.iloc[:half].mean() * 252, rets.iloc[:half].cov() * 252, rf=0.065)
w_second = portfolio.max_sharpe_weights(rets.iloc[half:].mean() * 252, rets.iloc[half:].cov() * 252, rf=0.065)
print(pd.DataFrame({"first half": w_first, "second half": w_second}).round(2).T)
print(f"Share of the portfolio that changes between halves: {(w_first - w_second).abs().sum() / 2:.0%}")

fig, ax = plt.subplots(figsize=(7, 5))
ax.plot(frontier["volatility"], frontier["return"], marker=".", label="efficient frontier (full sample)")
vols = rets.std() * np.sqrt(252)
ax.scatter(vols, rets.mean() * 252, c="grey", label="single stocks")
ax.set(xlabel="volatility", ylabel="expected return", title="Efficient frontier")
ax.legend()
print("Chart saved to", savefig(fig, "lab14a_frontier"))

# %% [markdown]
# ## 3. Allocating across strategy sleeves
# Three simple strategies from Module 10, each on its own market, combined with weights
# re-estimated every month from the previous six months only.

# %%
n, start_date, cost = 1500, "2019-01-01", 5
trend_px = data.gbm_prices(n, mu=0.12, sigma=0.22, seed=3, start=start_date)
revert_px = data.ar1_prices(n, phi=-0.15, seed=6, start=start_date)
pair = data.cointegrated_pair(n, seed=2, start=start_date)
sleeves = pd.DataFrame({
    "trend": bt.vectorized_backtest(trend_px, strategies.time_series_momentum(trend_px, 60), cost)["strategy_return"],
    "reversal": bt.vectorized_backtest(revert_px, strategies.rsi_reversal(revert_px, 2, 10, 90), cost)["strategy_return"],
    "pairs": bt.pairs_backtest(pair["y"], pair["x"], strategies.pairs_signals(pair["y"], pair["x"], formation=250, window=30),
                               capital=1_000_000, cost_bps=cost)["strategy_return"],
}).fillna(0.0)
live = sleeves.index[300:]            # after every sleeve's warm-up
print("Sleeve correlations:\n", sleeves.loc[live].corr().round(2))

combos = {}
for method in ("equal", "inverse_vol", "risk_parity", "hrp"):
    w = portfolio.rolling_allocation(sleeves, method=method, lookback=126, rebalance=21)
    combos[method] = portfolio.allocation_returns(sleeves, w)


def stats(r: pd.Series) -> dict:
    return {"cagr": metrics.cagr(r), "vol": metrics.annualized_volatility(r), "sharpe": metrics.sharpe_ratio(r),
            "max_dd": metrics.max_drawdown(metrics.equity_curve(r))}


table = pd.DataFrame({**{f"sleeve: {c}": stats(sleeves.loc[live, c]) for c in sleeves},
                      **{f"portfolio: {m}": stats(r.loc[live]) for m, r in combos.items()}}).T
print(table.round(3))
print("\nCombining imperfectly correlated sleeves lifts the Sharpe ratio above most single sleeves.")

w_rp = portfolio.rolling_allocation(sleeves, method="risk_parity", lookback=126, rebalance=21)
fig, axes = plt.subplots(2, 1, figsize=(10, 7))
pd.DataFrame({m: metrics.equity_curve(r.loc[live]) for m, r in combos.items()}).plot(
    ax=axes[0], title="Equity by allocation rule")
w_rp.loc[live].plot.area(ax=axes[1], title="Risk-parity weights over time")
print("Chart saved to", savefig(fig, "lab14a_allocation"))

# %% [markdown]
# ## Exercises
# 1. Add a 25% single-name cap to max-Sharpe and compare out of sample.
# 2. Add transaction costs on turnover to section 1. Which method wins after costs?
# 3. Add a fourth sleeve that is a copy of "trend" plus noise. What happens to equal weight,
#    inverse-vol and HRP? (HRP was designed for this.)
