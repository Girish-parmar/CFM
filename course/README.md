# CFMAT Course Handbook

The handbook for the **Certificate in Financial Market and Algorithmic Trading**. Everything
structural — modules, weeks, hours, labs, fees, routes and assessment weights — comes from one
file, [`course.yaml`](course.yaml). The tables marked *generated* are written by the route
manager, so they always agree with the manifest and with the repository.

<!-- BEGIN GENERATED: program-summary -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Duration | 52 weeks + 4 weeks of self-paced pre-work |
| Format | Hybrid — live online weekend classes, weekday lab clinics, three 3-day in-person bootcamps |
| Guided hours | 736 (plus 40 h pre-work and about 6 h/week self-study) |
| Structure | 6 terms, 24 modules + pre-work, 36 labs (35 ready) |
| Cohort | target 36, maximum 40; intakes January and July |
| Programme fee | **₹10,00,000.00 all-inclusive** = ₹8,47,457.63 + GST 18% ₹1,52,542.37 |
| Fee per guided hour | ₹1,358.70 (₹1,151.44 before GST) |
<!-- END GENERATED: program-summary -->

## Where to find what

| Document | What it answers |
|---|---|
| [00 · Mission, vision and values](00-mission.md) | Why the programme exists, what it promises and what it will never do |
| [01 · Programme overview](01-program-overview.md) | Who it is for, outcomes, structure, format |
| [02 · Curriculum map](02-curriculum-map.md) | All modules and labs, topic coverage, prerequisites |
| [03 · Fee plan (₹10,00,000.00)](03-fee-plan.md) | Fee split, what it includes, payment plans, scholarships, refunds, unit economics |
| [04 · Academic calendar](04-academic-calendar.md) | Weekly rhythm and the 52-week calendar |
| [05 · Assessment and certification](05-assessment-and-certification.md) | Weights, rubrics, grade bands, integrity and AI use |
| [06 · Capstone](06-capstone.md) | Timeline, project options, rules, jury |
| [07 · Faculty and infrastructure](07-faculty-and-infrastructure.md) | Faculty model, lab environment, support |
| [08 · Admissions and careers](08-admissions-and-careers.md) | Eligibility, selection, timeline, career services |
| [09 · Compliance and risk disclosures](09-compliance-and-risk-disclosures.md) | SEBI rules, advertising, data, privacy, disclaimers |
| [10 · Learning routes](10-learning-routes.md) | Six learner personas and how to follow a route |
| [11 · Operations runbook](11-operations-runbook.md) | Running a cohort week by week |
| [12 · Setup and run guide](12-setup-and-run-guide.md) | Install Python, the environment and the library; run the labs in order; optional extras |
| [Module guides](../curriculum/README.md) | Micro-level plans for every module and lab |
| [Devil's-advocate audit](../audit/2026-09-devils-advocate-review.md) | What was missing or wrong, what we fixed, what is still open |

## Guided hours (generated)

<!-- BEGIN GENERATED: hours -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
| Component | Hours |
|---|---:|
| Module weeks (44 × 12 h) | 528 |
| Review and exam weeks | 36 |
| In-person bootcamps | 72 |
| Capstone (studio weeks + track) | 76 |
| 1:1 mentoring | 24 |
| **Total guided hours** | **736** |
<!-- END GENERATED: hours -->

## Using the route manager

```bash
python tools/route_manager.py check              # validate the manifest against the repository
python tools/route_manager.py render             # regenerate the tables in these documents
python tools/route_manager.py status             # modules and labs, ready vs planned
python tools/route_manager.py week 25            # what happens in Week 25
python tools/route_manager.py route derivatives-trader
python tools/route_manager.py coverage           # the 15 committed topics and where they are taught
python tools/route_manager.py fees               # fee split, plans, unit economics
```

To change the programme: edit `course.yaml`, run `render`, then `check`, and commit both. CI
fails if a generated table is stale or the manifest disagrees with the repository.
