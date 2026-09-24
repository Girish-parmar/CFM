# %% [markdown]
# # Lab 19 — Strategy Optimisation by Segment: Day, Month, Regime, Pattern (Module 16)
#
# **Goals**
# 1. Split history into segments: weekday, month, turn of month, expiry week,
#    volatility regime, trend regime and price patterns, with no look-ahead.
# 2. Test every segment for abnormal returns, and control false discoveries
#    (Benjamini–Hochberg) because you are testing dozens of segments at once.
# 3. Optimise strategy parameters *per regime* and compare with one global set,
#    walk-forward.
# 4. Build a calendar/pattern filter and see how much it really adds.
# 5. "Boost it": feed every segment label to a tuned gradient-boosting model and
#    measure the out-of-sample gain and which segment families it used.
#
# The market is synthetic with planted effects (Monday −12 bp, Friday +12 bp,
# turn of month +15 bp, a bounce after 3 down days, momentum in calm regimes
# and reversal in turbulent ones). Real calendar effects are smaller and fade
# once published, so test them on real data before trusting them.

# %%
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.inspection import permutation_importance

from cfmat import data, ml, strategies
from cfmat.analytics import metrics
from cfmat.backtesting import vectorized as bt
from cfmat.infra.plotting import savefig
from cfmat.ml import tuning
from cfmat.research import segments as sg

pd.set_option("display.width", 170)
pd.set_option("display.max_columns", 14)
COST_BPS = 2

bars = data.seasonal_prices(3000, seed=1)
close = bars["close"]
rets = close.pct_change()

cal = sg.calendar_segments(bars.index)                      # describes the NEXT session
labels = pd.concat([
    cal[["weekday", "month", "turn_of_month"]],
    sg.expiry_week(bars.index, weekday=1).rename("expiry_week"),   # set to your exchange's current expiry weekday
    sg.volatility_regime(close),
    sg.trend_regime(close),
    sg.pattern_segments(bars),
], axis=1)
print(labels.dropna().tail(3).T)

# %% [markdown]
# ## 1. Which segments have abnormal returns?
# The return earned on day t belongs to the label decided at the close of t−1,
# hence `labels.shift(1)`.

# %%
table = sg.segment_stats(rets, labels.shift(1))
cols = ["family", "segment", "n", "mean_bp", "rest_bp", "hit_rate", "t_stat", "p_value", "q_value"]
print(f"{len(table)} segments tested")
print(table[cols].head(12).round(4).to_string(index=False))
raw, fdr = (table["p_value"] < 0.05).sum(), (table["q_value"] < 0.10).sum()
print(f"\nSignificant at raw p < 0.05: {raw}. After Benjamini–Hochberg (q < 0.10): {fdr}.")
print("With ~35 tests, about 2 'discoveries' at p < 0.05 are expected by pure chance.")

