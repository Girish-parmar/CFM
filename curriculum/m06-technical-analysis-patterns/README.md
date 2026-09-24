# M06 · Technical Indicators, Candlestick and Chart Patterns

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T2 · Analysis and Derivatives |
| Weeks | 12–13 |
| Hours | 24 guided |
| Labs | [06a](lab_06a_indicators_patterns.py) — Indicator dashboard, HAC event studies, 20 patterns with FDR control |
| Library | `cfmat.analytics.indicators`, `cfmat.analytics.patterns`, `cfmat.analytics.stats` |
| Prerequisites | [M04](../m04-statistics-time-series/README.md) |
| Committed topics | Technical indicators, chart and candlestick patterns, Statistics in finance |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Most retail traders start with indicators and chart patterns. Most of those rules do not
survive an honest test. This module teaches both halves: how every common indicator and pattern
is computed (so learners can build the Strategy Creator rules in M12), and how to test a rule as
a hypothesis with event studies, overlapping-window standard errors, random-date permutation
tests and false-discovery control.

## Learning outcomes

By the end of the module you can:

1. Compute moving averages, RSI, MACD, Bollinger bands, ATR, ADX/DI, Supertrend, Donchian channels, stochastics and the efficiency ratio from first principles, and say what each measures.
2. Show that many indicators are near-duplicates and explain why adding them adds parameters, not information.
3. Detect 15 candlestick patterns and chart structures (swing points, double tops/bottoms, consolidation, squeeze) with `cfmat.analytics.patterns`, and explain why swing-based patterns are only known with a delay.
4. Design an event study: event definition, first-day filter, horizons, benchmark ("other days").
5. Use HAC t-statistics and random-date permutation p-values, and control the false-discovery rate across many rules.
6. Write a pre-registered verdict on a popular rule.

## Before you start

- M04 complete, especially multiple testing and HAC errors.
- Pick one chart rule you (or a friend) believe in. Write it down precisely before Week 12.

## Weekly plan

### Week 12 — Indicators from first principles — and why most are redundant

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M04–M05 · 15–60 trend indicators: SMA/EMA, MACD, ADX/DI, Supertrend, Donchian; smoothing and lag · 60–70 break · 70–120 momentum and oscillators: RSI, stochastics, rate of change; volatility: ATR, Bollinger bands and bandwidth; efficiency ratio and Hurst · 120–170 live build: RSI and ATR from scratch vs `cfmat.analytics.indicators` · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 redundancy: correlation matrix of 8 indicators; what that means for rules and ML features · 60–70 break · 70–130 event-study design: events, first-day filter, horizons, overlapping windows · 130–170 HAC t-statistics and random-date permutation tests (`cfmat.analytics.stats.event_study`) · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–90 Lab 06a §1–§2: dashboard and redundancy · 90–120 blockers |
| OH · Wed · 60 min | Pre-registration help for the assignment rule |
| C2 · Thu · 120 min | 0–60 Lab 06a §3: event studies for three rules with BH q-values · 60–100 peer review · 100–120 discussion: why the RSI rule looks good in one test and not in nine |
| QP · Fri · 60 min | 0–20 quiz 6a · 20–50 peer review of pre-registrations · 50–60 preview |
| Self-study · ~6 h | Aronson ch. 1–6; indicator exercises |

### Week 13 — Candlestick and chart patterns as testable hypotheses

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 candlestick anatomy; single-, two- and three-candle patterns; context filters (after a decline, after a rise) · 60–70 break · 70–120 chart structure: swing highs/lows confirmed k bars later; higher highs/lows; double tops/bottoms with neckline breaks; consolidation and squeeze · 120–170 look-ahead traps in pattern code; the truncation test (`tests/test_analytics.py`) · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–70 workshop: scan 20 patterns, test each, control FDR · 70–80 break · 80–140 case: the synthetic-data leak we found — reusing a seed made engulfing patterns "predict" returns; how the salted stream fixed it · 140–170 from pattern to rule: turning a surviving pattern into a Strategy Creator entry (preview of M12) · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 06a §4: pattern scan and FDR · 100–120 review |
| OH · Wed · 60 min | Assignment clinic |
| C2 · Thu · 120 min | 0–60 run your pre-registered rule on 10 real stocks · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 6b · 20–50 peer review of assignment drafts · 50–60 preview of M07 |
| Self-study · ~6 h | Lo, Mamaysky and Wang (2000); finish the assignment |

## Labs

**Lab 06a — indicators, candlesticks and chart patterns as testable hypotheses** (`lab_06a_indicators_patterns.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Dashboard | Trend, momentum, volatility and ADX panels | Four labelled panels; you can explain each line |
| 2. Redundancy | Spearman correlations of 8 indicators | You find the clusters (momentum oscillators move together) |
| 3. Event studies | 3 rules × 3 horizons with HAC t and permutation p; BH q-values | One or two raw p < 0.05, none convincing after FDR |
| 4. Patterns | 20 patterns, 10-day excess returns, q-values | A handful of p < 0.05 by chance, none surviving at 10% FDR |

The price series has a small planted momentum (AR(1) 0.05), so most rules *should* fail. The
point is to see chance "discoveries" appear and disappear under correct testing.

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 6a, 6b | quizzes (10%) | Fri W12, W13 | Indicator formulas, test design |
| Lab 06a | labs (20%) | Sun W13 | Runs; each table interpreted in words |
| Assignment: verdict on a popular rule | assignments (15%) | Sun W14 | Pre-register a rule, test it on ≥ 30 stocks and ≥ 5 years, report HAC and permutation p-values and BH q-values across all tests run, and write a one-page verdict. Rubric: pre-registration 20, design 30, correctness 30, honesty 20 |

## Common mistakes

- Counting every day of an oversold spell as a separate event → first-day filter.
- Using ordinary t-statistics on 20-day forward returns sampled daily → HAC or permutation.
- Pattern code that peeks at the next bar (e.g. `shift(-1)`) → the truncation test must pass.
- Reporting the best of 20 patterns without correction → BH q-values in every table.

## Readings

- David Aronson, *Evidence-Based Technical Analysis*, ch. 1–6.
- Lo, Mamaysky and Wang (2000), "Foundations of Technical Analysis".
- Bajgrowicz and Scaillet (2012), "Technical trading revisited: false discoveries, persistence tests and transaction costs".
- Steve Nison, *Japanese Candlestick Charting Techniques* (definitions only).

## Instructor notes

- Owner: quant research lead.
- Keep the L2 W13 "synthetic-data leak" case: it shows how easily a data bug becomes a trading edge, and how the repository caught it (`test_candles_carry_no_information_about_future_closes`).
- Learners from a discretionary background may push back emotionally when their favourite rule fails. Frame the verdict as a measurement, not a judgement.
