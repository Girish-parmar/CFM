# M15 · Market Microstructure and Execution

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T4 · Risk, Portfolio and Trading Systems |
| Weeks | 32–33 |
| Hours | 24 guided |
| Labs | [15a](lab_15a_order_book_execution.py) — Order book, TWAP/VWAP/POV, Almgren–Chriss, impact, shortfall |
| Library | `cfmat.microstructure` |
| Prerequisites | [M11](../m11-backtesting-research/README.md) |
| Committed topics | Market microstructure |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

A strategy's paper edge is paid out through the order book. Spreads, depth, adverse selection
and market impact decide how much of it survives, and at what size. This module explains how
limit order books work, why trading moves prices, and how execution algorithms trade off impact
against risk — then measures the result with transaction-cost analysis.

## Learning outcomes

By the end of the module you can:

1. Explain limit order books, price–time priority, spreads, depth and resilience, and simulate a book.
2. Explain adverse selection and informed trading (Kyle, Glosten–Milgrom intuition) and why spreads exist.
3. Estimate market impact with the square-root law and relate it to participation rate.
4. Implement TWAP, VWAP and POV schedules and the Almgren–Chriss optimal trajectory.
5. Measure implementation shortfall and run a basic transaction-cost analysis against benchmarks.
6. Describe co-location, latency, high-frequency trading and market making (Avellaneda–Stoikov intuition) at a conceptual level, and the regulatory context in India.

## Before you start

- M11 complete (costs and fills).
- Read Harris, *Trading and Exchanges*, ch. 6–8.

## Weekly plan

### Week 32 — Order books, liquidity, adverse selection and market impact

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M14 · 15–60 limit order books: matching, price–time priority, spreads, depth, resilience; NSE market types and auctions · 60–70 break · 70–120 why spreads exist: inventory, order processing, adverse selection; Kyle and Glosten–Milgrom intuition · 120–170 live: simulate a book with random flow (`microstructure.OrderBook`) · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 market impact: temporary vs permanent; the square-root law; participation rates · 60–70 break · 70–130 workshop: impact estimates for small, mid and large caps at different order sizes · 130–170 HFT and market making (concepts), co-location and latency; the Indian regulatory context · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 15a §1: order book simulation · 100–120 blockers |
| OH · Wed · 60 min | Microstructure Q&A |
| C2 · Thu · 120 min | 0–60 Lab 15a §4 impact estimate · 60–100 peer review · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 15a · 20–50 read a real depth snapshot (≥ 3 months old) · 50–60 preview |
| Self-study · ~6 h | Harris ch. 6–14 (selected); Bouchaud et al. (square-root law) |

### Week 33 — Execution algorithms and transaction-cost analysis

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 TWAP, VWAP and POV: definitions, volume profiles, integer lots · 60–70 break · 70–120 Almgren–Chriss: impact vs risk, risk aversion, the efficient frontier of execution · 120–170 implementation shortfall and TCA benchmarks (arrival, VWAP, close) · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–70 workshop: schedules for 2,00,000 shares over a session; AC trajectories for three risk-aversion levels · 70–80 break · 80–140 a TCA report for a set of fills · 140–170 guest: a broker's execution desk · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 15a §2–§3 · 100–120 review |
| OH · Wed · 60 min | Assignment clinic |
| C2 · Thu · 120 min | 0–60 exercise: POV with a volume shock · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 15b · 20–50 peer review of assignment drafts · 50–60 preview of M16 |
| Self-study · ~6 h | Almgren and Chriss (2000); Kissell, *The Science of Algorithmic Trading*, ch. 1–4 |

## Labs

**Lab 15a — market microstructure and execution algorithms** (`lab_15a_order_book_execution.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Order book | Random order flow into a price–time book; spread and depth | Resting orders fill in time priority |
| 2. Schedules | TWAP, VWAP and POV for 2,00,000 shares in 25 buckets | Schedules sum exactly to the order |
| 3. Almgren–Chriss | Trajectories and cost/risk for different risk aversion | Faster is costlier, slower is riskier |
| 4. Impact and shortfall | Square-root impact; implementation shortfall of a fill set | Shortfall decomposed and explained |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 15a, 15b | quizzes (10%) | Fri W32, W33 | Concepts and numericals |
| Lab 15a | labs (20%) | Sun W33 | Runs; explanations |
| Assignment: an execution plan | assignments (15%) | Sun W34 | For a large order in a mid-cap stock: estimate impact, choose a schedule, justify risk aversion, and write the TCA you would run afterwards. Rubric: analysis 40, choice and justification 30, TCA design 30 |

## Common mistakes

- Assuming fills at the last traded price for size → impact estimates in §4.
- Using a flat volume profile for VWAP → U-shaped intraday profile (`data.intraday_volume_profile`).
- Rounding child orders independently so they no longer sum to the parent → integer split in `schedules`.
- Measuring performance against the VWAP you influenced → arrival-price benchmark.

## Readings

- Larry Harris, *Trading and Exchanges*, ch. 6–14 (selected).
- Almgren and Chriss (2000), "Optimal Execution of Portfolio Transactions".
- Robert Kissell, *The Science of Algorithmic Trading and Portfolio Management*, ch. 1–4.
- Cartea, Jaimungal and Penalva, *Algorithmic and High-Frequency Trading*, ch. 1–2.

## Instructor notes

- Owner: risk and execution lead.
- Depth snapshots used in class must be at least three months old and anonymised where required by the data licence.
- M16 builds on this module's data concepts; keep the vocabulary consistent (bars, ticks, sessions).
