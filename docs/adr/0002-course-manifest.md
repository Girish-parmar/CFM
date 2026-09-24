# ADR 0002 — One course manifest with a route manager and generated docs

**Status:** accepted (v2.0.0)

## Context

In version 1, weeks, hours, fees and lab lists were typed by hand into up to five documents.
Changing the programme length meant editing every one of them, and they drifted.

## Decision

`course/course.yaml` is the single source of truth for structure, schedule, fees, routes and
assessment. `tools/route_manager.py`:

- **checks** the manifest against the repository — module folders and guide sections, lab files vs status, contiguous weeks, prerequisites finishing before dependants start, required topic coverage, hours, fee arithmetic to the paisa, payment plans, cost bases, assessment weights, strict keys;
- **renders** tables between `<!-- BEGIN GENERATED: name -->` markers in the Markdown docs;
- **answers** questions: status, a week, a learner route, coverage, fees, lab paths.

CI runs `check`, which includes `render --check`.

## Consequences

- Structural edits happen in one place; documents cannot silently disagree.
- Authors must not edit generated sections; the check fails if they do.
- Values containing commas must be quoted in YAML flow mappings — the strict key check catches mistakes.
