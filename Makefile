# Common tasks. Run `make help` for the list.
PY ?= python

.PHONY: help install lint fix test labs course docs docs-check check all build clean serve

help:            ## show this help
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

install:         ## install the package with tested versions (Python 3.11+)
	$(PY) -m pip install -r requirements.txt

lint:            ## ruff lint
	$(PY) -m ruff check .

fix:             ## ruff lint with safe autofixes
	$(PY) -m ruff check . --fix

test:            ## unit tests (fast; excludes labs)
	$(PY) -m pytest -m "not lab"

labs:            ## run every ready lab as a smoke test
	$(PY) -m pytest -m lab

course:          ## validate course/course.yaml against the repository
	$(PY) tools/route_manager.py check

docs:            ## regenerate manifest tables and the API reference
	$(PY) tools/route_manager.py render
	$(PY) tools/gen_api_docs.py

docs-check:      ## fail if generated docs are stale
	$(PY) tools/route_manager.py render --check
	$(PY) tools/gen_api_docs.py --check

check: lint test course docs-check  ## everything CI checks except labs

all: check labs  ## everything CI checks

build:           ## build a wheel into dist/
	$(PY) -m pip wheel --no-deps . -w dist

clean:           ## remove build and cache folders
	rm -rf build dist .pytest_cache .ruff_cache *.egg-info
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

serve:           ## run the signal service used by the n8n workflows
	$(PY) -m cfmat.automation.signal_service --port 8000
