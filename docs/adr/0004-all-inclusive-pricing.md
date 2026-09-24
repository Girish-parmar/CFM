# ADR 0004 — One all-inclusive price for every payment plan

**Status:** accepted (v2.0.0); the all-inclusive vs plus-GST choice awaits the owner's confirmation

## Context

Version 1 showed ₹4,25,000 + GST = ₹5,01,500, but a pay-in-full discount made the "real" price
₹4,72,000 for some learners; learners who needed instalments paid more.

## Decision

- The programme fee is **₹10,00,000.00 including 18% GST** (fee ₹8,47,457.63 + GST ₹1,52,542.37), stored as `fee.total_all_inclusive` in the manifest.
- Every payment plan totals exactly that amount; concessions come only from published scholarships (capped at 10% of fee revenue).
- The GST split of every instalment is computed to the paisa by the route manager.

## Consequences

- One number in all marketing; no penalty for needing instalments.
- To price at ₹10,00,000 *plus* GST instead, set `fee.total_all_inclusive: 1180000.00`; every table regenerates.
- Unit economics and a price × cohort-size sensitivity table are generated from the same manifest.
