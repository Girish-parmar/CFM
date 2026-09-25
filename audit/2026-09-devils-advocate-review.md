# Devil's-Advocate Review — September 2026

**Scope.** The whole repository at commit `15d0e96` (course v1: 18 modules, 45 weeks, 22 labs,
₹5,01,500 fee): library code, labs, tests, documentation, programme design and pricing.
**Method.** Argue against every claim; reproduce every result under the null; read every
module for missing topics and forward references; check the repository against common
engineering practice; re-price the programme at ₹10,00,000.00 and look for what breaks.
**Outcome.** Course v2.0.0 (this repository): 52 weeks, 24 modules plus pre-work, 33 labs
(27 ready, 6 specified and planned), one manifest with a route manager, and the fixes below —
each with a regression test or an automated check.

| Severity | Found | Fixed | Open |
|---|---:|---:|---:|
| Critical | 1 | 1 | 0 |
| High | 5 | 5 | 0 |
| Medium | 12 | 12 | 0 |
| Low | 9 | 9 | 0 |
| Content gaps (the 15 committed topics and others) | 11 | 5 | 6 planned labs |
| Programme-design risks | 10 | – | 10 monitored |

## A. Errors in code and data

| # | Severity | Finding | Evidence | Fix | Guard |
|---|---|---|---|---|---|
| A1 | **Critical** | **Synthetic OHLC leaked the future.** `ohlcv_from_close(close, seed=s)` drew its open-price noise from the same random stream as the price generator given the same seed, so today's open "knew" tomorrow's return. Labs routinely passed one seed to both. Engulfing, piercing and dark-cloud patterns "predicted" next-day returns by about 1% on a pure random walk; ML features built from OHLC were contaminated too. | Under the null (random walk), 42–58% of tests on those patterns rejected at 5% | Derived generators (`ohlcv_from_close`, `implied_vol_series`) draw from salted, independent streams | `test_candles_carry_no_information_about_future_closes`; all labs re-run and narratives re-checked |
| A2 | High | **Event-study p-values were too optimistic** for sparse, clustered events: a Newey–West regression still rejected 9% under the null (16.6% before A1 was fixed) at a nominal 5% | Size simulation over 12 seeds × 20 patterns | `analytics.stats.event_study` reports HAC t-statistics but takes its p-value from a random-date (circular-shift) permutation test | Size back to 5.0%; `test_event_study_has_correct_size_under_the_null`, `test_event_study_finds_a_planted_edge` |
| A3 | High | **Markov-regime fits were not reproducible** on statsmodels ≥ 0.15 (the seed was ignored) and the function reseeded NumPy's global random state as a side effect | Two fits with the same seed differed; the caller's random stream changed | Pass `rng=` where supported, otherwise seed-and-restore the global state | `test_markov_fit_is_reproducible_and_leaves_global_rng_alone` |
| A4 | High | **Race condition in `parallel_map`**: shared values were process-global, so two concurrent thread-backend maps, or a nested serial map inside a thread worker, overwrote each other's data | Constructed concurrent maps | Per-thread storage for serial/thread backends; per-process for the process backend | `test_concurrent_thread_maps_keep_their_own_shared_values`, `test_nested_serial_map_inside_thread_worker_restores_values` |
| A5 | High | **Signal service accepted unbounded request bodies, non-object JSON and symbols used directly in a file path** (`data/<symbol>.csv`: path traversal) | Code review | 1 MB body limit (413), JSON-object and type checks, symbol whitelist, minimum-history check; journal storage split from HTTP | `test_signal_service_rejects_bad_requests`, `test_journal_store_round_trip` |
| A6 | High | **Rule language allowed `**`** (overflow and runaway work) and rules of any length | Code review | Power operator removed; 500-character cap | `test_rule_language_rejects_anything_not_whitelisted`, `test_rule_language_limits_rule_length` |
| A7 | Medium | `pairs_backtest` charged transaction costs at the next bar's price instead of the price the trade was made at | Hand example: cost doubled when price doubled | Costs use the previous close | `test_pairs_costs_use_the_price_the_trade_was_made_at` |
| A8 | Medium | `hrp_weights` / `rolling_allocation` crashed when a sleeve had zero variance in the look-back (a pairs sleeve in its formation period); the old lab avoided it only by starting late | New M14 lab crashed | Inactive sleeves get zero weight | `test_rolling_allocation_skips_sleeves_that_are_not_trading_yet` |
| A9 | Medium | **Import cycles hidden by the flat layout**: trading → backtesting → trading, and research ↔ backtesting | Surfaced by the restructure | Costs moved to `microstructure.costs`; calendar labels to `analytics.metrics` | `test_each_module_imports_in_a_fresh_interpreter` |
| A10 | Medium | **Manifest values silently truncated**: unquoted commas in YAML flow mappings cut titles, block names, the refund amount ("₹50,000" became "₹50") and cost bases | Rendered tables | Values quoted | Strict key schema in `route_manager.py check`; cost bases must multiply out to their amounts |
| A11 | Medium | Sample data lived outside the package, so a normal (non-editable) install broke the NLP labs and the signal service | Wheel inspection | Data moved to `cfmat/data/samples` as package data; learner data in git-ignored `data/` | `test_sample_data_ships_inside_the_package` |
| A12 | Medium | Factor teaching data was unrealistically clean (composite t ≈ 9.7, no dry spells, winsorising changed nothing) — it taught false confidence | Lab output | `factor_panel` has drifting premia, sector bias and 2% distorted fundamentals | `test_factor_panel_rewards_sector_neutral_value` |
| A13 | Medium | Labs wrote output inside the source tree (`labs/output`) and hard-coded paths | Code review | `cfmat.infra.paths.output_dir()` → `build/lab-output` or `CFMAT_OUTPUT_DIR`; tests write to a temp dir | `test_output_dir_honours_environment` |
| A14 | Medium | Tests leaned on a `sys.path` hack in `conftest.py` | Code review | `pythonpath` in pytest config; editable install documented | CI |
| A15 | Medium | Thread oversubscription made the lab suite time out under load (scikit-learn/OpenMP busy-waiting) | A 47 s lab took over 600 s beside other jobs | Lab runner caps `OMP_NUM_THREADS`; CI runs labs in their own job | CI |
| A16 | Medium | Lab 12 (old lab 22) mixed M09 derivatives content with M12 Strategy-Creator content, creating forward references | Curriculum review | Split into `lab_09b` (curves, structures) and `lab_12c` (signals, filters) | Prerequisite check in the route manager |
| A17 | Low | Naked-short option margin used an expression whose terms cancelled (`n × rate × S × lot / n`) | Code review | Replaced by the explicit SPAN-like proxy it computed, with a comment | Existing margin tests |
| A18 | Low | `StrategySpec.to_json/from_json` rejected `pathlib.Path` | Lab failure after the move | Accept `str` or `PathLike` | JSON round-trip test |
| A19 | Low | Five copies of `TRADING_DAYS = 252` | Code review | One constant in `analytics.metrics` | Lint |
| A20 | Low | Cost model had no depository (DP) charge and no "rates as of" date | Code review | Optional `dp_charge`, `RATES_AS_OF`, list of charges not modelled | `test_dp_charge_applies_only_to_delivery_sells` |
| A21 | Low | Library docstrings cited old module numbers | Review | Normalised to `M01`–`M24` | – |
| A22 | Low | `requirements.txt` duplicated `pyproject.toml` dependencies | Review | One source of truth plus a tested `constraints.txt` | – |
| A23 | Low | Version stayed 1.0.0 through breaking changes | Review | 2.0.0 with a CHANGELOG | `test_version_matches_pyproject` |
| A24 | Low | No lint configuration; unused imports and unsorted imports | Review | ruff configured and enforced | CI lint job |
| A25 | Low | No LICENSE, CONTRIBUTING, SECURITY, CODEOWNERS, templates, `.gitattributes` or `.editorconfig` | Review | Added | – |
| A26 | Low | The generated-looking tables in docs (hours, calendar, fees) were hand-maintained and drifted (old docs: "10½ months", "45 weeks" and per-term hours had to be edited in five files) | Review | Generated from the manifest; CI fails if stale | `route_manager.py render --check` |
| A27 | Low | Pay-in-full discount made the published fee ambiguous (₹4,72,000 vs ₹5,01,500) | Fee doc | One all-inclusive price for every plan; concessions only through scholarships | Plan totals checked to the paisa |

