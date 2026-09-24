# Module 13 — Deep Learning and Reinforcement Learning

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 4 · AI and Automation | 29–30 | 20 | [`lab13_deep_learning_rl.py`](../../labs/lab13_deep_learning_rl.py) |

## Learning outcomes

1. Train neural networks with proper regularisation, early stopping and chronological validation.
2. Apply sequence models (LSTM, GRU, temporal CNN, Transformer) to financial time series, and judge when they help.
3. Use autoencoders for denoising, factor extraction and anomaly detection.
4. Formulate trading and execution problems as Markov decision processes.
5. Implement Q-learning, and explain DQN and policy-gradient methods (PPO).
6. Design realistic RL environments (costs, latency, position limits) and reward functions.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Neural networks (Sat, W29) | Perceptrons to MLPs; backpropagation; optimisers; regularisation (weight decay, dropout, early stopping); why financial data is hard for deep learning |
| L2 | Sequence models (Sun, W29) | RNN, LSTM, GRU; temporal CNNs; attention and Transformers for time series; autoencoders; GPU training basics |
| L3 | Reinforcement learning (Sat, W30) | MDPs, value functions, Bellman equations; Q-learning; DQN; policy gradients and PPO; exploration |
| L4 | RL in trading (Sun, W30) | Environment design; reward shaping (P&L, risk-adjusted, costs); RL for execution and allocation; evaluation against strong baselines; common failure modes |
| C1–C4 | Clinics | MLP forecasting; LSTM exercise (below, on GPU lab); Q-learning (Lab 13); gymnasium environment |

## LSTM exercise (PyTorch)

Requires `pip install torch` (GPU optional). Reuse the `windows` and `target` arrays from Lab 13, split chronologically. This snippet is a starting scaffold; it is not run by the course test suite.

```python
import torch
from torch import nn


class LSTMForecaster(nn.Module):
    def __init__(self, n_features: int = 1, hidden: int = 32):
        super().__init__()
        self.lstm = nn.LSTM(n_features, hidden, batch_first=True)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x):                      # x: (batch, lookback, n_features)
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :]).squeeze(-1)   # logit of "next return > 0"


split = int(len(windows) * 0.7)                # chronological, never shuffled
windows_train, windows_test = windows[:split], windows[split:]
target_train = target[:split]

X_train = torch.tensor(windows_train, dtype=torch.float32).unsqueeze(-1)
y_train = torch.tensor(target_train, dtype=torch.float32)
X_test = torch.tensor(windows_test, dtype=torch.float32).unsqueeze(-1)

model = LSTMForecaster()
optimiser = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
loss_fn = nn.BCEWithLogitsLoss()
for epoch in range(30):
    model.train()
    for i in range(0, len(X_train), 128):      # chronological mini-batches
        optimiser.zero_grad()
        loss = loss_fn(model(X_train[i:i + 128]), y_train[i:i + 128])
        loss.backward()
        optimiser.step()

model.eval()
with torch.no_grad():
    proba = torch.sigmoid(model(X_test)).numpy()
```

Tasks: add a validation split and early stopping; compare with the logistic and MLP results from Lab 13; then repeat on real index data and explain the difference.

## Readings

- Goodfellow, Bengio and Courville, *Deep Learning*: chapters 6–8, 10.
- Sutton and Barto, *Reinforcement Learning: An Introduction*: chapters 1–6, 13.
- Hochreiter and Schmidhuber (1997), "Long Short-Term Memory".
- Vaswani et al. (2017), "Attention Is All You Need".
- Stefan Jansen, *Machine Learning for Algorithmic Trading*: chapters 17–22.

## Assessment

Quiz 13; Lab 13; LSTM exercise (part of the lab score).
