# M10 · Algorithmic Trading Strategies

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T3 · Strategy Research |
| Weeks | 20–22 |
| Hours | 36 guided |
| Labs | [10a](lab_10a_trading_strategies.py) — Trend, momentum, mean reversion, cross-sectional momentum, pairs<br>[10b](lab_10b_momentum_volatility.py) — Volatility estimators vs truth, cones and regimes, momentum scores, TSMOM with a vol target |
| Library | `cfmat.strategies.signals`, `cfmat.backtesting.vectorized`, `cfmat.analytics.momentum`, `cfmat.analytics.volatility`, `cfmat.viz` |
| Prerequisites | [M04](../m04-statistics-time-series/README.md), [M06](../m06-technical-analysis-patterns/README.md) |
| Committed topics | – |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Strategies are not recipes; each exploits a specific source of return — a risk premium, a
behavioural bias, a structural flow or paid liquidity provision — and each dies in specific
conditions. This module implements the main families on data where their effect is planted, so
learners see each one work, then see it fail in the wrong regime and after costs.

## Learning outcomes

By the end of the module you can:

1. Classify strategies by source of return and name the conditions each needs to work.
2. Implement moving-average, breakout and time-series momentum strategies, with volatility scaling.
3. Estimate volatility from OHLC bars (close-to-close, Parkinson, Garman–Klass, Rogers–Satchell, Yang–Zhang, EWMA), grade estimators against a known truth, and read volatility cones and regimes without look-ahead.
4. Implement short-term mean-reversion (RSI, Bollinger) strategies and explain their regime dependence.
5. Score momentum several ways (12-1, risk-adjusted, regression, information discreteness), implement cross-sectional momentum on a universe and control turnover.
6. Trade pairs with a formation period, an out-of-sample hedge ratio, entry/exit bands and a stop for breakdowns.
7. Describe event-driven, seasonality, carry and options-based strategies and when each is worth researching.
8. Combine strategies and reason about correlation, capacity and decay.

## Before you start

- M04 (cointegration) and M06 (event studies) complete.
- Read Chan, *Algorithmic Trading*, ch. 1.

## Weekly plan

### Week 20 — Trend following and time-series momentum

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M09 · 15–60 where returns come from: premia, biases, flows, liquidity; alpha vs beta; strategy decay · 60–70 break · 70–125 trend following: moving-average crossovers, breakouts, time-series momentum; volatility scaling · 125–170 why trend works in some markets and years and not others · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–70 workshop: `strategies.sma_crossover` and `time_series_momentum` on trending vs mean-reverting synthetic markets · 70–80 break · 80–140 position sizing by volatility; the no-look-ahead rule (positions shift one bar) · 140–170 guest: a CTA practitioner on trend in Indian futures · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–90 Lab 10a §1–2 · 90–120 blockers |
| OH · Wed · 60 min | Strategy design Q&A |
| C2 · Thu · 120 min | 0–50 Lab 10b §1–2 and §5: volatility estimators against the truth, cone and regimes, TSMOM with a volatility target · 50–95 parameter sensitivity of the trend system (a heat map, not a single number) · 95–120 peer review |
| QP · Fri · 60 min | 0–20 quiz 10a · 20–50 critique a trend-following claim from social media · 50–60 preview |
| Self-study · ~6 h | Moskowitz, Ooi and Pedersen (2012); Clenow ch. 1–4 |

### Week 21 — Mean reversion and cross-sectional momentum

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 short-term reversal; Bollinger and RSI systems; stop-loss design for mean reversion · 60–70 break · 70–120 cross-sectional momentum: ranking, holding periods, skip-month, turnover · 120–170 regime dependence: when reversion becomes a falling knife · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–70 workshop: `bollinger_mean_reversion`, `rsi_reversal`, `cross_sectional_momentum` · 70–80 break · 80–140 turnover and costs: why short-term reversal lives or dies on execution · 140–170 seasonality and calendar effects (preview of M23 segments) · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 10a §3 · 100–120 review |
| OH · Wed · 60 min | Mini-project clinic |
| C2 · Thu · 120 min | 0–50 Lab 10b §3–4 and §6: four momentum scores, top-6 backtest, momentum by volatility regime · 50–95 exercise: add a volatility filter to mean reversion · 95–120 peer review |
| QP · Fri · 60 min | 0–20 quiz 10b · 20–50 mini-project proposal review · 50–60 preview |
| Self-study · ~6 h | Jegadeesh and Titman (1993); Chan ch. 2–4 |

