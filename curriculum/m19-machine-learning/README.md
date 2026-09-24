# M19 · Machine Learning for Trading

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T5 · AI for Trading |
| Weeks | 39–40 |
| Hours | 24 guided |
| Labs | [19a](lab_19a_machine_learning.py) — Features, triple barrier, leakage vs purged CV, walk-forward trading |
| Library | `cfmat.ml` |
| Prerequisites | [M04](../m04-statistics-time-series/README.md), [M11](../m11-backtesting-research/README.md) |
| Committed topics | Machine-learning techniques |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Machine learning finds patterns with ruthless efficiency — including patterns that come from the
future through careless labels, shuffled folds or overlapping windows. In finance the signal is
weak and the leakage is strong, so the methodology matters more than the model. This module
teaches features, labels, validation and sizing so that M20–M23 and ML capstones are honest.

## Learning outcomes

By the end of the module you can:

1. Frame trading problems as supervised learning tasks with suitable targets and horizons.
2. Engineer features that use only information available at decision time (`cfmat.ml.make_features`).
3. Label with fixed-horizon and triple-barrier methods, and explain overlapping labels.
4. Validate with purged, embargoed K-fold and walk-forward splits, and show how shuffled K-fold leaks.
5. Train and compare linear models, random forests and gradient boosting; interpret with permutation importance on a held-out block.
6. Turn predicted probabilities into positions and bet sizes, and monitor models for decay.

## Before you start

- M04 (statistics) and M11 (walk-forward) complete.
- Read López de Prado, *Advances in Financial Machine Learning*, ch. 3 and 7.

## Weekly plan

### Week 39 — Features, labels and leakage

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M18 · 15–60 framing: classification vs regression, horizons, the base rate; why accuracy misleads · 60–70 break · 70–120 features from prices, volumes and fundamentals; point-in-time discipline; stationarity of features · 120–170 labels: fixed horizon, triple barrier, overlapping labels and sample uniqueness · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 leakage taxonomy: look-ahead features, overlapping labels across folds, scaling on the full sample, target leakage · 60–70 break · 70–130 workshop: Lab 19a §1 — shuffled vs purged K-fold on the same model · 130–170 capstone track kick-off: proposal template and pre-registration rules · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 19a §1–§2 · 100–120 blockers |
| OH · Wed · 60 min | ML Q&A; capstone proposals |
| C2 · Thu · 120 min | 0–60 exercise: add a leaky feature and watch the metrics jump · 60–100 peer review · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 19a · 20–50 leakage hunt on code cards · 50–60 preview |
| Self-study · ~6 h | López de Prado ch. 3–4, 7; capstone proposal |

### Week 40 — Purged cross-validation, walk-forward and model-driven trading

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 purged and embargoed K-fold; walk-forward splits; out-of-fold predictions · 60–70 break · 70–120 model families: regularised linear, random forests, gradient boosting (HGB); hyperparameters that matter · 120–170 interpretation: permutation importance on held-out blocks; SHAP (intuition); why MDI importance misleads · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 probabilities to positions: thresholds, bet sizing (`ml.proba_to_position`, `bet_size`), costs · 60–70 break · 70–130 workshop: Lab 19a §3–§4 — walk-forward trading simulation · 130–170 model monitoring and decay: calibration drift, feature drift, retraining cadence · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 19a §3–§4 and exercises · 100–120 review |
| OH · Wed · 60 min | Capstone pre-registration clinic (due W40) |
| C2 · Thu · 120 min | 0–60 exercise: sizing by probability vs fixed size · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 19b · 20–50 peer review of pre-registrations · 50–60 preview of M20 |
| Self-study · ~6 h | Jansen ch. 6–12 (selected); López de Prado ch. 8, 10 |

## Labs

**Lab 19a — machine learning for trading** (`lab_19a_machine_learning.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. The leakage trap | Same random forest, shuffled vs purged K-fold | Shuffled accuracy clearly higher — that gap is leakage |
| 2. Model comparison | Baseline, logistic, random forest under purged CV | Simple model competitive; RF not magic |
| 3. Importance | Permutation importance on a held-out block | The planted one-day momentum feature ranks first |
| 4. Walk-forward trading | Models trade out of sample after costs | Sharpe reported next to buy and hold |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 19a, 19b | quizzes (10%) | Fri W39, W40 | Leakage, validation, sizing |
| Lab 19a | labs (20%) | Sun W40 | Runs; the leakage gap explained |
| Assignment: an ML signal, honestly validated | assignments (15%) | Sun W42 | On a universe of ≥ 20 stocks: features, triple-barrier labels, purged CV, walk-forward trading after costs, and a leakage checklist signed off by a peer. Rubric: methodology 40, results 25, leakage checks 20, clarity 15 |
| Capstone pre-registration | capstone | Week 40 | See [capstone](../../course/06-capstone.md) |

## Common mistakes

- Shuffled K-fold on overlapping labels → purged K-fold with an embargo.
- Fitting the scaler on all data → pipelines fitted inside each fold.
- Reporting accuracy on imbalanced labels → compare with the base rate and use log loss or AUC.
- Tuning on the test period → walk-forward with the test window untouched; nested tuning in M23.

## Readings

- Marcos López de Prado, *Advances in Financial Machine Learning*, ch. 3–4, 7–8, 10.
- Stefan Jansen, *Machine Learning for Algorithmic Trading*, ch. 6–12 (selected).
- Gu, Kelly and Xiu (2020), "Empirical Asset Pricing via Machine Learning".

## Instructor notes

- Owner: ML/DL and advanced strategies lead.
- The capstone track (2 h a week, W39–W46) starts here: proposals in W39, pre-registration in W40.
- If a learner's ML result looks too good, assume leakage first. Model that habit in class.
