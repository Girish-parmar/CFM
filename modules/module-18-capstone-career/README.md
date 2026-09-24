# Module 18 — Capstone, Paper Trading, Ethics and Career

| Term | Weeks | Hours |
|---|---|---|
| 5 · Strategy Studio, Capstone and Career | 39–45 | 70 (studio sessions, reviews, workshops, Demo Day) |

## Learning outcomes

1. Pre-register a research question and carry it through data, testing, risk and live paper trading.
2. Run a strategy for four weeks under risk limits, keep a journal, and reconcile live results with the backtest.
3. Recognise the behavioural traps in trading (overconfidence, loss aversion, revenge trading) and use process controls against them.
4. Apply professional ethics and market-abuse rules.
5. Present work to an industry jury and to employers.

## Components

| Week | Studio (Sat) | Workshop (Sun) | Clinics |
|---|---|---|---|
| 39 | Research design and pre-registration | Trading psychology and discipline | Mentor 1:1 |
| 40 | Data and engineering reviews | Ethics: insider trading, front-running, spoofing, confidentiality | Code review |
| 41 | Research reviews; paper trading starts | Career studio: CV, LinkedIn, GitHub portfolio | Deployment |
| 42 | Paper-trading stand-up | Career studio: interviews and quant puzzles | Incident drills |
| 43 | Paper-trading stand-up | Employer connect | Mock interviews |
| 44 | Reconciliation and wrap-up | Peer review of reports | Rehearsal |
| 45 | **Demo Day** | Graduation and hiring showcase | – |

Project options, timeline and rules: [../../docs/05-capstone-projects.md](../../docs/05-capstone-projects.md). Rubric: [../../docs/04-assessment-and-certification.md](../../docs/04-assessment-and-certification.md).

## Capstone repository template

```
capstone/
├── README.md              # question, how to reproduce, results summary
├── PREREGISTRATION.md     # committed in Week 39, before any testing
├── data/                  # scripts only; raw licensed data is not committed
├── src/                   # features, signals, strategy (Strategy Creator specs), risk
├── tests/                 # pytest: no look-ahead, risk limits, cost model
├── notebooks/             # exploration (not the source of truth)
├── paper_trading/         # config, RMS limits, daily journal exports
└── report/                # final report (PDF) and slides
```

## Readings

- Mark Douglas, *Trading in the Zone*.
- Daniel Kahneman, *Thinking, Fast and Slow*: chapters on overconfidence and loss aversion.
- SEBI (Prohibition of Insider Trading) Regulations, 2015 and SEBI (PFUTP) Regulations, 2003: summaries provided in class.
- Gregory Zuckerman, *The Man Who Solved the Market* (culture of systematic research).

## Assessment

Capstone (30% of the final grade). See the rubric.
