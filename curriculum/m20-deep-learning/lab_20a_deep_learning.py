# %% [markdown]
# # Lab 20a — Neural Networks for Return Forecasting, Honestly Evaluated (M20)
#
# **Goals**
# 1. Frame forecasting as supervised learning on sliding windows of past returns.
# 2. Train a neural network (multi-layer perceptron) and compare it with logistic
#    regression on a chronological split, after costs.
# 3. See when a network earns its complexity: on a *linear* signal it does not; on a
#    *nonlinear* one (momentum after small moves, reversal after large ones) it does.
#
# The LSTM version (PyTorch) is an exercise in the module guide; this lab uses scikit-learn
# so it runs on any laptop without a GPU.

# %%
import warnings

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from cfmat import data
from cfmat.analytics import metrics
from cfmat.backtesting import vectorized as bt

warnings.filterwarnings("ignore", category=ConvergenceWarning)
LOOKBACK = 5        # five lags; every irrelevant input makes a network hungrier for data


def windows(rets: pd.Series, lookback: int = LOOKBACK) -> tuple[pd.DataFrame, pd.Series]:
    """Rows of the ``lookback`` returns before each target day; target = sign of that day's return."""
    values = rets.to_numpy()
    X = np.lib.stride_tricks.sliding_window_view(values, lookback)[:-1]
    index = rets.index[lookback:]                      # date of the return being predicted
    return (pd.DataFrame(X, index=index, columns=[f"lag_{lookback - i}" for i in range(lookback)]),
            pd.Series((values[lookback:] > 0).astype(int), index=index))


def models() -> dict:
    return {
        "logistic": make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=1000)),
        "MLP (16 hidden units)": make_pipeline(StandardScaler(), MLPClassifier(
            hidden_layer_sizes=(16,), alpha=1e-2, max_iter=400, random_state=0)),
    }


def evaluate(close: pd.Series, split_frac: float = 0.7) -> pd.DataFrame:
    X, y = windows(metrics.log_returns(close))
    split = int(len(X) * split_frac)
    rows = []
    for name, model in models().items():
        model.fit(X.iloc[:split], y.iloc[:split])                 # past only: no shuffling across the split
        proba = model.predict_proba(X.iloc[split:])[:, 1]
        test_index = X.index[split:]
        position = pd.Series(np.where(proba > 0.5, 1.0, -1.0), index=test_index)
        # the position for day t is decided at t−1's close; the backtester shifts by one bar itself
        signal = position.shift(-1).reindex(close.index).fillna(0.0)
        res = bt.vectorized_backtest(close, signal, cost_bps=5).loc[test_index]
        rows.append({"model": name, "accuracy": accuracy_score(y.iloc[split:], proba > 0.5),
                     "auc": roc_auc_score(y.iloc[split:], proba),
                     "sharpe_after_costs": metrics.sharpe_ratio(res["strategy_return"])})
    return pd.DataFrame(rows).set_index("model")


# %% [markdown]
# ## 1. A linear signal: returns follow AR(1) with coefficient 0.15

# %%
linear = data.ar1_prices(3000, phi=0.15, seed=31)
print(evaluate(linear).round(3))
print("\nThe network has over a hundred parameters and finds nothing the 6-parameter logistic model misses.")

# %% [markdown]
# ## 2. A nonlinear signal: momentum after small moves, reversal after large ones
# r_t = 0.3·r_{t−1} if |r_{t−1}| ≤ 1σ, else −0.5·r_{t−1}, plus noise. A linear model can
# only fit one average slope; a network can bend.

# %%
rng = np.random.default_rng(4)
sd, n = 0.012, 6000
r = np.zeros(n)
for t in range(1, n):
    slope = -0.5 if abs(r[t - 1]) > sd else 0.3
    r[t] = slope * r[t - 1] + rng.normal(0, sd)
nonlinear = pd.Series(100 * np.exp(np.cumsum(r)), index=data.trading_days(n, "2002-01-01"), name="close")
print(evaluate(nonlinear).round(3))
print("\nNow the network wins on AUC, because the relationship it can represent is actually there.")
print("Here the better ranking also pays after costs. That is not guaranteed: always check the Sharpe column.")

# %% [markdown]
# ## 3. What the network learned
# Probability of an up day as a function of yesterday's return (other lags set to zero).

# %%
X, y = windows(metrics.log_returns(nonlinear))
mlp = models()["MLP (16 hidden units)"].fit(X.iloc[: int(len(X) * 0.7)], y.iloc[: int(len(X) * 0.7)])
grid = np.linspace(-3 * sd, 3 * sd, 13)
probe = pd.DataFrame(0.0, index=range(len(grid)), columns=X.columns)
probe["lag_1"] = grid
curve = pd.Series(mlp.predict_proba(probe)[:, 1], index=np.round(grid / sd, 1))
print("P(up tomorrow) by yesterday's return (in σ):\n", curve.round(3).to_string())

# %% [markdown]
# ## Exercises
# 1. Replace the MLP with the PyTorch LSTM from the module guide. Does sequence modelling
#    help on section 2's data? On real Nifty data?
# 2. Set `LOOKBACK = 20`. The network now loses on section 2's data too: fifteen extra noise
#    inputs. How much more data does it need to win again?
# 3. Add a larger L2 penalty (`alpha`) and plot out-of-sample AUC against model size.
# 4. Walk the split forward (five folds, `cfmat.ml.walk_forward_splits`) and report the spread of
#    AUCs. How much of the gap between the two models is noise?
