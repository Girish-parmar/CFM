# Module 07 — Algorithmic Trading Strategies

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 2 · Trading and Strategy Design | 15–17 | 30 | [`lab07_trading_strategies.py`](../../labs/lab07_trading_strategies.py) |

## Learning outcomes

1. Classify strategies by their source of return (risk premium, behavioural effect, structural or liquidity provision) and name the conditions each needs.
2. Implement trend-following, time-series momentum, mean-reversion, cross-sectional momentum and pairs strategies.
3. Test pairs for cointegration and trade them with formation and trading periods.
4. Describe event-driven, seasonality, carry and options-based strategies.
5. Combine strategies and estimate capacity after costs.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Strategy taxonomy (Sat, W15) | Where returns come from; alpha vs beta; strategy life cycle and decay; why most retail strategies fail after costs |
| L2 | Trend and momentum (Sun, W15) | Moving-average systems, breakouts, time-series momentum; cross-sectional momentum; volatility scaling |
| L3 | Mean reversion (Sat, W16) | Short-term reversal, Bollinger and RSI systems, regime dependence, stop-loss design |
| L4 | Statistical arbitrage (Sun, W16) | Pairs trading (distance and cointegration methods), half-life, hedge ratios, basket stat-arb, breakdown risk |
| L5 | Other families (Sat, W17) | Event-driven (results, index rebalancing, corporate actions), seasonality and calendar effects, carry, options strategies (volatility premium, covered calls), market-making concepts |
| L6 | Portfolio of strategies (Sun, W17) | Correlation between strategies, risk budgeting, capacity and turnover; guest session from a prop desk |
| C1–C6 | Clinics | Trend systems; momentum ranking; pairs pipeline; Lab 7; strategy combination exercise |

## Assignment (Mini-project 1, due Week 19)

Design, implement and compare two strategies from different families on the same universe. Report gross and net performance, turnover, correlation between the two, and the result of combining them. Use the Module 8 methodology for the final evaluation.

## Readings

- Ernest P. Chan, *Algorithmic Trading: Winning Strategies and Their Rationale*.
- Andreas Clenow, *Following the Trend*.
- Moskowitz, Ooi and Pedersen (2012), "Time Series Momentum".
- Gatev, Goetzmann and Rouwenhorst (2006), "Pairs Trading: Performance of a Relative-Value Arbitrage Rule".
- Avellaneda and Lee (2010), "Statistical arbitrage in the US equities market".

## Assessment

Quiz 7; Lab 7; Mini-project 1.
