# %% [markdown]
# # Lab 07a — Fundamental Factors and Quantamental Scores (M07)
#
# **Goals**
# 1. Work with a (date, stock) panel of fundamentals the way a factor researcher does.
# 2. Measure a factor with the information coefficient (IC) and quantile spreads.
# 3. See why winsorising and sector-neutralising matter: raw "value" is partly a sector bet.
# 4. Combine value, quality and momentum into a composite and check its turnover.
#
# The panel is fictional: 200 stocks in 8 sectors over 10 years, with small monthly premia
# planted on sector-relative value, quality and momentum (see `cfmat.data.factor_panel`).
# Real premia are smaller, time-varying and crowded; the method is what transfers.

# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cfmat import data
from cfmat.analytics import factors as fx
from cfmat.infra.plotting import savefig

pd.set_option("display.width", 160)
panel = data.factor_panel(n_stocks=200, n_months=120, seed=1)
fwd = panel["fwd_ret"]            # next month's return, aligned to the date the score is known
sector = panel["sector"]
print(panel.head())
print(f"\n{panel.index.get_level_values('date').nunique()} month-ends × "
      f"{panel.index.get_level_values('stock').nunique()} stocks")
print("\nMedian earnings yield by sector (value is not sector-neutral):")
print(panel.groupby("sector")["earnings_yield"].median().sort_values().round(3).to_string())

# %% [markdown]
# ## 1. Raw value versus sector-neutral value
# The information coefficient (IC) is the rank correlation between this month's score and
# next month's return, computed separately for each month.

# %%
ey = panel["earnings_yield"]
value_raw = fx.zscore(ey)
# clip at the 2.5th/97.5th percentiles: the cut-off must be wider than the share of bad data points
value_neutral = fx.zscore(fx.neutralize(fx.winsorize(ey, 0.025, 0.975), sector))
ic_raw = fx.information_coefficient(value_raw, fwd)
ic_neutral = fx.information_coefficient(value_neutral, fwd)
print(pd.DataFrame({"raw value": fx.factor_summary(ic_raw),
                    "sector-neutral value": fx.factor_summary(ic_neutral)}).T.round(3).to_string())
print("\nRaw value mostly bets on cheap sectors (Metals, Banks) versus expensive ones (FMCG, IT);")
print("sector returns are noise here, so neutralising reveals the stock-level premium.")

# %% [markdown]
# ## 2. Quality, momentum and a composite
# Rank ICs ignore outliers, but composites average *z-scores*, and one distorted earnings
# yield (a one-off gain, a data error) can have a z-score of 8. Compare a composite of raw
# z-scores with one built from winsorised, sector-neutral z-scores.

# %%
quality = fx.zscore(fx.neutralize(fx.winsorize(panel["roe"]), sector)) - 0.5 * fx.zscore(
    fx.neutralize(fx.winsorize(np.log(panel["debt_equity"])), sector))
scores = pd.DataFrame({
    "value": value_neutral,
    "quality": fx.zscore(quality),
    "momentum": fx.zscore(fx.winsorize(panel["momentum_12_1"])),
})
scores["composite"] = scores[["value", "quality", "momentum"]].mean(axis=1)
raw_composite = (fx.zscore(ey) + fx.zscore(panel["roe"]) + fx.zscore(panel["momentum_12_1"])) / 3

summary = pd.DataFrame({c: fx.factor_summary(fx.information_coefficient(scores[c], fwd)) for c in scores}).T
summary.loc["composite of raw z-scores"] = fx.factor_summary(fx.information_coefficient(raw_composite, fwd))
print(summary.round(3).to_string())
print(f"\nLargest raw earnings-yield z-score: {value_raw.abs().max():.1f}; after winsorising and "
      f"neutralising: {value_neutral.abs().max():.1f}")
print("\nAverage cross-sectional correlation between factor scores:")
print(scores.groupby(level="date").corr().groupby(level=1).mean().round(2))

# %% [markdown]
# ## 3. Quintile portfolios
# Each month, sort stocks into five buckets by score; hold each bucket equally weighted for
# a month. A factor worth trading shows returns that rise from Q1 to Q5.

# %%
q = fx.quantile_returns(scores["composite"], fwd, q=5)
spread = q[5] - q[1]
table = pd.DataFrame({"mean_monthly_%": q.mean() * 100, "annualised_%": ((1 + q.mean()) ** 12 - 1) * 100})
print(table.round(2))
print(f"\nQ5 − Q1: {spread.mean() * 100:.2f}% a month, t = {spread.mean() / spread.std() * np.sqrt(len(spread)):.1f}, "
      f"positive in {(spread > 0).mean():.0%} of months")
turn = fx.turnover(scores["composite"], top=0.2)
print(f"Top-quintile turnover: {turn.mean():.0%} a month → at 30 bp per side that costs about "
      f"{turn.mean() * 2 * 0.30 * 12:.1f}% a year")

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
(q.mean() * 100).plot.bar(ax=axes[0], title="Mean monthly return by composite quintile (%)")
(1 + spread).cumprod().plot(ax=axes[1], title="Q5 − Q1 long-short, growth of ₹1")
print("Chart saved to", savefig(fig, "lab07a_quintiles"))

# %% [markdown]
# ## 4. Stability: dry spells
# Each premium drifts over time. Look at the worst 24-month average IC of each factor.

# %%
worst = {c: fx.information_coefficient(scores[c], fwd).rolling(24).mean().min() for c in scores}
print(pd.Series(worst, name="worst 24-month mean IC").round(3).to_string())
print("\nSingle factors go through two-year spells with no edge or a negative one; the composite's")
print("spells are shallower because the three premia do not dry up at the same time.")

# %% [markdown]
# ## Exercises
# 1. Drop the 0.5 weight on leverage in `quality`. How does the composite IC change?
# 2. Weight the composite by each factor's trailing 36-month ICIR instead of equally.
#    Make sure the weights use only past ICs.
# 3. Build the same panel from real data (screener exports or annual-report ratios for the
#    Nifty 200). Which factors survive? What does survivorship bias do to your universe?
