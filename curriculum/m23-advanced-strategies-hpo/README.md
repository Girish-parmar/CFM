# M23 · Advanced Strategies and Hyperparameter Optimisation

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T5 · AI for Trading |
| Weeks | 45–46 |
| Hours | 24 guided |
| Labs | [23a](lab_23a_boosting_hpo.py) — HGB/XGBoost/LightGBM, random search, Optuna, nested walk-forward, PBO<br>[23b](lab_23b_regimes_kalman_garch.py) — Markov regimes, GARCH volatility targeting, Kalman-filter pairs<br>[23c](lab_23c_meta_labeling_ensembles.py) — Meta-labelling, bet sizing, multi-strategy allocation<br>[23d](lab_23d_segment_optimisation.py) — Day/month/expiry/regime/pattern segments, FDR, per-segment walk-forward |
| Library | `cfmat.ml.tuning`, `cfmat.econometrics`, `cfmat.research.segments` |
| Prerequisites | [M14](../m14-portfolio-management/README.md), [M19](../m19-machine-learning/README.md) |
| Committed topics | Strategy optimisation by segment (day, month, regime, pattern), Machine-learning techniques, Portfolio management methods, Statistics in finance |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

This is where the programme's tools meet: tuned gradient boosting, regime models, adaptive
hedge ratios, meta-labelling, strategy ensembles and strategy optimisation by segment (day,
month, regime, pattern). Each is powerful, and each multiplies the number of things a researcher
can try. The module's real subject is paying for that search: nested walk-forward estimates,
the deflated Sharpe ratio, the probability of backtest overfitting and false-discovery control.

## Learning outcomes

By the end of the module you can:

1. Train gradient-boosted trees (HistGradientBoosting, XGBoost, LightGBM) for trading and explain their key hyperparameters.
2. Tune with random search and Bayesian optimisation (Optuna TPE) scored by purged cross-validation, and choose a sensible objective (log loss vs trading Sharpe).
3. Estimate performance honestly with nested walk-forward tuning, and charge the result with the deflated Sharpe ratio and the probability of backtest overfitting (CSCV).
4. Detect regimes with Markov-switching models and trade on filtered (not smoothed) probabilities; forecast volatility with GARCH and build volatility-managed strategies.
5. Trade pairs with a Kalman-filter hedge ratio that adapts as the relationship drifts.
6. Use meta-labelling to filter and size a primary strategy's trades, and combine strategy sleeves with rolling allocation.
7. Segment history by weekday, month, turn of month, expiry week, volatility and trend regime, and price pattern without look-ahead; test every segment with FDR control; optimise parameters per segment walk-forward; and feed segment labels to a boosted model.

## Before you start

- M14 (allocation) and M19 (purged CV, walk-forward) complete.
- `pip install -e ".[boost]"` (or `xgboost-cpu lightgbm optuna`); the labs skip those parts if absent.

## Weekly plan

### Week 45 — Boosting, hyperparameter optimisation, meta-labelling and regimes

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M22 · 15–60 gradient boosting: trees, learning rate, depth/leaves, subsampling, regularisation; HGB vs XGBoost vs LightGBM · 60–70 break · 70–125 hyperparameter optimisation: random search, TPE, purged-CV objectives; nested walk-forward; DSR and PBO · 125–170 live: Lab 23a §1–§4 · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 regimes: Markov switching, filtered vs smoothed probabilities; GARCH volatility targeting · 60–70 break · 70–120 Kalman-filter hedge ratios for drifting pairs · 120–170 meta-labelling and bet sizing (Lab 23c §1–§3) · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 23a §5–§6 (DSR, PBO, importance); Lab 23b · 100–120 blockers |
| OH · Wed · 60 min | Capstone research-review preparation |
| C2 · Thu · 120 min | 0–60 Lab 23c · 60–100 peer review · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 23a · 20–50 "count the trials" exercise on a capstone draft · 50–60 preview |
| Self-study · ~6 h | López de Prado ch. 3, 11–12; Bailey et al. (2016) on PBO |

