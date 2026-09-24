# M08 · Derivatives — Futures, Options Pricing and the Greeks

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T2 · Analysis and Derivatives |
| Weeks | 15–17 |
| Hours | 36 guided |
| Labs | [08a](lab_08a_options_pricing_greeks.py) — Option chain and Greeks, IV smile, binomial, payoffs, delta hedging |
| Library | `cfmat.derivatives.options` |
| Prerequisites | [M01](../m01-financial-markets/README.md), [M04](../m04-statistics-time-series/README.md) |
| Committed topics | Futures and options — Greeks, second-order Greeks and strategies |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Index derivatives are the most traded instruments in India, and weekly options have drawn in
millions of retail traders — most of whom lose money. Pricing, the Greeks and the volatility
surface are the language of every F&O strategy, hedge and margin call. This module builds that
language carefully, so that M09 (second-order Greeks and strategies) and M12 (F&O signals) rest
on solid ground.

## Learning outcomes

By the end of the module you can:

1. Price forwards and futures by cost of carry; analyse basis, convergence, rollover and calendar spreads.
2. Explain option payoffs, moneyness, put–call parity and no-arbitrage bounds.
3. Price options with binomial trees and Black–Scholes–Merton (with dividends), and value early exercise.
4. Compute and interpret delta, gamma, vega, theta and rho, and describe how they change with spot, time and volatility.
5. Extract implied volatility and read the smile, skew and term structure (including India VIX).
6. Build common structures (spreads, straddles, strangles, butterflies, condors, covered calls, protective puts) and read their payoff and margin.
7. Delta-hedge an option and explain its P&L as implied minus realised volatility.

## Before you start

- M01 (contract specifications, margins) and M04 (lognormal returns, Monte Carlo) complete.
- NISM Series VIII workbook ch. 5–8 read.

## Weekly plan

### Week 15 — Forwards and futures, cost of carry, option payoffs and parity

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M07 · 15–60 forwards and futures: cost of carry, basis, convergence, rollover, calendar spreads · 60–70 break · 70–120 cash-and-carry and reverse arbitrage; why costs and funding kill most "arbitrage" · 120–170 option payoffs, moneyness, intrinsic and time value · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 put–call parity with dividends; no-arbitrage bounds; synthetic positions · 60–70 break · 70–130 workshop: parity violations in a (historical) option chain — real or data errors? · 130–170 the NSE options market: weekly and monthly expiries, strikes, lot sizes, STT on exercise · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–90 futures fair value and parity exercises (`cfmat.derivatives.options.futures_fair_value`, `put_call_parity_gap`) · 90–120 blockers |
| OH · Wed · 60 min | Derivatives Q&A |
| C2 · Thu · 120 min | 0–60 payoff diagrams with `strategy_payoff` · 60–100 peer review · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 8a · 20–50 parity puzzles in pairs · 50–60 preview |
| Self-study · ~6 h | Hull ch. 2–5, 10–11 |

### Week 16 — Binomial trees, Black–Scholes–Merton and the first-order Greeks

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 one-step and multi-step binomial trees; risk-neutral pricing; American exercise · 60–70 break · 70–125 Black–Scholes–Merton: assumptions, intuition, dividends; where it fails · 125–170 live coding: binomial convergence to BS (`binomial_price`, `bs_price`) · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 the Greeks: delta, gamma, vega, theta, rho; units (vega per 1 vol point, theta per day) · 60–70 break · 70–130 how Greeks move with spot, time and volatility; gamma near expiry · 130–170 managing a book by its Greeks: net delta, gamma, vega limits · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 08a §1 and §3: option chain with Greeks; binomial convergence and early exercise · 100–120 review |
| OH · Wed · 60 min | Greeks intuition clinic |
| C2 · Thu · 120 min | 0–60 Greeks vs finite differences (why the check matters) · 60–100 peer review · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 8b · 20–50 Greeks estimation game · 50–60 preview |
| Self-study · ~6 h | Hull ch. 13–15, 19; Natenberg ch. 5–7 |

### Week 17 — Implied volatility, the smile and delta hedging

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 historical vs implied volatility; solving for IV; the smile, skew and term structure; India VIX · 60–70 break · 70–120 event volatility: results, budgets, policy days · 120–170 option structures and margins: spreads, straddles, strangles, butterflies, condors; SPAN and exposure margin for sellers · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 delta hedging: frequency, costs, and the P&L identity (implied vs realised) · 60–70 break · 70–130 workshop: hedge a short straddle daily through a calm and a turbulent month · 130–170 the volatility risk premium and the tail risk of selling options · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 08a §2, §4, §5: IV smile, payoffs, delta hedging · 100–120 review |
| OH · Wed · 60 min | Assignment clinic |
| C2 · Thu · 120 min | 0–60 margin and stress for an iron condor (±5%, ±10%, +5 vol points) · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 8c · 20–50 peer review of assignment drafts · 50–60 preview of M09 |
| Self-study · ~6 h | Natenberg ch. 8–9, 11; NISM VIII revision (exam voucher) |

## Labs

**Lab 08a — derivatives, options pricing and volatility** (`lab_08a_options_pricing_greeks.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Option chain | Prices and Greeks across strikes | Delta ≈ 0.5 at the money; gamma peaks at the money |
| 2. IV smile | Back out implied vol from quotes | The planted skew is recovered |
| 3. Binomial | Convergence to BS; American put premium | Error shrinks with steps; American ≥ European |
| 4. Payoffs | Per-lot payoffs of common structures | Break-evens and max loss read off correctly |
| 5. Delta hedging | Hedge with implied ≠ realised vol | P&L sign matches implied − realised |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 8a–8c | quizzes (10%) | Fri W15–W17 | Pricing and Greeks numericals |
| Lab 08a | labs (20%) | Sun W17 | Runs; each section interpreted |
| Assignment: an iron condor, end to end | assignments (15%) | Sun W18 | From a historical option chain (≥ 3 months old): IV smile for two expiries, price an iron condor, its Greeks and margin, stress for ±5%, ±10% and +5 vol points. Rubric: correctness 40, risk analysis 30, presentation 30 |
| NISM Series VIII | recommended | after W17 | Voucher included |

## Common mistakes

- Mixing vega per 1.00 and per 1 vol point, or theta per year and per day → units are fixed in `cfmat.derivatives.options.bs_greeks`.
- Using the wrong expiry convention (calendar vs trading days) → C1 W15 exercise.
- Reading a parity "violation" in stale quotes as an arbitrage → L2 W15 workshop.
- Selling options because the win rate is high → L2 W17 tail-risk session and M09's worst-trade tables.

## Readings

- John C. Hull, *Options, Futures, and Other Derivatives*, ch. 2–5, 10–15, 19–20.
- Sheldon Natenberg, *Option Volatility and Pricing*, ch. 5–9, 11.
- NISM Series VIII workbook (Equity Derivatives).
- Black and Scholes (1973); Merton (1973).
- SEBI study on F&O trading by individuals (latest edition).

## Instructor notes

- Owner: markets and derivatives lead.
- Use option-chain snapshots at least three months old; never discuss live positions.
- The SEBI F&O study is essential context for learners from retail trading backgrounds; discuss it without moralising.
- Refresh lot sizes, expiry days and margin practices before each cohort; they change often.
