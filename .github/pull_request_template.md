## What and why

<!-- One or two sentences: what changes and why. Link the issue or audit item if there is one. -->

## Type of change

- [ ] Library code (`cfmat/`)
- [ ] Lab (`curriculum/**/lab_*.py`)
- [ ] Module guide or course document
- [ ] Manifest (`course/course.yaml`) — structure, weeks, hours, fees or routes
- [ ] Tooling, CI or repository hygiene

## Checklist

- [ ] `make check` passes (lint, unit tests, manifest, API docs)
- [ ] Changed or new labs run (`make labs` or the lab file directly)
- [ ] New library functions have docstrings and tests; signal/feature code has a truncation (no look-ahead) test
- [ ] Manifest edited and `python tools/route_manager.py render` run, if anything structural changed
- [ ] No generated section edited by hand
- [ ] No licensed data, secrets or personal data committed
- [ ] Education-only content rules respected (no recommendations or return claims)
- [ ] CHANGELOG updated for user-visible changes

## Evidence

<!-- Test output, lab output excerpts or screenshots of rendered docs. -->
