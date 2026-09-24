# Module 02 — Python for Financial Analysis

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 1 · Market Foundations | 3–4 | 20 | [`lab02_python_for_finance.py`](../../labs/lab02_python_for_finance.py) |

## Learning outcomes

1. Write idiomatic, vectorised Python with NumPy and pandas for time-series data.
2. Load, clean, align and resample market data from CSV files and APIs.
3. Compute simple and log returns, rolling statistics, drawdowns and summary tables.
4. Produce clear charts with matplotlib.
5. Organise code into functions, classes and modules; manage environments; use Git and GitHub.
6. Write unit tests with pytest for financial calculations.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Python for finance (Sat, W3) | Data types, control flow, functions, comprehensions; NumPy arrays, broadcasting, vectorisation vs loops |
| L2 | pandas time series (Sun, W3) | DatetimeIndex, slicing, `resample`, `rolling`, `shift`, `pct_change`, joins and alignment, missing data, time zones |
| C1 | Clinic (Tue, W3) | Loading real and synthetic data (`cfmat.data`), cleaning and alignment |
| C2 | Clinic (Thu, W3) | Returns and volatility exercises |
| L3 | Visualisation and design (Sat, W4) | matplotlib; functions vs classes; dataclasses; packaging a small library |
| L4 | Engineering practice (Sun, W4) | Virtual environments, Git branching and pull requests, pytest, code style, reading other people's code (a tour of `cfmat`) |
| C3 | Clinic (Tue, W4) | Lab 2 |
| C4 | Clinic (Thu, W4) | First pull request and peer code review |

## Assignment

Add a function `rolling_beta(stock, index, window)` to a fork of `cfmat.metrics`, with tests in `tests/`, and open a pull request. Reviewers check correctness, tests and readability.

## Readings

- Yves Hilpisch, *Python for Finance*: chapters 4–8.
- Wes McKinney, *Python for Data Analysis*: time-series chapter.
- pandas user guide: "Time series / date functionality".

## Assessment

Quiz 2; Lab 2; graded pull request (part of the lab score).
