# Capstone

The capstone (M24, with a track running from Week 38) is where learners show they can do the
whole job: form a hypothesis, test it honestly, control its risk, run it on paper, and defend it
to practitioners. Work is individual; pairs are allowed for the two infrastructure-heavy projects
(7 and 10) with a larger scope.

## Timeline

| Week | Milestone | Deliverable |
|---|---|---|
| 38 | Topic approved | One-page proposal, usually built on the M12 pipeline assignment |
| 40 | **Pre-registration** | Hypothesis, economic rationale, data, universe, rules, parameters to search, the full list of trials, success criteria — committed to Git before any testing |
| 44 | Midpoint review | Reproducible data pipeline with quality checks; first walk-forward results |
| 47–48 | Research review and go/no-go | Walk-forward backtest with Indian costs, DSR with the pre-registered trial count, stress tests, RMS limits, monitoring |
| 48–51 | **Paper trading (4 weeks)** | Strategy on a static-IP server through `cfmat.trading.PaperBroker` or a broker sandbox, with RMS limits, kill switch, monitoring and a daily journal |
| 50 | Draft report | Peer review by two classmates |
| 51 | Final report and repository | One command reproduces the main results |
| 52 | **Demo Day** | 15-minute presentation and 10-minute viva before an industry jury |

## Project options

1. **Index futures trend following with volatility targeting.** Time-series momentum on Nifty and Bank Nifty futures with rollovers, volatility-scaled lots and a drawdown stop.
2. **Pairs trading within Indian sectors.** Cointegration screening in formation windows, Kalman or formation-period hedge ratios, breakdown handling and capacity after costs.
3. **Short-volatility options strategy with tail hedges.** Systematic index-option selling with defined risk, margin modelling, event filters, second-order Greek limits and stress tests against historical crashes.
4. **Multi-factor equity portfolio.** Value, quality, momentum and low volatility on a survivorship-free universe, sector-neutral, with turnover control and HRP or risk-parity weighting.
5. **Machine-learning meta-labelling.** A rule-based primary signal and a tuned gradient-boosted model (nested walk-forward) deciding whether and how much to trade.
6. **News and filings sentiment signal.** Timestamped news to signals (lexicon, FinBERT or LLM), aggregated by stock and day, tested with an event study and a trading rule.
7. **RAG research assistant for Indian filings** (pairs allowed). Retrieval over annual reports and announcements with an evaluation set, citation accuracy and prompt-injection tests, plus a screening use case.
8. **Execution algorithm and TCA.** VWAP/POV or Almgren–Chriss for a large order on intraday data, measured by implementation shortfall.
9. **Reinforcement-learning execution or allocation agent.** Compared with a strong classical baseline and reported as a seed distribution.
10. **End-to-end automated trading system** (pairs allowed). Market-data handler, signal service, OMS/RMS, broker-sandbox adapter, monitoring and n8n alerts, designed for SEBI's retail-algo requirements.
11. **Regime-aware multi-strategy portfolio.** Three or more sleeves with HRP or risk parity, scaled by filtered Markov regimes and GARCH forecasts, with PBO for every design choice.
12. **Seasonality and regime atlas.** A strategy mapped by weekday, month, turn of month, expiry week, volatility and trend regime and pattern on 15+ years of Indian data, keeping only segments that survive FDR and both halves of the sample.
13. **Screener-to-strategy system.** A regime screen, a Strategy Creator strategy per regime, and a futures or options implementation, validated walk-forward with an honest trial count.
14. **Macro event strategy.** Index or sector positioning around RBI policy, CPI or budget events, tested with event studies and permutation p-values, with lagged regime labels.

Learners may propose their own topic if the mentor approves it by Week 38. Each [learning route](10-learning-routes.md)
suggests matching options.

## Minimum technical requirements

- Repository with a README, an environment file and a single command that reproduces the main results (the layout in the [M24 guide](../curriculum/m24-capstone-career/README.md)).
- Unit tests for data processing, signals, costs and risk checks; `pytest` passes in CI.
- No look-ahead: every feature and signal uses data available at decision time; a truncation test proves it.
- Costs modelled with `cfmat.microstructure.costs.IndianCostModel` or an equivalent, with assumptions stated.
- Out-of-sample evidence: walk-forward or a held-out period untouched during development.
- Deflated Sharpe ratio reported with the trial count from the pre-registration; PBO or FDR where the design searches many options.
- RMS limits, a kill switch and monitoring configured for paper trading.

## Rules and ethics

- **Paper trading only** inside the programme. Learners who trade their own money do so outside the programme, at their own risk, and must not present course strategies to others as advice.
- Use licensed or permitted data only, and respect every source's terms.
- When discussing named securities, use data at least three months old and never frame results as recommendations ([compliance](09-compliance-and-risk-disclosures.md)).
- Report negative results honestly. A well-run study that finds no edge can earn a Distinction.

## Rubric

The capstone is 35% of the final grade. Criteria and marks are generated from the manifest in
[assessment](05-assessment-and-certification.md).

| Criterion | Distinction-level evidence |
|---|---|
| Hypothesis and pre-registration | Economic rationale written before testing; every trial declared; deviations disclosed |
| Data and engineering | Reproducible pipeline, point-in-time data, quality checks, tests pass, clean repository |
| Backtest rigour | Indian costs, walk-forward, no look-ahead, DSR with the true trial count, stress tests |
| Risk management | Sizing rules, drawdown limits, RMS limits and kill switch configured and tested |
| Paper-trading discipline | Four weeks run with journal, monitoring, reconciliation and an honest comparison with the backtest |
| Report and viva | Clear write-up of limits and failure modes; confident, candid answers |

## Jury

Three members: a practitioner from a trading desk or prop firm, a risk or compliance professional,
and a faculty member. Each scores independently; the median is used.
