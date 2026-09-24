# M04 · Statistics and Time Series for Finance

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T1 · Foundations |
| Weeks | 7–8 |
| Hours | 24 guided |
| Labs | [04a](lab_04a_statistics_time_series.py) — Fat tails, ADF, Ljung–Box, CAPM, cointegration, bootstrap Sharpe |
| Library | `cfmat.analytics.metrics`, `cfmat.analytics.stats` |
| Prerequisites | [M03](../m03-python-for-finance/README.md) |
| Committed topics | Statistics in finance |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Trading research is statistics under adversarial conditions: fat tails, dependence, regime
changes and thousands of tried ideas. Most false discoveries in this field come from misused
tests, not bad code. This module builds the statistical toolkit — and the scepticism — that
M06 (event studies), M11 (backtesting), M13 (VaR) and M19–M23 (machine learning) assume.

## Learning outcomes

By the end of the module you can:

1. Describe return distributions, measure skew, kurtosis and tail risk, and explain what fat tails do to normal-theory risk estimates.
2. Estimate parameters with confidence intervals, test hypotheses correctly, and explain p-values and their misuse.
3. Control for multiple testing with Bonferroni and Benjamini–Hochberg, and explain the difference between family-wise error and false-discovery rate.
4. Fit and interpret OLS regressions, including CAPM alpha and beta with heteroskedasticity- and autocorrelation-robust (HAC) standard errors.
5. Test time series for autocorrelation (Ljung–Box) and unit roots (ADF), and explain why prices and returns need different treatment.
6. Test for cointegration (Engle–Granger), estimate a spread's half-life and connect it to pairs trading.
7. Use the bootstrap and Monte Carlo simulation to measure uncertainty, including a confidence interval for a Sharpe ratio.

## Before you start

- M03 complete; pre-work Week −1 statistics refreshed.
- Be comfortable with `numpy.random.default_rng` and pandas `rolling`.

## Weekly plan

### Week 7 — Distributions, fat tails, estimation, hypothesis tests and multiple testing

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M03 · 15–60 return distributions: normal, lognormal, Student-t; skew, kurtosis, Jarque–Bera; QQ plots · 60–70 break · 70–120 estimation and standard errors; the standard error of a mean return vs of a volatility (why means are so hard to estimate) · 120–170 hypothesis tests and p-values: what they mean, the garden of forking paths · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 multiple testing: family-wise error, Bonferroni, Benjamini–Hochberg; `cfmat.analytics.stats.benjamini_hochberg` · 60–70 break · 70–130 simulation workshop: test 100 random "strategies" and count false positives, then apply BH · 130–170 Monte Carlo and bootstrap: resampling returns, block bootstrap for dependent data · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–90 Lab 04a §1 and §5: fat tails, bootstrap Sharpe interval · 90–120 blockers |
| OH · Wed · 60 min | Statistics clinic: interpreting intervals and p-values |
| C2 · Thu · 120 min | 0–60 exercise: how many years of data to distinguish Sharpe 0.5 from 0? (simulation) · 60–100 peer review · 100–120 results shared |
| QP · Fri · 60 min | 0–20 quiz 4a · 20–50 critique a published "strategy with Sharpe 3" claim · 50–60 preview |
| Self-study · ~6 h | Ruppert and Matteson ch. 2–5; Harvey, Liu and Zhu (2016) introduction |

### Week 8 — Regression, autocorrelation, stationarity, cointegration and the bootstrap

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 OLS: assumptions, interpretation, robust (HAC) errors; CAPM and multi-factor regressions · 60–70 break · 70–125 autocorrelation, Ljung–Box; random walks and unit roots; ADF; why regressing prices on prices is spurious · 125–170 volatility clustering and a first look at GARCH(1,1) (full treatment in M13) · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 cointegration: Engle–Granger, spreads, half-life; Johansen (intuition) · 60–70 break · 70–130 workshop: find cointegrated pairs in a synthetic universe, then count how many you would expect by chance · 130–170 linear algebra for portfolios: covariance matrices, eigenvalues, PCA of returns · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 04a §2–§4: Ljung–Box and ADF, CAPM regression, cointegration test · 100–120 review |
| OH · Wed · 60 min | Assignment clinic |
| C2 · Thu · 120 min | 0–60 problem set on regression diagnostics · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 4b · 20–50 peer review of assignment drafts · 50–60 preview of M05 |
| Self-study · ~6 h | Tsay ch. 1–3; Engle and Granger (1987); finish the assignment |

## Labs

**Lab 04a — quantitative methods and financial statistics** (`lab_04a_statistics_time_series.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Fat tails | Kurtosis, Jarque–Bera, tail frequencies vs the normal | You can say how often a "4-sigma" day happens in the data vs the model |
| 2. Autocorrelation and stationarity | Ljung–Box on returns and squared returns; ADF on prices and returns | Prices non-stationary, returns stationary; squared returns autocorrelated |
| 3. CAPM regression | α, β with standard errors | β interpreted; α's interval includes 0 |
| 4. Cointegration | Engle–Granger on a planted pair | p-value small for the pair, large for unrelated series |
| 5. Bootstrap Sharpe | 95% interval for an annual Sharpe | Interval width stated in words ("from roughly 0.2 to 1.8") |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 4a, 4b | quizzes (10%) | Fri W7, W8 | Conceptual and numerical |
| Lab 04a | labs (20%) | Sun W8 | Runs; interpretation of every test in words |
| Assignment: how sure are we? | assignments (15%) | Sun W9 | Five years of daily data for three stocks and an index: distribution statistics, rolling betas with HAC errors, ADF on prices and returns, bootstrap Sharpe intervals, and a BH-corrected screen of 20 "signals". Rubric: correctness 40, interpretation 30, honesty about uncertainty 20, clarity 10 |

## Common mistakes

- Reporting a p-value from the best of many tests without correction → the 100-random-strategies workshop.
- Ordinary t-statistics on overlapping returns → HAC errors in L1 W8; reused in M06.
- Regressing price levels on each other and finding "relationships" → spurious regression demo.
- Believing a 3-year Sharpe ratio to one decimal place → the bootstrap interval in Lab 04a §5.

## Readings

- Ruppert and Matteson, *Statistics and Data Analysis for Financial Engineering*, ch. 2–5, 9, 12.
- Ruey S. Tsay, *Analysis of Financial Time Series*, ch. 1–3.
- Engle and Granger (1987), "Co-integration and Error Correction".
- Harvey, Liu and Zhu (2016), "… and the Cross-Section of Expected Returns".
- Newey and West (1987), "A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix".

## Instructor notes

- Owner: quant research lead.
- The multiple-testing workshop is the most important hour of Term 1: keep it even if L2 runs late.
- Use `cfmat.analytics.stats` so learners meet the same functions in M06, M11 and M23.
- Term 1 exam (Week 11) draws 30% of its marks from this module.
