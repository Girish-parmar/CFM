# Academic Calendar (52 weeks)

The calendar is generated from [`course.yaml`](course.yaml). Week-level session plans with
minute-by-minute timings are in each [module guide](../curriculum/README.md). Ask the route
manager for any week: `python tools/route_manager.py week 25`.

## Weekly rhythm (generated)

<!-- BEGIN GENERATED: weekly-rhythm -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
| Code | Day | Time (IST) | Hours | Session |
|---|---|---|---|---|
| L1 | Saturday | 10:00–13:00 | 3 | Live lecture — concepts and cases |
| L2 | Sunday | 10:00–13:00 | 3 | Live workshop — worked examples and code |
| C1 | Tuesday | 19:30–21:30 | 2 | Lab clinic 1 — guided lab with TAs |
| OH | Wednesday | 20:00–21:00 | 1 | Office hours — faculty and TAs |
| C2 | Thursday | 19:30–21:30 | 2 | Lab clinic 2 — lab completion and code review |
| QP | Friday | 20:00–21:00 | 1 | Quiz and peer review |
|  |  |  | **12** | **Guided hours per module week** |
<!-- END GENERATED: weekly-rhythm -->

Plus about 6 hours of self-study a week (readings, lab completion, assignments). Recordings are
available within 24 hours; quizzes open on Friday evening and close the following Thursday.

### Standard session templates

| Session | Standard shape (minutes) |
|---|---|
| L1 lecture (180) | 0–15 retrieval quiz on last week · 15–60 concept block A · 60–70 break · 70–120 concept block B or case · 120–170 worked example or live code · 170–180 exit ticket |
| L2 workshop (180) | 0–10 recap · 10–60 guided build · 60–70 break · 70–130 hands-on workshop · 130–170 case, discussion or guest · 170–180 exit ticket |
| C1 clinic (120) | 0–10 environment check · 10–100 guided lab sections with TAs · 100–120 blockers and review |
| OH office hours (60) | Open questions, assignment and capstone clinics |
| C2 clinic (120) | 0–60 lab completion or exercise · 60–100 peer code review in pairs · 100–120 two solutions shown |
| QP quiz and peer review (60) | 0–20 quiz · 20–50 peer review or drill · 50–60 preview of next week |

Module guides adapt these shapes; where a guide differs, the guide wins.

## The 52 weeks (generated)

