# M12 · Strategy Studio: Screeners, Strategy Creator and Parallel Research

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T3 · Strategy Research |
| Weeks | 25–26 |
| Hours | 24 guided |
| Labs | [12a](lab_12a_screener_instrument_selection.py) — Parallel screener, regime labels, ranking, pattern scan, shortlist<br>[12b](lab_12b_strategy_creator_parallel.py) — Strategy library and creator, sweeps (serial/thread/process), walk-forward<br>[12c](lab_12c_fno_signals_and_filters.py) — Trend template on futures; regime filters for option structures |
| Library | `cfmat.studio`, `cfmat.research.screener`, `cfmat.infra.parallel`, `cfmat.backtesting.report` |
| Prerequisites | [M06](../m06-technical-analysis-patterns/README.md), [M09](../m09-fno-strategies-advanced-greeks/README.md), [M11](../m11-backtesting-research/README.md) |
| Committed topics | Technical indicators, chart and candlestick patterns, Futures and options — Greeks, second-order Greeks and strategies, Screeners and instrument selection, Threading and multiprocessing for research |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

This module turns Terms 1–3 into a working research toolkit that learners keep for the capstone
and after it: a screener that picks instruments by regime, a Strategy Creator where a strategy
is readable rules over indicators, patterns and parameters, a trade-level backtester with
realistic exits, futures and options implementations, and parallel search that is fast *and*
honest about how many things were tried.

## Learning outcomes

By the end of the module you can:

1. Screen a universe with 25+ analytics (returns, trend strength and fit, volatility, squeeze, liquidity, beta, drawdown), label regimes, and build preset and custom screens, composite ranks, pattern scans and diversified shortlists.
2. Write strategies as rules in the safe rule language (`cfmat.studio`) and use the template library: trend up, trend down, both-way trend, range-bound, either-way breakout and pattern strategies.
3. Backtest with next-open fills, slippage, ATR stops, targets, trailing stops, time exits and reversals, and read a full trade-level report.
4. Trade a Strategy Creator signal on index futures with lots, margin, rollovers and charges, and use rules as regime filters for option structures.
5. Speed up research with process pools, explain why threads do not help Python-heavy loops (the GIL), and search coarse-to-fine instead of brute force.
6. Validate walk-forward and charge the result for the trials run (deflated Sharpe).

## Before you start

- M06 (indicators, patterns), M09 (futures and option structures) and M11 (walk-forward, DSR) complete.
- Skim `cfmat/strategies/templates.py` and pick two templates you want to understand in depth.

## Weekly plan

### Week 25 — Screening and instrument selection; the rule language

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M11 · 15–60 what makes an instrument tradable: liquidity, impact, costs; trend strength (ADX, efficiency ratio, regression slope and R², Hurst); squeezes · 60–70 break · 70–120 regime labels and their error rates; composite ranking; correlation-aware shortlists; compliance: screener output is research, not a recommendation · 120–170 live: screen 40 instruments in parallel and grade the labels against the hidden archetypes · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 the rule language: fields, indicators, patterns, `recent`, `cross_above`; why it is parsed with `ast` and never `eval`'d · 60–70 break · 70–130 the execution model: signals at close, fills at next open, stops and targets intrabar, gap handling, stop-before-target rule · 130–170 strategy–instrument fit: running every template on every instrument · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 12a · 100–120 blockers |
| OH · Wed · 60 min | Rule-writing clinic |
| C2 · Thu · 120 min | 0–60 Lab 12b §1–§3: library, create and save your own strategy, compare on two instruments · 60–100 peer review of strategy specs · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 12a · 20–50 "read this rule aloud" drill · 50–60 preview |
| Self-study · ~6 h | Clenow, *Trading Evolved* (backtesting chapters); strategy templates source |

