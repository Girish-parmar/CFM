# M09 · F&O Strategies and Second-Order Greeks

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T2 · Analysis and Derivatives |
| Weeks | 18–19 |
| Hours | 24 guided |
| Labs | [09a](lab_09a_second_order_greeks.py) — Vanna, volga, charm, speed, zomma, colour; P&L attribution through a sell-off; gamma scalping<br>[09b](lab_09b_futures_options_structures.py) — Futures curve, cash-and-carry, seven option structures in parallel |
| Library | `cfmat.derivatives.options`, `cfmat.derivatives.futures`, `cfmat.derivatives.option_strategies` |
| Prerequisites | [M08](../m08-derivatives-pricing-greeks/README.md) |
| Committed topics | Futures and options — Greeks, second-order Greeks and strategies |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

First-order Greeks explain a position at a moment; second-order Greeks explain how it changes.
Vanna and volga drive the P&L of short-volatility books when markets fall and volatility jumps
together; charm decides how fast delta drifts into expiry; speed and gamma decide what a pin does
to a weekly option seller. This module adds those tools, then studies futures curves, carry and
seven option structures by market view — with worst-case trades, not win rates, at the centre.

## Learning outcomes

By the end of the module you can:

1. Define and compute vanna, volga (vomma), charm, speed, zomma and colour, and explain which market move each responds to.
2. Attribute an option position's daily P&L to delta, gamma, theta, vega and the second-order terms, and find the unexplained remainder.
3. Explain gamma scalping and the P&L of a delta-hedged option in terms of realised vs implied variance.
4. Build a futures curve, measure basis and carry, and handle rollovers in a backtest.
5. Test cash-and-carry arbitrage after Indian costs and explain why retail traders rarely capture it.
6. Choose and backtest option structures by market view (range, trend, volatility) with targets, stops and margin, judging them by worst trade and return on margin.

## Before you start

- M08 complete, including the delta-hedging lab section.
- Comfortable with partial derivatives and Taylor expansions (M00 refresher if needed).

## Weekly plan

### Week 18 — Second-order Greeks (vanna, volga, charm, speed) and Greek P&L attribution

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M08 · 15–60 the Taylor expansion of option value in spot, vol and time; which cross terms matter · 60–70 break · 70–125 vanna and volga: skew, smile dynamics and why short-vol books lose twice in a sell-off · 125–170 charm, speed, zomma, colour: delta and gamma drift into expiry; pin risk · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 Greek P&L attribution: daily explain vs unexplained · 60–70 break · 70–130 workshop: attribute a short straddle's P&L over a turbulent week · 130–170 gamma scalping and variance: the hedged option as a bet on realised vs implied · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 09a §1–§3: closed forms against finite differences, Greek maps, and the short-straddle P&L explain · 100–120 blockers |
| OH · Wed · 60 min | Greeks Q&A |
| C2 · Thu · 120 min | 0–60 P&L attribution exercise · 60–100 peer review · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 9a · 20–50 "which Greek hurt?" case cards · 50–60 preview |
| Self-study · ~6 h | Taleb, *Dynamic Hedging* (selected chapters); Haug, *The Complete Guide to Option Pricing Formulas* (Greeks chapter) |

### Week 19 — Futures curves, carry and option structures by market view

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 futures curves: near, next, far; basis and carry; expiry convergence; rollover mechanics and costs · 60–70 break · 70–120 cash-and-carry after STT, stamp duty and funding; who really earns the basis · 120–170 structures by view: range (short straddle, strangle, iron condor), volatility (long straddle, strangle), direction (bull call, bear put spreads) · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 targets, stops and defined risk; margin for defined vs undefined risk · 60–70 break · 70–130 workshop: Lab 09b §3 — seven structures in parallel; read worst trade, profit factor, return on margin · 130–170 discussion: why most weekly-option sellers eventually blow up without tail rules · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 09b §1–§2: futures curve, cash-and-carry · 100–120 review |
| OH · Wed · 60 min | Assignment clinic |
| C2 · Thu · 120 min | 0–60 Lab 09b §3 and exercises (iron fly; Greek attribution of the worst straddle trade) · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 9b · 20–50 peer review of assignment drafts · 50–60 preview of M10 |
| Self-study · ~6 h | Natenberg ch. on spreads; SEBI F&O study; assignment |

## Labs

**Lab 09a — second-order Greeks and P&L attribution** (`lab_09a_second_order_greeks.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Closed forms | Vanna, volga, charm, speed, zomma and colour for a call; check each by bumping a first-order Greek | Every closed form within 1e-4 of its finite difference |
| 2. Where they live | Maps across strike/spot and days to expiry | You say where each Greek peaks and why (wings for vanna/volga, at-the-money near expiry for the rest) |
| 3. P&L attribution | A short straddle through a sell-off with rising IV, explained day by day | Largest daily residual below 5% of that day's gross Greek P&L; about 1% unexplained over the period |
| 4. Gamma scalping | Delta-hedged long straddle bought at 16% on paths realising 10–28% | Average P&L follows realised − implied; you explain the spread across paths |

**Lab 09b — futures and option structures** (`lab_09b_futures_options_structures.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Futures curve | Near/next contracts, basis, calendar spread | Basis shrinks to zero at expiry |
| 2. Cash-and-carry | Basis trade before and after Indian costs | The 15 bp edge disappears after ~25 bp of costs |
| 3. Seven structures | Parallel backtests with targets and stops | Sellers win often and lose big; buyers pay the premium; worst trade read before win rate |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 9a, 9b | quizzes (10%) | Fri W18, W19 | Greeks and structures |
| Labs 09a, 09b | labs (20%) | Sun W19 | Runs; the attribution and the worst-trade analysis written up |
| Assignment: a tail-aware option strategy | assignments (15%) | Sun W20 | Choose one structure, add a tail rule (wing, stop or event filter), backtest on the synthetic IV index and on a historical IV series if licensed, attribute the worst three trades to Greeks. Rubric: design 25, risk analysis 35, correctness 25, clarity 15 |

## Common mistakes

- Judging an option-selling strategy by win rate → every table in Lab 09b shows worst trade first.
- Ignoring that IV rises when spot falls → vanna/volga session and the sell-off attribution.
- Rolling futures on expiry day without costs → rollover costs in `backtest_futures`.
- Treating the synthetic IV index as a real option chain → labs state it; the assignment asks for historical IV where licensed.

## Readings

- Nassim Taleb, *Dynamic Hedging*, chapters on second-order Greeks and exotic risks.
- Espen Haug, *The Complete Guide to Option Pricing Formulas*, Greeks chapter.
- Sheldon Natenberg, *Option Volatility and Pricing*, ch. 11–14.
- Carr and Wu (2009), "Variance Risk Premiums".
- SEBI study on F&O trading by individuals.

## Instructor notes

- Owner: markets and derivatives lead.
- Lab 09a §4 (gamma scalping) makes a good opener for the W19 L1 discussion of volatility trading.
- Lot size, strike step and expiry weekday are parameters in the labs; set them from current circulars before class.
- This module's assignment feeds directly into derivatives capstones.
