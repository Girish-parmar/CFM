# Contributing

Faculty, TAs and learners improve this course through pull requests. The rules below keep the
course, the code and the documentation consistent.

## Set up

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # tested versions; or pip install -e ".[dev,boost]"
pip install pre-commit && pre-commit install
make check                               # must pass before you push
```

## Branches and commits

- `main` is protected. Work on a branch named `topic/short-description` (for example `lab/09a-second-order-greeks`, `fix/pairs-cost-price`, `docs/m13-guide`).
- One logical change per commit. Write the subject in the imperative ("Add Kupiec test", not "Added…"), under 72 characters, and explain *why* in the body.
- Open a pull request using the template. A second module owner reviews content changes; CI must be green.

## What must pass

| Check | Command | Why |
|---|---|---|
| Lint | `make lint` | ruff rules in `pyproject.toml` |
| Unit tests | `make test` | one test file per subpackage |
| Manifest | `make course` | `course/course.yaml` agrees with the repository; generated tables are current |
| API docs | `python tools/gen_api_docs.py --check` | the reference is generated from docstrings |
| Labs | `make labs` | every ready lab runs (CI runs this in its own job) |

## Changing the course

1. Edit `course/course.yaml` for anything structural: weeks, hours, labs, fees, routes, assessment.
2. Run `python tools/route_manager.py render`, then `check`. Commit the manifest and the regenerated docs together.
3. Never edit text between `<!-- BEGIN GENERATED: … -->` and `<!-- END GENERATED: … -->` by hand.
4. Module guides keep the standard sections (the route manager checks them) and a `### Week N — theme` plan for every week.

## Adding or finishing a lab

1. Name it `lab_NNx_topic.py` in the module's folder (`NN` = module number, `x` = a, b, c…).
2. Jupytext percent format: a markdown header with goals, then short sections with printed, interpreted results and a closing Exercises cell.
3. Offline and deterministic: synthetic or fictional data from `cfmat.data`, fixed seeds, under about 60 s on a laptop. Write charts with `cfmat.infra.plotting.savefig`.
4. If the lab needs new library code, add it to the right subpackage with docstrings and tests.
5. Set the lab's status to `ready` in the manifest; the lab test then runs it.

## Library code

- Put code in the subpackage that owns the concern; do not import "upwards" (for example `analytics` must not import `backtesting`). `test_each_module_imports_in_a_fresh_interpreter` catches cycles.
- Every public function and class has a docstring (tested); the first paragraph becomes the API reference summary.
- No look-ahead: any function that produces signals, labels or features must pass a truncation test (results on the first *n* bars do not change when later bars are added).
- Derived random data (noise added to an existing series) must use an independent stream — see [ADR 0003](docs/adr/0003-synthetic-data-first.md).

## Content rules

- Education only: no recommendations, tips or return claims; named securities only with data at least three months old ([compliance](course/09-compliance-and-risk-disclosures.md)).
- Report negative results honestly. If a lab's narrative stops matching its output, fix the narrative or the data — never tune a seed until a claim looks true.
- Record user-visible changes in [CHANGELOG.md](CHANGELOG.md).