# Are the effects stable? Compare the two halves of the sample.
half = rets.index[len(rets) // 2]
first = sg.segment_stats(rets.loc[:half], labels.shift(1)).set_index(["family", "segment"])["mean_bp"]
second = sg.segment_stats(rets.loc[half:], labels.shift(1)).set_index(["family", "segment"])["mean_bp"]
stable = pd.DataFrame({"first_half_bp": first, "second_half_bp": second}).dropna()
top = table.head(8).set_index(["family", "segment"]).index
print("\nStability of the strongest segments:\n", stable.reindex(top).round(1))

# %% [markdown]
# ## 2. Where does the effect live? Weekday × volatility regime

# %%
grid = pd.DataFrame({"ret_bp": rets * 1e4, "weekday": labels["weekday"].shift(1),
                     "vol": labels["vol_regime"].shift(1)}).dropna()
heat = grid.pivot_table(index="vol", columns="weekday", values="ret_bp", aggfunc="mean")
heat = heat.reindex(index=["low", "mid", "high"], columns=["Mon", "Tue", "Wed", "Thu", "Fri"])
print(heat.round(1))
fig, ax = plt.subplots(figsize=(7, 3.5))
im = ax.imshow(heat.to_numpy(), cmap="RdYlGn", aspect="auto")
ax.set_xticks(range(5), heat.columns)
ax.set_yticks(range(3), heat.index)
ax.set_title("Mean next-day return (bp) by weekday and volatility regime")
for i in range(3):
    for j in range(5):
        ax.text(j, i, f"{heat.iat[i, j]:.0f}", ha="center", va="center")
fig.colorbar(im)
print("Chart saved to", savefig(fig, "lab19_weekday_regime_heatmap"))

# %% [markdown]
# ## 3. Optimise parameters per volatility regime (walk-forward)
# Strategy: follow or fade the last N-day move. Grid: N ∈ {1, 2, 5}, direction ∈ {+1, −1}.

# %%
param_grid = {"lookback": [1, 2, 5], "direction": [1, -1]}
glob, per_regime, chosen = sg.walk_forward_by_segment(close, strategies.short_term_signal, param_grid,
                                                      labels["vol_regime"], train=1000, test=250, cost_bps=COST_BPS)
print(chosen.tail(3).to_string(index=False))
print(f"\nOut-of-sample Sharpe — one global parameter set: {metrics.sharpe_ratio(glob):.2f} | "
      f"one set per volatility regime: {metrics.sharpe_ratio(per_regime):.2f}")
print(f"Probabilistic Sharpe of the per-regime out-of-sample returns (true Sharpe > 0): "
      f"{metrics.probabilistic_sharpe_ratio(per_regime):.1%}")
print("The 24 parameter/segment combinations were searched inside each training window only, so these")
print("out-of-sample numbers are not inflated by that search. Deflate a Sharpe when you pick the best of")
print("many *backtests on the same data*, as in Lab 16.")

attribution = sg.segment_stats(per_regime, labels[["vol_regime", "weekday"]].shift(1).reindex(per_regime.index), min_obs=20)
print("\nWhere the per-regime strategy earns (attribution):")
cols = ["family", "segment", "n", "mean_bp", "sharpe"]
print(attribution[cols].sort_values(["family", "segment"]).round(2).to_string(index=False))

# %% [markdown]
# ## 4. A calendar and pattern filter (long/flat)
# Each year, using all data so far, find segments with significantly *negative*
# returns and stay flat in them over the next year.

# %%
filter_labels = labels[["weekday", "month", "turn_of_month"] + list(sg.pattern_segments(bars).columns)]
pos, avoided = sg.segment_filter_positions(rets, filter_labels, train=750, test=250, q_max=0.10)
tested = pos.dropna().index
filtered = bt.vectorized_backtest(close, pos.reindex(close.index).fillna(0.0), COST_BPS)["strategy_return"].loc[tested]
print(avoided.to_string(index=False))
print(f"\nFilter: Sharpe {metrics.sharpe_ratio(filtered):.2f}, exposure {pos.dropna().mean():.0%} | "
      f"buy & hold: Sharpe {metrics.sharpe_ratio(rets.loc[tested]):.2f}")
print("Small calendar effects rarely survive a strict significance filter with only a few years of data.")

# %% [markdown]
# ## 5. Boost it: a tuned gradient-boosting model with segment features
# Same nested walk-forward tuning as Lab 16, once with price features only and
# once adding every calendar, regime and pattern label.

# %%
fwd = rets.shift(-1).rename("fwd")
price_feats = ml.make_features(bars)
seg_feats = sg.segment_features(bars)
df = price_feats.join(seg_feats).join(fwd).dropna(subset=list(price_feats.columns) + ["fwd", "reg_vol", "cal_weekday"])
y = (df["fwd"] > 0).astype(int)
CV = dict(fwd_ret=df["fwd"], horizon=1, embargo=5)
feature_sets = {"price features only": list(price_feats.columns),
                "price + segment features": list(price_feats.columns) + list(seg_feats.columns)}
rows, probas = {}, {}
for name, columns in feature_sets.items():
    proba, _ = tuning.nested_walk_forward(df[columns], y, "hgb", n_trials=6, train_size=1000, test_size=250, gap=5, **CV)
    probas[name] = proba
    r = tuning.strategy_returns(proba.dropna(), df["fwd"], threshold=0.52, cost_bps=COST_BPS)
    rows[name] = {"sharpe": metrics.sharpe_ratio(r), "cagr": metrics.cagr(r),
                  "max_dd": metrics.max_drawdown(metrics.equity_curve(r))}
oos = probas["price + segment features"].dropna().index
rows["buy & hold"] = {"sharpe": metrics.sharpe_ratio(df["fwd"].loc[oos]), "cagr": metrics.cagr(df["fwd"].loc[oos]),
                      "max_dd": metrics.max_drawdown(metrics.equity_curve(df["fwd"].loc[oos]))}
print(pd.DataFrame(rows).T.round(3))

# Which segment families does the boosted model rely on? Grouped permutation importance
# on the last 30% of the sample, with the model trained on the first 70%.
all_cols = feature_sets["price + segment features"]
split = int(len(df) * 0.7)
model = tuning.make_booster("hgb", learning_rate=0.03, max_iter=200, max_depth=3, min_samples_leaf=80)
model.fit(df[all_cols].iloc[: split - 5], y.iloc[: split - 5])
imp = permutation_importance(model, df[all_cols].iloc[split:], y.iloc[split:], scoring="neg_log_loss",
                             n_repeats=10, random_state=0)
by_feature = pd.Series(imp.importances_mean, index=all_cols)
family = {c: ("calendar" if c.startswith("cal_") else "regime" if c.startswith("reg_")
              else "pattern" if c.startswith("pat_") else "price") for c in all_cols}
print("\nImportance by family:\n", by_feature.groupby(family).sum().sort_values(ascending=False).round(5).to_string())
print("\nTop features:\n", by_feature.sort_values(ascending=False).head(8).round(5).to_string())

# %% [markdown]
# ## Exercises
# 1. Replace the synthetic market with 15 years of Nifty 50 data. Which segments
#    survive Benjamini–Hochberg? Do they hold in both halves?
# 2. Optimise the Lab 7 pairs strategy per *trend* regime instead of volatility regime.
# 3. Add a "budget/RBI policy day" segment from a list of event dates, and test it.
# 4. Report the total number of segment × parameter combinations you tried and the
#    Deflated Sharpe of your best result.
