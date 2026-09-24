# Module 12 — Machine Learning for Trading

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 4 · AI and Automation | 27–28 | 20 | [`lab12_machine_learning.py`](../../labs/lab12_machine_learning.py) |

## Learning outcomes

1. Frame trading problems as supervised learning tasks with suitable targets.
2. Engineer features that use only information available at decision time.
3. Label data with fixed-horizon and triple-barrier methods, and use meta-labelling.
4. Validate with purged, embargoed cross-validation and walk-forward splits.
5. Train and compare linear models, random forests and gradient boosting; interpret them with permutation importance and SHAP.
6. Convert predicted probabilities into positions and bet sizes, and monitor models for decay.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Framing and features (Sat, W27) | Classification vs regression targets; stationarity of features; fractional differencing (intro); feature families (price, volume, volatility, fundamentals, alternative data) |
| L2 | Labels and validation (Sun, W27) | Fixed-horizon vs triple-barrier labels; sample overlap and uniqueness; purged K-fold with embargo; walk-forward |
| L3 | Models and interpretation (Sat, W28) | Regularised logistic regression, random forests, gradient boosting; hyperparameter search inside CV; permutation importance, SHAP; meta-labelling |
| L4 | From model to strategy (Sun, W28) | Probabilities to positions; bet sizing; costs; model monitoring, drift and decay; model risk governance |
| C1–C4 | Clinics | Feature and label pipeline; leakage hunt; Lab 12; meta-labelling exercise |

## Assignment (Mini-project 3, due Week 33)

Build an ML-driven strategy or meta-labelling layer on real data using purged CV. Report the gap between shuffled and purged CV scores, out-of-sample performance after costs, and feature importance, and say honestly whether there is an edge.

## Readings

- Marcos López de Prado, *Advances in Financial Machine Learning*: chapters 2–9.
- Stefan Jansen, *Machine Learning for Algorithmic Trading*: chapters 6–12.
- Gu, Kelly and Xiu (2020), "Empirical Asset Pricing via Machine Learning".

## Assessment

Quiz 12; Lab 12; Mini-project 3.
