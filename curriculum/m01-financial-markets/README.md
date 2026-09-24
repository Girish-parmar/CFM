# M01 · Financial Markets, Instruments and Regulation

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T1 · Foundations |
| Weeks | 1–2 |
| Hours | 24 guided |
| Labs | [01a](lab_01a_markets_instruments.py) — Notional, margin, fair value, corporate actions, T+1 |
| Library | `cfmat.derivatives.options`, `cfmat.microstructure.costs` |
| Prerequisites | [M00](../m00-prework/README.md) |
| Committed topics | – |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Every strategy in this programme ends as an order that an exchange matches, a clearing
corporation settles and a regulator can audit. Learners who skip the plumbing build backtests
that ignore lot sizes, circuit limits, T+1 settlement, margins and a tax-and-charge stack that
can exceed the edge. This module gives the vocabulary and the numbers the other 23 modules rely on.

## Learning outcomes

By the end of the module you can:

1. Describe the structure of Indian markets (NSE, BSE, MCX; SEBI and RBI; clearing corporations and depositories) and how they connect to global markets.
2. Explain each instrument class (equity, ETFs, government and corporate bonds, currency, commodity, futures, options): who uses it and why.
3. Trace an order from placement to settlement: order types, matching, pre-open and closing auctions, circuit limits, clearing, T+1 settlement and margins.
4. Compute contract notional, margin and leverage, and a future's fair value by cost of carry.
5. Back-adjust a price history for splits, bonuses and dividends.
6. List every charge and tax on a trade (brokerage, STT, exchange fees, SEBI fee, stamp duty, GST, DP charge, capital-gains tax) and compute them with `cfmat.microstructure.costs`.

## Before you start

- Pre-work complete, including `lab_00a`.
- Skim the NSE pages on trading hours, order types and settlement (30 min).
- Download the current NSE F&O contract specifications and one recent SEBI circular; bring them to L1.

## Weekly plan

Session codes follow the weekly rhythm in the [academic calendar](../../course/04-academic-calendar.md).
Times are minutes from the start of the session.

### Week 1 — Market structure, participants and instruments

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 course kick-off and ground rules · 15–60 primary vs secondary markets; exchanges, clearing corporations, depositories; SEBI and RBI roles · 60–70 break · 70–120 participants: retail, HNI, DII, FPI, prop desks, market makers — who trades what, and why it matters for a strategy · 120–165 case: a day in the life of a Nifty 50 stock (volume by participant, delivery %, index weight) · 165–180 exit ticket (3 questions) |
| L2 · Sun · 180 min | 0–10 recap · 10–60 equity and ETFs; index construction (Nifty 50, Sensex): free float, rebalancing and index-inclusion effects · 60–70 break · 70–120 G-secs and corporate bonds, yields and prices; currency and commodity markets · 120–170 workshop: reading a contract specification (lot size, tick size, expiry, settlement) · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 environment check · 10–70 Lab 01a §1: notional, margin and leverage for index futures; P&L as a % of margin · 70–110 exercise: repeat for Bank Nifty and a stock future using current specs · 110–120 blockers |
| OH · Wed · 60 min | Open questions; spot help with contract specifications and the reading list |
| C2 · Thu · 120 min | 0–60 reading exchange circulars: lot-size revisions, margin changes, new F&O entrants · 60–100 peer check of C1 exercises · 100–120 two learners present their numbers |
| QP · Fri · 60 min | 0–20 quiz 1a (10 MCQ) · 20–50 peer review: one-paragraph explanation of who takes the other side of a retail trade · 50–60 preview of Week 2 |
| Self-study · ~6 h | Harris ch. 1–3; NISM VIII ch. 1–2; start the module assignment outline |

