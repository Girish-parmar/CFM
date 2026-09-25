# %% [markdown]
# # Lab 10b — Momentum and Volatility (M10)
#
# **Goals**
# 1. Measure volatility five ways and grade each estimator against a known truth.
# 2. Read a volatility cone and a volatility regime without look-ahead.
# 3. Score momentum four ways and see where the scores disagree.
# 4. Backtest cross-sectional momentum and volatility-targeted time-series momentum.
# 5. Split momentum's results by volatility regime, and say what the evidence can and cannot show.
#
# All scores at date t use data up to t; every backtest trades them from t + 1.

# %%
import numpy as np
import pandas as pd
from scipy import stats

from cfmat import data, viz
from cfmat.analytics import metrics
from cfmat.analytics import momentum as mom
from cfmat.analytics import volatility as vol

pd.set_option("display.width", 140)

# %% [markdown]
# ## 1. Five volatility estimators against the truth
# `brownian_ohlc` simulates each day minute by minute, so the true volatility is
# known. Volatility doubles halfway through, and 20% of each day's variance
# arrives overnight as a gap. Range estimators (Parkinson, Garman–Klass,
# Rogers–Satchell) cannot see the gap; Yang–Zhang adds it back.

# %%
sigma = np.r_[np.full(400, 0.18), np.full(400, 0.36)]
bars = data.brownian_ohlc(800, sigma=sigma, overnight_share=0.2, seed=10)
estimates = vol.compare_estimators(bars, window=21).dropna()
truth = bars["true_vol"].loc[estimates.index]
error = estimates.sub(truth, axis=0).div(truth, axis=0)
grade = pd.DataFrame({"bias %": 100 * error.mean(), "RMSE %": 100 * np.sqrt((error**2).mean()),
                      "noise (std) %": 100 * error.std()}).round(1)
print(grade.sort_values("RMSE %").to_string())
print("\nClose-to-close is unbiased but noisy; range estimators are precise but miss the overnight gap.")
print("Chart:", viz.savefig(viz.volatility_chart(bars, 21, true_vol=bars["true_vol"]), "lab10b_estimators"))

# %% [markdown]
# ## 2. Volatility clustering: cone, percentile and regime
# GARCH returns cluster: calm stretches and storms. The cone shows where today's
# volatility sits for each horizon; the trailing percentile and regime labels
# use only past data.

# %%
g = data.garch_prices(1500, seed=4)
garch_bars = data.brownian_ohlc(1500, sigma=g["sigma"].to_numpy() * np.sqrt(252), seed=5)
realised = vol.yang_zhang(garch_bars, 21)
cone = vol.volatility_cone(garch_bars["close"], windows=(10, 21, 63, 126, 252))
print(cone.round(3).to_string())
regime = vol.volatility_regime(realised, lookback=252)
print("\nRegime share:", regime.value_counts(normalize=True).round(2).to_dict())
print(f"EWMA (λ = 0.94) today {vol.ewma_volatility(garch_bars['close']).iloc[-1]:.1%}, "
      f"21-day Yang–Zhang {realised.iloc[-1]:.1%}, vol of vol {vol.vol_of_vol(realised).iloc[-1]:.2f}")
print("Chart:", viz.savefig(viz.cone_chart(cone, "Volatility cone, GARCH market"), "lab10b_cone"))

# %% [markdown]
# ## 3. Four ways to score momentum
# 30 stocks share one market factor; each has its own drift (so past winners
# tend to keep winning) and its own volatility, between 15% and 45%. The four
# scores reward different things: raw 12-1 return, return per unit of risk,
# trend smoothness (regression slope × R²) and how continuous the move was
# (information discreteness).

# %%
prices = data.universe(30, 1512, idio_vol=(0.15, 0.45), seed=21)
scores = pd.DataFrame({
    "12-1 return": mom.momentum(prices).iloc[-1],
    "risk-adjusted": mom.risk_adjusted_momentum(prices).iloc[-1],
    "regression 90d": mom.regression_momentum(prices, 90).iloc[-1],
    "−discreteness": -mom.information_discreteness(prices).iloc[-1],
})
print("Rank correlation between scores today:\n", scores.corr(method="spearman").round(3).to_string())
print("\nTop 5 by each score:")
for col in scores:
    print(f"  {col:<15} {', '.join(scores[col].nlargest(5).index)}")
print("Chart:", viz.savefig(viz.ranking_chart(100 * scores["12-1 return"], title="12-1 momentum today (%)",
                                              fmt="{:.0f}%"), "lab10b_ranking"))

# %% [markdown]
# Raw and risk-adjusted momentum order the stocks almost identically; dividing
# by volatility only swaps names whose returns are close. That is enough to
# change who sits just inside a top-6 cut, which is where the backtests below
# differ. Discreteness measures something else entirely: how the move happened.

# %% [markdown]
# ## 4. Cross-sectional momentum: monthly rebalance, top 6 of 30
# Rebalance on the last trading day of each month into the top 6 names by each
# score, equal weight, and hold for the month. Costs: 10 bps each way on
# turnover. The benchmark holds all 30 equally.

# %%
daily = prices.pct_change()
month_end = prices.groupby(prices.index.to_period("M")).tail(1).index
score_frames = {
    "12-1 return": mom.momentum(prices),
    "risk-adjusted": mom.risk_adjusted_momentum(prices),
    "regression 90d": mom.regression_momentum(prices, 90),
}


