# M24 · Capstone, Paper Trading, Ethics and Career

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T6 · Capstone and Career |
| Weeks | 48–52 |
| Hours | 60 guided |
| Labs | [24a](lab_24a_capstone_template.py) — Pre-registration to paper-trading report: a reproducible capstone skeleton |
| Library | `cfmat` |
| Prerequisites | [M18](../m18-monitoring-automation/README.md), [M23](../m23-advanced-strategies-hpo/README.md) |
| Committed topics | Monitoring systems, Risk management and position sizing |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

The capstone is where learners show they can do the whole job: form a hypothesis, pre-register
it, test it honestly, control its risk, run it on paper under limits for four weeks, reconcile
live with backtest, and defend it to practitioners. Profit is not graded; discipline is. The
same five weeks cover trading psychology, professional ethics and the career studio.

## Learning outcomes

By the end of the module you can:

1. Carry a pre-registered research question through data, testing, risk and live paper trading, with a reproducible repository.
2. Run a strategy for four weeks under RMS limits and a kill switch, keep a daily journal, and reconcile paper results with the backtest.
3. Recognise behavioural traps (overconfidence, loss aversion, revenge trading) and use process controls against them.
4. Apply professional ethics and market-abuse rules (insider trading, front-running, spoofing, confidentiality).
5. Present research to an industry jury and to employers, including its limits and failure modes.

## Before you start

- Capstone track milestones met: topic approved (W38), pre-registration committed (W40), midpoint review passed (W44).
- Paper-trading server provisioned with a static IP; RMS limits configured and tested (M17); monitoring and alerts live (M18).

## Weekly plan

The capstone track runs 2 h a week in Weeks 39–46 (proposal clinics, pre-registration review,
midpoint review). Weeks 48–52 are full capstone weeks on the normal rhythm.

### Week 48 — Final validation, deployment and paper-trading launch

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–20 cohort stand-up · 20–90 research reviews in panels of 4 (walk-forward, costs, DSR with the pre-registered trial count) · 90–100 break · 100–170 go/no-go checklist for paper trading · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–60 trading psychology: process over outcome; pre-commitment; journals · 60–70 break · 70–150 deployment clinic: strategy, RMS, journal, monitoring, n8n alerts · 150–180 launch: paper trading starts Monday |
| C1 · Tue · 120 min | Incident drill 1 (feed stall); journal review |
| OH · Wed · 60 min | Mentor 1:1 slots |
| C2 · Thu · 120 min | Code review clinic; reproducibility check (one command reproduces the main results) |
| QP · Fri · 60 min | Weekly journal submission; peer reading |
| Self-study · ~6 h | Report outline; Douglas ch. 1–5 |

### Week 49 — Paper trading, monitoring and incident drills

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–60 paper-trading stand-ups (3 min each) · 60–70 break · 70–150 ethics: insider trading, front-running, spoofing, confidentiality, conflicts; case discussions · 150–180 exit ticket |
| L2 · Sun · 180 min | 0–90 career studio: CV, LinkedIn and GitHub portfolio reviews · 90–100 break · 100–180 quant interview practice: probability, statistics and coding puzzles |
| C1 · Tue · 120 min | Incident drill 2 (runaway orders → kill switch) |
| OH · Wed · 60 min | Mentor 1:1 slots |
| C2 · Thu · 120 min | Reconciliation clinic: paper vs backtest fills, slippage, signal agreement |
| QP · Fri · 60 min | Weekly journal submission |
| Self-study · ~6 h | Report draft: method and data sections |

### Week 50 — Paper trading, reconciliation and risk review

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–60 stand-ups · 60–70 break · 70–170 risk committee role-play: each learner defends limits, drawdown and exposures · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–90 employer connect session · 90–100 break · 100–180 mock interviews (panels of practitioners) |
| C1 · Tue · 120 min | Report writing clinic: results, limitations, what would change your mind |
| OH · Wed · 60 min | Mentor 1:1 slots |
| C2 · Thu · 120 min | Peer review of draft reports (two reviewers each) |
| QP · Fri · 60 min | Weekly journal submission |
| Self-study · ~6 h | Report draft: results and limitations |

### Week 51 — Report, peer review, mock jury and career studio

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–60 paper-trading wrap-up and final reconciliation · 60–70 break · 70–180 mock jury (15-minute talk + 10-minute questions, recorded) |
| L2 · Sun · 180 min | 0–90 feedback on mock juries · 90–100 break · 100–180 career studio: salary negotiation, offers, next 12 months of learning |
| C1 · Tue · 120 min | Rehearsals |
| OH · Wed · 60 min | Final mentor 1:1 |
| C2 · Thu · 120 min | Repository freeze check: tests pass, README reproduces results |
| QP · Fri · 60 min | Final report and repository submitted (23:59) |
| Self-study · ~6 h | Slides and rehearsal |

