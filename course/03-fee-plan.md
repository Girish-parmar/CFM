# Fee Plan — ₹10,00,000.00 All-Inclusive

One price, published in full: **₹10,00,000.00 including 18% GST**. Every table marked
*generated* is computed from [`course.yaml`](course.yaml) by the route manager, so the split,
the instalments and the unit economics always add up to the paisa.

> **Planning decision to confirm.** This plan treats ₹10,00,000.00 as the *all-inclusive* amount
> (fee ₹8,47,457.63 + GST ₹1,52,542.37). If the intended price is ₹10,00,000 *plus* GST
> (₹11,80,000 payable), change `fee.total_all_inclusive` to `1180000.00` in the manifest and run
> `python tools/route_manager.py render`; every table below updates, and the sensitivity table
> already shows the economics at nearby prices.

## 1. The fee (generated)

<!-- BEGIN GENERATED: fee-breakup -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
| Item | Amount |
|---|---:|
| Programme fee (before GST) | ₹8,47,457.63 |
| GST @ 18% | ₹1,52,542.37 |
| **Total payable (all-inclusive)** | **₹10,00,000.00** |
| Application fee (adjusted against the first payment) | ₹2,500.00 |
| Per guided hour, all-inclusive | ₹1,358.70 |
<!-- END GENERATED: fee-breakup -->

## 2. What the fee includes (generated)

<!-- BEGIN GENERATED: inclusions -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
**Included**

- 736 guided hours: live classes, lab clinics, office hours, reviews, bootcamps, capstone studio and 1:1 mentoring
- Three 3-day in-person bootcamps with venue, trading-floor simulation, stay (3 nights each, twin sharing) and meals
- 24 hours of 1:1 mentoring with a practitioner mentor
- Licensed NSE cash and F&O historical data (education licence) for the programme and 6 months after
- Cloud lab, GPU hours for M20–M23, and a static-IP server for capstone paper trading
- Vouchers for NISM Series VIII (Equity Derivatives) and Series XV (Research Analyst)
- Digital access to the core texts or equivalent reading packs
- Career services, employer connect, Demo Day with an industry jury
- Two years of alumni access to recordings, updated labs and alumni events

**Not included**

- Travel to and from bootcamp venues
- A laptop (minimum 8 GB RAM, 4 cores; 16 GB recommended)
- Personal broker accounts and any live trading capital; live trading is outside the programme
- Re-sit fees for external exams beyond the included vouchers
<!-- END GENERATED: inclusions -->

## 3. Where each rupee goes (generated)

Transparency about cost is part of the promise in the [mission](00-mission.md).

<!-- BEGIN GENERATED: fee-allocation -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
| Where one learner's fee goes (cohort of 36) | Amount | Share |
|---|---:|---:|
| GST (paid to the government) | ₹1,52,542 | 15.3% |
| Scholarships | ₹84,746 | 8.5% |
| Marketing and admissions | ₹1,01,695 | 10.2% |
| Payment processing | ₹15,000 | 1.5% |
| Direct per-learner costs | ₹1,54,000 | 15.4% |
| Share of fixed delivery costs (÷ 36) | ₹3,87,444 | 38.7% |
| Surplus (reinvestment and risk buffer) | ₹1,04,573 | 10.5% |
| **Total** | **₹10,00,000** | **100%** |

Amounts are rounded to the rupee. Scholarships are a cohort average: a learner without a scholarship funds part of another's.
<!-- END GENERATED: fee-allocation -->

## 4. Payment plans (generated)

Every plan totals the same ₹10,00,000.00; there is no cheaper "pay in full" price, so no learner
pays more for needing instalments. A GST invoice is issued for every payment.

<!-- BEGIN GENERATED: payment-plans -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
**Plan A — Pay in full.** One payment on accepting the offer.

| When | Fee | GST | Total |
|---|---:|---:|---:|
| On accepting the offer | ₹8,47,457.63 | ₹1,52,542.37 | ₹10,00,000.00 |

**Plan B — Four instalments (no interest).** Each instalment falls due before a term starts; a missed instalment pauses LMS access after 15 days.

| When | Fee | GST | Total |
|---|---:|---:|---:|
| On accepting the offer (seat booking) | ₹84,745.76 | ₹15,254.24 | ₹1,00,000.00 |
| Before Week 1 (Term 1) | ₹2,54,237.29 | ₹45,762.71 | ₹3,00,000.00 |
| Before Week 20 (Term 3) | ₹2,54,237.29 | ₹45,762.71 | ₹3,00,000.00 |
| Before Week 39 (Term 5) | ₹2,54,237.29 | ₹45,762.71 | ₹3,00,000.00 |
| **Total** | **₹8,47,457.63** | **₹1,52,542.37** | **₹10,00,000.00** |

**Plan C — Education loan through a partner bank or NBFC.** The lender pays the institute in full; the learner repays the lender over 12–60 months at the lender's rate. The institute does not subsidise interest.

| When | Fee | GST | Total |
|---|---:|---:|---:|
| Disbursed by the lender before Week 1 | ₹8,47,457.63 | ₹1,52,542.37 | ₹10,00,000.00 |

