# M20 · Deep Learning for Financial Time Series

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T5 · AI for Trading |
| Weeks | 41 |
| Hours | 12 guided |
| Labs | [20a](lab_20a_deep_learning.py) — Sliding windows, MLP vs logistic on linear and nonlinear signals |
| Library | `cfmat.ml` |
| Prerequisites | [M19](../m19-machine-learning/README.md) |
| Committed topics | Deep-learning techniques |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Deep learning dominates images and language, but daily financial returns are short, noisy and
non-stationary. A network earns its complexity only when the relationship it can represent is
actually there and there is enough data to learn it. This one-week module teaches the tools
(MLPs, sequence models, autoencoders) and, above all, the judgement: when to reach for them and
how to prove they help.

## Learning outcomes

By the end of the module you can:

1. Train neural networks with regularisation (weight decay, dropout, early stopping) and chronological validation.
2. Frame forecasting on sliding windows without leakage.
3. Compare a network with a strong linear baseline after costs, and explain the result by the structure of the data.
4. Describe sequence models (LSTM, GRU, temporal CNN, Transformer) and when each is plausible for markets.
5. Use autoencoders for denoising and anomaly detection (concepts), and know their failure modes on financial data.

## Before you start

- M19 complete.
- Optional: `pip install torch` for the LSTM exercise (CPU is enough; GPU hours are provided).

## Weekly plan

### Week 41 — Neural networks for sequences — when they earn their complexity

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M19 · 15–60 from perceptrons to MLPs; backpropagation; optimisers; regularisation · 60–70 break · 70–120 why financial data is hard for deep learning: signal-to-noise, non-stationarity, small samples · 120–170 live: Lab 20a §1 — MLP vs logistic on a linear signal · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 sequence models: RNN, LSTM, GRU, temporal CNN; attention and Transformers for time series · 60–70 break · 70–130 workshop: Lab 20a §2–§3 — a nonlinear signal the network can find, and what it learned · 130–170 autoencoders: denoising, factor extraction, anomaly detection · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 20a and exercise 2 (20 lags) · 100–120 blockers |
| OH · Wed · 60 min | GPU lab help for the LSTM exercise |
| C2 · Thu · 120 min | 0–90 LSTM exercise (below) · 90–120 results compared |
| QP · Fri · 60 min | 0–20 quiz 20 · 20–50 capstone midpoint preparation · 50–60 preview of M21 |
| Self-study · ~6 h | Goodfellow et al. ch. 6–8, 10; ML signal assignment |

## Labs

**Lab 20a — neural networks for return forecasting, honestly evaluated** (`lab_20a_deep_learning.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Linear signal | MLP vs logistic on AR(1) returns (5 lags) | No real gain from the network |
| 2. Nonlinear signal | Momentum after small moves, reversal after large ones | The MLP beats logistic on AUC and after costs |
| 3. What it learned | P(up) as a function of yesterday's return | The curve bends: reversal at the extremes, momentum near zero |

**LSTM exercise (PyTorch, optional).** Not run by the course test suite.

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


# X, y from windows(...) in Lab 20a; split chronologically, never shuffle across the split
split = int(len(X) * 0.7)
X_train = torch.tensor(X.iloc[:split].to_numpy(), dtype=torch.float32).unsqueeze(-1)
y_train = torch.tensor(y.iloc[:split].to_numpy(), dtype=torch.float32)
X_test = torch.tensor(X.iloc[split:].to_numpy(), dtype=torch.float32).unsqueeze(-1)

model = LSTMForecaster()
optimiser = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
loss_fn = nn.BCEWithLogitsLoss()
for epoch in range(30):
    model.train()
    for i in range(0, len(X_train), 128):
        optimiser.zero_grad()
        loss = loss_fn(model(X_train[i:i + 128]), y_train[i:i + 128])
        loss.backward()
        optimiser.step()

model.eval()
with torch.no_grad():
    proba = torch.sigmoid(model(X_test)).numpy()
```

Tasks: add a validation split and early stopping; compare with Lab 20a's logistic and MLP; repeat
on real index data and explain the difference.

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quiz 20 | quizzes (10%) | Fri W41 | Concepts |
| Lab 20a (+ LSTM exercise) | labs (20%) | Sun W41 | Runs; comparison explained by data structure |
| Capstone midpoint | capstone | Week 44 | See [capstone](../../course/06-capstone.md) |

## Common mistakes

- Shuffling sequences across the train/test boundary → chronological split only.
- Comparing a tuned network with an untuned baseline → tune both or neither.
- Declaring victory on accuracy without costs → the Sharpe column.
- Feeding 20 noisy lags to a small network and blaming deep learning → exercise 2.

## Readings

- Goodfellow, Bengio and Courville, *Deep Learning*, ch. 6–8, 10.
- Hochreiter and Schmidhuber (1997), "Long Short-Term Memory".
- Vaswani et al. (2017), "Attention Is All You Need".
- Stefan Jansen, *Machine Learning for Algorithmic Trading*, ch. 17–20.

## Instructor notes

- Owner: ML/DL and advanced strategies lead.
- GPU hours are provisioned for this week and M23; check quotas before the session.
- One week is short: keep Transformers to intuition and one diagram; the lab carries the lesson.
