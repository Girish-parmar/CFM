# Changelog

All notable changes to the course and its library. Versions follow [Semantic Versioning](https://semver.org/)
for the `cfmat` library; the course edition is recorded in `course/course.yaml`.

## [Unreleased]

## [2.2.0] — 2026-09-25

### Added
- `course/12-setup-and-run-guide.md`: which Python to install and how on Windows, macOS and
  Linux; the virtual environment; the must and optional install steps; the environment check;
  the order to run every lab (generated from the manifest); optional extras, services and API
  keys; using the library in your own code; a weekly routine; commands without `make`;
  troubleshooting.
- Lab entries in `course/course.yaml` can name the optional pip extras that unlock a section or
  exercise (`extras: [boost]`); the route manager checks them against `pyproject.toml` and
  renders the `run-order` table.

- Market data from brokers and vendors: `data.alpaca_bars` (US stocks from Alpaca) and
  `data.ibkr_bars` (Interactive Brokers, including NSE, with paced paging back in time), new
  optional extras `alpaca` and `ibkr`, and the `cfmat-fetch` command
  (`python -m cfmat.data.fetch {yahoo,alpaca,ibkr} SYMBOL ...`) that saves checked
  `data/<SYMBOL>.csv` files.
- Lab 16a, market data handler, and `cfmat.data.handler`: `validate_ticks` (duplicates,
  late ticks, spikes that still accept a genuine jump, frozen prices, outages), time/volume/
  dollar `aggregate_bars` and the live `BarBuilder`, `InstrumentMaster` (lot and tick checks,
  front month with a roll rule), `continuous_futures` (none, back- and ratio-adjusted),
  partitioned `store_ticks`/`load_ticks` (Parquet or CSV) and deterministic `replay`; the
  generators `data.tick_stream` (with planted faults and an answer key) and `data.futures_chain`.
  pyarrow joins the `data` extra.
- Lab 18b, live monitoring, and `cfmat.automation.monitoring`: `heartbeat_gaps`, `staleness`
  (silent vs frozen feeds), `drift_report` (tracking, return distribution, signal agreement,
  slippage; every field always present), `pnl_attribution` (signal + execution + costs, adding
  up exactly to the broker's equity change), and `AlertRule`/`AlertManager`/`webhook_sink`
  (severity, de-duplication, reminders, resolutions, failure-tolerant delivery).
- Lab 24a, capstone template: pre-registration generated and checked (fields, hold-out after
  research, grid within the trial budget), data quality and split, Indian cost per side from the
  cost model, walk-forward with the DSR charged for the trial budget, one hold-out look with a
  MET/NOT MET verdict, paper trading through the OMS and RMS with a journal and monitoring (acting
  only on the previous close), three checks (no look-ahead, risk limits, costs), and a capstone
  folder with README, PREREGISTRATION, report tables and a passing `pytest` file.
- Lab 09a, second-order Greeks: `derivatives.options.bs_second_order_greeks` (vanna, volga,
  charm, speed, zomma, colour in the same units as `bs_greeks`, checked against finite
  differences) and `greek_pnl_attribution` (daily explain of an option position by delta,
  gamma, vega, theta, vanna, volga, charm and speed, with the residual); Greek maps; a short
  straddle through a sell-off; gamma scalping against realised volatility.
- Lab 22b, news to signals: `data.news_stream` (timestamped headlines at all hours with
  re-publications and a planted, decaying response), `nlp.news_events` (de-duplication, scoring,
  assignment to the first session that can act) and `nlp.news_signal` (decayed per-stock
  sentiment known at each close); `analytics.stats.event_study` accepts a panel (one column per
  stock), shifting every stock's events together in the permutation test.
- Lab 02a, RBI policy days, CPI surprises and the yield curve: `data.macro_calendar` (a synthetic
  economy: release calendar in IST with consensus and surprises, CPI/IIP vintages with
  revisions, an equity index with planted announcement effects, the repo rate and a G-sec curve
  built from known Nelson–Siegel factors); `analytics.rates` (`bond_price`, `bond_risk`,
  `nelson_siegel`, `nelson_siegel_fit`, `nelson_siegel_tau`, `nelson_siegel_panel`,
  `inversion_episodes`); `analytics.macro` (`release_sessions`, vintage-aware `latest_known`,
  causal `growth_inflation_regimes` with a hindsight mode for comparison); and
  `analytics.stats.event_day_effect` (same-day quantities on event days vs other days, HAC t and
  a studentised circular-shift permutation test, which keeps its size when event days are more
  volatile). With it every planned lab has shipped.
- `data.standardize_ohlcv` (one OHLCV shape for every source: lower-case columns, exchange-local
  naive timestamps, sorted, no duplicates) and `data.ohlcv_problems` (plain-language data-quality
  checks).

### Changed
- Docs recommend Python 3.11 or 3.12 (the tested pins) instead of "3.11+".
- `data.download_prices` returns the standard shape via `standardize_ohlcv`.
- `nlp.news_events` assigns sessions with the shared `analytics.macro.release_sessions` (same rule).

## [2.1.0] — 2026-09-25

### Added
- **Order management** (`cfmat.trading.oms.OrderManager`): order state machine with an audit trail;
  idempotent client order ids; stop and stop-limit orders held until triggered; DAY, IOC and GTC
  time in force; amend as cancel/replace; bracket orders whose exits follow the filled entry
  quantity; OCO groups; reconciliation against the broker; flatten. See [ADR 0005](docs/adr/0005-order-management-layer.md).
- **Trading journal**: notes on fills (`setup`, `stop`, `target`, `tags`), `annotate`, flat-to-flat
  `round_trips` with net P&L and R-multiples, `excursions` (MAE/MFE, exit efficiency),
  `trade_summary` (expectancy in ₹ and R, SQN, costs, streaks), `trade_breakdown` (by setup, tag,
  weekday, hour), CSV and SQLite persistence.
- **Momentum and volatility**: `analytics.momentum` (12-1, risk-adjusted, regression, information
  discreteness, acceleration, TSMOM with a volatility target, cross-sectional ranks, dual momentum)
  and `analytics.volatility` (close-to-close, Parkinson, Garman–Klass, Rogers–Satchell, Yang–Zhang,
  EWMA, ATR %, cones, percentiles, regimes, vol of vol).
- **Analysis tools**: `analytics.performance` (tearsheet with benchmark, drawdown periods,
  underwater curve, rolling metrics, monthly and annual returns, ulcer, omega, tail ratio,
  gain-to-pain) and `analytics.relative` (CAPM alpha with a Newey–West t, beta, capture ratios,
  rolling beta and correlation, relative strength, Mansfield RS, RS rating, relative rotation).
- **Visualisation**: `cfmat.viz` — price charts with overlays, trade and pattern markers, volume
  and indicator panels; equity and drawdown, monthly heatmap, rolling metrics, return
  distribution, trade review; correlation heatmap, volatility estimators, cone, rankings,
  rotation graph, efficient frontier.
- `data.brownian_ohlc` (bars from a simulated one-minute path with a known true volatility);
  `data.universe(idio_vol=(low, high))` draws a volatility per stock.
- Labs 10b (momentum and volatility), 11b (performance analysis and the tearsheet) and 17b (order
  management and the trading journal); module guides M10, M11 and M17 updated.

### Changed
- `PaperBroker` supports partial fills (`max_fill_qty`), publishes fills to listeners and reports
  working orders; `Order` tracks `filled_qty` and `avg_fill_price` and must be MARKET or LIMIT.
- `backtesting.report.monthly_returns_table` delegates to `analytics.performance.monthly_returns`.

### Fixed
- A limit order that was marketable on arrival filled at its limit price instead of the market
  price, overstating the cost of aggressive limit orders.
- `backtesting.report.__all__` exported `np`.

## [2.0.0] — 2026-09-24

A full review and restructure: see the [devil's-advocate audit](audit/2026-09-devils-advocate-review.md).

### Programme
- 52 weeks, 6 terms, 24 modules plus pre-work (was 45 weeks, 18 modules); 736 guided hours (was 510).
- New modules: M02 Macroeconomics, M07 Fundamental and factor investing, M09 F&O strategies and second-order Greeks, M14 Portfolio management, M16 Market data handling, M20 Deep learning and M21 Reinforcement learning (split), M18 Monitoring and automation (expanded).
- Fee plan at **₹10,00,000.00 all-inclusive** (₹8,47,457.63 + GST ₹1,52,542.37) with four payment plans, scholarships, refunds, fee allocation, unit economics and price sensitivity — all generated from the manifest.
- Mission, vision and values; six learning routes; operations runbook; third bootcamp; 24 h of mentoring.
- Micro-level module guides with minute-by-minute session plans for every week.

### Added
- `course/course.yaml` manifest and `tools/route_manager.py` (check, render, status, week, route, coverage, fees, labs).
- New labs: 00a environment check, 06a indicators and patterns with FDR, 07a factor research, 12c F&O signals and filters, 13a risk and VaR backtests, 14a portfolio construction and strategy allocation, 20a deep learning, 21a reinforcement learning. Six more labs specified as planned.
- `cfmat.analytics.stats` (HAC t-statistics, Benjamini–Hochberg, random-date event studies), `cfmat.analytics.factors`, `data.factor_panel`, `portfolio.risk.kupiec_test`, `cfmat.infra.paths`, `cfmat.studio`, `cfmat.automation.journal_store`.
- Generated API reference (`docs/reference`), repository map, decision records, governance files, Makefile, pre-commit, constraints, multi-job CI.

### Changed (breaking)
- `cfmat` reorganised into 14 subpackages; multi-behaviour modules split. Old imports such as `cfmat.backtest`, `cfmat.broker`, `cfmat.strategy_builder` and `cfmat.signal_server` are gone — see [ADR 0001](docs/adr/0001-subpackage-layout.md) for the mapping.
- Labs moved to `curriculum/mNN-*/lab_NNx_*.py`; sample data moved into the package; lab output goes to `build/lab-output`.
- Signal service: `python -m cfmat.automation.signal_service`.

### Fixed
- Synthetic OHLC generator leaked the next day's return when given the same seed as the price generator (critical).
- Event-study p-values too optimistic for sparse events; Markov-regime fits not reproducible and mutating global RNG state; `parallel_map` shared-state race; pairs-backtest cost price; HRP crash on inactive sleeves; signal-service input handling; rule-language `**`; import cycles; and more — see the audit.

## [1.3.0] — 2026-09-24
### Added
- Strategy Studio: screener and instrument selection, candlestick and chart patterns, rule-based Strategy Creator with a trade-level backtester and template library, futures and option-structure backtesters, parallel research engine (labs 20–22).

## [1.2.0] — 2026-09-24
### Added
- Strategy optimisation by segment (day, month, turn of month, expiry week, regime, pattern) with false-discovery control (lab 19).

## [1.1.0] — 2026-09-24
### Added
- Module 16: gradient boosting and hyperparameter optimisation, regime switching, GARCH, Kalman-filter pairs, meta-labelling and strategy ensembles (labs 16–18).

## [1.0.0] — 2026-09-24
### Added
- The course: 18 modules over 45 weeks, programme documents, the `cfmat` library, 15 labs, n8n workflows and tests.