### Week 26 — Strategy Creator, parallel optimisation and F&O signals

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 processes vs threads and the GIL; sharing data with workers; chunking; reproducibility (`cfmat.infra.parallel`) · 60–70 break · 70–120 coarse-to-fine search; walk-forward; charging for trials · 120–170 live benchmark: 216 backtests serial vs threads vs processes · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 F&O implementation of a view: futures lots, margin and rollover; option structures and regime filters · 60–70 break · 70–130 workshop: Lab 12c — a trend template on futures; filters for five option structures · 130–170 judging a filter: average trade, worst trade and trades left; the filter is a parameter too · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 12b §4–§6: sweeps, coarse-to-fine, walk-forward · 100–120 review |
| OH · Wed · 60 min | Pipeline assignment clinic |
| C2 · Thu · 120 min | 0–60 Lab 12c · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 12b · 20–50 peer review of pipeline plans · 50–60 briefing for Review 2 and Bootcamp 2 |
| Self-study · ~6 h | Python docs on `concurrent.futures`; finish the pipeline assignment |

## Labs

**Lab 12a — screeners and instrument selection** (`lab_12a_screener_instrument_selection.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Screen | 25+ analytics for 40 instruments, serial vs process pool | Same table either way; parallel faster |
| 2. Grade labels | Crosstab of screener regime vs hidden archetype | Roughly three-quarters labelled correctly |
| 3–4. Screens, rank, shortlist | Presets, custom filters, composite rank, pattern scan, low-correlation shortlist | Shortlist names pairwise |corr| < 0.5 |
| 5. Strategy fit | Every template on every instrument | Trend templates earn on trending names, range templates on range-bound ones |

**Lab 12b — Strategy Creator and parallel optimisation** (`lab_12b_strategy_creator_parallel.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1–3. Library and your strategy | Browse templates; build, save (JSON), reload and backtest a custom spec; compare strategies | Full trade report; spec reloads identically |
| 4. Sweeps | 216 combinations serial vs threads vs processes | Processes ≈ 3–4× faster on 4 cores; threads no faster (GIL) |
| 5. Coarse-to-fine | Search with fewer evaluations | Near the grid winner with less than half the work |
| 6. Walk-forward | Optimise on the past, trade the future | Out-of-sample Sharpe below the best in-sample Sharpe |

**Lab 12c — Strategy Creator signals on futures and options** (`lab_12c_fno_signals_and_filters.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Futures | Supertrend template on index futures with lots, margin, rollovers, charges | Survives rollovers and charges; drawdown compared with buy and hold |
| 2. Filters | Rule-based regime filters for five option structures | Filters judged on average trade, worst trade and trades left |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 12a, 12b | quizzes (10%) | Fri W25, W26 | Rules, execution model, parallelism |
| Labs 12a–12c | labs (20%) | Sun W26 | Run; results explained |
| Assignment: screen → strategy → backtest pipeline | assignments (15%) | Sun W28 | A screen that selects instruments, a strategy in the rule language, a parallel walk-forward backtest, and a futures or options implementation of the same view; report the trial count and DSR. Rubric: pipeline 30, rigour 30, F&O implementation 20, write-up 20. Usually becomes the capstone starting point |
| Term exam 2 | term exams (20%) | Week 27 | Covers M06–M12 |

## Common mistakes

- Screening at the end of the sample and trading the past → the lab says so; the exercise re-classifies monthly with past data only.
- Believing threads speed up the backtest loop → measured in §4.
- Choosing a filter because it looks good on the whole sample → Lab 12c exercise 2 tunes on the first half only.
- Hiding the number of combinations tried → DSR requires the full count.

## Readings

- Andreas Clenow, *Following the Trend* and *Trading Evolved*.
- David Aronson, *Evidence-Based Technical Analysis* (again: pattern rules are hypotheses).
- Sheldon Natenberg, *Option Volatility and Pricing*, spreads and volatility trading.
- Python documentation: `concurrent.futures`; David Beazley on the GIL.
- NSE/BSE circulars on F&O contract specifications; your broker's charge sheet.

## Instructor notes

- Owner: quant research lead with the markets and derivatives lead for Week 26 L2.
- Bootcamp 2 (Week 27) runs a live trading-floor simulation using these tools; confirm the lab images are ready a week before.
- Encourage learners to register their own indicators with `studio.register` — it is the best test of understanding the rule language.