<!-- BEGIN GENERATED: calendar -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
| Week | Term | Module / block | Theme | Due / notes |
|---|---|---|---|---|
| -3 | T0 | M00 Pre-work | Python basics, Jupyter and VS Code | self-paced |
| -2 | T0 | M00 Pre-work | pandas first steps and Excel-to-Python | self-paced |
| -1 | T0 | M00 Pre-work | Algebra, probability and statistics refresher | self-paced |
| 0 | T0 | M00 Pre-work | How stock markets work; entry assessment | self-paced |
| 1 | T1 | [M01](../curriculum/m01-financial-markets/README.md) Financial Markets, Instruments and Regulation | Market structure, participants and instruments |  |
| 2 | T1 | [M01](../curriculum/m01-financial-markets/README.md) Financial Markets, Instruments and Regulation | Orders, clearing and settlement, costs and regulation | lab 01a |
| 3 | T1 | [M02](../curriculum/m02-macroeconomics/README.md) Macroeconomics for Traders | Growth, inflation and the RBI — how macro moves Indian markets |  |
| 4 | T1 | [M02](../curriculum/m02-macroeconomics/README.md) Macroeconomics for Traders | Rates, the yield curve, the rupee and macro event trading | lab 02a |
| 5 | T1 | [M03](../curriculum/m03-python-for-finance/README.md) Python for Financial Analysis | Python, NumPy and pandas for market data |  |
| 6 | T1 | [M03](../curriculum/m03-python-for-finance/README.md) Python for Financial Analysis | Clean code — functions, tests, Git and packaging | lab 03a |
| 7 | T1 | [M04](../curriculum/m04-statistics-time-series/README.md) Statistics and Time Series for Finance | Distributions, fat tails, estimation, hypothesis tests and multiple testing |  |
| 8 | T1 | [M04](../curriculum/m04-statistics-time-series/README.md) Statistics and Time Series for Finance | Regression, autocorrelation, stationarity, cointegration and the bootstrap | lab 04a |
| 9 | T1 | [M05](../curriculum/m05-data-engineering-databases/README.md) Databases and Market Data Engineering | Relational design, SQL, window functions and time-series storage |  |
| 10 | T1 | [M05](../curriculum/m05-data-engineering-databases/README.md) Databases and Market Data Engineering | Pipelines, data quality, corporate actions and survivorship-free universes | lab 05a |
| 11 | T1 | **R1** | Review, Term 1 exam and Bootcamp 1 | exam + in-person bootcamp |
| 12 | T2 | [M06](../curriculum/m06-technical-analysis-patterns/README.md) Technical Indicators, Candlestick and Chart Patterns | Indicators from first principles — and why most are redundant |  |
| 13 | T2 | [M06](../curriculum/m06-technical-analysis-patterns/README.md) Technical Indicators, Candlestick and Chart Patterns | Candlestick and chart patterns as testable hypotheses | lab 06a |
| 14 | T2 | [M07](../curriculum/m07-fundamental-factor-investing/README.md) Fundamental Analysis and Factor Investing | Statements, ratios and cross-sectional factor scores | lab 07a |
| 15 | T2 | [M08](../curriculum/m08-derivatives-pricing-greeks/README.md) Derivatives — Futures, Options Pricing and the Greeks | Forwards and futures, cost of carry, option payoffs and parity |  |
| 16 | T2 | [M08](../curriculum/m08-derivatives-pricing-greeks/README.md) Derivatives — Futures, Options Pricing and the Greeks | Binomial trees, Black–Scholes–Merton and the first-order Greeks |  |
| 17 | T2 | [M08](../curriculum/m08-derivatives-pricing-greeks/README.md) Derivatives — Futures, Options Pricing and the Greeks | Implied volatility, the smile and delta hedging | lab 08a |
| 18 | T2 | [M09](../curriculum/m09-fno-strategies-advanced-greeks/README.md) F&O Strategies and Second-Order Greeks | Second-order Greeks (vanna, volga, charm, speed) and Greek P&L attribution |  |
| 19 | T2 | [M09](../curriculum/m09-fno-strategies-advanced-greeks/README.md) F&O Strategies and Second-Order Greeks | Futures curves, carry and option structures by market view | lab 09a, lab 09b |
| 20 | T3 | [M10](../curriculum/m10-trading-strategies/README.md) Algorithmic Trading Strategies | Trend following and time-series momentum |  |
| 21 | T3 | [M10](../curriculum/m10-trading-strategies/README.md) Algorithmic Trading Strategies | Mean reversion and cross-sectional momentum |  |
| 22 | T3 | [M10](../curriculum/m10-trading-strategies/README.md) Algorithmic Trading Strategies | Statistical arbitrage — pairs and cointegration | lab 10a |
| 23 | T3 | [M11](../curriculum/m11-backtesting-research/README.md) Backtesting and Research Methodology | Backtest engines, Indian costs and the classic biases |  |
| 24 | T3 | [M11](../curriculum/m11-backtesting-research/README.md) Backtesting and Research Methodology | Walk-forward testing, the deflated Sharpe ratio and research hygiene | lab 11a |
| 25 | T3 | [M12](../curriculum/m12-strategy-studio/README.md) Strategy Studio: Screeners, Strategy Creator and Parallel Research | Screening and instrument selection; the rule language |  |
| 26 | T3 | [M12](../curriculum/m12-strategy-studio/README.md) Strategy Studio: Screeners, Strategy Creator and Parallel Research | Strategy Creator, parallel optimisation and F&O signals | lab 12a, lab 12b, lab 12c |
| 27 | T3 | **R2** | Review, Term exam 2 and Bootcamp 2 | exam + in-person bootcamp |
| 28 | T4 | [M13](../curriculum/m13-risk-position-sizing/README.md) Risk Management and Position Sizing | VaR, expected shortfall, VaR backtesting and stress tests |  |
| 29 | T4 | [M13](../curriculum/m13-risk-position-sizing/README.md) Risk Management and Position Sizing | Position sizing, Kelly, volatility targeting and drawdown control | lab 13a |
| 30 | T4 | [M14](../curriculum/m14-portfolio-management/README.md) Portfolio Management and Strategy Allocation | Mean–variance, estimation error, shrinkage and risk parity |  |
| 31 | T4 | [M14](../curriculum/m14-portfolio-management/README.md) Portfolio Management and Strategy Allocation | Hierarchical risk parity and allocating across strategies | lab 14a |
| 32 | T4 | [M15](../curriculum/m15-microstructure-execution/README.md) Market Microstructure and Execution | Order books, liquidity, adverse selection and market impact |  |
| 33 | T4 | [M15](../curriculum/m15-microstructure-execution/README.md) Market Microstructure and Execution | Execution algorithms and transaction-cost analysis | lab 15a |
| 34 | T4 | [M16](../curriculum/m16-market-data-handling/README.md) Market Data Handling | Feeds, ticks to bars, instrument masters, data quality and storage | lab 16a |
| 35 | T4 | [M17](../curriculum/m17-trading-platform-compliance/README.md) Trading Platform, Broker APIs and Compliance | OMS/RMS architecture, broker APIs and paper trading |  |
| 36 | T4 | [M17](../curriculum/m17-trading-platform-compliance/README.md) Trading Platform, Broker APIs and Compliance | SEBI's retail-algo framework, audit trails and operational risk | lab 17a |
| 37 | T4 | [M18](../curriculum/m18-monitoring-automation/README.md) Monitoring and Automation with n8n | Live monitoring: health checks, drift, P&L attribution and kill switches |  |
| 38 | T4 | [M18](../curriculum/m18-monitoring-automation/README.md) Monitoring and Automation with n8n | Automation with n8n — alerts, digests and trade journals | lab 18a, lab 18b |
| 39 | T5 | [M19](../curriculum/m19-machine-learning/README.md) Machine Learning for Trading | Features, labels and leakage | CT +2 h |
| 40 | T5 | [M19](../curriculum/m19-machine-learning/README.md) Machine Learning for Trading | Purged cross-validation, walk-forward and model-driven trading | lab 19a, CT +2 h |
| 41 | T5 | [M20](../curriculum/m20-deep-learning/README.md) Deep Learning for Financial Time Series | Neural networks for sequences — when they earn their complexity | lab 20a, CT +2 h |
| 42 | T5 | [M21](../curriculum/m21-reinforcement-learning/README.md) Reinforcement Learning for Trading | Agents, rewards and costs — Q-learning taken apart | lab 21a, CT +2 h |
| 43 | T5 | [M22](../curriculum/m22-nlp-news-llm-rag/README.md) NLP, News Sentiment, LLMs and RAG | News, sentiment and event studies | CT +2 h |
| 44 | T5 | [M22](../curriculum/m22-nlp-news-llm-rag/README.md) NLP, News Sentiment, LLMs and RAG | LLMs and retrieval-augmented generation for research | lab 22a, lab 22b, CT +2 h |
| 45 | T5 | [M23](../curriculum/m23-advanced-strategies-hpo/README.md) Advanced Strategies and Hyperparameter Optimisation | Boosting, hyperparameter optimisation, meta-labelling and regimes | CT +2 h |
| 46 | T5 | [M23](../curriculum/m23-advanced-strategies-hpo/README.md) Advanced Strategies and Hyperparameter Optimisation | Segment optimisation, strategy ensembles and overfitting control | lab 23a, lab 23b, lab 23c, lab 23d, CT +2 h |
| 47 | T5 | **R3** | Review, Term exam 3 and Bootcamp 3 | exam + in-person bootcamp |
| 48 | T6 | [M24](../curriculum/m24-capstone-career/README.md) Capstone, Paper Trading, Ethics and Career | Final validation, deployment and paper-trading launch |  |
| 49 | T6 | [M24](../curriculum/m24-capstone-career/README.md) Capstone, Paper Trading, Ethics and Career | Paper trading, monitoring and incident drills |  |
| 50 | T6 | [M24](../curriculum/m24-capstone-career/README.md) Capstone, Paper Trading, Ethics and Career | Paper trading, reconciliation and risk review |  |
| 51 | T6 | [M24](../curriculum/m24-capstone-career/README.md) Capstone, Paper Trading, Ethics and Career | Report, peer review, mock jury and career studio |  |
| 52 | T6 | [M24](../curriculum/m24-capstone-career/README.md) Capstone, Paper Trading, Ethics and Career | Demo Day and graduation | lab 24a |
<!-- END GENERATED: calendar -->

