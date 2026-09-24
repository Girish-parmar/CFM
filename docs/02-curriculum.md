# Curriculum

17 modules across five terms. Each module has a detailed lesson plan in [`modules/`](../modules) and, for technical modules, runnable labs in [`labs/`](../labs) built on the course library [`cfmat`](../cfmat).

| # | Module | Term | Weeks | Hours | Lab |
|---|---|---|---|---|---|
| 00 | Pre-work: Python, Excel for finance, maths refresher | – | −4–0 | 40 self-paced | entry assessment |
| 01 | [Financial Markets, Instruments and Regulation](../modules/module-01-financial-markets/README.md) | 1 | 1–2 | 20 | lab01 |
| 02 | [Python for Financial Analysis](../modules/module-02-python-for-finance/README.md) | 1 | 3–4 | 20 | lab02 |
| 03 | [Quantitative Methods and Financial Statistics](../modules/module-03-quant-methods/README.md) | 1 | 5–6 | 20 | lab03 |
| 04 | [Databases and Market Data Engineering](../modules/module-04-databases-data-engineering/README.md) | 1 | 7–8 | 20 | lab04 |
| – | Term 1 review, exam and **Bootcamp 1** (in person) | 1 | 9 | 10 + 24 | – |
| 05 | [Technical, Fundamental and Quantamental Analysis](../modules/module-05-technical-fundamental/README.md) | 2 | 10–11 | 20 | lab05 |
| 06 | [Derivatives, Options Pricing and Volatility](../modules/module-06-derivatives-options/README.md) | 2 | 12–14 | 30 | lab06 |
| 07 | [Algorithmic Trading Strategies](../modules/module-07-trading-strategies/README.md) | 2 | 15–17 | 30 | lab07 |
| 08 | [Backtesting and Research Methodology](../modules/module-08-backtesting/README.md) | 2 | 18–19 | 20 | lab08 |
| 09 | [Risk Management and Portfolio Construction](../modules/module-09-risk-portfolio/README.md) | 3 | 20–21 | 20 | lab09 |
| 10 | [Market Microstructure and Execution Algorithms](../modules/module-10-microstructure-execution/README.md) | 3 | 22–23 | 20 | lab10 |
| 11 | [Trading Infrastructure, Broker APIs and Compliance](../modules/module-11-infrastructure-compliance/README.md) | 3 | 24–25 | 20 | lab11 |
| – | Terms 2–3 review, exam and **Bootcamp 2** (in person) | 3 | 26 | 10 + 24 | – |
| 12 | [Machine Learning for Trading](../modules/module-12-machine-learning/README.md) | 4 | 27–28 | 20 | lab12 |
| 13 | [Deep Learning and Reinforcement Learning](../modules/module-13-deep-rl/README.md) | 4 | 29–30 | 20 | lab13 |
| 14 | [NLP, LLMs and RAG for Financial Research](../modules/module-14-nlp-llm-rag/README.md) | 4 | 31–32 | 20 | lab14 |
| 15 | [Automation with n8n and AI Agents](../modules/module-15-n8n-automation/README.md) | 4 | 33 | 10 | lab15 + `n8n/` |
| 16 | [Advanced Strategies and Hyperparameter Optimisation](../modules/module-16-advanced-strategies/README.md) | 4 | 34–35 | 20 | lab16, lab17, lab18 |
| 17 | [Capstone, Paper Trading, Ethics and Career](../modules/module-17-capstone-career/README.md) | 5 | 36–42 | 70 | capstone |
| – | 1:1 mentoring (6 sessions × 2 h) | all | 1–42 | 12 | – |
| | **Total guided hours** | | | **480** | |

## Module summaries

### Term 1: Market Foundations

**M01 Financial Markets, Instruments and Regulation (20 h).** Indian and global market structure; primary and secondary markets; NSE, BSE, MCX; SEBI, RBI and the exchanges' roles; equities, ETFs, bonds, currency, commodities and derivatives; order types, auctions and circuit limits; clearing, T+1 settlement and margins; corporate actions; transaction costs and taxes; how retail, institutional, FPI and prop participants behave.