**Plan D — Employer sponsored.** Invoiced to the employer with the institute's GSTIN; a GST-registered employer may be able to claim input tax credit (confirm with its tax adviser).

| When | Fee | GST | Total |
|---|---:|---:|---:|
| On accepting the offer | ₹8,47,457.63 | ₹1,52,542.37 | ₹10,00,000.00 |
<!-- END GENERATED: payment-plans -->

## 5. Scholarships (generated)

<!-- BEGIN GENERATED: scholarships -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
| Scholarship | Benefit | Criteria |
|---|---|---|
| Need-based | up to 50% of the fee before GST (₹4,23,729) | Household income below the published threshold; documents verified |
| Merit | up to 25% of the fee before GST (₹2,11,864) | Top 10% in the admission test and interview |
| Women in quantitative finance | up to 25% of the fee before GST (₹2,11,864) | Women applicants who meet the admission standard |
| Armed forces | up to 20% of the fee before GST (₹1,69,492) | Veterans and dependants of serving personnel |

One scholarship per learner. Total scholarships are capped at 10% of the cohort's fee revenue before GST. GST is charged on the fee after the scholarship.
<!-- END GENERATED: scholarships -->

**Process.** Applications with the admission form; decisions by a panel of the programme director,
a faculty member and the programme manager, before offers are issued; need-based awards verified
from documents; merit awards from the admission test and interview only. A scholarship reduces the
fee before GST, and GST is charged on the reduced fee (for example, a 25% merit scholarship makes
the total payable ₹7,50,000.00).

## 6. Refunds and deferrals (generated)

<!-- BEGIN GENERATED: refund-policy -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
| When the learner withdraws | Refund |
|---|---|
| Within 14 days of paying the seat booking, and before Week 1 | 100% of all amounts paid |
| More than 14 days after seat booking, and at least 15 days before Week 1 | All amounts paid minus ₹50,000 |
| Less than 15 days before Week 1, up to the end of Week 2 | 50% of all amounts paid |
| After Week 2 | No refund of instalments already due; later instalments are not charged. One free deferral to the next cohort |
| The institute cancels the cohort or postpones it by more than 30 days | 100% of all amounts paid, or a free move to the next cohort |
<!-- END GENERATED: refund-policy -->

Refunds are paid within 30 days to the original payment method, with a GST credit note for the
refunded fee. Where a loan partner paid the fee, the refund goes to the lender first. The
application fee is not refundable. Medical or family emergencies are handled case by case by the
programme director and may convert a withdrawal into a free deferral.

## 7. Why ₹10,00,000 — and the case against it

**The case for.**

- **Hours.** 736 guided hours, about ₹1,359 per hour all-inclusive (₹1,151 before GST). Compare the per-hour cost of any alternative you consider, counting only live, small-group hours with practitioners.
- **Depth.** Markets and macro, Python and data engineering, statistics, derivatives with second-order Greeks, strategy research, risk and portfolios, microstructure, trading systems and monitoring, and the full AI stack — areas normally sold as five or six separate programmes.
- **Things learners cannot buy alone.** Licensed NSE data, a static-IP paper-trading server, GPU hours, a trading-floor simulation, three residential bootcamps and an industry jury.
- **Evidence of skill.** Every graduate leaves with a public portfolio, a pre-registered and reproducible capstone and a four-week paper-trading record reviewed by practitioners.

