# %% [markdown]
# # Lab 19a — Machine Learning for Trading (M19)
#
# **Goals**
# 1. Engineer leakage-free features and triple-barrier labels.
# 2. Show how shuffled K-fold cross-validation inflates accuracy, and fix it with
#    purged K-fold and walk-forward validation.
# 3. Compare logistic regression with a random forest; read permutation importance.
# 4. Turn out-of-sample probabilities into positions and evaluate after costs.

# %%
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from cfmat import data, ml
from cfmat.analytics import metrics
from cfmat.backtesting import vectorized as bt

HORIZON = 3
# Synthetic prices with planted one-day momentum (AR(1) coefficient 0.2), so there
# is a real but modest signal to find. Real markets are much less generous.
bars = data.ohlcv_from_close(data.ar1_prices(2500, phi=0.20, seed=7), seed=7)
X_all = ml.make_features(bars)
labels = ml.triple_barrier_labels(bars["close"], horizon=HORIZON, pt_mult=1.0, sl_mult=1.0)
df = X_all.join(labels).dropna()
features = list(X_all.columns)
X, y = df[features], (df["label"] > 0).astype(int)
print(f"{len(df)} samples, {len(features)} features, label balance {y.mean():.1%} up")
print(labels["label"].value_counts().to_string())

# %% [markdown]
# ## 1. The leakage trap
# Overlapping 3-day labels mean neighbouring rows share the same future. Shuffled
# K-fold puts those neighbours on both sides of the split.

# %%
make_rf = lambda: RandomForestClassifier(n_estimators=200, min_samples_leaf=20, max_features=0.5,  # noqa: E731
                                         n_jobs=-1, random_state=0)
shuffled = cross_val_score(make_rf(), X, y, cv=KFold(5, shuffle=True, random_state=0)).mean()


def purged_score(make_model) -> float:
    scores = []
    for train, test in ml.purged_kfold(len(X), 5, horizon=HORIZON, embargo=HORIZON):
        model = make_model().fit(X.iloc[train], y.iloc[train])
        scores.append(model.score(X.iloc[test], y.iloc[test]))
    return float(np.mean(scores))


print(f"Random forest accuracy — shuffled K-fold: {shuffled:.3f}  |  purged K-fold: {purged_score(make_rf):.3f}")
print("The gap is information leaking from the future, not skill.")

# %% [markdown]
# ## 2. Model comparison with purged CV

# %%
make_lr = lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=1000))  # noqa: E731
print(f"Baseline (always predict majority): {max(y.mean(), 1 - y.mean()):.3f}")
print(f"Logistic regression (purged):       {purged_score(make_lr):.3f}")
print(f"Random forest (purged):             {purged_score(make_rf):.3f}")

# %% [markdown]
# ## 3. What is the model using? Permutation importance on a held-out block

# %%
split = int(len(X) * 0.7)
rf = make_rf().fit(X.iloc[: split - HORIZON], y.iloc[: split - HORIZON])
imp = permutation_importance(rf, X.iloc[split:], y.iloc[split:], n_repeats=10, random_state=0)
print(pd.Series(imp.importances_mean, index=features).sort_values(ascending=False).round(4).to_string())
print("\nThe planted signal is one-day momentum: do the short-horizon return features rank near the top?")

# %% [markdown]
# ## 4. Walk-forward trading simulation
# Retrain every 250 days on all prior data (with a gap equal to the label horizon),
# trade the next 250 days, and pay 5 bps per unit of turnover.

# %%
splits = list(ml.walk_forward_splits(len(X), train_size=750, test_size=250, gap=HORIZON))
results = {}
for name, factory in {"logistic": make_lr, "random forest": make_rf}.items():
    proba = ml.out_of_fold_proba(factory, X, y, splits).dropna()
    position = ml.proba_to_position(proba, threshold=0.55)
    close = bars["close"].reindex(proba.index)
    res = bt.vectorized_backtest(close, position, cost_bps=5)
    results[name] = metrics.performance_summary(res["strategy_return"])
oos_close = bars["close"].reindex(proba.index)
results["buy & hold"] = metrics.performance_summary(oos_close.pct_change().dropna())
print(pd.DataFrame(results).loc[["cagr", "volatility", "sharpe", "max_drawdown", "hit_rate"]].round(3))

# %% [markdown]
# ## Exercises
# 1. Add meta-labelling: train a second model that decides *whether* to take the
#    primary SMA signal, using the triple-barrier outcome as its label.
# 2. Replace the random forest with gradient boosting (`HistGradientBoostingClassifier`).
# 3. Run the pipeline on real Nifty data. Is there anything left after costs?
