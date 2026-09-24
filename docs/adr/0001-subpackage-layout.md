# ADR 0001 — Organise `cfmat` into subpackages by concern

**Status:** accepted (v2.0.0)

## Context

Version 1 had 24 modules in one flat package. Several mixed behaviours: `strategy_builder` held a
rule language, a strategy spec, a template library, a backtest engine and optimisers; `broker`
held orders, risk checks, a paper broker and a journal; `signal_server` mixed HTTP handling with
storage. The flat layout hid two import cycles and made it hard for learners to find things.

## Decision

Fourteen subpackages, each owning one concern, with a strict dependency direction
(`analytics`/`infra` at the bottom; `trading`, `automation` and `research` near the top):

| Old module | New location |
|---|---|
| `data` | `data.synthetic`, `data.loaders` (+ `data/samples` package data) |
| `metrics`, `indicators`, `patterns` | `analytics.metrics`, `analytics.indicators`, `analytics.patterns` (+ new `analytics.stats`, `analytics.factors`) |
| `options`, `futures`, `options_backtest` | `derivatives.options`, `derivatives.futures`, `derivatives.option_strategies` |
| `strategies` | `strategies.signals` (re-exported by `cfmat.strategies`) |
| `strategy_builder` | `strategies.rules`, `strategies.spec`, `strategies.templates`, `backtesting.rule_engine`, `backtesting.optimize` (facade: `cfmat.studio`) |
| `backtest` | `backtesting.vectorized` + `microstructure.costs` |
| `engine`, `report` | `backtesting.event_driven`, `backtesting.report` |
| `risk`, `portfolio` | `portfolio.risk`, `portfolio.construction` (re-exported by `cfmat.portfolio`) |
| `execution` | `microstructure.order_book`, `.schedules`, `.tca` |
| `broker` | `trading.orders`, `.risk_checks`, `.paper_broker`, `.journal` |
| `signal_server` | `automation.signal_service`, `automation.journal_store` |
| `ml`, `tuning`, `rl` | `ml.features`, `.labels`, `.validation`, `.sizing`, `ml.tuning`, `ml.reinforcement` |
| `advanced` | `econometrics.kalman`, `.garch`, `.regimes` |
| `segments`, `screener` | `research.segments`, `research.screener` |
| `parallel`, `plotting` | `infra.parallel`, `infra.plotting` (+ `infra.paths`) |

## Consequences

- Breaking import paths: version 2.0.0. Labs and tests were migrated in the same change.
- `test_each_module_imports_in_a_fresh_interpreter` guards against new cycles; `__all__` lists are tested.
- The API reference is generated per subpackage.