### Week 2 — Orders, clearing and settlement, costs and regulation

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on Week 1 · 15–60 order types (market, limit, SL, SL-M, IOC, GTT), price–time priority, pre-open call auction, closing price · 60–70 break · 70–120 circuit breakers, price bands, F&O ban lists; T+1 settlement, pledging and margins (SPAN + exposure) · 120–165 case: March 2020 — circuit breakers, margin calls and liquidity · 165–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 futures and options primer, F&O eligibility, weekly vs monthly expiries · 60–70 break · 70–120 corporate actions (split, bonus, dividend, rights) and their effect on price series · 120–170 the full cost stack: brokerage, STT, exchange fees, SEBI fee, stamp duty, GST, DP charge; taxation overview (STCG, LTCG, business income for F&O) · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 01a §2–§4: futures fair value and basis, corporate-action back-adjustment, T+1 settlement dates with a holiday calendar · 100–120 review |
| OH · Wed · 60 min | Assignment clinic: structure and sources for the order-life note |
| C2 · Thu · 120 min | 0–50 cost stack with `IndianCostModel`: delivery vs intraday vs futures vs options; set `dp_charge` from a real broker sheet · 50–100 Lab 01a exercises and peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 1b · 20–50 peer review of assignment drafts · 50–60 preview of M02 |
| Self-study · ~6 h | Harris ch. 4–5; NISM VIII ch. 3–4; finish the assignment |

## Labs

**Lab 01a — markets, instruments and the mechanics of a trade** (`lab_01a_markets_instruments.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Notional, margin, leverage | Compute notional and margin per lot; P&L for ±1–2% index moves as a % of margin | You can state that a 2% move is roughly a 17% gain or loss on margin at 12% margin |
| 2. Fair value and basis | Price futures by cost of carry for 7–90 days; compare with a market quote | Mispricing is compared with the round-trip cost before calling it an arbitrage |
| 3. Corporate actions | Back-adjust for a 1:2 split and a 1:2 bonus | Adjusted returns show no artificial −50% day |
| 4. T+1 settlement | Settlement dates with an exchange holiday calendar | Friday and pre-holiday trades settle on the correct day |

Stretch: add the cost stack to the cash-and-carry trade in §2 (exercise 3).

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 1a, 1b | quizzes (10%) | Fri W1, W2 | 10 MCQ each, instant feedback |
| Lab 01a | labs (20%) | Sun W2, 23:59 | Runs cleanly; exercises answered in the notebook; numbers explained in words |
| Assignment: the life of two orders | assignments (15%) | Sun W3 | 2 pages comparing a retail delivery order with an index-options order: who touches it, margins, charges, when cash and securities move; cites current exchange documents. Rubric: accuracy 40, completeness 30, sources 15, clarity 15 |

## Common mistakes

- Using a stale lot size or margin rate → the lab keeps them as parameters and the C2 session makes learners fetch current circulars.
- Treating a futures premium over spot as free money → §2 forces the comparison with costs and funding.
- Forgetting corporate actions in a price history → §3 shows the fake crash; M05 automates the fix.
- Quoting brokerage as "the cost" → the cost-stack exercise shows STT and exchange fees often dominate for options.

## Readings

- Larry Harris, *Trading and Exchanges*, ch. 1–5.
- NISM Series VIII workbook (Equity Derivatives), ch. 1–4.
- M. Y. Khan, *Indian Financial System*, chapters on capital markets and regulation.
- NSE: trading, clearing and settlement sections; current F&O contract specifications.
- SEBI master circular for stock exchanges and clearing corporations (read the table of contents and the sections on margins).

## Instructor notes

- Owner: markets and derivatives lead. Before each cohort, refresh lot sizes, margin rates, STT and exchange charges, and the holiday calendar; update `RATES_AS_OF` in `cfmat/microstructure/costs.py` if the charge sheet changed.
- Use market data at least three months old in every case study, and never frame an example as a recommendation (see [compliance](../../course/09-compliance-and-risk-disclosures.md)).
- The March 2020 case works best with actual index levels and circuit timings; keep the slide deck in the faculty drive.
- Common pace problem: L2 of Week 2 overruns on taxation. Keep taxation to an overview; point to a CA-led optional session.
