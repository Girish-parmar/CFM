# M11 · Backtesting and Research Methodology

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T3 · Strategy Research |
| Weeks | 23–24 |
| Hours | 24 guided |
| Labs | [11a](lab_11a_backtesting_costs_walk_forward.py) — Indian costs, grid search vs walk-forward, deflated Sharpe, event engine |
| Library | `cfmat.backtesting.vectorized`, `cfmat.backtesting.event_driven`, `cfmat.microstructure.costs`, `cfmat.analytics.metrics` |
| Prerequisites | [M10](../m10-trading-strategies/README.md) |
| Committed topics | Statistics in finance |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

A backtest is a claim about the future made with data from the past. It fails when it uses
information it could not have had, charges less than the market does, or is the best of many
tries presented as the only one. This module makes learners good at catching all three in their
own work. Every later module, and the capstone gate, uses these methods.

## Learning outcomes

By the end of the module you can:

1. Build vectorised and event-driven backtests and explain when to use each.
2. Identify and prevent look-ahead bias, survivorship bias, data snooping and unrealistic fills.
3. Model Indian transaction costs, slippage and market impact, and show a strategy's sensitivity to them.
4. Report the right metrics (CAGR, volatility, Sharpe, Sortino, drawdown, Calmar, turnover, hit rate, profit factor) against a sensible benchmark.
5. Run walk-forward optimisation and keep a true hold-out period.
6. Quantify multiple-testing risk with the probabilistic and deflated Sharpe ratios, counting trials honestly.
7. Keep a research log and pre-register hypotheses.

## Before you start

- M10 complete; Mini-project 1 strategies implemented.
- Read Bailey and López de Prado (2014), "The Deflated Sharpe Ratio", sections 1–3.

## Weekly plan

### Week 23 — Backtest engines, Indian costs and the classic biases

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M10 · 15–60 vectorised vs event-driven: bar timing, fills at next open vs close, the one-bar shift · 60–70 break · 70–120 biases: look-ahead, survivorship, data snooping, corporate actions, stale prices · 120–170 live: break a backtest on purpose five ways and catch each · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 Indian costs with `IndianCostModel`: brokerage, STT, exchange fees, SEBI fee, stamp duty, GST, DP charge; slippage and impact · 60–70 break · 70–130 metrics and benchmarks: what each metric hides · 130–170 the event-driven engine (`backtesting.event_driven`) with a paper broker and RMS · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–90 Lab 11a §1 costs; §4 event engine vs vectorised · 90–120 blockers |
| OH · Wed · 60 min | Mini-project 1 clinic |
| C2 · Thu · 120 min | 0–60 cost sensitivity: double costs, move fills, add slippage · 60–100 peer review · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 11a · 20–50 "spot the bias" code cards · 50–60 preview |
| Self-study · ~6 h | López de Prado ch. 11–12; Mini-project 1 |

### Week 24 — Walk-forward testing, the deflated Sharpe ratio and research hygiene

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 in-sample vs out-of-sample; parameter stability; walk-forward optimisation · 60–70 break · 70–125 the probabilistic and deflated Sharpe ratios; counting trials; the variance of trial Sharpe ratios · 125–170 probability of backtest overfitting (CSCV) — intuition; full use in M23 · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 pre-registration and research logs: templates and Git history as evidence · 60–70 break · 70–130 workshop: grid search vs walk-forward on the same strategy (Lab 11a §2–3) · 130–170 case studies: backtests that failed live and why · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 11a §2–§3 · 100–120 review |
| OH · Wed · 60 min | Assignment clinic |
| C2 · Thu · 120 min | 0–60 backtest audit of Mini-project 1 · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 11b · 20–50 peer review of audits · 50–60 preview of M12 |
| Self-study · ~6 h | Bailey et al. (2014); Harvey, Liu and Zhu (2016); finish the audit |

## Labs

**Lab 11a — backtesting and research methodology** (`lab_11a_backtesting_costs_walk_forward.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. What a trade costs | Charges by segment; round-trip basis points | Options STT and exchange fees dominate small premiums |
| 2. In-sample vs walk-forward | Grid search vs walk-forward on one strategy | Walk-forward Sharpe clearly below the best in-sample Sharpe |
| 3. Deflated Sharpe | DSR for the grid winner with the true trial count | DSR well below the naive confidence |
| 4. Event engine | Same strategy in event-driven and vectorised form | Results agree within costs and fill differences |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 11a, 11b | quizzes (10%) | Fri W23, W24 | Biases, metrics, DSR |
| Lab 11a | labs (20%) | Sun W24 | Runs; interpretation |
| Assignment: backtest audit | assignments (15%) | Sun W25 | For Mini-project 1: list every assumption, double costs, move fills to next open, run walk-forward, report DSR with an honest trial count. Rubric: completeness 35, correctness 35, honesty 30 |

## Common mistakes

- Optimising on the whole sample and calling the result "out of sample" → walk-forward in §2.
- Reporting DSR with a trial count of 1 → count every configuration you ran, including discarded ones.
- Believing the event-driven engine is always "more realistic" → it is only as realistic as its fill model.
- Forgetting that costs depend on price and lot size → use `IndianCostModel.charges`, not a flat bp guess, for options.

## Readings

- Marcos López de Prado, *Advances in Financial Machine Learning*, ch. 11–14.
- Bailey and López de Prado (2014), "The Deflated Sharpe Ratio".
- Bailey, Borwein, López de Prado and Zhu (2014), "Pseudo-Mathematics and Financial Charlatanism".
- Harvey, Liu and Zhu (2016), "… and the Cross-Section of Expected Returns".

## Instructor notes

- Owner: quant research lead.
- The audit assignment is the template for the capstone's research review — keep its rubric aligned.
- Make every learner say their trial count out loud in C2 W24. It changes behaviour.
