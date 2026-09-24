# Module 08 — Backtesting and Research Methodology

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 2 · Trading and Strategy Design | 18–19 | 20 | [`lab08_backtesting_research.py`](../../labs/lab08_backtesting_research.py) |

## Learning outcomes

1. Build vectorised and event-driven backtests and explain when to use each.
2. Identify and prevent look-ahead bias, survivorship bias, data snooping and unrealistic fills.
3. Model Indian transaction costs, slippage and market impact.
4. Report the right metrics (CAGR, volatility, Sharpe, Sortino, drawdown, Calmar, turnover, hit rate, profit factor).
5. Use walk-forward optimisation and hold-out periods.
6. Quantify multiple-testing risk with the Probabilistic and Deflated Sharpe Ratios.
7. Keep a research log and pre-register hypotheses.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Backtest design (Sat, W18) | Vectorised vs event-driven; bar timing and fills; the `cfmat` engines; corporate actions and data alignment |
| L2 | Costs and metrics (Sun, W18) | Brokerage, STT, exchange fees, SEBI fee, stamp duty, GST (`IndianCostModel`); slippage and impact; performance and risk metrics; benchmark choice |
| L3 | Overfitting (Sat, W19) | In-sample vs out-of-sample; parameter stability; walk-forward; combinatorial purged cross-validation (intro); backtest overfitting probability |
| L4 | Research honesty (Sun, W19) | Probabilistic and Deflated Sharpe Ratios; counting trials; pre-registration; research logs; case studies of backtests that failed live |
| C1–C4 | Clinics | Event-driven engine; costs; walk-forward; Lab 8 |

## Assignment

Take your Mini-project 1 strategy and write a "backtest audit": list every assumption, test the effect of doubling costs, move the fill from close to next open, run walk-forward, and report the Deflated Sharpe Ratio with an honest count of the trials you ran.

## Readings

- Marcos López de Prado, *Advances in Financial Machine Learning*: chapters 11–14.
- Bailey and López de Prado (2014), "The Deflated Sharpe Ratio".
- Bailey, Borwein, López de Prado and Zhu (2014), "Pseudo-Mathematics and Financial Charlatanism".
- Harvey, Liu and Zhu (2016), "…and the Cross-Section of Expected Returns".

## Assessment

Quiz 8; Lab 8; backtest audit; Mini-project 1.
