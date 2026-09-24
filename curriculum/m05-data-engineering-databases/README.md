# M05 · Databases and Market Data Engineering

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T1 · Foundations |
| Weeks | 9–10 |
| Hours | 24 guided |
| Labs | [05a](lab_05a_market_database.py) — SQLite schema, window functions, query plans, data-quality checks |
| Library | `cfmat.data` |
| Prerequisites | [M03](../m03-python-for-finance/README.md) |
| Committed topics | Market data handling, Trading platform structure and infrastructure |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Research is only as good as its data. Survivorship bias, unadjusted corporate actions,
duplicated bars and silent gaps create strategies that exist only in the database. This module
teaches the storage and pipeline skills to keep market data correct, reproducible and fast to
query — the foundation for M16 (market data handling) and the capstone's reproducibility gate.

## Learning outcomes

By the end of the module you can:

1. Design a normalised relational schema for instruments, bars, ticks, corporate actions and trades, with keys and constraints that reject bad rows.
2. Write SQL with joins, aggregates, CTEs and window functions to answer research questions.
3. Use indexes, read query plans and explain when a query will scan the whole table.
4. Choose between row stores (PostgreSQL/TimescaleDB), columnar files (Parquet) and embedded analytics (DuckDB, SQLite) for a given workload.
5. Build idempotent, scheduled pipelines with data-quality checks (gaps, duplicates, spikes, stale prices, OHLC consistency).
6. Build point-in-time, survivorship-free universes and adjust for corporate actions.

## Before you start

- M03 complete. Install DB Browser for SQLite or DBeaver.
- Optional: Docker, to run PostgreSQL + TimescaleDB locally in Week 9.

## Weekly plan

### Week 9 — Relational design, SQL, window functions and time-series storage

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M04 · 15–60 keys, constraints, normal forms; the course schema (instruments, bars, corporate actions, trades) · 60–70 break · 70–125 SQL: SELECT, JOIN, GROUP BY, CTEs; window functions (LAG, ROW_NUMBER, moving averages) · 125–170 live drill: ten research questions in SQL · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 storage for market data: row vs column; PostgreSQL + TimescaleDB hypertables and compression; Parquet; DuckDB · 60–70 break · 70–130 indexes and query plans (`EXPLAIN QUERY PLAN`); partitioning by date · 130–170 benchmark: the same query on SQLite, DuckDB over Parquet and pandas · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–90 Lab 05a: load a synthetic universe into SQLite, queries 1–2 · 90–120 blockers |
| OH · Wed · 60 min | SQL clinic |
| C2 · Thu · 120 min | 0–60 Lab 05a: query 3, query plans · 60–100 SQL research drills in pairs · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 5a · 20–50 schema review: find the design flaws in a sample schema · 50–60 preview |
| Self-study · ~6 h | Kleppmann ch. 2–3; PostgreSQL docs on window functions |

### Week 10 — Pipelines, data quality, corporate actions and survivorship-free universes

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 ingestion from files and APIs; idempotent upserts; retries; logging · 60–70 break · 70–120 data-quality rules: gaps, duplicates, spikes, stale prices, OHLC consistency, volume sanity · 120–170 scheduling (cron, n8n preview) and alerting on failed checks · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 survivorship bias and index-membership history; delisted symbols · 60–70 break · 70–120 corporate-action adjustment as a view, not a destructive update; point-in-time fundamentals · 120–170 data lineage and documentation: a data card for each dataset · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 05a: data-quality checks section; the assignment pipeline skeleton · 100–120 review |
| OH · Wed · 60 min | Assignment clinic |
| C2 · Thu · 120 min | 0–60 pipeline review in pairs (re-run twice: row counts must not change) · 60–120 Term 1 revision |
| QP · Fri · 60 min | 0–20 quiz 5b · 20–50 peer review of assignment drafts · 50–60 Term 1 exam briefing |
| Self-study · ~6 h | TimescaleDB and DuckDB docs; finish the assignment; revise for the Term 1 exam |

## Labs

**Lab 05a — databases and market data engineering** (`lab_05a_market_database.py`)

| Section | You do | What good looks like |
|---|---|---|
| Load a universe | Create tables with keys and constraints; insert bars | Re-running does not duplicate rows |
| Query 1 | Latest close and 1-year return per symbol with window functions | Matches a pandas cross-check |
| Query 2 | 20-day moving average and a crossover flag in SQL | Flags match `cfmat.analytics.indicators.sma` |
| Query 3 | Monthly returns by sector | Sector aggregation correct |
| Query plans | Compare plans with and without an index | You can point to the index being used |
| Data quality | Gap, duplicate, spike and OHLC checks | Planted problems are found; clean data passes |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 5a, 5b | quizzes (10%) | Fri W9, W10 | SQL reading and writing |
| Lab 05a | labs (20%) | Sun W10 | Runs; queries correct |
| Assignment: an idempotent pipeline | assignments (15%) | Sun W12 | Loads daily bars for 20 symbols into SQLite or PostgreSQL, applies corporate actions through an adjusted view, runs the data-quality checks, logs results, and can be re-run safely. Rubric: correctness 35, idempotency 25, quality checks 25, documentation 15 |
| Term 1 exam | term exams (20%) | Week 11 | 4 h, covers M01–M05 |

## Common mistakes

- Overwriting raw prices with adjusted prices → keep raw data immutable; adjust in a view.
- `INSERT` without a uniqueness constraint → duplicated bars after a retry; use keys and upserts.
- Building a universe from today's index members → survivorship bias; use membership history.
- Storing timestamps without a time zone → IST/UTC mix-ups in intraday data.

## Readings

- Martin Kleppmann, *Designing Data-Intensive Applications*, ch. 2–3.
- PostgreSQL documentation: window functions; TimescaleDB documentation: hypertables.
- DuckDB documentation: querying Parquet files.
- Brown, Goetzmann and Ross (1995), "Survival" (survivorship bias).

## Instructor notes

- Owner: Python and data engineering lead.
- SQLite is enough for the lab; PostgreSQL + TimescaleDB is optional and demonstrated in L2 W9.
- Plant three data problems in the C2 W10 pipeline review dataset and see who finds them.
- Keep Term 1 exam questions on SQL to reading and short writing tasks; no syntax trivia.
