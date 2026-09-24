# Changelog

All notable changes to the course and its library. Versions follow [Semantic Versioning](https://semver.org/)
for the `cfmat` library; the course edition is recorded in `course/course.yaml`.

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
