# Operations Runbook

How the programme office runs a cohort. Owners: programme manager (PM), programme director (PD),
module owners (MO), teaching assistants (TA), career services lead (CS).

## Cohort lifecycle

| When | Activity | Owner | Done when |
|---|---|---|---|
| T − 20 weeks | Open applications; publish fee plan and calendar generated from the manifest | PM | `route_manager.py check` passes on the published version |
| T − 16 to −8 weeks | Admission tests and interviews; scholarship panel; offers | PM, PD | Offers within 10 days of interview |
| T − 8 weeks | Cohort go/no-go against minimum-to-run size | PD | Decision recorded; refunds if cancelled |
| T − 6 weeks | Faculty contracts, mentors matched, TAs hired; venues and data licences confirmed | PM | Signed |
| T − 5 weeks | Module owners refresh guides (regulation, charges, lot sizes, APIs); planned labs reviewed | MO | Changes merged; CI green |
| T − 4 weeks (Week −3) | Pre-work starts; LMS, GitHub Classroom and Slack live | PM, TA | All learners pass `lab_00a` by Week −2 |
| Week 0 | Entry assessment; test-out quizzes; route confirmation | PM, TA | Results recorded |
| Weeks 1–52 | Weekly operations (below) | All | – |
| Weeks 11, 27, 47 | Exams and bootcamps | PD, PM | Bootcamp checklist complete |
| Week 38 | Capstone topics approved | Mentors, PD | All topics approved |
| Week 52 | Demo Day and graduation | PD, CS | Jury scores in |
| Week 52 + 2 | Grades and certificates | PM | Credential IDs issued |
| Week 52 + 4 | Cohort retrospective; audit update; manifest version bump | PD | Retro notes and audit merged |

## Weekly operations checklist

| Day | Task | Owner |
|---|---|---|
| Monday | Publish the week's plan from the module guide (`route_manager.py week N`); check lab CI is green | PM, TA |
| Tuesday | C1 clinic; TA notes on blockers posted by 22:00 | TA |
| Wednesday | Office hours; attendance export | MO, PM |
| Thursday | C2 clinic; peer review pairings | TA |
| Friday | Quiz opens; peer review; at-risk learner list (missed ≥ 2 sessions or 2 submissions) | TA, PM |
| Saturday | L1; exit-ticket summary to the module owner | MO |
| Sunday | L2; lab and assignment deadlines 23:59 | MO |
| Weekly | Feedback form for the module week; issues triaged | PM |

## Service levels

| Item | Target |
|---|---|
| Recordings published | Within 24 hours |
| Forum questions answered | Within 12 hours on weekdays |
| Lab and assignment feedback | Within 7 days |
| Exam results | Within 14 days |
| Fee and invoice queries | Within 1 working day |
| Lab-infrastructure incidents | Acknowledged within 2 hours during programme hours |

## Learner support and escalation

1. At-risk learners (Friday list) get a TA check-in within 48 hours.
2. Two consecutive weeks at risk → mentor conversation and a catch-up plan.
3. Four weeks at risk → PD meeting; options: catch-up plan, deferral to the next cohort (free, once), or withdrawal under the [refund policy](03-fee-plan.md).
4. Academic-integrity concerns go to the PD within 24 hours; the learner is heard before any decision.
5. Complaints about faculty go to the PD; complaints about the PD go to the advisory board.

## Content change process

1. Change the module guide, lab or library on a branch; keep `course/course.yaml` in step.
2. Run `make check` (lint, unit tests, manifest check) and `make labs` for changed labs.
3. Open a pull request using the template; a second module owner reviews.
4. For structural changes (weeks, hours, fees, labs), run `python tools/route_manager.py render` and include the regenerated docs in the same pull request.
5. Record user-visible changes in [CHANGELOG](../CHANGELOG.md).

## Bootcamp checklist

- Venue, rooms (twin sharing), meals and dietary requirements confirmed 4 weeks ahead.
- Simulation environment tested end to end 1 week ahead (Strategy Studio images, simulated exchange, RMS dashboards).
- Travel guidance sent; emergency contacts collected; code of conduct shared.
- Exam papers moderated and printed (or proctoring configured) 1 week ahead.

## Quality metrics reported after each cohort

Completion rate, module feedback scores, lab CI status, capstone reproducibility pass rate,
mentor utilisation, bootcamp attendance, incident log, and the status of every open item in the
[audit](../audit/2026-09-devils-advocate-review.md). See the targets in the [mission](00-mission.md).
