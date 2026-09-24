# Learning Routes

Every learner takes every module — the cohort moves together and the certificate means the same
thing for everyone. What differs is where each learner **goes deeper** (stretch exercises,
optional readings, clinic extension work and matching capstones) and which modules they **may test
out of** (pass a challenge quiz in Week 0 and use that module's clinics for extension work
instead). Routes are defined in [`course.yaml`](course.yaml) and printed by the route manager.

## The six routes (generated)

<!-- BEGIN GENERATED: routes -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
| Route | Persona | For | Go deeper in | May test out of | Suggested capstones |
|---|---|---|---|---|---|
| `quant-researcher` | Quant researcher | Graduates in maths, statistics, economics or engineering aiming at research roles | M04, M07, M10, M11, M19, M23 | – | Multi-factor portfolio; ML meta-labelling; Seasonality and regime atlas |
| `algo-developer` | Algo developer | Software engineers moving into trading systems | M05, M15, M16, M17, M18 | M03 | End-to-end automated trading system; Execution algorithm and TCA |
| `derivatives-trader` | Derivatives trader | F&O traders and dealers who want systematic, risk-controlled option strategies | M08, M09, M12, M13 | M01 | Short-volatility options strategy with tail hedges; Screener-to-strategy system |
| `systematic-trader` | Discretionary to systematic trader | Chart-based traders who want to test and automate their process | M06, M10, M11, M12, M13 | M01 | Index futures trend following with volatility targeting; Screener-to-strategy system |
| `risk-portfolio` | Risk and portfolio analyst | BFSI professionals in risk, treasury or asset management | M02, M04, M13, M14, M15 | – | Regime-aware multi-strategy portfolio; Multi-factor portfolio |
| `ai-engineer` | AI engineer in finance | Data scientists and ML engineers bringing models to markets | M19, M20, M21, M22, M23 | M03 | News and filings sentiment signal; RAG research assistant for filings; ML meta-labelling |
<!-- END GENERATED: routes -->

## Following a route

```bash
python tools/route_manager.py routes                     # list routes
python tools/route_manager.py route algo-developer       # the full 25-module plan for a route
python tools/route_manager.py week 34                    # what happens in a given week
```

A route plan marks each module as:

| Mark | Meaning | What the learner does |
|---|---|---|
| ▲ deepen | A core module for this route's career | All stretch exercises; optional readings; one extra mentor session on the topic; capstone options draw on it |
| ○ test-out option | Prior knowledge likely | Challenge quiz in Week 0 (pass mark 75%); if passed, the module's quizzes are waived and its clinics become extension time; the lab is still submitted |
| · core | Everyone | The standard plan in the module guide |

## Choosing and changing a route

- Learners choose a route in the application (statement of purpose) and confirm it with their mentor in Week 2.
- A route can be changed once, up to Week 20, with the mentor's agreement. The capstone topic (Week 38) usually settles it.
- Routes never change the fee, the assessment weights or the certificate.

## Why routes and not electives

A 52-week cohort with one faculty team cannot run parallel electives without splitting the cohort
and raising cost. Routes give most of the personalisation of electives — depth where it matters for
the learner's career — while keeping one timetable, one set of labs and one standard for the
certificate. The [audit](../audit/2026-09-devils-advocate-review.md) lists electives as a future
option once two intakes run each year.
