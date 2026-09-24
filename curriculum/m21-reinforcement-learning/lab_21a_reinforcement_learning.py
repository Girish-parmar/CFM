# %% [markdown]
# # Lab 21a — Reinforcement Learning for Trading: a Q-learning Agent, Taken Apart (M21)
#
# **Goals**
# 1. Train a tabular Q-learning agent: state = sign of the last return + current position,
#    actions = short / flat / long, reward = next return × position − costs.
# 2. Read its policy and compare it with the simple rule it *should* discover.
# 3. See how transaction costs change what the agent learns.
# 4. Measure how much the result depends on the random seed. RL results are fragile;
#    report the spread, never the best run.
#
# The market is synthetic with planted momentum (AR(1) coefficient 0.15). Train on the first
# 70%, freeze the policy, trade the last 30%.

# %%
import numpy as np
import pandas as pd

from cfmat import data
from cfmat.analytics import metrics
from cfmat.backtesting import vectorized as bt
from cfmat.ml.reinforcement import QLearningTrader

pd.set_option("display.width", 160)
close = data.ar1_prices(3000, phi=0.15, seed=31)
rets = metrics.log_returns(close)
split = int(len(rets) * 0.7)
train_r, test_r = rets.iloc[:split], rets.iloc[split:]
test_close = close.loc[test_r.index]


def oos_sharpe(agent: QLearningTrader, cost_bps: float = 5) -> tuple[float, float]:
    pos = agent.positions(test_r)
    res = bt.vectorized_backtest(test_close, pos, cost_bps=cost_bps)
    return metrics.sharpe_ratio(res["strategy_return"]), float(pos.diff().abs().sum())


# %% [markdown]
# ## 1. Train the agent and read its policy
# A small learning rate matters: daily rewards are mostly noise, so each Q-value must
# average many visits before the planted edge shows through.

# %%
agent = QLearningTrader(n_lags=1, alpha=0.005, gamma=0.5, epsilon=0.1, cost=0.0005, seed=0).fit(train_r, episodes=30)
print(agent.policy_table().round(5).to_string(index=False))
print("\nState = (sign of last return, current position). With momentum, 'best' should follow the last return.")

# %% [markdown]
# ## 2. Out of sample: the agent vs the rule it should have found

# %%
sharpe_agent, trades_agent = oos_sharpe(agent)
momentum_rule = np.sign(test_r).replace(0, 1.0)            # long after an up day, short after a down day
res_rule = bt.vectorized_backtest(test_close, momentum_rule, cost_bps=5)
print(pd.DataFrame({
    "Q-learning agent": {"sharpe": sharpe_agent, "position changes": trades_agent},
    "sign-of-last-return rule": {"sharpe": metrics.sharpe_ratio(res_rule["strategy_return"]),
                                 "position changes": float(momentum_rule.diff().abs().sum())},
    "buy & hold": {"sharpe": metrics.sharpe_ratio(test_close.pct_change().dropna()), "position changes": 0.0},
}).T.round(2))
print("\nAn agent that merely rediscovers a one-line rule is not a failure: it tells you the RL loop works.")

# %% [markdown]
# ## 3. Costs change the policy
# Train the same agent with 0, 5 and 20 bp of cost per unit of turnover in the reward.

# %%
rows = []
for cost_bp in (0, 5, 20):
    a = QLearningTrader(n_lags=1, alpha=0.005, gamma=0.5, epsilon=0.1, cost=cost_bp / 1e4, seed=0).fit(train_r, episodes=30)
    sr, changes = oos_sharpe(a, cost_bps=cost_bp)
    policy = a.policy_table().set_index("state")["best"]
    rows.append({"cost_bp": cost_bp, "oos_sharpe_after_costs": sr, "position changes": changes,
                 "states where it holds its position": int(sum(policy[s] == s[-1] for s in policy.index))})
print(pd.DataFrame(rows).set_index("cost_bp").round(2).to_string())
print("\nCosts in the reward change the policy: the agent trades less, and when the edge no longer")
print("pays for the turnover it learns to stay out. Both are the right answers.")

# %% [markdown]
# ## 4. Seed sensitivity: report the distribution, not the best run

# %%
results = []
for seed in range(10):
    a = QLearningTrader(n_lags=1, alpha=0.005, gamma=0.5, epsilon=0.1, cost=0.0005, seed=seed).fit(train_r, episodes=30)
    results.append(oos_sharpe(a)[0])
results = pd.Series(results, name="out-of-sample Sharpe")
print(results.describe().round(2).to_string())
fast = [oos_sharpe(QLearningTrader(n_lags=1, alpha=0.1, gamma=0.5, epsilon=0.1, cost=0.0005, seed=s)
                   .fit(train_r, episodes=30))[0] for s in range(10)]
print(f"\nWith a 20× larger learning rate (0.1): mean Sharpe {np.mean(fast):.2f}, "
      f"range {min(fast):.2f} to {max(fast):.2f}. Noisy rewards + fast learning = unstable policies.")

# %% [markdown]
# ## Exercises
# 1. Add a volatility regime (high/low) to the state. What does the agent learn on
#    `data.regime_prices`?
# 2. Replace the table with a function approximator: `sklearn.neural_network.MLPRegressor`
#    predicting Q-values from (last 5 returns, position). This is the core idea of DQN.
# 3. Build a gymnasium environment around `cfmat.backtesting.vectorized` and train PPO with
#    stable-baselines3. Compare its seed spread with section 4.
