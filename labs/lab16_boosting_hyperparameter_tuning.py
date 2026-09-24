# %% [markdown]
# # Lab 16 — Gradient Boosting and Hyperparameter Optimisation (Module 16)
#
# **Goals**
# 1. Train gradient-boosted trees (scikit-learn HistGradientBoosting, XGBoost,
#    LightGBM) on a market with a *non-linear* signal a linear model cannot see.
# 2. Tune hyperparameters with random search and Bayesian optimisation (Optuna),
#    scoring every trial with purged cross-validation.
# 3. See why "best CV score" is an optimistic number, and get an honest one with
#    nested walk-forward tuning.
# 4. Charge the strategy for every configuration you tried: Deflated Sharpe
#    Ratio and Probability of Backtest Overfitting (CSCV).
#
# Optional: `pip install xgboost lightgbm optuna` (or `xgboost-cpu`). Sections
# that need them are skipped when they are missing.

# %%
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from cfmat import data, metrics, ml, tuning

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 12)

# Two hidden regimes: in calm markets yesterday's move continues (momentum),
# in turbulent markets it reverses. Which one applies depends on volatility,
# so the signal is an interaction between two features.
market = data.regime_prices(2500, mu=(0.08, 0.02), sigma=(0.12, 0.30), phi=(0.3, -0.3),
                            p_stay=(0.98, 0.98), seed=42)
bars = data.ohlcv_from_close(market["close"], seed=42)
features = ml.make_features(bars)
fwd_ret = bars["close"].pct_change().shift(-1).rename("fwd_ret")   # earned by a position taken at today's close
df = features.join(fwd_ret).dropna()
X, fwd = df[features.columns], df["fwd_ret"]
y = (fwd > 0).astype(int)                                           # next-day direction
H = 1                                                               # label horizon (days) for purging
CV = dict(fwd_ret=fwd, horizon=H, embargo=5, n_splits=4)
print(f"{len(X)} samples, {X.shape[1]} features, {y.mean():.1%} up days")


def trade_stats(proba: pd.Series, cost_bps: float = 5.0) -> dict:
    r = tuning.strategy_returns(proba.dropna(), fwd, threshold=0.55, cost_bps=cost_bps)
    return {"sharpe": metrics.sharpe_ratio(r), "cagr": metrics.cagr(r), "max_dd": metrics.max_drawdown(metrics.equity_curve(r))}


# %% [markdown]
# ## 1. Baselines: linear model vs untuned boosting (purged 4-fold CV)

# %%
make_lr = lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=1000))  # noqa: E731
make_default = lambda: tuning.make_booster("hgb")                                              # noqa: E731
rows = []
for name, factory in {"logistic regression": make_lr, "boosting, default params": make_default}.items():
    score, oof = tuning.cv_score(factory, X, y, **CV)
    rows.append({"model": name, "cv_log_loss": -score, **trade_stats(oof)})
baseline = pd.DataFrame(rows).set_index("model")
print(baseline.round(4))
print("Log loss of a coin flip is 0.6931. Lower is better; tiny differences matter at daily horizons.")
if baseline.loc["boosting, default params", "cv_log_loss"] > 0.6931:
    print("Untuned boosting is worse than a coin flip on log loss: its default capacity memorises noise.")

# %% [markdown]
# ## 2. Random search: 25 configurations, every one scored with purged CV

# %%
rand = tuning.random_search(X, y, "hgb", n_trials=25, seed=0, **CV)
print(rand.trials.head(5).round(4).to_string(index=False))
print("\nBest parameters:", {k: round(v, 4) if isinstance(v, float) else v for k, v in rand.best_params.items()})

# %% [markdown]
# ## 3. Bayesian optimisation with Optuna (TPE), and XGBoost / LightGBM

# %%
searches = {"HGB random search": rand}
try:
    searches["HGB Optuna TPE"] = tuning.optuna_search(X, y, "hgb", n_trials=25, seed=0, **CV)