**The case against** (from the [devil's-advocate audit](../audit/2026-09-devils-advocate-review.md)).

- ₹10 lakh sits above most Indian algo-trading certificates. Learners will compare it with self-paced courses at a tenth of the price; the programme must win on outcomes, not content lists.
- Break-even needs about 28 learners at this price. A weak first intake is a real financial risk (see the sensitivity table).
- The six labs the audit found planned have now shipped (v2.2.0), but they are new: a premium price makes any rough edge in them more visible, so they need a first cohort's feedback before the price rests on them.
- Part of the value (bootcamp stay, data licences, GPU hours) is only valuable if learners use it; unused inclusions feel like overpricing.

**Mitigations.** Publish audited outcomes with their base and period; review the new labs with
the first intake before charging the full price to a second; offer corporate cohorts (GST input credit makes the
effective cost ₹8,47,457.63 for many employers); keep the scholarship budget at 10% to protect
access.

## 8. Unit economics (generated)

Indicative planning numbers per cohort. Every cost line is an assumption to replace with quotes.

<!-- BEGIN GENERATED: unit-economics -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
| Per cohort | 30 learners | 36 learners | 40 learners |
|---|---:|---:|---:|
| Fee before GST | ₹2,54,23,729 | ₹3,05,08,475 | ₹3,38,98,305 |
| Scholarships | −₹25,42,373 | −₹30,50,847 | −₹33,89,831 |
| Marketing and admissions | −₹30,50,847 | −₹36,61,017 | −₹40,67,797 |
| Payment processing | −₹4,50,000 | −₹5,40,000 | −₹6,00,000 |
| Direct per-learner costs | −₹46,20,000 | −₹55,44,000 | −₹61,60,000 |
| **Contribution** | **₹1,47,60,509** | **₹1,77,12,610** | **₹1,96,80,678** |
| Fixed delivery costs | −₹1,39,48,000 | −₹1,39,48,000 | −₹1,39,48,000 |
| **Surplus** | **₹8,12,509** (3.2%) | **₹37,64,610** (12.3%) | **₹57,32,678** (16.9%) |

Contribution per learner: **₹4,92,017**. Fixed costs: **₹1,39,48,000** per cohort. Break-even: **28.3 learners** (the cohort runs only with 30 or more).
<!-- END GENERATED: unit-economics -->

### Fixed costs per cohort (generated)

<!-- BEGIN GENERATED: fixed-costs -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
| Fixed cost (per cohort) | Basis | Amount |
|---|---|---:|
| Faculty — module delivery | 528 h × ₹8,000 | ₹42,24,000 |
| Faculty — reviews and term exams | 36 h × ₹6,000 | ₹2,16,000 |
| Faculty — bootcamps | 72 h × ₹10,000 | ₹7,20,000 |
| Capstone supervision | 76 h × ₹8,000 | ₹6,08,000 |
| Industry jury and guest practitioners | 3 juries + 10 guest sessions | ₹3,00,000 |
| Teaching assistants | 3 × 12 months × ₹70,000 | ₹25,20,000 |
| Programme manager and learner success | 12 months × ₹1,20,000 | ₹14,40,000 |
| Career services | 12 months × ₹60,000 | ₹7,20,000 |
| Content refresh and lab QA | annual refresh of 24 modules and 30 labs | ₹10,00,000 |
| LMS, video, code hosting and CI | platform licences | ₹4,00,000 |
| Bootcamp venues and simulation | 3 × ₹2,00,000 | ₹6,00,000 |
| Compliance, legal, audit and insurance | allocation | ₹4,00,000 |
| Administration and overheads | allocation | ₹8,00,000 |
| **Total** |  | **₹1,39,48,000** |
<!-- END GENERATED: fixed-costs -->

### Direct costs per learner (generated)

<!-- BEGIN GENERATED: variable-costs -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
| Direct cost per learner | Amount |
|---|---:|
| Market-data licence (education seat) | ₹35,000 |
| Cloud lab, GPU hours and static-IP server | ₹24,000 |
| Bootcamp stay and meals (9 nights) | ₹36,000 |
| 1:1 mentoring (24 h × ₹2,000) | ₹48,000 |
| NISM vouchers, books and kit | ₹8,000 |
| Exams, proctoring and credential | ₹3,000 |
| **Total per learner** | **₹1,54,000** |
<!-- END GENERATED: variable-costs -->

### Sensitivity: price × cohort size (generated)

Surplus (and margin on fee revenue before GST) for other all-inclusive prices.

<!-- BEGIN GENERATED: price-sensitivity -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
| All-inclusive price | Break-even learners | 24 learners | 30 learners | 36 learners | 40 learners |
|---|---:|---:|---:|---:|---:|
| ₹8,00,000 | 38.4 | −₹52,40,475 (−32%) | −₹30,63,593 (−15%) | −₹8,86,712 (−4%) | ₹5,64,542 (2%) |
| ₹9,00,000 | 32.6 | −₹36,90,034 (−20%) | −₹11,25,542 (−5%) | ₹14,38,949 (5%) | ₹31,48,610 (10%) |
| ₹10,00,000 ← plan | 28.3 | −₹21,39,593 (−11%) | ₹8,12,509 (3%) | ₹37,64,610 (12%) | ₹57,32,678 (17%) |
| ₹11,00,000 | 25.1 | −₹5,89,153 (−3%) | ₹27,50,559 (10%) | ₹60,90,271 (18%) | ₹83,16,746 (22%) |
<!-- END GENERATED: price-sensitivity -->

Reading the table: at ₹10 lakh the programme needs about 28 learners to cover costs and earns a
12% margin at the target cohort of 36. At ₹8 lakh it does not break even even at 36. Two intakes a
year share content-refresh and platform costs, which lowers break-even for the second intake.

## 9. GST, invoicing and accounting notes

- GST at 18% is assumed because a private certificate programme is a taxable commercial training service. If the certificate is awarded jointly with a university as a recognised qualification, the position may differ — confirm with a chartered accountant before publishing prices.
- Issue a GST invoice for every instalment; for employer-sponsored learners, invoice the employer with its GSTIN.
- Bootcamp stay and meals are part of a composite supply of education services at the programme's GST rate; confirm the treatment with the CA.
- Scholarships are discounts shown on the invoice before GST, not refunds.
- Revenue is recognised over the programme period; instalments received in advance are deferred revenue.

## 10. Before publishing prices — checklist

- [ ] Confirm the all-inclusive vs plus-GST decision (see the note at the top).
- [ ] Replace every cost assumption with quotes (faculty, venues, data licences, cloud, loan partner fees).
- [ ] CA sign-off on GST treatment and invoicing.
- [ ] Legal review of the refund policy against consumer-protection rules.
- [ ] Marketing copy checked against [compliance](09-compliance-and-risk-disclosures.md) (no return or placement promises).
- [ ] `python tools/route_manager.py check` passes after the final edit.