### Week 22 — Statistical arbitrage: pairs and cointegration

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 pairs trading: distance vs cointegration methods; formation and trading periods · 60–70 break · 70–120 hedge ratios: formation-period OLS vs rolling vs Kalman (M23); why a noisy rolling beta loses money · 120–170 breakdown risk, stops, and basket stat-arb · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 other families: event-driven (results, index rebalancing), carry, volatility premium, market making (concepts) · 60–70 break · 70–130 combining strategies: correlation, risk budgets, capacity · 130–170 guest: prop-desk stat-arb practitioner · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 10a §4 pairs · 100–120 review |
| OH · Wed · 60 min | Mini-project clinic |
| C2 · Thu · 120 min | 0–60 pairs with a cointegration screen in a sector (count false pairs by chance) · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 10c · 20–50 peer review of mini-project drafts · 50–60 preview of M11 |
| Self-study · ~6 h | Gatev, Goetzmann and Rouwenhorst (2006); Avellaneda and Lee (2010) |

## Labs

**Lab 10a — algorithmic trading strategies** (`lab_10a_trading_strategies.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1–2. Trend and reversion on two regimes | Run trend and mean-reversion systems on a trending and a mean-reverting market, after costs | Each family wins on its own regime and loses on the other |
| 3. Cross-sectional momentum | Rank a 20-stock universe, long winners | Weights sum to one; turnover reported |
| 4. Pairs | Formation-period hedge ratio, z-score bands | Positive after costs on the cointegrated pair; no trades in formation |

**Lab 10b — momentum and volatility** (`lab_10b_momentum_volatility.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Estimators against the truth | Grade five estimators on bars with a known, shifting volatility and overnight gaps | You can say which are biased (range estimators miss gaps) and which are noisy (close-to-close) |
| 2. Cone, percentile, regime | Read where today's volatility sits on a GARCH market | Labels use only past data; you can explain why a lasting shift becomes "normal" |
| 3. Four momentum scores | 12-1, risk-adjusted, regression, discreteness on 30 stocks | You explain where the scores agree and where they differ |
| 4. Cross-sectional backtest | Monthly top-6 by each score, after costs, against equal weight | Trades from the day after; the small edge explained by signal-to-noise |
| 5. Volatility targeting | TSMOM sign-only vs vol-targeted on a clustered-volatility market | The targeted version's risk band is narrower; no claim of extra return |
| 6. Momentum by regime | Split returns by the prior day's market regime and test the difference | A Welch test, not three separate t-statistics, decides |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 10a–10c | quizzes (10%) | Fri W20–W22 | Concepts and short code reading |
| Lab 10a | labs (20%) | Sun W22 | Runs; results explained by regime |
| Lab 10b | labs (20%) | Sun W22 | Runs; estimator grades and the regime test interpreted correctly |
| Mini-project 1: two families, one universe | assignments (15%) | Sun W24 | Implement and compare two strategies from different families on the same universe: gross and net performance, turnover, correlation, and the combination. Evaluated with M11 methods. Rubric: implementation 30, evaluation 30, combination 20, write-up 20 |

## Common mistakes

- Estimating a pairs hedge ratio over the trading period → look-ahead; the lab uses the formation period.
- Using same-bar signals and returns → the backtester shifts positions one bar; never undo it.
- Picking parameters from the best cell of a heat map → M11 walk-forward.
- Ignoring turnover in reversal strategies → costs applied throughout at 5 bp per unit turnover.

## Readings

- Ernest P. Chan, *Algorithmic Trading: Winning Strategies and Their Rationale*.
- Andreas Clenow, *Following the Trend*.
- Moskowitz, Ooi and Pedersen (2012), "Time Series Momentum".
- Gatev, Goetzmann and Rouwenhorst (2006), "Pairs Trading".
- Avellaneda and Lee (2010), "Statistical arbitrage in the US equities market".

## Instructor notes

- Owner: quant research lead.
- Synthetic markets have planted effects; say so every time, and ask learners to predict which family will win before running.
- Mini-project 1 is evaluated with M11 tools, so its deadline sits after Week 24.
