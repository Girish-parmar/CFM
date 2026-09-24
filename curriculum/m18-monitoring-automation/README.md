# M18 · Monitoring and Automation with n8n

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T4 · Risk, Portfolio and Trading Systems |
| Weeks | 37–38 |
| Hours | 24 guided |
| Labs | [18a](lab_18a_n8n_signal_service.py) — Signal service endpoints used by the n8n workflows<br>18b (planned) — Heartbeats, live-vs-backtest drift, alert rules, incident drill |
| Library | `cfmat.automation` |
| Prerequisites | [M17](../m17-trading-platform-compliance/README.md) |
| Committed topics | Monitoring systems, Trading platform structure and infrastructure, Sentiment and news analysis |
| Status | partial |
<!-- END GENERATED: module-header -->

## Why this module

A live strategy fails quietly: a feed freezes, fills drift from the backtest, a position does not
reconcile, a cron job stops. Monitoring turns those into alerts before they become losses, and
automation removes the manual steps where mistakes happen. This module builds live-monitoring
checks and uses n8n to schedule signals, digest news, journal trades and alert humans.

## Learning outcomes

By the end of the module you can:

1. Define the health checks a live strategy needs: heartbeats, data staleness, order-to-fill latency, rejected-order rates, position reconciliation, P&L vs expectation.
2. Detect drift between live (or paper) trading and its backtest: fills, slippage, signal agreement and return distribution.
3. Attribute daily P&L to signals, execution and costs, and set kill-switch triggers from it.
4. Build n8n workflows with schedule and webhook triggers, HTTP requests, code, branching and notifications, connected to the CFMAT signal service.
5. Handle errors, retries and alert fatigue; manage credentials and webhook security.
6. Use n8n AI-agent nodes for tool-calling workflows such as a morning research brief, with guardrails.

## Before you start

- M17 complete; the paper strategy from M17 running on the course VM.
- Docker installed (for self-hosted n8n); read [`n8n/README.md`](../../n8n/README.md).

## Weekly plan

### Week 37 — Live monitoring: health checks, drift, P&L attribution and kill switches

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M17 · 15–60 what to monitor: heartbeats, staleness, latency, rejects, reconciliation, exposure; SLOs for a trading system · 60–70 break · 70–120 drift: live vs backtest fills, slippage, signal agreement, return distribution tests · 120–170 P&L attribution (signal, execution, costs) and kill-switch triggers · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 alert design: severity, routing, deduplication, alert fatigue · 60–70 break · 70–130 workshop: a monitoring dashboard for the M17 paper strategy (heartbeat, staleness, drift, daily risk report from M13) · 130–170 incident drill: stale feed at 11:02 · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 18b (when released) or the exercise pack: staleness and drift detectors on the paper strategy's journal · 100–120 blockers |
| OH · Wed · 60 min | Monitoring design clinic |
| C2 · Thu · 120 min | 0–60 daily P&L attribution report · 60–100 peer review · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 18a · 20–50 "false alarm or real?" alert cards · 50–60 preview |
| Self-study · ~6 h | Google SRE book ch. 6 (monitoring); capstone topic finalisation |

### Week 38 — Automation with n8n: alerts, digests and trade journals

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 n8n fundamentals: self-hosting, nodes, items and expressions, schedule and webhook triggers, HTTP Request and Code nodes, credentials · 60–70 break · 70–120 the three course workflows and the signal service they call (`python -m cfmat.automation.signal_service`) · 120–170 live: import, run and adapt the daily signal alert · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 error workflows, retries, audit logging · 60–70 break · 70–130 AI-agent nodes with tools: a morning brief from the news digest; guardrails, costs and prompt-injection risks · 130–170 security: secrets, webhook authentication, network exposure, request-size limits · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 Lab 18a: every signal-service endpoint; import the workflows · 100–120 review |
| OH · Wed · 60 min | Capstone topic approval deadline (Week 38) |
| C2 · Thu · 120 min | 0–60 connect Telegram or Slack; an error workflow · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 18b · 20–50 peer review of the assignment · 50–60 briefing for Term 5 and the capstone track |
| Self-study · ~6 h | n8n docs; finish the assignment |

## Labs

**Lab 18a — the signal service used by the n8n workflows** (`lab_18a_n8n_signal_service.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Daily signal alert | Call `/signal` for a watchlist | Crossover flips produce an action |
| 2. News sentiment digest | Call `/sentiment` on headlines | Scores and average returned |
| 3. Trade journal | POST fills to `/journal`; read them back | Bad rows rejected by the schema |
| 4. In n8n | Import the three workflows | Workflows run against the local service |

**Lab 18b — live monitoring** (`lab_18b_live_monitoring.py`) · *planned*

| Section | Content | Library support needed |
|---|---|---|
| 1. Heartbeats and staleness | Detect a frozen feed and a dead process from timestamps | `automation.monitoring.staleness`, `heartbeat_gaps` |
| 2. Drift | Live vs backtest: slippage, signal agreement, KS test on returns | `automation.monitoring.drift_report` |
| 3. P&L attribution | Signal vs execution vs costs per day | `automation.monitoring.pnl_attribution` |
| 4. Alert rules | Severity, dedupe, routing to the n8n webhook | `automation.monitoring.AlertRule` |

Acceptance: planted incidents detected with no alerts on a clean day; runs offline in under 15 s;
tests in `tests/test_automation.py`.

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 18a, 18b | quizzes (10%) | Fri W37, W38 | Monitoring and automation |
| Labs 18a (+ 18b when released) | labs (20%) | Sun W38 | Runs; workflows imported |
| Assignment: monitoring and automation for your capstone | assignments (15%) | Sun W39 | An error workflow for all CFMAT workflows, a new workflow of your design (for example an end-of-day P&L summary from the journal), and a monitoring checklist with thresholds for your capstone strategy. Rubric: reliability 35, usefulness 35, security 30 |

## Common mistakes

- Alerting on everything → alert fatigue; severity and dedupe rules.
- Exposing the signal service or n8n to the internet without auth → bind to localhost or a private network; the service limits request bodies to 1 MB and has no authentication by design.
- Letting an AI agent act without a human in the loop → agents draft; humans decide.
- Monitoring P&L only → by the time P&L alarms, the cause is hours old.

## Readings

- Beyer et al., *Site Reliability Engineering*, ch. 6 ("Monitoring Distributed Systems").
- n8n documentation: workflows, error workflows, credentials, AI agents.
- López de Prado, *Advances in Financial Machine Learning*, ch. on backtest vs live discrepancies (selected).

## Instructor notes

- Owner: NLP/LLM and automation lead with the risk and execution lead for Week 37.
- The n8n workflows are validated in real n8n (ids `CfmatSignalAlrt1`, `CfmatNewsDigest2`, `CfmatTradeJrnl03`); re-import them on the current n8n version before each cohort.
- Lab 18b is planned; until it ships, C1 W37 uses the exercise pack. See the [audit](../../audit/2026-09-devils-advocate-review.md).
- Capstone topics are approved this week; OH W38 is reserved for that.