**M02 Python for Financial Analysis (20 h).** Python fundamentals for finance, NumPy vectorisation, pandas time series (indexing, resampling, rolling windows, joins), data acquisition from files and APIs, plotting, functions and classes, virtual environments, Git and GitHub, and unit testing with pytest.

**M03 Quantitative Methods and Financial Statistics (20 h).** Returns and compounding; probability distributions and fat tails; estimation and hypothesis testing; linear regression and CAPM; autocorrelation, stationarity and ADF tests; ARMA/GARCH basics; cointegration; bootstrap and Monte Carlo; linear algebra for portfolios.

**M04 Databases and Market Data Engineering (20 h).** Relational design for instruments, bars, ticks and corporate actions; SQL including window functions and CTEs; indexing and query plans; PostgreSQL with TimescaleDB for tick data; Parquet and DuckDB for research; data pipelines, data-quality checks, survivorship-free universes and corporate-action adjustment; scheduling and idempotent loads.

### Term 2: Trading and Strategy Design

**M05 Technical, Fundamental and Quantamental Analysis (20 h).** Indicators from first principles (moving averages, RSI, MACD, Bollinger bands, ATR, volume); testing chart rules as hypotheses with event studies; financial statements and ratios; factor investing (value, quality, momentum, low volatility, size); building and neutralising multi-factor scores.

**M06 Derivatives, Options Pricing and Volatility (30 h).** Forwards and futures, cost of carry, basis and calendar spreads; option payoffs and put–call parity; binomial trees and Black–Scholes–Merton; the Greeks; implied volatility, smile and term structure; option strategies (spreads, straddles, strangles, iron condors, calendars); delta and gamma hedging; volatility trading; index options on NSE and weekly expiries; margins for option sellers.

**M07 Algorithmic Trading Strategies (30 h).** Strategy taxonomy; trend following and time-series momentum; mean reversion; cross-sectional momentum and factor rotation; pairs trading and statistical arbitrage; carry and seasonality; event-driven strategies; options strategies (covered calls, volatility premium, dispersion concepts); market making concepts; combining strategies and capacity.

**M08 Backtesting and Research Methodology (20 h).** Vectorised vs event-driven backtesting; look-ahead, survivorship and data-snooping biases; realistic Indian transaction costs (brokerage, STT, exchange fees, stamp duty, GST, slippage, impact); performance and risk metrics; in-sample vs out-of-sample; walk-forward optimisation; the Probabilistic and Deflated Sharpe Ratios; pre-registration and research logs.

### Term 3: Risk, Portfolio and Execution

**M09 Risk Management and Portfolio Construction (20 h).** VaR (historical, parametric, Monte Carlo), expected shortfall and VaR backtesting; stress and scenario testing; position sizing (fixed fractional, ATR, Kelly, volatility targeting); drawdown control; mean–variance optimisation and its estimation error; minimum variance, risk parity and Hierarchical Risk Parity; covariance shrinkage.

**M10 Market Microstructure and Execution Algorithms (20 h).** Limit order books and matching; bid–ask spread, depth and liquidity; adverse selection and informed trading (Kyle, Glosten–Milgrom intuition); market impact and the square-root law; TWAP, VWAP and POV; Almgren–Chriss optimal execution; implementation shortfall and transaction-cost analysis; co-location and latency (concepts); high-frequency trading and market making (Avellaneda–Stoikov intuition).

**M11 Trading Infrastructure, Broker APIs and Compliance (20 h).** Architecture of an automated trading system (data, signal, OMS, RMS, execution, monitoring); broker APIs (Kite Connect, Upstox, Angel SmartAPI, Interactive Brokers) and FIX concepts; order management and state machines; pre-trade risk checks and kill switches; logging, alerting and reconciliation; cloud deployment, static IP and secrets; SEBI's retail algo framework (algo IDs, broker as principal, empanelled algo providers, order-per-second thresholds, white-box vs black-box algos); research-analyst and investment-adviser rules; audit trails.

### Term 4: AI and Automation in Trading

**M12 Machine Learning for Trading (20 h).** Framing prediction problems; feature engineering from prices, volumes and fundamentals; labelling (fixed horizon, triple barrier, meta-labelling); purged and embargoed cross-validation; linear models, trees, random forests and gradient boosting; feature importance; from probabilities to positions and bet sizing; model monitoring and decay.

