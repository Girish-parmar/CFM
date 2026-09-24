# Module 05 — Technical, Fundamental and Quantamental Analysis

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 2 · Trading and Strategy Design | 10–11 | 20 | [`lab05_technical_fundamental.py`](../../labs/lab05_technical_fundamental.py) |

## Learning outcomes

1. Compute common indicators from first principles and explain what each measures.
2. Turn a chart rule into a testable hypothesis and evaluate it with an event study and standard errors.
3. Read financial statements and compute valuation, profitability, leverage and cash-flow ratios.
4. Explain the main equity factors (value, quality, momentum, low volatility, size) and the evidence for them.
5. Build a multi-factor score with standardisation, winsorisation and sector neutralisation.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Indicators (Sat, W10) | Moving averages, RSI, MACD, Bollinger bands, ATR, volume and breadth indicators; what they measure and why many are redundant |
| L2 | Testing TA claims (Sun, W10) | Event-study design; forward returns; overlapping windows and standard errors; multiple testing; case: evaluating popular chart patterns |
| C1 | Clinic (Tue, W10) | Build an indicator library in `cfmat.indicators` style, with tests |
| C2 | Clinic (Thu, W10) | Event studies |
| L3 | Fundamentals (Sat, W11) | Income statement, balance sheet, cash flow; ratios; accounting red flags; Indian disclosure sources (annual reports, exchange filings, shareholding patterns) |
| L4 | Quantamental (Sun, W11) | Factor definitions and evidence; z-scores, winsorisation, sector neutralisation; composite scores; turnover and capacity |
| C3 | Clinic (Tue, W11) | Lab 5 |
| C4 | Clinic (Thu, W11) | Factor screen on real data |

## Assignment

Pick one technical rule popular with retail traders. Pre-register its definition, test it with an event study on at least 30 stocks and 5 years of data, correct for multiple testing, and write a one-page verdict.

## Readings

- David Aronson, *Evidence-Based Technical Analysis*: chapters 1–6.
- Fama and French (1993), "Common risk factors in the returns on stocks and bonds".
- Jegadeesh and Titman (1993), "Returns to Buying Winners and Selling Losers".
- Asness, Frazzini and Pedersen (2019), "Quality minus junk".

## Assessment

Quiz 5; Lab 5; event-study assignment.