## B. What the course was missing

| Committed topic | v1 status | v2 | Remaining work |
|---|---|---|---|
| Macroeconomics | missing | M02 (2 weeks) | Lab 02a planned |
| Market data handler | missing | M16 (1 week) | Lab 16a planned |
| Monitoring system | missing | M18 week 37 | Lab 18b planned |
| F&O with second-order Greeks | first-order only | M09 (2 weeks) | Lab 09a planned |
| Deep learning | shared lab, thin | M20 with its own lab (linear vs nonlinear signals) | – |
| Reinforcement learning | one section | M21 with its own lab (costs, seeds) | – |
| Portfolio management | one section | M14 with its own lab (shrinkage, frontier, sleeves) | – |
| Risk management and sizing | one section | M13 with its own lab (Kupiec, GARCH VaR, ruin) | – |
| Technical indicators and patterns | indicators only in lab 5 | M06 lab with event studies and FDR over 20 patterns | – |
| Sentiment and news | sentiment only | M22 week 43 | Lab 22b planned |
| Capstone scaffold | none | M24 repository layout | Lab 24a planned |

Also missing in v1 and now present: a mission statement, learning routes for different
backgrounds, an operations runbook, a published fee split and unit-economics sensitivity,
mentoring hours proportionate to a premium price (24 h, was 12 h), and a third bootcamp.

