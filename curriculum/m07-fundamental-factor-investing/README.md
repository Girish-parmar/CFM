# M07 · Fundamental Analysis and Factor Investing

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T2 · Analysis and Derivatives |
| Weeks | 14 |
| Hours | 12 guided |
| Labs | [07a](lab_07a_factors_quantamental.py) — IC, winsorising, sector neutrality, composites, quintile spreads |
| Library | `cfmat.analytics.factors` |
| Prerequisites | [M04](../m04-statistics-time-series/README.md) |
| Committed topics | Fundamental and factor investing |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Fundamentals drive long-horizon returns, and factor portfolios (value, quality, momentum, low
volatility) are the most widely used systematic equity strategies. This one-week module connects
accounting ratios to cross-sectional scores and teaches the factor researcher's tools: the
information coefficient, winsorising, sector neutralisation, quintile spreads, turnover and
dry spells. It prepares learners for M14 (portfolio construction) and factor capstones.

## Learning outcomes

By the end of the module you can:

1. Read an income statement, balance sheet and cash-flow statement and compute valuation, profitability, leverage and cash-flow ratios.
2. Explain the main equity factors (value, quality, momentum, low volatility, size), the evidence for them and why they can stop working.
3. Build cross-sectional scores date by date: winsorise, z-score, sector-neutralise and combine.
4. Evaluate a factor with the information coefficient (mean IC, ICIR, hit rate) and quintile spreads.
5. Estimate a factor's turnover and its cost, and measure its dry spells.

## Before you start

- M04 complete (ranks, correlation, t-statistics).
- Skim one annual report of an Indian listed company (financial statements section).

## Weekly plan

### Week 14 — Statements, ratios and cross-sectional factor scores

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M06 · 15–60 the three statements; ratios: P/E, earnings yield, P/B, ROE, ROCE, debt/equity, interest cover, cash conversion · 60–70 break · 70–120 accounting red flags and Indian disclosure sources (annual reports, exchange filings, shareholding patterns) · 120–170 factor evidence: value, quality, momentum, low volatility, size — and their crashes · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 cross-sectional research on a (date, stock) panel: why every step is date by date · 60–70 break · 70–130 workshop with `cfmat.analytics.factors`: winsorise, z-score, neutralise, IC, quantile returns · 130–170 composites, turnover and capacity; point-in-time data and survivorship · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 07a §1–§2 · 100–120 blockers |
| OH · Wed · 60 min | Assignment clinic: sourcing real fundamentals |
| C2 · Thu · 120 min | 0–60 Lab 07a §3–§4 · 60–100 peer review · 100–120 discussion: which factor would you trust with your own money, and why? |
| QP · Fri · 60 min | 0–20 quiz 7 · 20–50 peer review of assignment drafts · 50–60 preview of M08 |
| Self-study · ~6 h | Fama–French (1993); Asness, Frazzini and Pedersen (2019); assignment |

## Labs

**Lab 07a — fundamental factors and quantamental scores** (`lab_07a_factors_quantamental.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Raw vs sector-neutral value | IC of raw and neutralised earnings yield | Raw value IC ≈ 0; neutral value clearly positive — raw value was a sector bet |
| 2. Composite | Quality and momentum scores; composite of raw vs cleaned z-scores | Cleaned composite beats the raw one; factor scores nearly uncorrelated |
| 3. Quintiles | Monthly quintile returns, Q5 − Q1 spread, turnover and its cost | Monotonic quintiles; cost estimated from turnover |
| 4. Dry spells | Worst 24-month mean IC per factor | Single factors have negative spells; the composite's are shallower |

The panel is fictional (`cfmat.data.factor_panel`), with small, drifting premia and 2% distorted
earnings yields. Real premia are smaller, time-varying and crowded.

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quiz 7 | quizzes (10%) | Fri W14 | Ratios and factor concepts |
| Lab 07a | labs (20%) | Sun W14 | Runs; results explained |
| Assignment: a real factor screen | assignments (15%) | Sun W16 | Build value, quality and momentum scores for at least 100 Indian stocks over at least 5 years with point-in-time data; report ICs, quintile spreads and turnover; discuss survivorship. Rubric: data handling 30, method 30, results 20, limitations 20 |

## Common mistakes

- Z-scoring across all dates at once → look-ahead; every step is per date.
- Winsorising at 1% when 2% of the data is bad → cut-off must exceed the bad-data share.
- Using today's constituents for a 10-year test → survivorship bias.
- Ignoring turnover → a 36% monthly turnover factor costs several percent a year.

## Readings

- Fama and French (1993), "Common risk factors in the returns on stocks and bonds".
- Jegadeesh and Titman (1993), "Returns to Buying Winners and Selling Losers".
- Asness, Frazzini and Pedersen (2019), "Quality minus junk".
- Grinold and Kahn, *Active Portfolio Management*, ch. on the information coefficient.
- Damodaran, *Investment Valuation* (ratio chapters, reference).

## Instructor notes

- Owner: quant research lead, with a buy-side guest for L1 (fundamentals).
- M07 is one week: keep accounting to what factor construction needs; point to optional readings for deeper valuation.
- The assignment needs real fundamentals; confirm the education data licence covers them before the cohort starts.
