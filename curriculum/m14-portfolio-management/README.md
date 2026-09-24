# M14 · Portfolio Management and Strategy Allocation

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T4 · Risk, Portfolio and Trading Systems |
| Weeks | 30–31 |
| Hours | 24 guided |
| Labs | [14a](lab_14a_portfolio_construction.py) — Optimisers out of sample, Ledoit–Wolf, frontier, strategy sleeves |
| Library | `cfmat.portfolio.construction` |
| Prerequisites | [M13](../m13-risk-position-sizing/README.md) |
| Committed topics | Portfolio management methods |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

Most professional money is run as a portfolio — of stocks, of factors, or of strategies. The
textbook optimiser is unstable because its inputs are noisy; practical portfolio construction is
the art of using less information more robustly. This module compares optimisers out of sample,
shrinks covariance matrices, and allocates capital across strategy sleeves with weights that use
only the past.

## Learning outcomes

By the end of the module you can:

1. Build mean–variance, minimum-variance, maximum-Sharpe and risk-parity portfolios, and explain why max-Sharpe weights are unstable.
2. Reduce estimation error with Ledoit–Wolf shrinkage and constraints.
3. Build Hierarchical Risk Parity portfolios and explain how clustering avoids matrix inversion.
4. Compare methods out of sample with a rolling estimate-then-hold loop, including turnover.
5. Allocate across strategy sleeves with rolling equal, inverse-volatility, risk-parity and HRP weights, without look-ahead.
6. Explain risk budgeting, factor risk models (intuition) and capacity.

## Before you start

- M13 complete; linear algebra refresher (M04 Week 8 L2).
- Read López de Prado (2016) on HRP, sections 1–3.

## Weekly plan

### Week 30 — Mean–variance, estimation error, shrinkage and risk parity

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M13 · 15–60 Markowitz: the efficient frontier, the tangency portfolio, constraints · 60–70 break · 70–120 estimation error: why expected returns are the weak link; resampling demo · 120–170 minimum variance and Ledoit–Wolf shrinkage; risk parity and risk contributions · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–70 workshop: Lab 14a §1 — five optimisers, rolling out of sample, with turnover · 70–80 break · 80–140 Lab 14a §2 — the frontier and the instability of max-Sharpe weights across two halves · 140–170 discussion: what would you actually run with client money? · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 14a §1–§2 · 100–120 blockers |
| OH · Wed · 60 min | Portfolio Q&A |
| C2 · Thu · 120 min | 0–60 exercise: single-name caps and turnover costs · 60–100 peer review · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 14a · 20–50 "which portfolio is this?" weight cards · 50–60 preview |
| Self-study · ~6 h | Grinold and Kahn ch. on risk; Ledoit and Wolf (2004) |

### Week 31 — Hierarchical risk parity and allocating across strategies

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 HRP: correlation distance, clustering, quasi-diagonalisation, recursive bisection · 60–70 break · 70–120 factor risk models (intuition): systematic vs specific risk, exposures, risk attribution · 120–170 portfolios of strategies: correlation, risk budgets, capacity and decay · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–70 workshop: Lab 14a §3 — trend, reversal and pairs sleeves combined with rolling weights · 70–80 break · 80–140 sleeves that switch on and off: zero-variance windows and why the allocator must handle them · 140–170 guest: a multi-strategy PM on allocation committees · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 14a §3 and exercise 3 (a near-duplicate sleeve) · 100–120 review |
| OH · Wed · 60 min | Assignment clinic |
| C2 · Thu · 120 min | 0–60 allocation with costs on rebalancing · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 14b · 20–50 peer review of assignment drafts · 50–60 preview of M15 |
| Self-study · ~6 h | López de Prado (2016); assignment |

## Labs

**Lab 14a — portfolio construction and allocation across strategies** (`lab_14a_portfolio_construction.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Optimisers out of sample | Equal weight, min variance (sample and Ledoit–Wolf), max Sharpe, risk parity, HRP; turnover | Max Sharpe worst out of sample; simple methods competitive |
| 2. Frontier and instability | Max-Sharpe weights on two halves | Most of the portfolio changes between halves |
| 3. Strategy sleeves | Rolling allocation of three sleeves by four methods | Combinations beat most single sleeves on Sharpe; HRP and inverse-vol near the top |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 14a, 14b | quizzes (10%) | Fri W30, W31 | Concepts and numericals |
| Lab 14a | labs (20%) | Sun W31 | Runs; comparisons explained |
| Assignment: allocate your strategies | assignments (15%) | Sun W32 | Combine at least three strategy sleeves (from M10–M12 work) with two allocation rules, costs on rebalancing and a comparison with the best single sleeve. Rubric: design 30, no look-ahead 30, analysis 25, clarity 15 |

## Common mistakes

- Estimating weights on the full sample and reporting their performance → rolling estimate-then-hold only.
- Trusting max-Sharpe weights → the two-halves test.
- Allocators that crash or give weight to inactive sleeves → `rolling_allocation` gives zero weight to zero-variance sleeves; test yours the same way.
- Ignoring turnover of the allocation itself → report it.

## Readings

- Grinold and Kahn, *Active Portfolio Management*, ch. 2–4.
- Ledoit and Wolf (2004), "Honey, I Shrunk the Sample Covariance Matrix".
- López de Prado (2016), "Building Diversified Portfolios that Outperform Out of Sample".
- Maillard, Roncalli and Teïletche (2010), "The Properties of Equally Weighted Risk Contribution Portfolios".

## Instructor notes

- Owner: risk and execution lead.
- The sleeves in §3 use only M10 strategies to avoid forward references; M23 revisits allocation with Kalman, GARCH and meta-labelled sleeves.
- A good discussion prompt: "the equal-weight portfolio is a very strong baseline — why?"
