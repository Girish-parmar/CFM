# ADR 0003 — Synthetic data with planted effects, independent random streams

**Status:** accepted (v1.0.0, amended in v2.0.0)

## Context

Labs must run offline, fast and identically for every learner, and must show a method working
when an effect exists. Licensed market data cannot be redistributed.

## Decision

- Every lab uses synthetic or fictional data from `cfmat.data`, with documented, planted effects (momentum, mean reversion, regimes, calendar effects, factor premia, archetypes).
- Every lab says what was planted, and every module has an exercise on real data.
- **Amendment (v2.0.0):** generators that add noise to an existing series (`ohlcv_from_close`, `implied_vol_series`) draw from a *salted* random stream (`default_rng([salt, seed])`), independent of `default_rng(seed)`. Reusing one seed for a price series and its OHLC bars previously made the open price reveal the next day's return (audit item A1).

## Consequences

- Results are reproducible across machines and CI.
- Learners may over-trust planted effects: every lab's narrative must match its output, and re-tuning seeds to make a claim look true is not allowed (CONTRIBUTING).
- A regression test checks that bars carry no information about future closes.