**M13 Deep Learning and Reinforcement Learning (20 h).** Neural networks and training; sequence models (RNN, LSTM, GRU, temporal CNN, Transformers) for time series; autoencoders for denoising and anomaly detection; overfitting controls; reinforcement learning (MDPs, Q-learning, DQN, policy gradients/PPO) for trading and execution; realistic environments and reward design; the limits of deep learning on noisy financial data.

**M14 NLP, LLMs and RAG for Financial Research (20 h).** Text as data; lexicon methods (Loughran–McDonald); TF-IDF classifiers; transformer models and FinBERT; news and earnings-call sentiment as signals; LLMs for extraction and summarisation; Retrieval-Augmented Generation over annual reports and exchange filings (chunking, embeddings, vector databases, reranking, grounded prompts with citations, evaluation); hallucination and prompt-injection risks; cost control.

**M15 Automation with n8n and AI Agents (10 h).** Workflow automation concepts; n8n nodes, triggers, credentials and expressions; scheduled data pipelines; signal alerts to Telegram or Slack; news digests; trade-journal webhooks; error handling and monitoring; AI agent nodes and tool calling; security of self-hosted automations.

**M16 Advanced Strategies and Hyperparameter Optimisation (20 h).** Gradient boosting (HistGradientBoosting, XGBoost, LightGBM) for trading; hyperparameter optimisation with random search and Bayesian optimisation (Optuna) scored by purged cross-validation; nested walk-forward tuning; Deflated Sharpe Ratio and Probability of Backtest Overfitting (CSCV); Markov regime switching with filtered probabilities; GARCH volatility forecasting and volatility-managed portfolios; Kalman-filter pairs trading; meta-labelling and bet sizing; portfolios of strategies with inverse-volatility, risk-parity and HRP allocation.

### Term 5: Capstone and Career

**M17 Capstone, Paper Trading, Ethics and Career (70 h).** Pre-registered strategy research; walk-forward backtest with costs and the Deflated Sharpe Ratio; four weeks of live paper trading with risk limits; trading psychology and discipline; professional ethics and market-abuse rules (insider trading, front-running, spoofing); career studio (CV, GitHub portfolio, interviews, quant puzzles); Demo Day with an industry jury.

## Teaching approach

- **Weekend live sessions** (Saturday and Sunday, 3 h each): concepts, worked examples and case studies.
- **Weekday lab clinics** (Tuesday and Thursday evenings, 2 h each): guided coding on the lab for the week, with TAs.
- **Case studies** from Indian market episodes (for example the 2020 Covid crash, the 2008 crisis, IPO frenzies, index rebalancing, weekly expiry dynamics), always analysed with data at least three months old and never framed as a recommendation.
- **Peer code review** every module through GitHub pull requests.
- **Industry guest sessions** each term from prop desks, AMCs, brokers, exchanges and regtech firms.

## Recommended texts

Core:
- John C. Hull, *Options, Futures, and Other Derivatives*
- Ernest P. Chan, *Quantitative Trading* and *Algorithmic Trading: Winning Strategies and Their Rationale*
- Marcos López de Prado, *Advances in Financial Machine Learning*
- Stefan Jansen, *Machine Learning for Algorithmic Trading*
- Yves Hilpisch, *Python for Finance*
- Larry Harris, *Trading and Exchanges: Market Microstructure for Practitioners*

Supplementary: Sheldon Natenberg, *Option Volatility and Pricing*; Rishi K. Narang, *Inside the Black Box*; David Aronson, *Evidence-Based Technical Analysis*; Cartea, Jaimungal and Penalva, *Algorithmic and High-Frequency Trading*; Grinold and Kahn, *Active Portfolio Management*; Ruey S. Tsay, *Analysis of Financial Time Series*; Sutton and Barto, *Reinforcement Learning: An Introduction*; Tunstall, von Werra and Wolf, *Natural Language Processing with Transformers*; Martin Kleppmann, *Designing Data-Intensive Applications*; NISM workbooks for Series VIII (Equity Derivatives) and Series XV (Research Analyst).

Module-specific papers are listed in each module README.
