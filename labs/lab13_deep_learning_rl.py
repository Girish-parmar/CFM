# %% [markdown]
# # Lab 13 — Deep Learning and Reinforcement Learning (Module 13)
#
# **Goals**
# 1. Frame forecasting as supervised learning on sliding windows.
# 2. Train a neural network (multi-layer perceptron) with early stopping and
#    compare it honestly with a linear model, out of sample.
# 3. Train a Q-learning agent, inspect its policy, and test it on unseen data.
#
# The LSTM version of part 2 (PyTorch) is in the Module 13 README as an exercise;
# this lab uses scikit-learn so it runs on any laptop without a GPU.

# %%
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from cfmat import backtest as bt
from cfmat import data, metrics
from cfmat.rl import QLearningTrader

# %% [markdown]
# ## 1. Sliding windows: the last 20 returns predict the sign of the next one

# %%
close = data.ar1_prices(3000, phi=0.15, seed=31)
rets = metrics.log_returns(close)
LOOKBACK = 20
windows = np.lib.stride_tricks.sliding_window_view(rets.to_numpy(), LOOKBACK)[:-1]
target = (rets.to_numpy()[LOOKBACK:] > 0).astype(int)
index = rets.index[LOOKBACK:]                     # date of the return being predicted
X = pd.DataFrame(windows, index=index, columns=[f"lag_{LOOKBACK - i}" for i in range(LOOKBACK)])
y = pd.Series(target, index=index)
print(X.shape, "— each row holds the 20 returns before the target day")

split = int(len(X) * 0.7)
X_train, X_test, y_train, y_test = X.iloc[:split], X.iloc[split:], y.iloc[:split], y.iloc[split:]

# %% [markdown]
# ## 2. Neural network vs logistic regression (chronological split, no shuffling)

# %%
models = {
    "logistic": make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=1000)),
    "MLP 32-16": make_pipeline(StandardScaler(), MLPClassifier(
        hidden_layer_sizes=(32, 16), alpha=1e-2, early_stopping=True, validation_fraction=0.2,
        n_iter_no_change=20, max_iter=500, random_state=0, shuffle=False)),
}
rows = []
for name, model in models.items():
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    position = pd.Series(np.where(proba > 0.5, 1.0, -1.0), index=X_test.index)
    # The position is known at the prior close, so align it to the previous bar for the backtester.
    signal = position.shift(-1).reindex(close.index).fillna(0.0)
    res = bt.vectorized_backtest(close, signal, cost_bps=5).loc[X_test.index]
    rows.append({"model": name, "accuracy": accuracy_score(y_test, proba > 0.5),
                 "auc": roc_auc_score(y_test, proba), "sharpe_after_costs": metrics.sharpe_ratio(res["strategy_return"])})
print(pd.DataFrame(rows).set_index("model").round(3))
print("\nIf the network does not beat the linear model, that is the lesson: the planted signal is linear.")

# %% [markdown]
# ## 3. Reinforcement learning: tabular Q-learning
# State = sign of the last return + current position; actions = short/flat/long.
# Train on the first 70%, freeze the policy, trade the last 30%. A small learning
# rate matters: daily rewards are mostly noise, so each Q-value must average many
# visits before the planted edge shows through.

# %%
train_r, test_r = rets.iloc[:split], rets.iloc[split:]
agent = QLearningTrader(n_lags=1, alpha=0.005, gamma=0.5, epsilon=0.1, cost=0.0005, seed=0).fit(train_r, episodes=30)
print(agent.policy_table().round(5).to_string(index=False))
print("State = (sign of last return, current position). Does 'best' follow the momentum?")

test_close = close.loc[test_r.index]
pos = agent.positions(test_r)
res = bt.vectorized_backtest(test_close, pos, cost_bps=5)
print(f"\nQ-learning out of sample: Sharpe {metrics.sharpe_ratio(res['strategy_return']):.2f}, "
      f"time in market {pos.abs().mean():.0%}")
print(f"Buy & hold same period : Sharpe {metrics.sharpe_ratio(test_close.pct_change().dropna()):.2f}")

# %% [markdown]
# ## Exercises
# 1. Replace the MLP with the PyTorch LSTM from the module README. Does sequence
#    modelling help on this data? On real data?
# 2. Add volatility regime (high/low) to the Q-learning state. What does the agent learn?
# 3. Swap the tabular agent for DQN (stable-baselines3) on a gymnasium environment
#    built from `cfmat.backtest.vectorized_backtest`.
