"""Reinforcement learning for trading (Module 13): tabular Q-learning.

Deliberately small so every moving part is visible — state, action, reward,
Bellman update, exploration. Deep RL (DQN, PPO) replaces the table with a
neural network but keeps exactly this loop.

State  = (signs of the last ``n_lags`` returns, current position)
Action = target position in {−1, 0, +1}
Reward = position · next return − cost · |change in position|
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

ACTIONS = (-1, 0, 1)


@dataclass
class QLearningTrader:
    n_lags: int = 3
    alpha: float = 0.05          # learning rate
    gamma: float = 0.9           # discount factor
    epsilon: float = 0.1         # exploration rate
    cost: float = 0.0005         # per unit of turnover
    seed: int = 0
    q: dict = field(default_factory=dict)

    def _state(self, returns: np.ndarray, t: int, position: int) -> tuple:
        window = returns[t - self.n_lags + 1 : t + 1]
        return (*np.sign(window).astype(int).tolist(), position)

    def _values(self, state: tuple) -> np.ndarray:
        return self.q.setdefault(state, np.zeros(len(ACTIONS)))

    def fit(self, returns: pd.Series, episodes: int = 20) -> "QLearningTrader":
        rng = np.random.default_rng(self.seed)
        r = returns.to_numpy(dtype=float)
        for _ in range(episodes):
            position = 0
            for t in range(self.n_lags - 1, len(r) - 1):
                state = self._state(r, t, position)
                values = self._values(state)
                a = int(rng.integers(len(ACTIONS))) if rng.random() < self.epsilon else int(np.argmax(values))
                new_position = ACTIONS[a]
                reward = new_position * r[t + 1] - self.cost * abs(new_position - position)
                next_state = self._state(r, t + 1, new_position)
                target = reward + self.gamma * self._values(next_state).max()
                values[a] += self.alpha * (target - values[a])
                position = new_position
        return self

    def positions(self, returns: pd.Series) -> pd.Series:
        """Greedy positions decided at each bar's close (to be held over the next bar)."""
        r = returns.to_numpy(dtype=float)
        out = np.zeros(len(r))
        position = 0
        for t in range(self.n_lags - 1, len(r)):
            position = ACTIONS[int(np.argmax(self._values(self._state(r, t, position))))]
            out[t] = position
        return pd.Series(out, index=returns.index)

    def policy_table(self) -> pd.DataFrame:
        rows = [{"state": s, **{f"Q[{a:+d}]": v for a, v in zip(ACTIONS, vals)}, "best": ACTIONS[int(np.argmax(vals))]}
                for s, vals in sorted(self.q.items())]
        return pd.DataFrame(rows)
