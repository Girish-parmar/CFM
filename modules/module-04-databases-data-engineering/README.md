# Module 04 — Databases and Market Data Engineering

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 1 · Market Foundations | 7–8 | 20 | [`lab04_market_database.py`](../../labs/lab04_market_database.py) |

## Learning outcomes

1. Design a normalised relational schema for instruments, bars, ticks, corporate actions and trades.
2. Write SQL with joins, aggregates, CTEs and window functions for research questions.
3. Use indexes and read query plans.
4. Store tick and minute data in PostgreSQL with TimescaleDB, and research data in Parquet with DuckDB.
5. Build idempotent, scheduled data pipelines with data-quality checks.
6. Build point-in-time, survivorship-free universes and adjust for corporate actions.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Relational design and SQL (Sat, W7) | Keys, constraints, normal forms; SELECT, JOIN, GROUP BY; CTEs; window functions (LAG, ROW_NUMBER, moving averages) |
| L2 | Storage for market data (Sun, W7) | Row vs column stores; PostgreSQL and TimescaleDB hypertables and compression; Parquet; DuckDB; when to use which |
| C1 | Clinic (Tue, W7) | Build the course database in SQLite and PostgreSQL |
| C2 | Clinic (Thu, W7) | SQL research drills |
| L3 | Pipelines and quality (Sat, W8) | Ingestion from files and APIs; idempotent upserts; validation rules; handling holidays, halts and bad ticks; scheduling (cron, n8n preview) |
| L4 | Research-grade data (Sun, W8) | Survivorship bias and index membership history; corporate-action adjustment; point-in-time fundamentals; data lineage and documentation |
| C3 | Clinic (Tue, W8) | Lab 4 |
| C4 | Clinic (Thu, W8) | Pipeline review; Term 1 revision |

## Assignment

Build a pipeline that loads daily bars for 20 symbols into PostgreSQL (or SQLite), applies corporate actions to produce an adjusted-close view, runs the data-quality checks from Lab 4, and can be re-run safely without duplicating rows.

## Readings

- Martin Kleppmann, *Designing Data-Intensive Applications*: chapters 2–3.
- PostgreSQL documentation: window functions; TimescaleDB documentation: hypertables.
- DuckDB documentation: querying Parquet files.

## Assessment

Quiz 4; Lab 4; pipeline assignment; Term 1 exam (Week 9).