## Review and bootcamp weeks

| Week | Block | Programme |
|---|---|---|
| 11 | R1 | Sat–Sun: Term 1 review and 4-hour Term 1 exam (M01–M05). Bootcamp 1 (3 days, in person): market microstructure simulation, data-engineering sprint, team case on a market episode |
| 27 | R2 | Review and exam 2 (M06–M12). Bootcamp 2: live trading-floor simulation with the Strategy Studio, RMS limits, incident drills and a risk committee role-play |
| 47 | R3 | Review and exam 3 (M13–M23). Bootcamp 3: capstone research reviews, go/no-go for paper trading, employer day |

Bootcamps run Thursday to Saturday; stay (3 nights, twin sharing) and meals are included in the
fee; travel is not. A learner who misses a bootcamp for a documented emergency attends the next
cohort's bootcamp at no charge.

## Mentoring schedule

Twenty-four 1-hour 1:1 sessions, roughly fortnightly: Weeks 2, 4, 6, 8, 10, 13, 15, 17, 19, 21,
23, 25, 29, 31, 33, 35, 37, 39, 41, 43, 45, 48, 49 and 50. Mentors are matched to the learner's
route in Week 1 and may be changed once.

## Capstone track

| Week | Milestone |
|---|---|
| 38 | Topic approved |
| 39–46 | Capstone track: 2 h a week (proposal clinics, pre-registration review, midpoint review) |
| 40 | Pre-registration committed to Git |
| 44 | Midpoint review |
| 47–48 | Research review and go/no-go (Bootcamp 3 and Week 48) |
| 48–51 | Four weeks of paper trading |
| 51 | Final report and repository |
| 52 | Demo Day |

## Holidays and exchange closures

Sessions that fall on a national holiday move to the nearest weekday evening, announced two weeks
ahead. Diwali week is a reading week; the calendar shifts by one week for that cohort and the
route manager's week numbers stay the same (week numbers are teaching weeks, not calendar weeks).
