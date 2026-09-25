# M00 · Pre-work: Python, Statistics and Markets Primer

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T0 · Pre-work |
| Weeks | −3 to 0 |
| Hours | 40 self-paced |
| Labs | [00a](lab_00a_environment_check.py) — Environment check and first chart |
| Library | `cfmat.data`, `cfmat.analytics.metrics` |
| Prerequisites | – |
| Committed topics | – |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

A cohort moves at the pace of its slowest week-1 laptop. Pre-work makes sure every learner
arrives with a working environment, enough Python to read the labs, enough statistics to
follow a t-test, and a mental model of what an exchange does. It is self-paced over the four
weeks before Week 1 and ends with an entry assessment. Nothing here is advanced; skipping it
is the most common reason learners fall behind in Term 1.

## Learning outcomes

By Week 0 you can:

1. Install Python 3.11 (or 3.12), create a virtual environment, install the course package and run a lab from VS Code or JupyterLab.
2. Write short Python programs with variables, lists, dictionaries, loops, functions and f-strings.
3. Load a CSV into pandas, select rows and columns, compute a new column and plot it.
4. Compute a mean, standard deviation, percentile and correlation, and explain what a p-value is (and is not).
5. Explain what a stock, an index, a broker and an exchange are, and what "T+1 settlement" means.

## Before you start

- Hardware: a laptop with at least 8 GB RAM and 4 cores (16 GB recommended), admin rights to install software.
- Follow the [setup and run guide](../../course/12-setup-and-run-guide.md) (Steps 1–6) before the Week −3 install clinic.
- Accounts: GitHub (free), the course LMS invitation, and the course Slack or Discord.
- Time: about 10 hours a week for 4 weeks. Block the time in your calendar now.

## Weekly plan

Pre-work is self-paced. Each week has short videos (V), reading (R), exercises (E) and one
live 60-minute onboarding call (C) on Saturday at 10:00 IST, recorded for those who cannot join.

### Week −3 — Python basics, Jupyter and VS Code

| Block | Plan |
|---|---|
| V · 90 min | Installing Python, VS Code and Git; virtual environments; running a script vs a notebook |
| R · 60 min | *Python Crash Course* (Matthes) ch. 1–4, or the official Python tutorial sections 3–5 |
| E · 4 h | 40 graded exercises on types, lists, dictionaries, loops, functions (auto-graded) |
| C · 60 min | 0–10 welcome · 10–40 live install clinic · 40–55 run `lab_00a` together · 55–60 next steps |
| Checkpoint | `lab_00a_environment_check.py` prints "All required checks passed"; paste the output into the pre-work form |

### Week −2 — pandas first steps and Excel-to-Python

| Block | Plan |
|---|---|
| V · 90 min | Series and DataFrames; reading CSVs; selecting, filtering, sorting; `groupby`; simple plots |
| R · 60 min | *Python for Data Analysis* (McKinney) ch. 5 |
| E · 4 h | Re-do three familiar Excel tasks in pandas: daily returns, a pivot table, a chart |
| C · 60 min | 0–10 recap · 10–45 live coding: returns from a price CSV · 45–60 questions |
| Checkpoint | Notebook with the three Excel-to-pandas tasks pushed to your GitHub |

### Week −1 — Algebra, probability and statistics refresher

| Block | Plan |
|---|---|
| V · 120 min | Logs and exponentials; summation; mean, variance, covariance, correlation; normal distribution; sampling; confidence intervals; hypothesis tests |
| R · 60 min | *OpenIntro Statistics* ch. 1–5 (free) |
| E · 4 h | 30 problems, half on paper and half in pandas |
| C · 60 min | 0–10 recap · 10–40 worked problems · 40–60 "p-values in plain English" discussion |
| Checkpoint | Problem set submitted |

### Week 0 — How stock markets work; entry assessment

| Block | Plan |
|---|---|
| V · 90 min | Exchanges, brokers, depositories and clearing corporations; order types; indices; what SEBI does |
| R · 60 min | NSE "Investor education" pages on trading and settlement; NISM Series VIII ch. 1 |
| E · 2 h | Practice entry assessment |
| Assessment · 90 min | Entry assessment: Python (40%), statistics (40%), markets (20%); pass mark 60%; one retake |
| C · 60 min | 0–20 how the programme runs (rhythm, LMS, GitHub Classroom) · 20–50 meet your TA group · 50–60 questions |

## Labs

**Lab 00a — environment check and first chart.** Checks Python and package versions, confirms
the `cfmat` library and its sample data are installed, and saves a price-and-drawdown chart.
What good looks like: every required line prints `OK` and the chart file exists. The printout
also makes a first point about randomness: a series built with a +10% drift can lose money over
three years.

## Assessment

| Item | Weight | Pass condition |
|---|---|---|
| Environment checkpoint (Week −3) | gate | `lab_00a` passes |
| Exercises (Weeks −3 to −1) | gate | 70% of auto-graded exercises correct |
| Entry assessment (Week 0) | gate | 60%; one retake within 5 days |

Pre-work does not count towards the final grade. Learners who miss the pass mark after the
retake join a 2-week bridge track and start with the next cohort, with no extra fee.

## Common mistakes

- Installing packages into the system Python instead of a virtual environment → the Week −3 clinic walks through `python -m venv` and `pip install -e ".[dev]"`.
- Working only in notebooks and never running a script → the checkpoint requires running `lab_00a` from a terminal.
- Treating a p-value as "the probability the result is true" → Week −1 discussion and assessment questions target this directly.

## Readings

- Eric Matthes, *Python Crash Course*, ch. 1–8.
- Wes McKinney, *Python for Data Analysis*, ch. 4–5.
- Diez, Çetinkaya-Rundel and Barr, *OpenIntro Statistics* (free PDF), ch. 1–5.
- NSE investor education pages; NISM Series VIII workbook, ch. 1.

## Instructor notes

- Owner: programme manager with the M03 lead. Refresh the installation videos each cohort for current Python and OS versions.
- Watch the Week −3 checkpoint closely: chase learners without a passing `lab_00a` by Week −2.
- The entry assessment bank lives in the LMS; rotate at least 30% of questions per cohort.
- Learners with a CS background may request the M03 test-out quiz after passing the entry assessment (see [learning routes](../../course/10-learning-routes.md)).
