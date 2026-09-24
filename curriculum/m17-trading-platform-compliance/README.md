# M17 · Trading Platform, Broker APIs and Compliance

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T4 · Risk, Portfolio and Trading Systems |
| Weeks | 35–36 |
| Hours | 24 guided |
| Labs | [17a](lab_17a_oms_rms_paper_trading.py) — Paper broker, RMS rejects, throttle, kill switch, trade journal |
| Library | `cfmat.trading`, `cfmat.backtesting.event_driven` |
| Prerequisites | [M11](../m11-backtesting-research/README.md), [M13](../m13-risk-position-sizing/README.md) |
| Committed topics | Trading platform structure and infrastructure, Risk management and position sizing |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Between a signal and a fill sit the order management system (OMS), the pre-trade risk manager
(RMS), a broker API and a regulator. In India, SEBI's retail-algo framework makes brokers
responsible for every algo order and requires identification, limits and audit trails. This
module builds the platform pieces learners need for capstone paper trading, and teaches the rules
they must design for from day one.

## Learning outcomes

By the end of the module you can:

1. Design the architecture of an automated trading system: market data, signal, OMS, RMS, execution, storage and monitoring, with latency budgets and failure modes.
2. Integrate with a broker API through an adapter interface (`cfmat.trading.BrokerAdapter`) and describe FIX at a conceptual level.
3. Implement order state machines, pre-trade risk checks (size, value, price band, position, daily loss, orders per second), a kill switch and position reconciliation.
4. Deploy a strategy on a cloud server with a static IP, secrets management, logging and alerting.
5. Explain SEBI's retail-algo framework (algo IDs, broker as principal, empanelled providers, order-rate thresholds, white-box vs black-box) and the research-analyst and investment-adviser rules as they apply to algo builders.
6. Keep audit trails suitable for broker and exchange review.

## Before you start

- M11 (event-driven engine) and M13 (risk limits) complete.
- Read the SEBI circular of 4 February 2025 on safer participation of retail investors in algorithmic trading, and the NSE implementation standards.

## Weekly plan

### Week 35 — OMS/RMS architecture, broker APIs and paper trading

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M16 · 15–60 architecture: components, event loops, queues, latency budgets, failure modes · 60–70 break · 70–120 the OMS: order states, idempotent order IDs, partial fills, cancels and modifies; reconciliation · 120–170 tour of `cfmat.trading` and `backtesting.event_driven`: why the same strategy code runs in backtest and paper · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 broker APIs: REST and WebSocket (Kite Connect, Upstox, SmartAPI, IBKR); auth and sessions; rate limits · 60–70 break · 70–130 the RMS: pre-trade checks, throttles, kill switch, mark-to-market loss limits · 130–170 workshop: configure `RiskLimits` for a capstone-like strategy and try to break them · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 17a §1–§3 · 100–120 blockers |
| OH · Wed · 60 min | Adapter design clinic |
| C2 · Thu · 120 min | 0–60 Lab 17a §4–§5: kill switch; a `BrokerAdapter` skeleton for a sandbox or mock · 60–100 peer review · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 17a · 20–50 incident role-play: runaway orders · 50–60 preview |
| Self-study · ~6 h | Narang, *Inside the Black Box*, execution and infrastructure chapters; broker API docs |

### Week 36 — SEBI's retail-algo framework, audit trails and operational risk

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 the retail-algo framework: algo IDs, broker as principal, empanelled algo providers, order-rate thresholds, white-box vs black-box, static IPs, API-key controls · 60–70 break · 70–120 RA and IA regulations: when sharing a strategy becomes advice; market-abuse rules (spoofing, front-running, insider trading) · 120–170 guest: a broker's compliance head · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 deployment: cloud VM, static IP, secrets, process supervision, time sync · 60–70 break · 70–130 audit trails: what to log, retention, tamper evidence; the trade journal (`cfmat.trading.TradeJournal`, `automation.journal_store`) · 130–170 incident runbooks: disconnects, stuck orders, reconciliation breaks · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 deploy the paper strategy on a VM with a static IP (course cloud) · 100–120 review |
| OH · Wed · 60 min | Assignment clinic |
| C2 · Thu · 120 min | 0–60 incident drill: kill the network mid-session · 60–100 peer review of runbooks · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 17b · 20–50 compliance case cards · 50–60 preview of M18 |
| Self-study · ~6 h | SEBI circular and exchange standards; finish the assignment |

## Labs

**Lab 17a — trading infrastructure, pre-trade risk and paper trading** (`lab_17a_oms_rms_paper_trading.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Limits and paper broker | Configure `RiskLimits`; place orders | Accounting matches hand calculation |
| 2. RMS in action | Trigger size, value, band, position and throttle rejects | Every reject has a readable reason |
| 3. Intraday strategy | Momentum strategy with a hard square-off | Flat at the close every day |
| 4. Kill switch | Loss-limit breach halts trading | No orders after the switch; positions flattened |
| 5. From paper to live | Sketch a `BrokerAdapter` | Same strategy code, different adapter |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 17a, 17b | quizzes (10%) | Fri W35, W36 | Architecture and regulation |
| Lab 17a | labs (20%) | Sun W36 | Runs; rejects and switch explained |
| Assignment: adapter and runbook | assignments (15%) | Sun W37 | A `BrokerAdapter` for a broker sandbox or a documented mock, `RiskManager` in front of it, and an incident runbook (runaway orders, API disconnect, reconciliation break). Rubric: adapter 35, risk controls 30, runbook 35 |

## Common mistakes

- Retrying a timed-out order without an idempotent client ID → duplicate orders.
- Risk checks in the strategy instead of in front of the broker → RMS sits in the order path.
- API keys in code or notebooks → secrets management; `.env` is git-ignored.
- Sharing strategy signals with friends "for fun" → RA/IA rules in L1 W36.

## Readings

- SEBI circular (4 February 2025), "Safer participation of retail investors in algorithmic trading", and NSE/BSE implementation standards.
- SEBI (Research Analysts) and (Investment Advisers) Regulations — scope sections.
- Rishi K. Narang, *Inside the Black Box*, execution and infrastructure chapters.
- Your chosen broker's API documentation.

## Instructor notes

- Owner: risk and execution lead with a compliance guest.
- Re-check the regulatory framework and exchange standards before every cohort; update this guide and [compliance](../../course/09-compliance-and-risk-disclosures.md) together.
- Learners must not connect to live trading in the programme. Sandbox and paper only.