### Week 46 — Segment optimisation, strategy ensembles and overfitting control

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 segmentation: calendar (weekday, month, turn of month, expiry week), regime (volatility, trend) and pattern labels known before the session · 60–70 break · 70–120 testing many segments: BH q-values, split-half stability · 120–170 live: Lab 23d §1–§3 · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 per-segment parameters walk-forward; calendar and pattern filters; boosting with segment features · 60–70 break · 70–130 workshop: Lab 23d §4–§5 and Lab 23c §4 (a portfolio of strategies) · 130–170 synthesis: a checklist for any "advanced" result — trials, nesting, DSR, PBO, FDR, stability · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 23d exercises · 100–120 review |
| OH · Wed · 60 min | Assignment clinic |
| C2 · Thu · 120 min | 0–60 capstone research review rehearsals · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 23b · 20–50 peer review of mini-project drafts · 50–60 briefing for Review 3 and Bootcamp 3 |
| Self-study · ~6 h | Harvey and Liu on multiple testing; finish the assignment |

## Labs

| Lab | You do | What good looks like |
|---|---|---|
| **23a** boosting and HPO (`lab_23a_boosting_hpo.py`) | Baselines, random search, Optuna, XGBoost/LightGBM, nested walk-forward, DSR and PBO, importance | Nested estimate below the best CV score; DSR and PBO reported with the trial count |
| **23b** regimes, Kalman, GARCH (`lab_23b_regimes_kalman_garch.py`) | Filtered vs smoothed regime filter; GARCH recovery and volatility targeting; Kalman pairs vs static hedge | Smoothed (look-ahead) filter flatters; Kalman tracks a drifting beta |
| **23c** meta-labelling and ensembles (`lab_23c_meta_labeling_ensembles.py`) | Primary trend model, meta-model, bet sizing, multi-strategy allocation | Meta-labels raise precision; ensembles beat most single sleeves |
| **23d** segment optimisation (`lab_23d_segment_optimisation.py`) | 34 segments with FDR, stability, per-regime walk-forward, filters, boosting with segment features | Planted effects survive BH and both halves; per-regime parameters beat one global set out of sample |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 23a, 23b | quizzes (10%) | Fri W45, W46 | Concepts and trial-counting |
| Labs 23a–23d | labs (20%) | Sun W46 | Run; overfitting controls reported |
| Assignment: an advanced strategy, honestly priced | assignments (15%) | Sun W48 | One advanced method applied to your capstone universe, with nested walk-forward, the full trial count, DSR, PBO or FDR as appropriate, and a stability check. Rubric: rigour 40, results 25, controls 25, clarity 10 |
| Term exam 3 | term exams (20%) | Week 47 | Covers M13–M23 |

## Common mistakes

- Tuning on the same folds you report → nested walk-forward.
- Trading on smoothed regime probabilities → filtered only (the smoothed series uses the future).
- Keeping every segment with p < 0.05 → BH q-values and split-half stability.
- Reporting the ensemble built from the best sleeves of a large search without charging for the search → PBO/DSR.

## Readings

- Marcos López de Prado, *Advances in Financial Machine Learning*, ch. 3, 6, 11–12, 14.
- Bailey, Borwein, López de Prado and Zhu (2016), "The Probability of Backtest Overfitting".
- Akiba et al. (2019), "Optuna".
- Hamilton (1989) on regime switching; Engle (2001), "GARCH 101".
- Chan, *Algorithmic Trading*, ch. 3 (Kalman filter).

## Instructor notes

- Owner: ML/DL and advanced strategies lead.
- Labs 23a and 23d are the slowest in the course (~60 s each on a laptop); run them before class and discuss outputs live.
- CI installs `xgboost-cpu`, `lightgbm` and `optuna`; learners without them see those sections skipped, not failed.
