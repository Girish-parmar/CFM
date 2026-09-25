# %% [markdown]
# # Lab 11b — Performance Analysis and the Tearsheet (M11)
#
# **Goals**
# 1. Produce a full tearsheet for a strategy against its benchmark and read every line.
# 2. Take drawdowns apart: depth, time to trough, time to recover, and the ones still open.
# 3. Read the calendar, rolling and distribution views, and know what each can mislead you about.
# 4. Separate skill from market exposure with CAPM alpha, beta and capture ratios.
# 5. Look at the universe itself: relative strength, RS rating, rotation and correlation.
#
# A single Sharpe ratio hides almost everything that matters when you decide
# whether to trust, size or stop a strategy. This lab is the checklist.

# %%
import numpy as np
import pandas as pd

from cfmat import data, viz
from cfmat.analytics import momentum as mom
from cfmat.analytics import performance as perf
from cfmat.analytics import relative as rel

pd.set_option("display.width", 140)

# %% [markdown]
# ## 1. A strategy and its benchmark
# Dual momentum on 20 stocks: each month hold the 5 strongest by 12-1 momentum,
# but only those whose momentum is positive (the rest of the money waits in
# cash). Costs are 10 bps each way on turnover. The benchmark holds all 20
# equally, rebalanced daily.

# %%
prices = data.universe(20, 1764, idio_vol=(0.15, 0.40), seed=33)
daily = prices.pct_change()
month_end = prices.groupby(prices.index.to_period("M")).tail(1).index
target = mom.dual_momentum_weights(prices, top_n=5).loc[month_end]
weights = target.reindex(prices.index).ffill().shift(1).fillna(0.0)          # trade the day after
turnover = weights.diff().abs().sum(axis=1)
strategy = ((weights * daily).sum(axis=1) - turnover * 10 / 1e4).iloc[260:].rename("dual momentum")
benchmark = daily.mean(axis=1).iloc[260:].rename("equal weight")
print(f"{len(strategy)} days, average exposure {weights.iloc[260:].sum(axis=1).mean():.0%}, "
      f"annual turnover {turnover.iloc[260:].sum() / (len(strategy) / 252):.1f}x")

# %% [markdown]
# ## 2. The tearsheet
# Returns, risk, drawdown, distribution, and — because there is a benchmark —
# the relative rows: alpha (annualised, with a Newey–West t-statistic), beta,
# tracking error, information ratio and up/down capture.

# %%
sheet = perf.tearsheet(strategy, benchmark)
print(sheet.round(3).to_string())

# %% [markdown]
# Read it in this order: (1) is the return worth the risk (Sharpe, Sortino)?
# (2) could you live through the worst stretch (max drawdown, longest drawdown,
# ulcer index)? (3) are the tails worse than the volatility suggests (skew,
# kurtosis, CVaR vs VaR)? (4) is it skill or beta (alpha t-stat, beta,
# capture)? An alpha t-statistic under 2 means you cannot tell this alpha from luck.
#
# Here the verdict is quick: the strategy trails its benchmark with a deeper
# and longer worst drawdown, a beta near 1 and a negative alpha that is
# indistinguishable from zero. It is mostly the market, concentrated in five
# names, minus costs. That is a common, honest result, and exactly what a
# tearsheet exists to show you before an investor does.

# %% [markdown]
# ## 3. Drawdown anatomy
# Depth is only half the story: how long it took to hit bottom and how long to
# recover decide whether you (or your investors) stay the course.

# %%
periods = perf.drawdown_periods(strategy, top=5)
print(periods.to_string())
still_open = periods["recovery"].isna().sum()
print(f"\nOpen drawdowns among the worst five: {still_open}; "
      f"ulcer index {perf.ulcer_index(strategy):.1f} vs benchmark {perf.ulcer_index(benchmark):.1f}")
print("Chart:", viz.savefig(viz.equity_chart(strategy, benchmark, title="Dual momentum vs equal weight"),
                            "lab11b_equity"))

# %% [markdown]
# ## 4. Calendar view
# Monthly returns show streaks and seasonality; the yearly column shows how
# lumpy the result is. A strategy that made all its money in one year needs a
# reason why that year will repeat.

