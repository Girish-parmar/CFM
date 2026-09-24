# %% [markdown]
# # Lab 05a — Databases and Market Data Engineering (M05)
#
# **Goals**
# 1. Design a normalised schema for instruments, daily bars and corporate actions.
# 2. Load data with parameterised inserts inside a transaction.
# 3. Answer research questions in SQL: window functions, aggregates, joins.
# 4. Check index usage with EXPLAIN QUERY PLAN and move results into pandas.
#
# SQLite ships with Python, so this lab runs anywhere. The same SQL runs on
# PostgreSQL/TimescaleDB, which we use in class for tick data.

# %%
import sqlite3

import pandas as pd

from cfmat import data

con = sqlite3.connect(":memory:")
con.executescript(
    """
    CREATE TABLE instruments (
        symbol      TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        sector      TEXT NOT NULL,
        exchange    TEXT NOT NULL DEFAULT 'NSE',
        lot_size    INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE daily_bars (
        symbol  TEXT NOT NULL REFERENCES instruments(symbol),
        date    TEXT NOT NULL,             -- ISO yyyy-mm-dd
        open REAL, high REAL, low REAL, close REAL NOT NULL,
        volume  INTEGER,
        PRIMARY KEY (symbol, date)
    );
    CREATE TABLE corporate_actions (
        symbol   TEXT NOT NULL REFERENCES instruments(symbol),
        ex_date  TEXT NOT NULL,
        action   TEXT NOT NULL CHECK (action IN ('SPLIT', 'BONUS', 'DIVIDEND')),
        value    REAL NOT NULL
    );
    CREATE INDEX idx_bars_date ON daily_bars(date);
    """
)

# %% [markdown]
# ## Load a synthetic universe

# %%
prices = data.universe(6, 500, seed=8, start="2024-01-01")
sectors = ["Banking", "IT", "Pharma", "Energy", "Auto", "FMCG"]
with con:  # one transaction: all rows or none
    con.executemany(
        "INSERT INTO instruments(symbol, name, sector) VALUES (?, ?, ?)",
        [(s, f"Synthetic {sec} Co", sec) for s, sec in zip(prices.columns, sectors)],
    )
    for sym in prices.columns:
        bars = data.ohlcv_from_close(prices[sym], seed=1)
        con.executemany(
            "INSERT INTO daily_bars VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(sym, d.strftime("%Y-%m-%d"), *row) for d, row in
             zip(bars.index, bars[["open", "high", "low", "close", "volume"]].itertuples(index=False))],
        )
    con.execute("INSERT INTO corporate_actions VALUES ('SYN02', '2024-06-14', 'DIVIDEND', 12.5)")
print(con.execute("SELECT COUNT(*) FROM daily_bars").fetchone()[0], "bars loaded")

# %% [markdown]
# ## Query 1 — latest close and 1-year return per symbol (window functions)

# %%
q1 = """
WITH ranked AS (
    SELECT symbol, date, close,
           LAG(close, 250) OVER (PARTITION BY symbol ORDER BY date) AS close_1y_ago,
           ROW_NUMBER()    OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
    FROM daily_bars
)
SELECT r.symbol, i.sector, r.date, ROUND(r.close, 2) AS close,
       ROUND(100.0 * (r.close / r.close_1y_ago - 1), 2) AS ret_1y_pct
FROM ranked r JOIN instruments i USING (symbol)
WHERE r.rn = 1
ORDER BY ret_1y_pct DESC;
"""
print(pd.read_sql(q1, con))

# %% [markdown]
# ## Query 2 — 20-day moving average and a crossover flag in pure SQL

# %%
q2 = """
SELECT date, ROUND(close, 2) AS close,
       ROUND(AVG(close) OVER w20, 2) AS sma20,
       CASE WHEN close > AVG(close) OVER w20 THEN 1 ELSE 0 END AS above_sma
FROM daily_bars
WHERE symbol = 'SYN01'
WINDOW w20 AS (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
ORDER BY date DESC LIMIT 5;
"""
print(pd.read_sql(q2, con))

# %% [markdown]
# ## Query 3 — monthly returns by sector (aggregation)

# %%
q3 = """
WITH month_end AS (
    SELECT symbol, substr(date, 1, 7) AS month, close,
           ROW_NUMBER() OVER (PARTITION BY symbol, substr(date, 1, 7) ORDER BY date DESC) AS rn
    FROM daily_bars
), monthly AS (
    SELECT symbol, month, close / LAG(close) OVER (PARTITION BY symbol ORDER BY month) - 1 AS ret
    FROM month_end WHERE rn = 1
)
SELECT i.sector, COUNT(m.ret) AS months, ROUND(100 * AVG(m.ret), 2) AS avg_monthly_ret_pct,
       ROUND(100 * MIN(m.ret), 2) AS worst_pct, ROUND(100 * MAX(m.ret), 2) AS best_pct
FROM monthly m JOIN instruments i USING (symbol)
WHERE m.ret IS NOT NULL
GROUP BY i.sector ORDER BY avg_monthly_ret_pct DESC;
"""
print(pd.read_sql(q3, con))

# %% [markdown]
# ## Query plans: is the index used?

# %%
for sql in ("SELECT * FROM daily_bars WHERE symbol = 'SYN03' AND date >= '2025-01-01'",
            "SELECT * FROM daily_bars WHERE date = '2025-03-03'",
            "SELECT * FROM daily_bars WHERE volume > 1000000"):
    plan = con.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    print(f"{sql}\n   → {plan[0][-1]}")

# %% [markdown]
# ## Data-quality checks every pipeline should run

# %%
checks = {
    "high below low": "SELECT COUNT(*) FROM daily_bars WHERE high < low",
    "close outside range": "SELECT COUNT(*) FROM daily_bars WHERE close > high OR close < low",
    "non-positive volume": "SELECT COUNT(*) FROM daily_bars WHERE volume <= 0",
    "daily move > 20%": """SELECT COUNT(*) FROM (SELECT close / LAG(close) OVER (PARTITION BY symbol ORDER BY date) - 1 AS r
                            FROM daily_bars) WHERE ABS(r) > 0.20""",
}
for name, sql in checks.items():
    print(f"{name:<22}: {con.execute(sql).fetchone()[0]} rows")
con.close()

# %% [markdown]
# ## Exercises
# 1. Add a `minute_bars` table and write a query that builds 15-minute bars from it.
# 2. Write SQL that applies `corporate_actions` splits to produce adjusted closes.
# 3. Port the schema to PostgreSQL + TimescaleDB (`create_hypertable`) and compare
#    query speed on 5 years of minute data.
