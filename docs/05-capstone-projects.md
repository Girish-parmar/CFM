# Capstone Projects

The capstone (Module 17, Weeks 37–43) is where learners show they can do the whole job: form a hypothesis, test it honestly, control its risk, run it live on paper, and defend it to practitioners. Work is individual; pairs are allowed for the two infrastructure-heavy projects (7 and 10) with a larger scope.

## Timeline

| Week | Milestone | Deliverable |
|---|---|---|
| 36 | Topic approved by mentor | One-page proposal |
| 37 | **Pre-registration** | Hypothesis, economic rationale, data, universe, rules, parameters to search, the full list of trials, success criteria (committed to Git before any testing) |
| 38 | Data and engineering review | Reproducible pipeline, tests passing, data-quality report |
| 39 | Research review | Walk-forward backtest with costs, Deflated Sharpe Ratio, stress tests, risk limits |
| 39–42 | **Live paper trading (4 weeks)** | Strategy running on a static-IP server through `PaperBroker` or a broker sandbox, with RMS limits, kill switch and daily journal |
| 42 | Draft report | Peer review by two classmates |
| 43 | **Demo Day** | 15-minute presentation and 10-minute viva before an industry jury; final report and repository |

## Project options

1. **Index futures trend following with volatility targeting.** Time-series momentum on Nifty and Bank Nifty futures, including roll handling, volatility-scaled sizing and a drawdown stop.
2. **Pairs trading within Indian sectors.** Screen same-sector stocks for cointegration in a formation window, trade in the next window, handle breakdowns, and measure capacity after costs.
3. **Short-volatility options strategy with tail hedges.** Systematic index option selling (for example iron condors) with defined risk, margin modelling, event filters and stress testing against historical crashes.
4. **Multi-factor equity portfolio.** Value, quality, momentum and low-volatility factors on a survivorship-free universe, with sector neutrality, turnover control and HRP or risk-parity weighting.
5. **Machine-learning meta-labelling.** A primary rule-based signal plus a tuned gradient-boosted model (XGBoost or LightGBM, nested walk-forward) that decides whether to take each trade and how much to bet, with triple-barrier labels and purged cross-validation.
6. **News and filings sentiment signal.** Build a headline or announcement sentiment pipeline (lexicon, FinBERT or LLM), aggregate it by stock and day, and test it with an event study and a trading rule.
7. **RAG research assistant for Indian filings** (pairs allowed). A retrieval-augmented assistant over annual reports and exchange announcements, with an evaluation set, citation accuracy and hallucination checks, plus a trading or screening use case.
8. **Execution algorithm and TCA.** Implement VWAP/POV or Almgren–Chriss for a large order on intraday data, and measure implementation shortfall against benchmarks.
9. **Reinforcement-learning execution or allocation agent.** An RL agent for optimal execution or dynamic allocation, compared with a strong classical baseline.
10. **End-to-end automated trading system** (pairs allowed). Data ingestion, signal service, OMS/RMS, broker-sandbox adapter, n8n monitoring and alerts, logging and reconciliation, designed to meet SEBI's retail-algo requirements.

11. **Regime-aware multi-strategy portfolio.** Three or more strategy sleeves combined with HRP or risk parity, switched or scaled by a Markov regime filter and GARCH volatility forecasts, with PBO reported for every design choice.

12. **Seasonality and regime atlas.** Map a strategy's performance by weekday, month, turn of month, expiry week, volatility regime and pattern on 15+ years of Indian data; keep only segments that survive false-discovery control and both halves of the sample; then test per-segment parameters and a boosted model with segment features, walk-forward.

Learners may propose their own topic if the mentor approves it by Week 36.

## Minimum technical requirements

- Public or shared private Git repository with a README, environment file and a single command that reproduces the main results.
- Unit tests for data processing, signals and risk checks; `pytest` passing.
- No look-ahead: every feature and signal uses data available at decision time. Reviewers will check.
- Costs modelled with `cfmat.backtest.IndianCostModel` or an equivalent, with the assumptions stated.
- Out-of-sample evidence: walk-forward or a held-out period that was not touched during development.
- Deflated Sharpe Ratio reported using the number of trials from the pre-registration.
- Risk limits and a kill switch configured in paper trading.

## Rules and ethics

- **Paper trading only** inside the program. Learners who trade their own money do so outside the program, at their own risk, and must not present course strategies to others as investment advice.
- Use licensed or permitted data only, and respect the terms of any data source or API.
- When discussing named securities, use data at least three months old and never frame results as recommendations or forecasts (see [09-compliance-and-disclaimers.md](09-compliance-and-disclaimers.md)).
- Report negative results honestly. A well-run study that finds no edge can earn a Distinction; a profitable backtest built on leakage cannot pass.

## Jury

Three members: a practitioner from a trading desk or prop firm, a risk or compliance professional, and a faculty member. Each scores the rubric in [04-assessment-and-certification.md](04-assessment-and-certification.md) independently, and the median score is used.
