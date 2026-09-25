# Changelog

All notable changes to the course and its library. Versions follow [Semantic Versioning](https://semver.org/)
for the `cfmat` library; the course edition is recorded in `course/course.yaml`.

## [Unreleased]

### Added
- `course/12-setup-and-run-guide.md`: which Python to install and how on Windows, macOS and
  Linux; the virtual environment; the must and optional install steps; the environment check;
  the order to run every lab (generated from the manifest); optional extras, services and API
  keys; using the library in your own code; a weekly routine; commands without `make`;
  troubleshooting.
- Lab entries in `course/course.yaml` can name the optional pip extras that unlock a section or
  exercise (`extras: [boost]`); the route manager checks them against `pyproject.toml` and
  renders the `run-order` table.

### Changed
- Docs recommend Python 3.11 or 3.12 (the tested pins) instead of "3.11+".

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
