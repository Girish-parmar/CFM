# M02 · Macroeconomics for Traders

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T1 · Foundations |
| Weeks | 3–4 |
| Hours | 24 guided |
| Labs | [02a](lab_02a_macro_event_study.py) — Macro calendar and vintages, announcement-day tests, CPI surprises, Nelson–Siegel curves and inversions, causal growth × inflation regimes |
| Library | `cfmat.analytics.stats`, `cfmat.analytics.rates`, `cfmat.analytics.macro` |
| Prerequisites | [M01](../m01-financial-markets/README.md) |
| Committed topics | Macroeconomics |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Index levels, sector leadership, bond yields and the rupee all respond to growth, inflation and
policy. A systematic trader does not forecast GDP, but must know which scheduled events move
volatility (RBI policy days, CPI releases, the Union Budget, US Fed meetings), how the yield
curve prices those expectations, and why a strategy's edge can vanish across macro regimes.
This module turns macro from newspaper reading into measurable event studies and regime labels.

## Learning outcomes

By the end of the module you can:

1. Explain the transmission from growth, inflation and liquidity to interest rates, the rupee and equity valuations in India.
2. Read the RBI monetary policy framework (repo rate, inflation targeting, liquidity operations) and the calendar of market-moving releases.
3. Describe the yield curve (level, slope, curvature), fit a Nelson–Siegel curve and explain what an inversion signals — and does not.
4. Measure how Nifty returns and volatility behave around scheduled macro events with an event study and honest standard errors.
5. Build a simple macro regime label (growth up/down × inflation up/down) and test whether strategy returns differ by regime without look-ahead.
6. Use economic data correctly: release dates vs reference periods, revisions, and first-release vintages.

## Before you start

- M01 complete. Refresh logs, compounding and the difference between nominal and real rates (M00 Week −1).
- Read the latest RBI Monetary Policy Statement (the resolution, 4 pages) and one MOSPI CPI press release.

## Weekly plan

### Week 3 — Growth, inflation and the RBI: how macro moves Indian markets

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M01 · 15–60 national accounts in one hour: GDP, GVA, IIP, PMI; what surprises matter · 60–70 break · 70–120 inflation (CPI, WPI, core), the 4% ± 2% target, the MPC and the repo rate; liquidity (LAF, VRRR) · 120–165 case: the 2022 tightening cycle — repo, 10-year G-sec, bank index, IT index · 165–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 the macro calendar: RBI policy, CPI, GDP, Budget, FOMC; release time vs reference period; revisions · 60–70 break · 70–130 workshop: build an event calendar table in pandas from a CSV of release dates · 130–170 discussion: why "the market already priced it in" is a testable statement · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–90 event-study mechanics on synthetic index data: event windows, abnormal returns, `cfmat.analytics.stats.event_study` · 90–120 blockers |
| OH · Wed · 60 min | Reading an RBI statement; turning text into a hawkish/dovish label |
| C2 · Thu · 120 min | 0–60 exercise: volatility on policy days vs other days (realised range, absolute returns) · 60–100 peer review · 100–120 two presentations |
| QP · Fri · 60 min | 0–20 quiz 2a · 20–50 peer review: one-paragraph macro briefing for a week · 50–60 preview |
| Self-study · ~6 h | Mohan and Ray ch. on monetary policy; RBI MPC statements for the last 4 meetings; start the assignment dataset |

### Week 4 — Rates, the yield curve, the rupee and macro event trading

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 bond maths refresher: price–yield, duration, convexity · 60–70 break · 70–120 the yield curve: level, slope, curvature; Nelson–Siegel; term premium; inversions and recessions (with the base-rate caveat) · 120–165 the rupee: interest-rate differentials, FPI flows, RBI intervention; carry and its crashes · 165–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–70 macro regimes: growth × inflation quadrants, built only from data available at each date · 70–80 break · 80–140 workshop: do trend and mean-reversion strategies behave differently by regime? (label with a lag; count observations per regime) · 140–170 pitfalls: few regimes, many parameters, revisions · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 02a sections 2–3: announcement-day tests, CPI surprises, Nelson–Siegel fits and inversions · 100–120 review |
| OH · Wed · 60 min | Assignment clinic |
| C2 · Thu · 120 min | 0–60 Lab 02a section 4: regime labels with a publication lag, the truncation test, attribution of a strategy's returns by regime · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 2b · 20–50 peer review of assignment drafts · 50–60 preview of M03 |
| Self-study · ~6 h | Ilmanen, *Expected Returns*, ch. on macro and carry; finish the assignment |

