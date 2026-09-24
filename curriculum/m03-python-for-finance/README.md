# M03 · Python for Financial Analysis

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T1 · Foundations |
| Weeks | 5–6 |
| Hours | 24 guided |
| Labs | [03a](lab_03a_python_for_finance.py) — Returns, resampling, rolling volatility, drawdowns |
| Library | `cfmat.data`, `cfmat.analytics.metrics` |
| Prerequisites | [M00](../m00-prework/README.md) |
| Committed topics | – |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Every later module is taught through code. Learners who can load, align and transform time
series quickly, and who write small tested functions, spend their clinic time on finance
instead of fighting pandas. This module also sets the engineering habits the capstone is graded
on: version control, tests, readable code and reproducible environments.

## Learning outcomes

By the end of the module you can:

1. Write idiomatic, vectorised Python with NumPy and pandas for time-series data.
2. Load, clean, align and resample market data from CSV files and APIs, including time zones and missing days.
3. Compute simple and log returns, rolling statistics, drawdowns and month × year tables.
4. Produce clear, labelled charts with matplotlib.
5. Organise code into functions, dataclasses and modules; manage a virtual environment; use Git branches and pull requests.
6. Write unit tests with pytest for financial calculations, including edge cases.

## Before you start

- Pre-work Weeks −3 and −2 complete.
- Clone the course repository and run `pytest -m "not lab"` once; it should pass.

## Weekly plan

### Week 5 — Python, NumPy and pandas for market data

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M02 · 15–60 Python refresher at speed: comprehensions, functions, `*args/**kwargs`, f-strings, exceptions · 60–70 break · 70–125 NumPy: arrays, broadcasting, vectorisation vs loops (timed demo) · 125–170 simple vs log returns; why log returns add over time and simple returns add across assets · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 pandas time series: `DatetimeIndex`, slicing, `shift`, `pct_change`, `rolling`, `resample` · 60–70 break · 70–130 alignment and joins of multiple symbols; missing days, holidays, time zones (IST vs UTC) · 130–170 live exercise: build a returns panel for 10 synthetic stocks with `cfmat.data.universe` · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–90 Lab 03a §1–§2: returns, resampling to weekly/monthly bars · 90–120 blockers |
| OH · Wed · 60 min | pandas troubleshooting: `SettingWithCopyWarning`, index alignment surprises |
| C2 · Thu · 120 min | 0–60 Lab 03a §3–§4: month × year table, rolling volatility, drawdown · 60–100 peer code review in pairs · 100–120 two solutions shown |
| QP · Fri · 60 min | 0–20 quiz 3a · 20–50 code-reading exercise: find three bugs in a returns function · 50–60 preview |
| Self-study · ~6 h | McKinney ch. 11 (time series); Hilpisch ch. 4–6; exercises |

### Week 6 — Clean code: functions, tests, Git and packaging

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 functions vs classes; dataclasses; type hints; docstrings · 60–70 break · 70–120 matplotlib: figures and axes, subplots, labelling, saving (`cfmat.infra.plotting.savefig`) · 120–170 tour of the `cfmat` package: subpackages, public API, where tests live · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 virtual environments, `pip install -e .`, dependencies and constraints · 60–70 break · 70–130 Git: branches, commits, pull requests, reviews; the repository's contributing rules · 130–170 pytest: arrange-act-assert, fixtures, parametrisation, testing floating-point results · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 write `rolling_beta(stock, index, window)` with tests (the assignment) · 100–120 review |
| OH · Wed · 60 min | Git clinic: rebases gone wrong, merge conflicts |
| C2 · Thu · 120 min | 0–60 first pull request on GitHub Classroom · 60–110 peer code review with the course checklist · 110–120 wrap-up |
| QP · Fri · 60 min | 0–20 quiz 3b · 20–50 review feedback on pull requests · 50–60 preview of M04 |
| Self-study · ~6 h | *Python for Data Analysis* ch. 11; pytest docs "Getting started"; Git book ch. 3 |

## Labs

**Lab 03a — Python for financial analysis** (`lab_03a_python_for_finance.py`)

| Section | You do | What good looks like |
|---|---|---|
| Simple vs log returns | Compare sums of log returns with products of (1 + r) | Both reproduce the actual growth to 4 decimals |
| Resampling | Weekly OHLCV bars; monthly returns | Correct aggregation rules (first/max/min/last/sum) |
| Month × year table | Pivot monthly returns | Columns in calendar order, values in % |
| Rolling volatility and drawdown | 20-day annualised vol; drawdown series; summary | Chart saved with three labelled panels |

Stretch: switch `USE_REAL_DATA = True` for three NSE stocks (needs `pip install yfinance`).

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 3a, 3b | quizzes (10%) | Fri W5, W6 | 10 questions; half are code-reading |
| Lab 03a | labs (20%) | Sun W6 | Runs; exercises answered |
| Assignment: `rolling_beta` pull request | assignments (15%) | Sun W7 | Correct (matches `np.cov` reference), vectorised, tested (≥ 3 tests incl. an edge case), reviewed by a peer. Rubric: correctness 40, tests 30, readability 20, review etiquette 10 |

## Common mistakes

- Looping over rows where a vectorised expression exists → timed demo in L1 W5.
- Joining symbols with different calendars and silently forward-filling prices → alignment exercise in L2 W5.
- Comparing floats with `==` in tests → `pytest.approx` in L2 W6.
- Committing data files, notebooks with outputs or secrets → `.gitignore` walkthrough; the `data/` folder is ignored by design.

## Readings

- Wes McKinney, *Python for Data Analysis*, ch. 4–5 and 11.
- Yves Hilpisch, *Python for Finance*, ch. 4–8.
- pandas user guide: "Time series / date functionality".
- *Pro Git* (Chacon and Straub), ch. 2–3.

## Instructor notes

- Owner: Python and data engineering lead.
- Learners who pass the M03 test-out quiz in Week 0 act as peer mentors in clinics and take the stretch exercises instead.
- Keep GitHub Classroom set up before Week 5; the pull-request assignment needs it.
- Show `cfmat`'s own tests as examples of good tests (for example `tests/test_analytics.py`).
