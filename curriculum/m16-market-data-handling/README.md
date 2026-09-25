# M16 · Market Data Handling

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T4 · Risk, Portfolio and Trading Systems |
| Weeks | 34 |
| Hours | 12 guided |
| Labs | [16a](lab_16a_market_data_handler.py) — Tick validation with scored detectors, time/volume/dollar bars, instrument master, continuous futures, storage and replay |
| Library | `cfmat.data`, `cfmat.data.handler`, `cfmat.data.providers`, `cfmat.data.fetch` |
| Prerequisites | [M05](../m05-data-engineering-databases/README.md), [M15](../m15-microstructure-execution/README.md) |
| Committed topics | Market data handling |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

A live strategy lives or dies on its data handler: the component that turns feeds into clean
bars, knows every instrument's lot size and expiry, detects stale or bad ticks, and stores
everything so research and trading see the same numbers. M05 built research databases; this
week builds the real-time and near-real-time side that M17's platform and M18's monitoring need.

## Learning outcomes

By the end of the module you can:

1. Describe market-data feeds (broker WebSocket APIs, exchange snapshots, vendor files) and their failure modes: gaps, duplicates, out-of-order and stale ticks.
2. Aggregate ticks into time, volume and dollar bars with correct open/high/low/close/volume and session boundaries.
3. Maintain an instrument master: symbols, tokens, lot sizes, tick sizes, expiries, corporate actions, F&O eligibility.
4. Build continuous futures series with back-adjustment or ratio adjustment and explain the trade-offs.
5. Validate data in real time: spike filters, gap detection, staleness alarms, cross-source reconciliation.
6. Store ticks and bars efficiently (Parquet partitioned by date and symbol) and replay them for testing.

## Before you start

- M05 (pipelines, quality checks) and M15 (order books) complete.
- Read one broker's WebSocket API documentation (for example Kite Connect or SmartAPI streaming).

## Weekly plan

### Week 34 — Feeds, ticks to bars, instrument masters, data quality and storage

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M15 · 15–60 feeds: WebSocket streams, snapshots, vendor files; ticks vs depth; failure modes and reconnection · 60–70 break · 70–120 bars from ticks: time, volume and dollar bars; session boundaries, pre-open and auctions; what "close" means · 120–170 the instrument master: tokens, lot sizes, tick sizes, expiries, F&O ban lists; daily refresh · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 continuous futures: roll rules, back-adjusted vs ratio-adjusted series, and what each does to returns and indicators · 60–70 break · 70–130 real-time validation: spike filters, gap and staleness alarms, cross-source checks; logging for audit · 130–170 storage and replay: Parquet partitioning, DuckDB queries, deterministic replay for testing · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 16a §1–§4: the faulty feed, bars from raw ticks, scored validation, time/volume/dollar bars and the live bar builder · 100–120 blockers |
| OH · Wed · 60 min | Assignment clinic |
| C2 · Thu · 120 min | 0–60 Lab 16a §5–§6: instrument master, continuous futures three ways, partitioned storage and deterministic replay · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 16 · 20–50 incident cards: "the feed froze at 11:02 — what does your system do?" · 50–60 preview of M17 |
| Self-study · ~6 h | López de Prado ch. 2 (bars); broker API docs; assignment |

## Labs

**Lab 16a — market data handler** (`lab_16a_market_data_handler.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. The feed | Read a day of ticks in arrival order, with its answer key of planted faults | You can name each fault and how a real feed produces it |
| 2. Bars from the raw feed | Build one-minute bars without cleaning | You show the fake high from a bad print, the double-counted volume and the thin outage minutes |
| 3. Validation | Duplicates, late ticks, spikes, frozen prices and outages, scored against the answer key; a clean day; a genuine +3% jump | Precision and recall 1.0; no alarms on the clean day; the real jump accepted |
| 4. Bars | Time (from the session open), volume and dollar bars; the live `BarBuilder` | Live bars equal batch bars exactly |
| 5. Instruments and continuous futures | Lot and tick checks, front month with a roll rule; raw vs back- vs ratio-adjusted | You explain which series to use for returns, for point P&L and for levels |
| 6. Storage and replay | Partitions by date and symbol; load one day; replay a toy strategy | Same signals on every replay and from memory |

The detectors were checked on 40 seeded days: every planted fault found, no false alarms on
faulty or clean days. Parquet storage needs `pip install -e ".[data]"` (pyarrow); without it
the handler stores CSV.

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quiz 16 | quizzes (10%) | Fri W34 | Concepts and incident handling |
| Lab 16a | labs (20%) | Sun W34 | Runs; each fault, its detector and its effect on bars explained |
| Assignment: a data-handler design | assignments (15%) | Sun W35 | Design document (≤ 3 pages) for the capstone's data handler: sources, bar types, validation rules with thresholds, instrument-master refresh, storage and replay, alerting. Rubric: completeness 35, failure handling 35, clarity 30 |

## Common mistakes

- Building bars from ticks without de-duplication and ordering → planted faults in the lab.
- Using unadjusted futures series across rolls for indicators → continuous-futures session.
- Hard-coding lot sizes → instrument master with a daily refresh.
- Silent staleness: a frozen feed that keeps the last price → staleness alarms in M18.

## Readings

- Marcos López de Prado, *Advances in Financial Machine Learning*, ch. 2.
- Broker streaming API documentation (Kite Connect, SmartAPI, Upstox).
- NSE market data documentation (snapshot and tick-by-tick product descriptions).
- Apache Parquet and DuckDB documentation.

## Instructor notes

- Owner: Python and data engineering lead.
- Lab 16a uses a synthetic, seeded feed with an answer key, so detector quality can be graded; the exercise on real bars uses `python -m cfmat.data.fetch`.
- Do not connect learners to live broker feeds in class; use recorded or synthetic streams.