## C. Wrong practices in the repository (all fixed)

1. **One flat package for everything.** 24 modules at one level mixed pricing, brokers, NLP and plotting; several modules mixed behaviours (for example `strategy_builder` held a language, a spec, a library, an engine and optimisers). Now 14 subpackages by concern; split modules; `cfmat.studio` as one namespace for the Strategy Creator.
2. **Test files mixed subjects** (`test_broker_ml_nlp.py`). Now one test file per subpackage, plus layout tests.
3. **Docs as a second source of truth.** Now a manifest with generated sections and a CI check.
4. **No local quality gate.** Now `make check`, pre-commit hooks, and a CI pipeline with separate lint, unit (3.10 / pinned 3.11 / 3.12), labs and course-check jobs.
5. **Unpinned environment for learners.** Now `constraints.txt` with the tested versions.
6. **Repository without governance files.** Now LICENSE, CONTRIBUTING, SECURITY, CODEOWNERS, PR and issue templates, CHANGELOG, `.editorconfig`, `.gitattributes`, a repository map and decision records.

**Still open (needs the owner's decision):** the repository has a single working branch and no
default `main` branch. Create `main` from this branch, make it the default, protect it (required
reviews and the CI checks), and use feature branches with pull requests from then on.

## D. Programme-design risks (monitored)

| # | Risk | Why it matters | Mitigation | Owner |
|---|---|---|---|---|
| D1 | **Price.** ₹10 lakh is above most Indian algo-trading certificates | Demand may not reach break-even (≈ 28 learners) | Sensitivity table in the fee plan; corporate cohorts (GST input credit); publish audited outcomes; 10% scholarship budget | PD |
| D2 | **Break-even at 71% of maximum capacity** | One weak intake loses money | Minimum-to-run size 30; go/no-go at T − 8 weeks; second intake shares fixed content costs | PD, PM |
| D3 | **Twelve-month commitment** for working professionals (≈ 18 h a week) | Drop-out risk | At-risk tracking every Friday, catch-up plans, free deferral once | PM |
| D4 | **Synthetic data with planted effects** | Learners may over-trust effects that real markets do not have | Every lab says so; every module has a real-data exercise; capstones use licensed data | Module owners |
| D5 | **Six planned labs** at a premium price | Visible gaps | Backlog below, two labs per cohort, exercise packs meanwhile | PD |
| D6 | **Faculty depth and key-person risk** across 24 modules | Refresh quality depends on six people | Named owners, peer observation, shared "what went wrong" log, deputy per area | PD |
| D7 | **Regulatory drift** (SEBI retail-algo phases, charges, lot sizes) | Content goes stale quickly | Compliance review before every cohort; `RATES_AS_OF` in code | PD, compliance adviser |
| D8 | **Assessment integrity with AI assistants** | Grades lose meaning | Disclosed AI use, viva on every capstone, proctored exams without AI | PD |
| D9 | **Bootcamp travel excluded** from an "all-inclusive" fee | Perceived as a hidden cost | Stated in inclusions/exclusions and on the offer letter; travel support within the need-based scholarship | PM |
| D10 | **Mentoring capacity**: 24 h × 36 learners = 864 mentor-hours | Under-staffing hurts the premium promise | One mentor per six learners; utilisation reported per cohort | PM |

## E. Planned-lab backlog (priority order)

| Priority | Lab | Why first | Library work | Acceptance |
|---|---|---|---|---|
| P1 | 24a capstone template | Every learner uses it; highest value per hour | glue only | One command reproduces every capstone table; look-ahead, risk and cost tests |
| P1 | 16a market data handler — **shipped in v2.2.0** | Algo-developer route; feeds M17–M18 | `data.handler`, tick-stream generator | Planted faults found with no false alarms; deterministic replay (40 seeds: 960/960 found, 0 false alarms) |
| P1 | 18b live monitoring | Committed topic "monitoring system" | `automation.monitoring` | Planted incidents detected; no alerts on a clean day |
| P2 | 09a second-order Greeks | Committed topic; derivatives route | `bs_second_order_greeks`, `pnl_attribution` | Closed forms match finite differences; attribution residual < 5% |
| P2 | 22b news to signals | Committed topic "sentiment and news" | `data.news_stream`, `nlp.news_signal` | Planted response recovered; vanishes beyond its half-life |
| P2 | 02a macro event study | Committed topic "macroeconomics" | `data.macro_calendar`, `analytics.rates.nelson_siegel_fit` | Known Nelson–Siegel parameters recovered; causal regime labels |

Each lab's full specification is in its module guide. When a lab ships, flip its status to
`ready` in `course/course.yaml`; the route manager then requires the file and the lab test runs it.

## F. Evidence

- Unit tests: 181 passing on Python 3.10 and 3.11 (one file per subpackage, plus layout, course-manifest, docstring-coverage, link and regression tests).
- Labs: all 27 ready labs run as smoke tests (`pytest -m lab`, 3 min 37 s on Python 3.11); outputs re-checked against each lab's narrative after the A1 fix.
- Manifest: `python tools/route_manager.py check` — 25 modules, 33 labs (27 ready), 736 guided hours, fee ₹10,00,000.00, all generated sections current.
- Statistical checks: event-study size 5.0% under the null (was 16.6%); zero false discoveries after Benjamini–Hochberg on random walks.

## G. What this review could not verify

- Current SEBI circulars, exchange standards, charge sheets, lot sizes and margin rates — they must be checked against official sources before each cohort.
- Market prices of comparable programmes, and every cost line in the unit economics — replace the assumptions with quotes.
- GST treatment of bootcamp stay and joint certification — needs a chartered accountant.
- Learner outcomes — none exist yet for v2; publish only audited numbers with their base and period.

## H. Addendum — v2.1.0 (2026-09-25)

Adding order management, the trading journal, momentum and volatility, analysis tools and
visualisation (see the [CHANGELOG](../CHANGELOG.md)) exposed these issues in v2.0.0.

| # | Severity | Finding | Fix | Guard |
|---|---|---|---|---|
| B1 | Medium | A limit order that was marketable on arrival filled at its **limit** price, not the market price, overstating the cost of aggressive limit orders in every paper-trading result | Fill at the market price with slippage, never worse than the limit | `test_marketable_limit_fills_at_the_market_not_at_its_limit` |
| B2 | Medium | No order-management layer: stops, brackets, time in force, safe retries and reconciliation lived in strategy code or nowhere, so M17 taught them only in slides | `trading.oms.OrderManager` with a state machine, audit trail and reconciliation ([ADR 0005](../docs/adr/0005-order-management-layer.md)); lab 17b | 14 OMS tests, including idempotent retries, bracket resizing on partial fills and reconciliation breaks |
| B3 | Low | `metrics.drawdown_series` measures from the first close, so a loss on the first day is not counted as a drawdown | Documented; `analytics.performance.underwater` and the tearsheet measure from the starting capital. `drawdown_series` is unchanged so existing results stay comparable | `test_underwater_counts_losses_from_the_starting_capital` |
| B4 | Low | The trade journal stored fills only: R-multiples, round trips and excursions had to be rebuilt by hand, and reversals were easy to get wrong | `round_trips`, `excursions`, `trade_summary`, `trade_breakdown`; charges split pro rata on reversals | `test_round_trips_handle_scaling_partial_exits_and_reversals`; journal P&L and charges equal the broker's |
| B5 | Low | `backtesting.report.__all__` exported `np` (a leftover that silenced an unused-import warning) | Removed | `test_public_names_resolve` |
| B6 | Teaching | Volatility-regime labels from trailing percentiles adapt: a lasting shift to high volatility is labelled "normal" within months. Learners would read that as calm returning | Stated in the docstring and in lab 10b | `test_ewma_cone_percentile_and_regime_follow_a_volatility_shift` |

Evidence for v2.1.0: 228 unit tests passing on Python 3.10 and 3.11; 30 ready labs run as smoke
tests; the wheel installs and runs outside the repository; manifest and API reference current.
Lab narratives were checked against their outputs. Where the synthetic data shows no edge
(dual momentum in lab 11b, time-series momentum on the GARCH market in lab 10b), the lab says so.
