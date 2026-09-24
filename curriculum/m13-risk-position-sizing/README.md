# M13 · Risk Management and Position Sizing

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T4 · Risk, Portfolio and Trading Systems |
| Weeks | 28–29 |
| Hours | 24 guided |
| Labs | [13a](lab_13a_risk_sizing_stress.py) — VaR/ES, Kupiec, GARCH VaR, sizing, risk of ruin, stress tests |
| Library | `cfmat.portfolio.risk`, `cfmat.econometrics.garch` |
| Prerequisites | [M04](../m04-statistics-time-series/README.md), [M11](../m11-backtesting-research/README.md) |
| Committed topics | Risk management and position sizing |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Traders are rarely ruined by a bad signal; they are ruined by size. This module measures risk
honestly (VaR, expected shortfall, backtests of the risk model itself), stresses the book beyond
history, and sizes positions so that a string of bad days cannot end the strategy. It also
introduces GARCH as a risk model, reused in M23.

## Learning outcomes

By the end of the module you can:

1. Measure VaR (historical, parametric, bootstrap) and expected shortfall, and explain the square-root-of-time rule and its limits.
2. Backtest a VaR model with Kupiec's proportion-of-failures test and inspect breach clustering.
3. Fit a GARCH(1,1) on a training period and use its one-step forecast for a VaR that adapts to volatility clusters.
4. Design historical and hypothetical stress scenarios, including liquidity and margin-call effects.
5. Size positions by fixed fractional risk, ATR stops, volatility targeting and fractional Kelly, and explain why full Kelly is dangerous with estimated edges.
6. Estimate risk of ruin by simulation and set drawdown-based de-risking rules.

## Before you start

- M04 (distributions, bootstrap) and M11 (metrics) complete.
- Read Jorion, *Value at Risk*, ch. 1–2.

## Weekly plan

### Week 28 — VaR, expected shortfall, VaR backtesting and stress tests

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M12 · 15–60 volatility, VaR, expected shortfall; historical, parametric and bootstrap methods; square-root-of-time · 60–70 break · 70–120 backtesting a VaR: breach rates, Kupiec's test, clustering (Christoffersen, intuition) · 120–170 GARCH(1,1) as a risk model: fit on a training window, forecast one step ahead · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 stress testing: historical scenarios (2008, 2013 taper tantrum, 2016 demonetisation, 2020 Covid), hypothetical shocks, correlation breakdown · 60–70 break · 70–130 liquidity risk and margin calls: when a hedge fund must sell what it can, not what it wants · 130–170 workshop: a stress table for a derivatives book · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 13a §1–§2: VaR/ES, Kupiec, GARCH vs historical VaR · 100–120 blockers |
| OH · Wed · 60 min | Risk Q&A; capstone topic ideas |
| C2 · Thu · 120 min | 0–60 Lab 13a §4 stress test; add your own scenario · 60–100 peer review · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 13a · 20–50 risk-report critique · 50–60 preview |
| Self-study · ~6 h | Jorion ch. 1–5; Christoffersen (1998) |

### Week 29 — Position sizing, Kelly, volatility targeting and drawdown control

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 fixed fractional sizing from stops; ATR stops; lot-size rounding for F&O · 60–70 break · 70–120 Kelly and fractional Kelly; estimation error in the edge; the standard error of a Sharpe ratio · 120–170 volatility targeting and leverage caps; drawdown-based de-risking and its whipsaw cost · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 risk of ruin by simulation · 60–70 break · 70–130 workshop: Lab 13a §3 — sizing and the 0.25–2× Kelly ruin table · 130–170 the daily risk report: exposure, VaR/ES, contributors, limits with RAG status · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 13a §3 and exercises · 100–120 review |
| OH · Wed · 60 min | Assignment clinic |
| C2 · Thu · 120 min | 0–60 build the daily risk report function · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 13b · 20–50 peer review of risk reports · 50–60 preview of M14 |
| Self-study · ~6 h | Thorp (2006) on Kelly; assignment |

## Labs

**Lab 13a — measuring risk, sizing positions and stress testing** (`lab_13a_risk_sizing_stress.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. VaR and ES | Three VaR methods and ES at 95/99%; 10-day scaling | Methods agree roughly; ES > VaR |
| 2. VaR backtest | Historical vs GARCH VaR on clustered returns; Kupiec and worst-50-day breach counts | Breach rates near 1%; clustering discussed |
| 3. Sizing | Fixed fractional, ATR, vol targeting, Kelly with its standard error, ruin simulation | Half Kelly already has a high chance of a 30% drawdown |
| 4. Stress | Scenario P&L for a four-position book | Worst scenario several times the 99% VaR |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 13a, 13b | quizzes (10%) | Fri W28, W29 | Numericals and interpretation |
| Lab 13a | labs (20%) | Sun W29 | Runs; risk statements in plain language |
| Assignment: a daily risk report | assignments (15%) | Sun W30 | For a multi-strategy paper book: gross and net exposure, VaR and ES, top contributors, stress table, limit utilisation with red/amber/green flags, generated by code. Rubric: correctness 35, completeness 30, clarity 20, automation 15 |

## Common mistakes

- Scaling 1-day VaR by √10 during a volatility cluster → GARCH forecasts and stress tests.
- Declaring a VaR model fine because the breach rate is right → look at clustering too.
- Sizing with full Kelly from a backtest Sharpe → the ruin table.
- Stress scenarios that are all "a bit worse than normal" → include a Covid-style gap and a margin call.

## Readings

- Philippe Jorion, *Value at Risk*, ch. 1–5.
- Kupiec (1995); Christoffersen (1998), "Evaluating Interval Forecasts".
- Edward Thorp (2006), "The Kelly Criterion in Blackjack, Sports Betting and the Stock Market".
- Engle (2001), "GARCH 101".

## Instructor notes

- Owner: risk and execution lead.
- The daily risk report built here is reused in M17 (RMS) and M18 (monitoring) and in capstone paper trading — keep its format stable across cohorts.
- Capstone topics are due by Week 38; start the conversation in OH this week.