def top_n_backtest(score: pd.DataFrame, n: int = 6, cost_bps: float = 10.0) -> pd.Series:
    rank = score.loc[month_end].rank(axis=1, ascending=False)
    target = (rank <= n).astype(float).div(n).where(score.loc[month_end].notna().all(axis=1), axis=0).dropna()
    weights = target.reindex(prices.index).ffill().shift(1).fillna(0.0)       # trade from the next day
    turnover = weights.diff().abs().sum(axis=1)
    return (weights * daily).sum(axis=1) - turnover * cost_bps / 1e4


start = month_end[13]                                                        # a full year of history first
results = pd.DataFrame({name: top_n_backtest(s) for name, s in score_frames.items()})
results["equal weight"] = daily.mean(axis=1)
results = results.loc[start:]
table = pd.DataFrame({k: metrics.performance_summary(v)[["cagr", "volatility", "sharpe", "max_drawdown"]]
                      for k, v in results.items()}).T
print(table.round(3).to_string())

# %% [markdown]
# Why is the edge small? The drifts differ by about 6% a year across stocks,
# while each stock's own noise is 15–45% a year: one year of return is a very
# noisy estimate of drift. Momentum needs persistent differences in expected
# return that are large relative to noise, and it concentrates risk in a few
# names. Scoring by return per unit of risk favours the calmer winners.

# %% [markdown]
# ## 5. Time-series momentum with a volatility target
# Trade the GARCH market from section 2, long or short by the sign of its
# 12-month return. Volatility targeting sizes the position at 15% / recent
# volatility (capped at 2×): smaller in storms, larger in calm. Compare how
# steady the risk is. (On the constant-volatility universe above, targeting
# would change almost nothing: it needs volatility that clusters.)

# %%
close = garch_bars["close"]
asset = close.pct_change()
positions = {"sign only": np.sign(close / close.shift(252) - 1),
             "vol-targeted": mom.tsmom_position(close, lookback=252, target_vol=0.15, vol_window=21,
                                                max_leverage=2.0)}
tsmom = pd.DataFrame({k: w.shift(1) * asset for k, w in positions.items()}).iloc[300:]
tsmom["vol-targeted"] *= tsmom["sign only"].std() / tsmom["vol-targeted"].std()   # same average risk
rolling_vol = tsmom.rolling(63).std() * np.sqrt(252)
print(pd.DataFrame({k: metrics.performance_summary(v)[["cagr", "volatility", "sharpe", "max_drawdown"]]
                    for k, v in tsmom.items()}).T.round(3).to_string())
print("\nRolling 63-day volatility, 5th–95th percentile range:")
print(rolling_vol.quantile([0.05, 0.95]).T.round(3).to_string())

# %% [markdown]
# The vol-targeted version's risk moves in a much narrower band: that is what
# targeting buys. It does not create an edge: on this GARCH market the past
# year's sign has no predictive power, so neither version makes money. A 63-day
# volatility window reacts too slowly to help much (try it).

# %% [markdown]
# ## 6. Momentum by volatility regime
# Split the 12-1 portfolio's daily returns by the market's volatility regime on
# the previous day. On real equity markets, momentum has crashed after sharp
# market falls in high-volatility periods (Daniel and Moskowitz, 2016). This
# synthetic market has no such effect planted, so any difference you see here
# is noise: that is the lesson. Check the sample size and the t-statistic
# before you believe a regime split.

# %%
market = (1 + daily.mean(axis=1).fillna(0.0)).cumprod()             # equal-weight index
market_vol = vol.ewma_volatility(market)
market_regime = vol.volatility_regime(market_vol, lookback=252).shift(1)
by_regime = results["12-1 return"].groupby(market_regime.loc[results.index]).agg(["count", "mean", "std"])
by_regime["annualised %"] = 100 * by_regime["mean"] * 252
by_regime["t-stat"] = by_regime["mean"] / (by_regime["std"] / np.sqrt(by_regime["count"]))
print(by_regime.round(4).to_string())
lagged = market_regime.loc[results.index]
high, rest = results["12-1 return"][lagged == "high"], results["12-1 return"][lagged.isin(["low", "normal"])]
test = stats.ttest_ind(high, rest, equal_var=False)
print(f"\nHigh-vol days vs the rest: difference {252 * (high.mean() - rest.mean()):+.1%} a year, "
      f"Welch t = {test.statistic:.2f}, p = {test.pvalue:.2f}")

# %% [markdown]
# Each regime's mean can look 'significant' on its own because the strategy
# earns a positive average everywhere; the question a regime filter answers is
# whether the regimes *differ*, and that needs the test above (and, with three
# regimes and several strategies, a multiple-testing correction).

# %% [markdown]
# ## Exercises
# 1. Set `overnight_share=0.0` in section 1 and regrade. Which estimator wins now, and why?
# 2. Change the momentum lookback to 6 months and the skip to 0. What happens to turnover and costs?
# 3. Combine the three scores into one (average of cross-sectional ranks) and backtest it.
# 4. Replace the synthetic universe with 30 NSE stocks (`data.download_prices` or your CSVs) and
#    repeat section 6 with Newey–West t-statistics (`analytics.stats.hac_tstat`).