# %%
print(perf.monthly_returns(strategy).round(1).to_string())
print("\nAnnual returns vs benchmark (%):")
print((100 * pd.DataFrame({"strategy": perf.annual_returns(strategy),
                           "benchmark": perf.annual_returns(benchmark)})).round(1).to_string())
print("Chart:", viz.savefig(viz.monthly_heatmap(strategy), "lab11b_monthly"))

# %% [markdown]
# ## 5. Rolling view — and how often a good strategy looks bad
# Rolling Sharpe and beta show drift in behaviour. But short windows are noisy:
# simulate a strategy whose *true* Sharpe is 1.0 and count how often its
# 63-day Sharpe is negative. That is the base rate of "bad quarters" you must
# expect before you conclude anything broke.

# %%
roll = perf.rolling_metrics(strategy, 63, benchmark=benchmark)
print(roll.describe().loc[["mean", "min", "max"]].round(2).to_string())
rng = np.random.default_rng(0)
good = pd.Series(rng.normal(1.0 * 0.15 / 252, 0.15 / np.sqrt(252), 252 * 20),
                 index=pd.bdate_range("2000-01-03", periods=252 * 20))
negative = (perf.rolling_metrics(good, 63)["sharpe"].dropna() < 0).mean()
print(f"\nTrue Sharpe 1.0: rolling 63-day Sharpe below zero {negative:.0%} of the time "
      "(theory: about 31%)")
print("Chart:", viz.savefig(viz.rolling_chart(strategy, 63, benchmark), "lab11b_rolling"))

# %% [markdown]
# ## 6. The return distribution
# Compare the histogram with the normal fit and read the Q-Q plot: points that
# bend away at the ends are fat tails. Historical VaR says how bad a normal bad
# day is; CVaR says how bad the days beyond it are on average.

# %%
print("Chart:", viz.savefig(viz.distribution_chart(strategy), "lab11b_distribution"))
tail = sheet.loc[["var_95", "cvar_95", "skew", "excess_kurtosis", "tail_ratio"], "strategy"]
print(tail.round(4).to_string())

# %% [markdown]
# ## 7. Skill or exposure?
# Rolling beta shows how the market exposure moved as the strategy rotated
# between stocks and cash. Up-capture above down-capture is what a good
# defensive strategy looks like.

# %%
capm = pd.Series(rel.capm(strategy, benchmark))
print(capm.round(3).to_string())
beta = rel.rolling_beta(strategy, benchmark, 126)
print(f"\nRolling 126-day beta ranged from {beta.min():.2f} to {beta.max():.2f}")

# %% [markdown]
# ## 8. The universe: relative strength, RS rating, rotation, correlation
# The same tools rank the stocks themselves: the ratio to the benchmark (rising
# = outperforming), an RS rating from 1 to 99, and a relative rotation graph
# that shows which names are leading, weakening, lagging or improving.

# %%
bench_close = (1 + daily.mean(axis=1).fillna(0.0)).cumprod()
rating = rel.rs_rating(prices).iloc[-1].sort_values(ascending=False)
ratio, momentum = rel.relative_rotation(prices, bench_close, window=63, momentum_window=10)
quadrant = rel.rotation_quadrant(ratio.iloc[-1], momentum.iloc[-1])
view = pd.DataFrame({"RS rating": rating, "quadrant": quadrant,
                     "Mansfield RS": rel.mansfield_rs(prices, bench_close, 200).iloc[-1].round(1)})
print(view.sort_values("RS rating", ascending=False).head(8).to_string())
print("\nQuadrant counts:", quadrant.value_counts().to_dict())
leaders = rating.index[:6]
print("Charts:",
      viz.savefig(viz.rotation_chart(ratio[leaders], momentum[leaders], tail=8), "lab11b_rotation"),
      viz.savefig(viz.correlation_heatmap(daily.iloc[-504:]), "lab11b_correlation"))

# %% [markdown]
# ## Exercises
# 1. Change `top_n` to 2 and to 10. Which tearsheet lines move most, and why?
# 2. Add 30 bps of costs. At what cost level does the information ratio fall below zero?
# 3. Run section 5 for a true Sharpe of 0.5 and of 2.0, and with a 252-day window. Write the rule
#    you would use to decide that a live strategy has stopped working.
# 4. Put a real strategy's daily returns (your Mini-project 1) through sections 2–7 and write a
#    half-page review a risk committee could act on.