except ImportError:
    print("Optuna not installed — skipping (pip install optuna)")
for kind in ("xgboost", "lightgbm"):
    if kind in tuning.available_boosters():
        searches[f"{kind} random search"] = tuning.random_search(X, y, kind, n_trials=15, seed=0, **CV)
    else:
        print(f"{kind} not installed — skipping")

summary = []
for name, res in searches.items():
    best_trial = res.trials.iloc[0]["trial"]
    summary.append({"search": name, "trials": len(res.trials), "best_cv_log_loss": -res.best_score,
                    **trade_stats(res.oof[best_trial])})
print(pd.DataFrame(summary).set_index("search").round(4))
print("\nThese 'best' numbers are optimistic: the same folds were used to choose the winner.")

# %% [markdown]
# ## 4. The honest estimate: nested walk-forward tuning
# For each yearly test window, run a fresh search using only data *before* it,
# fit the winner on that past data, and trade the window.

# %%
nested_proba, chosen = tuning.nested_walk_forward(X, y, "hgb", search="random", n_trials=8,
                                                  train_size=1000, test_size=250, gap=5, **CV)
print(chosen.set_index("test_start").round(4))
honest = trade_stats(nested_proba)
tested = nested_proba.dropna().index
best_insample = trade_stats(rand.oof[rand.trials.iloc[0]["trial"]].loc[tested])
print(f"\nSame dates — best-of-25 CV predictions: Sharpe {best_insample['sharpe']:.2f} | "
      f"nested walk-forward: Sharpe {honest['sharpe']:.2f}")
print(f"Buy & hold over those dates: Sharpe {metrics.sharpe_ratio(fwd.loc[tested]):.2f}")
print("The gap between the two is the price of choosing hyperparameters on the data you report.")

# %% [markdown]
# ## 5. Paying for the search: Deflated Sharpe Ratio and PBO

# %%
trial_returns = pd.DataFrame({t: tuning.strategy_returns(rand.oof[t], fwd, cost_bps=5.0) for t in rand.oof.columns})
per_period_sr = trial_returns.mean() / trial_returns.std()
n_trials = sum(len(r.trials) for r in searches.values())
best_r = trial_returns[rand.trials.iloc[0]["trial"]]
print(f"Configurations tried across all searches: {n_trials}")
print(f"Probabilistic Sharpe of the best config (vs 0): {metrics.probabilistic_sharpe_ratio(best_r):.1%}")
print(f"Deflated Sharpe (charged for {n_trials} trials): "
      f"{metrics.deflated_sharpe_ratio(best_r, n_trials, per_period_sr.var()):.1%}")

pbo = tuning.probability_of_backtest_overfitting(trial_returns, n_blocks=10)
print(f"Probability of Backtest Overfitting across the 25 random-search configs: {pbo['pbo']:.0%} "
      f"({pbo['n_splits']} CSCV splits)")
print("PBO near 0: the in-sample winner tends to stay good. Near 50%: choosing it was luck.")

# %% [markdown]
# ## 6. What did the tuned model learn?

# %%
split = int(len(X) * 0.7)
model = tuning.make_booster("hgb", **rand.best_params).fit(X.iloc[: split - 5], y.iloc[: split - 5])
imp = permutation_importance(model, X.iloc[split:], y.iloc[split:], scoring="neg_log_loss", n_repeats=10, random_state=0)
print(pd.Series(imp.importances_mean, index=X.columns).sort_values(ascending=False).round(5).to_string())
print("\nThe planted signal needs ret_1 (yesterday's move) together with a volatility feature.")

# %% [markdown]
# ## Exercises
# 1. Switch the search metric to `metric="sharpe"`. Does optimising the trading
#    objective directly help out of sample, or just overfit faster?
# 2. Add early stopping on an inner, chronologically later validation slice.
# 3. Run the nested walk-forward with `search="optuna"` and `kind="lightgbm"`.
#    Report the Deflated Sharpe with the *total* number of configurations you tried.
