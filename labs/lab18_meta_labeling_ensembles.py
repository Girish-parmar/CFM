# %% [markdown]
# # Lab 18 — Meta-Labelling, Bet Sizing and Strategy Ensembles (Module 16)
#
# **Goals**
# 1. Keep a simple primary strategy for the *side* of each trade, and train a
#    gradient-boosted secondary model that decides *whether* to take it.
# 2. Turn the secondary model's probability into a bet size.
# 3. Combine four uncorrelated strategy sleeves and compare allocation rules
#    (equal, inverse-volatility, risk parity, HRP) re-estimated from trailing data.

# %%
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import precision_score, recall_score

from cfmat import data, econometrics, ml, portfolio, strategies
from cfmat.analytics import metrics
from cfmat.backtesting import vectorized as bt
from cfmat.infra.plotting import savefig
from cfmat.ml import tuning

pd.set_option("display.width", 160)
COST_BPS = 5


def summary(r: pd.Series) -> dict:
    s = metrics.performance_summary(r)
    return {"cagr": s["cagr"], "vol": s["volatility"], "sharpe": s["sharpe"], "max_dd": s["max_drawdown"]}


# %% [markdown]
# ## 1. Primary model: a trend follower that is right about half the time

# %%
market = data.regime_prices(2500, mu=(0.15, -0.20), sigma=(0.12, 0.32), phi=(0.05, -0.15), seed=5)
bars = data.ohlcv_from_close(market["close"], seed=5)
close = bars["close"]
side = strategies.sma_crossover(close, 10, 40, allow_short=True)       # +1 / −1 every day after warm-up
H = 10
labels = ml.meta_labels(close, side, horizon=H, pt_mult=1.0, sl_mult=1.0)
print(f"Primary model precision (share of days whose trade would win): {labels['label'].mean():.1%}")

# %% [markdown]
# ## 2. Secondary model: when should we trust the primary signal?
# Features describe the market (volatility, trend strength, RSI…) plus the side.
# Walk-forward training with a gap of H days so labels never overlap the test block.

# %%
features = ml.make_features(bars).assign(side=side)
df = features.join(labels[["label"]]).dropna()
df = df[df["side"] != 0]
X, y = df[features.columns], df["label"].astype(int)
splits = list(ml.walk_forward_splits(len(X), train_size=800, test_size=250, gap=H))
make_meta = lambda: tuning.make_booster("hgb", learning_rate=0.05, max_iter=150, max_depth=3,  # noqa: E731
                                        min_samples_leaf=50)
proba = ml.out_of_fold_proba(make_meta, X, y, splits).dropna()
test = proba.index
take = proba > 0.5
print(f"Out-of-sample days: {len(test)}")
print(f"Precision — primary alone: {y.loc[test].mean():.1%} | primary + meta filter: "
      f"{precision_score(y.loc[test], take):.1%} (recall {recall_score(y.loc[test], take):.1%})")

# %% [markdown]
# ## 3. From probabilities to positions

# %%
size = ml.bet_size(proba)
variants = {
    "buy & hold": pd.Series(1.0, index=test),
    "primary only": side.loc[test],
    "primary + meta filter (p > 0.5)": side.loc[test] * take,
    "primary + meta bet sizing": side.loc[test] * size,
}
results = {}
for name, pos in variants.items():
    r = bt.vectorized_backtest(close, pos.reindex(close.index).fillna(0.0), COST_BPS)["strategy_return"].loc[test]
    results[name] = {**summary(r), "avg_exposure": pos.abs().mean()}
res_table = pd.DataFrame(results).T
print(res_table.round(3))
if res_table["sharpe"].idxmax() == "buy & hold":
    print("\nBuy & hold wins here: a long/short trend follower fights a rising market. Always benchmark.")
print("\nMeta-labelling cannot create an edge the primary signal lacks; it filters and sizes the trades")
print("the primary model already makes. Compare risk-adjusted numbers (Sharpe, drawdown), not CAGR alone.")

# %% [markdown]
# ## 4. A portfolio of strategies
# Four sleeves with different return sources, all on the same calendar:
# trend, short-term reversal, a Kalman-filter pair, and a volatility-managed long.

# %%
n, start = 2000, "2016-01-01"
trend_px = data.ar1_prices(n, phi=0.10, seed=5, start=start)
revert_px = data.ar1_prices(n, phi=-0.15, seed=6, start=start)
pair = data.drifting_pair(n, seed=2, start=start)
regime_px = data.regime_prices(n, seed=9, start=start)["close"]
regime_rets = metrics.simple_returns(regime_px)
garch = econometrics.garch11_fit(regime_rets.iloc[:500])

sleeves = pd.DataFrame({
    "trend": bt.vectorized_backtest(trend_px, strategies.time_series_momentum(trend_px, 60), COST_BPS)["strategy_return"],
    "reversal": bt.vectorized_backtest(revert_px, strategies.rsi_reversal(revert_px, 2, 10, 90), COST_BPS)["strategy_return"],
    "kalman_pair": bt.pairs_backtest(pair["y"], pair["x"], econometrics.kalman_pairs_signals(pair["y"], pair["x"]),
                                     capital=1_000_000, cost_bps=COST_BPS)["strategy_return"],
    "vol_managed": bt.vectorized_backtest(
        regime_px, econometrics.vol_target_weights(econometrics.garch11_forecast(regime_rets, garch)), COST_BPS
    )["strategy_return"],
}).fillna(0.0)
live = sleeves.index[500:]                                   # after every sleeve's warm-up and the GARCH fit
print("Sleeve correlations:\n", sleeves.loc[live].corr().round(2))

combos = {}
for method in ("equal", "inverse_vol", "risk_parity", "hrp"):
    w = portfolio.rolling_allocation(sleeves, method=method, lookback=126, rebalance=21)
    combos[method] = portfolio.allocation_returns(sleeves, w)
table = pd.DataFrame({**{f"sleeve: {c}": summary(sleeves[c].loc[live]) for c in sleeves},
                      **{f"portfolio: {m}": summary(r.loc[live]) for m, r in combos.items()}}).T
print(table.round(3))

w_hrp = portfolio.rolling_allocation(sleeves, method="hrp", lookback=126, rebalance=21)
fig, axes = plt.subplots(2, 1, figsize=(10, 7))
equity = pd.DataFrame({m: metrics.equity_curve(r.loc[live]) for m, r in combos.items()})
equity.plot(ax=axes[0], title="Portfolio equity by allocation rule")
w_hrp.loc[live].plot.area(ax=axes[1], title="HRP weights over time", legend=True)
print("Chart saved to", savefig(fig, "lab18_ensemble"))

# %% [markdown]
# ## Exercises
# 1. Tune the meta-model with `cfmat.tuning.nested_walk_forward` and charge the
#    Deflated Sharpe for every configuration tried.
# 2. Replace the SMA primary with the Lab 16 boosted model and meta-label *that*.
# 3. Add a drawdown brake to the ensemble: halve all weights while the portfolio
#    is more than 10% below its peak. Does it help out of sample?
