# Module 16 — Advanced Strategies and Hyperparameter Optimisation

| Term | Weeks | Hours | Labs |
|---|---|---|---|
| 4 · AI and Automation | 34–35 | 20 (4 live × 3 h + 4 clinics × 2 h) | [`lab16_boosting_hyperparameter_tuning.py`](../../labs/lab16_boosting_hyperparameter_tuning.py), [`lab17_regimes_kalman_garch.py`](../../labs/lab17_regimes_kalman_garch.py), [`lab18_meta_labeling_ensembles.py`](../../labs/lab18_meta_labeling_ensembles.py) |

Prerequisites: Modules 7, 8, 9 and 12. Optional packages: `pip install xgboost lightgbm optuna` (`xgboost-cpu` is a small CPU-only build).

## Learning outcomes

1. Train gradient-boosted tree models (HistGradientBoosting, XGBoost, LightGBM) for trading and explain their main hyperparameters (learning rate, number of trees, depth/leaves, minimum leaf size, subsampling, regularisation).
2. Tune hyperparameters with random search and Bayesian optimisation (Optuna TPE) scored by purged cross-validation, and choose a sensible objective (log loss vs trading Sharpe).
3. Estimate performance honestly with nested walk-forward tuning, and charge the result for every configuration tried with the Deflated Sharpe Ratio and the Probability of Backtest Overfitting (CSCV).
4. Detect market regimes with Markov-switching models and trade on *filtered* (not smoothed) regime probabilities.
5. Forecast volatility with GARCH(1,1) and build volatility-managed strategies.
6. Trade pairs with a Kalman-filter hedge ratio that adapts as the relationship drifts.
7. Use meta-labelling to filter and size the trades of a primary strategy.
8. Combine uncorrelated strategy sleeves with inverse-volatility, risk-parity and HRP allocation re-estimated from trailing data.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Gradient boosting for trading (Sat, W34) | How boosting works (additive trees, shrinkage, regularisation); HistGradientBoosting vs XGBoost vs LightGBM; why untuned boosting overfits noisy financial data; non-linear and interaction effects (for example momentum that flips sign in high volatility) |
| L2 | Hyperparameter optimisation done honestly (Sun, W34) | Search spaces and log-scales; random search vs Bayesian optimisation (TPE); purged CV as the objective; the optimism of "best CV score"; nested walk-forward; counting trials; Deflated Sharpe Ratio; Probability of Backtest Overfitting with CSCV |
| C1 | Clinic (Tue, W34) | Lab 16: boosting, random search, Optuna, XGBoost and LightGBM, nested walk-forward, DSR and PBO |
| C2 | Clinic (Thu, W34) | Lab 16 exercises: optimise Sharpe directly; early stopping; LightGBM + Optuna nested |
| L3 | Regimes, volatility and adaptive hedges (Sat, W35) | Markov-switching models; Hamilton filter vs Kim smoother (and why the smoother is look-ahead); GARCH(1,1) estimation and forecasting; volatility-managed portfolios; Kalman filters for time-varying hedge ratios |
| L4 | Meta-labelling and strategy portfolios (Sun, W35) | Primary vs secondary models; meta-labels from triple barriers; precision, recall and bet sizing; building a book of uncorrelated sleeves; inverse-vol, risk parity and HRP across strategies; capacity and decay |
| C3 | Clinic (Tue, W35) | Lab 17: regime filter, GARCH vol targeting, Kalman pairs |
| C4 | Clinic (Thu, W35) | Lab 18: meta-labelling and strategy ensembles; Mini-project 3 surgery |

## What the labs show (on synthetic data with planted effects)

| Lab | Result you should reproduce |
|---|---|
| 16 | Untuned boosting scores *worse* than a coin flip on log loss; tuned boosting finds the regime-dependent signal that logistic regression misses; nested walk-forward Sharpe is lower than the "best-of-search" Sharpe on the same dates; the edge survives the Deflated Sharpe Ratio and has a low PBO |
| 17 | The filtered regime strategy cuts drawdown versus buy & hold; the smoothed version looks far better only because it peeks at the future; GARCH recovers known parameters and vol-targeting improves Sharpe; the Kalman hedge ratio tracks a drifting beta far better than fixed or rolling OLS |
| 18 | Meta-labelling raises the precision of a trend follower and cuts its drawdown; allocation across four uncorrelated sleeves beats every single sleeve on a risk-adjusted basis, with HRP/risk parity ahead of equal weights |

Results on real market data will be weaker. The labs are built so that you can see each method work when an effect exists, and then check honestly whether it exists in real data.

## Assignment (feeds Mini-project 3, due Week 35)

Take the ML strategy from Module 12. Tune a gradient-boosted model with nested walk-forward (random search or Optuna), report the in-sample vs nested out-of-sample gap, the Deflated Sharpe Ratio with the total number of configurations you tried, and the PBO. Then add one of: a regime filter, GARCH volatility targeting, or a meta-labelling layer, and show whether it helps out of sample.

## Readings

- Chen and Guestrin (2016), "XGBoost: A Scalable Tree Boosting System"; Ke et al. (2017), "LightGBM".
- Bergstra and Bengio (2012), "Random Search for Hyper-Parameter Optimization"; Akiba et al. (2019), "Optuna".
- Bailey, Borwein, López de Prado and Zhu (2017), "The Probability of Backtest Overfitting".
- Marcos López de Prado, *Advances in Financial Machine Learning*: chapters 3.6 (meta-labelling), 9 (hyperparameter tuning with CV), 10 (bet sizing), 11–12.
- Hamilton (1989), "A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle".
- Bollerslev (1986), "Generalized Autoregressive Conditional Heteroskedasticity"; Moreira and Muir (2017), "Volatility-Managed Portfolios".
- Ernest P. Chan, *Algorithmic Trading*: chapter 3 (Kalman filter pairs).

## Assessment

Quiz 16; Labs 16–18; Mini-project 3.