### Week 52 — Demo Day and graduation

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · full day | Demo Day: 15-minute presentation + 10-minute viva per learner before an industry jury (three members) |
| L2 · Sun · 180 min | Graduation, hiring-partner showcase, alumni onboarding |
| Rest of week | Jury scores consolidated (median of three); grades released within 10 days |

## Labs

**Lab 24a — capstone template** (`lab_24a_capstone_template.py`)

A reproducible skeleton that runs end to end on synthetic data and that learners copy into their
capstone repository as `src/pipeline.py`. Hand it out in Week 39 with the capstone track, so the
Week 40 pre-registration is written in its format. Edit `CONFIG`, point `data_csv` at your data,
and one command reproduces every table.

| Section | You do | What good looks like |
|---|---|---|
| 1. Pre-registration | Fill `CONFIG`; generate and check `PREREGISTRATION.md` | Every field present; hold-out after research; grid within the trial budget; committed before testing |
| 2. Data | Load, check quality, split research and hold-out | Problems listed and explained; the hold-out untouched until section 5 |
| 3. Strategy and costs | A Strategy Creator spec; Indian charges for a typical order | Cost per side derived from the cost model, not guessed |
| 4. Walk-forward and DSR | Re-optimise yearly; charge the DSR for the trial budget | Out-of-sample Sharpe reported next to the in-sample best |
| 5. One look at the hold-out | Freeze parameters; run once; state the verdict | The pre-registered criterion decides MET or NOT MET |
| 6. Paper trading | OMS with RMS limits, journal and monitoring; decisions made only from the previous close | Paper tracks the backtest; the gap is measured and explained |
| 7. Tests | No look-ahead, risk limits, costs | All pass, in the lab and as `pytest` in the capstone folder |
| 8. Report and folder | Tables to `report/`; README, PREREGISTRATION, tests, limits | `pytest tests` passes in the copied folder |

On the synthetic data the criterion is not met (the deflated Sharpe is below 95%): the template
shows how to report a negative result honestly.

**Capstone repository layout**

```
capstone/
├── README.md              # question, how to reproduce, results summary
├── PREREGISTRATION.md     # committed in Week 40, before any testing
├── data/                  # scripts only; licensed raw data is never committed
├── src/                   # features, signals, strategy specs, risk
├── tests/                 # pytest: no look-ahead, risk limits, cost model
├── notebooks/             # exploration (not the source of truth)
├── paper_trading/         # config, RMS limits, daily journal exports
└── report/                # final report (PDF) and slides
```

## Assessment

The capstone is 35% of the final grade. The rubric, timeline, project options and rules are in
[course/06-capstone.md](../../course/06-capstone.md); weights are generated from the manifest in
[course/05-assessment-and-certification.md](../../course/05-assessment-and-certification.md).

| Milestone | Week | Gate |
|---|---|---|
| Topic approved | 38 | Mentor sign-off |
| Pre-registration committed | 40 | Hypothesis, data, rules, parameter grid, trial list, success criteria in Git before testing |
| Midpoint review | 44 | Data pipeline and first walk-forward results |
| Research review and go/no-go | 48 | Costs, DSR, stress tests, RMS limits |
| Paper trading | 48–51 | Four weeks, daily journal, reconciliation |
| Final report and repository | 51 | Reproducible with one command |
| Demo Day | 52 | Jury viva |

## Common mistakes

- Changing the hypothesis after seeing results without saying so → pre-registration in Git; deviations must be declared.
- Paper-trading P&L as the headline → graded on discipline and reconciliation, not profit.
- A repository that only runs on the learner's laptop → reproducibility check in W49 and W51.
- Presenting a capstone strategy to others as advice → compliance rules in the ethics session.

## Readings

- Mark Douglas, *Trading in the Zone*.
- Daniel Kahneman, *Thinking, Fast and Slow* — chapters on overconfidence and loss aversion.
- SEBI (Prohibition of Insider Trading) Regulations, 2015 and SEBI (PFUTP) Regulations, 2003 — summaries provided.
- Gregory Zuckerman, *The Man Who Solved the Market*.

## Instructor notes

- Owner: programme director; jury of a practitioner, a risk or compliance professional and a faculty member.
- Paper trading only. Learners who trade their own money do so outside the programme, at their own risk.
- Lab 24a is the starting point for every capstone repository. Check in Week 40 that learners' pre-registrations pass its `check_preregistration` and are committed before their first backtest.