## Labs

**Lab 02a — RBI policy days, CPI surprises and the yield curve** (`lab_02a_macro_event_study.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Macro calendar | Read ten years of RBI, CPI, IIP, GDP, Budget and FOMC events: reference period, release time (IST), consensus, actual, surprise; map each to the first session it can move; compare first prints with revisions | Every after-close release on the next session; you say how often an IIP revision flips the direction of growth |
| 2. Announcement days | Volatility and mean returns on event sessions vs other days (HAC t and a studentised permutation test); the minimum detectable effect; the price response to surprises on the session and on the release date; drift after hawkish CPI surprises, then the same study started a day early | RBI-day volatility detected; you explain why smaller planted effects are not; the surprise response recovered on the session and lost on the release date; no tradable drift, and the look-ahead version named as such |
| 3. Yield curve | Fit Nelson–Siegel to single days and to the panel with one tau; compare with the true factors and the 10y / 10y−3m / butterfly proxies; list inversion episodes; duration and convexity of a 10-year G-sec | Panel tau within 0.05 of the planted 1.5; level and slope correlate > 0.99 with the truth; a +50 bp reprice explained by duration + convexity |
| 4. Regimes | Growth × inflation labels three ways (hindsight, causal, first release); the truncation test; next-day index returns and a trend rule's P&L by regime, with the days per regime | The causal label passes truncation and hindsight fails; the hindsight spread between regimes shrinks once only known data are used, and you report the smaller number |

The data are synthetic (`data.macro_calendar`) with planted effects and an answer key; the
runtime is about 5 s offline. The exercises move the same tables to real RBI and MOSPI dates.

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 2a, 2b | quizzes (10%) | Fri W3, W4 | 10 MCQ each |
| Lab 02a | labs (20%) | Sun W4 | Correct event sessions, honest p-values with the number of events, lagged regime labels that pass truncation, interpretation in words |
| Assignment: a macro event study | assignments (15%) | Sun W5 | Pick one scheduled event type; test index volatility and returns around it on at least 8 years of data; report HAC and permutation p-values and the number of events; one-page verdict. Rubric: design 30, correctness 30, honesty about power 20, clarity 20 |

## Common mistakes

- Using the reference period instead of the release date → the calendar exercise makes both columns explicit.
- Using revised data as if it were known at the time → vintages discussion in L2 W3 and the lagged-label rule.
- Declaring a regime effect from 3 regimes and 40 observations → count observations per cell before looking at means.
- Confusing "the curve inverted" with "a recession is coming next quarter" → base rates and lead-time dispersion in L1 W4.

## Readings

- Rakesh Mohan and Partha Ray, *Development of Financial Markets in India* (monetary policy chapters).
- Antti Ilmanen, *Expected Returns*, chapters on macro factors and carry.
- RBI Monetary Policy Reports and MPC resolutions (latest four).
- Diebold and Li (2006), "Forecasting the term structure of government bond yields".
- Savor and Wilson (2013), "How much do investors care about macroeconomic risk? Evidence from scheduled economic announcements".

## Instructor notes

- Owner: markets and derivatives lead with an economist guest (one session).
- Refresh the event calendar for the latest year before each cohort; keep release times in IST.
- Lab 02a uses seed 7, the first seed meeting criteria fixed in advance (effects not planted come out insignificant, at least two inversion episodes); do not swap seeds for a cleaner story. Stress what the tests *cannot* see: the planted RBI-day premium needs about a century of meetings.
- Keep policy discussion descriptive. Do not make or invite predictions about specific future policy decisions.
