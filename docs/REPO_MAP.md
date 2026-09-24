# Repository Map

Where everything lives, how files are named, and where to go for common tasks.

## Top level

| Path | What it is | Generated? |
|---|---|---|
| `README.md` | Front page; summary and module table are generated | partly |
| `course/` | The programme: `course.yaml` manifest and handbook documents 00–11 | partly (marked sections) |
| `curriculum/` | One folder per module with its guide and labs | headers and indexes |
| `cfmat/` | The course library | no |
| `tools/` | `route_manager.py`, `gen_api_docs.py` | no |
| `tests/` | Unit, layout, course and lab tests | no |
| `n8n/` | Importable n8n workflows and their README | no |
| `docs/reference/` | API reference, one page per subpackage | **yes** (`make docs`) |
| `docs/adr/` | Architecture decision records | no |
| `audit/` | Devil's-advocate reviews | no |
| `data/` | Your own price files (git-ignored except the README) | – |
| `build/` | Lab output and build artefacts (git-ignored) | – |
| `pyproject.toml` | Packaging, dependencies, pytest and ruff configuration | no |
| `constraints.txt`, `requirements.txt` | Tested versions; one-command install | no |
| `Makefile`, `.pre-commit-config.yaml` | Local quality gates | no |
| `.github/` | CI workflow, CODEOWNERS, PR and issue templates | no |

## Naming conventions

| Thing | Pattern | Example |
|---|---|---|
| Module ID | `MNN` | `M12` |
| Module folder | `curriculum/mNN-slug/` | `curriculum/m12-strategy-studio/` |
| Lab file | `lab_NNx_topic.py` (NN = module, x = a, b, c …) | `lab_12b_strategy_creator_parallel.py` |
| Lab title (line 2) | `# # Lab NNx — Title (MNN)` | `# # Lab 12b — Strategy Creator … (M12)` |
| Chart file | `labNNx_description.png` in `build/lab-output/` | `lab12a_regime_map.png` |
| Test file | `tests/test_<subpackage>.py` | `tests/test_microstructure.py` |
| ADR | `docs/adr/NNNN-slug.md` | `docs/adr/0002-course-manifest.md` |
| Audit | `audit/YYYY-MM-topic.md` | `audit/2026-09-devils-advocate-review.md` |

## The library at a glance

| Subpackage | Owns | Depends on |
|---|---|---|
| `analytics` | metrics, indicators, patterns, stats, factors | numpy, pandas, scipy, statsmodels |
| `infra` | parallel map, paths, plotting | stdlib, matplotlib |
| `data` | synthetic generators, loaders, sample data | analytics |
| `derivatives` | options, futures, option-structure backtests | analytics, microstructure, infra |
| `strategies` | signal functions, rule language, specs, templates | analytics |
| `microstructure` | order book, schedules, TCA, Indian costs | numpy, pandas |
| `trading` | orders, risk checks, paper broker, journal | microstructure |
| `backtesting` | vectorised, event-driven and rule engines, optimisers, reports | analytics, strategies, trading, microstructure, research |
| `research` | screener, segments | analytics, backtesting, infra |
| `portfolio` | risk, construction | numpy, pandas, scipy |
| `econometrics` | Kalman, GARCH, regimes | analytics, strategies |
| `ml` | features, labels, validation, sizing, tuning, RL | analytics, scikit-learn (+ optional boosters) |
| `nlp` | sentiment, RAG, LLM step | scikit-learn, infra (+ optional anthropic) |
| `automation` | signal service, journal store | analytics, data, nlp, infra |
| `studio` (module) | one namespace for the Strategy Creator workflow | strategies, backtesting |

## Where do I…

| Task | Go to |
|---|---|
| Change the fee, weeks, hours, labs or routes | `course/course.yaml`, then `python tools/route_manager.py render` |
| See what happens in a given week | `python tools/route_manager.py week N` |
| Write or update a module guide | `curriculum/mNN-*/README.md` (keep the standard sections) |
| Add a lab | `curriculum/mNN-*/lab_NNx_*.py` + its manifest entry ([CONTRIBUTING](../CONTRIBUTING.md)) |
| Add a library function | the owning subpackage + a test in `tests/test_<subpackage>.py` + a docstring |
| Find a function | [API reference](reference/README.md) |
| Check everything before pushing | `make check` (and `make labs`) |
| Understand a past decision | [ADRs](adr/README.md), [CHANGELOG](../CHANGELOG.md), the [audit](../audit/2026-09-devils-advocate-review.md) |
