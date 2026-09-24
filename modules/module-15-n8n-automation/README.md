# Module 15 — Automation with n8n and AI Agents

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 4 · AI and Automation | 33 | 10 (2 live × 3 h + 2 clinics × 2 h) | [`lab15_n8n_automation.py`](../../labs/lab15_n8n_automation.py) and [`n8n/`](../../n8n) |

## Learning outcomes

1. Explain workflow automation and where it fits in a trading research and operations stack.
2. Build n8n workflows with triggers (schedule, webhook), HTTP requests, code, branching and notifications.
3. Connect n8n to a Python service (the CFMAT signal service) and to messaging (Telegram or Slack).
4. Handle errors, retries and monitoring; manage credentials safely.
5. Use n8n AI agent nodes for tool-calling workflows such as a research brief.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | n8n fundamentals (Sat, W33) | Self-hosting with Docker; nodes, items and expressions; schedule and webhook triggers; HTTP Request and Code nodes; credentials; the three course workflows |
| L2 | Operations and agents (Sun, W33) | Error workflows, retries, alert fatigue; audit logging; AI agent nodes with tools; security (secrets, webhook authentication, network exposure) |
| C1 | Clinic (Tue, W33) | Lab 15: run the signal service and exercise every endpoint |
| C2 | Clinic (Thu, W33) | Import and adapt the workflows; connect Telegram |

## Workflows provided

| File | Trigger | What it does |
|---|---|---|
| `01_daily_signal_alert.json` | Weekdays 15:45 IST | Calls `/signal` for a watchlist and sends a Telegram alert when a crossover flips |
| `02_news_sentiment_digest.json` | Weekdays 08:45 IST | Reads an RSS feed, scores headlines via `/sentiment`, posts a ranked digest |
| `03_trade_journal_webhook.json` | Webhook | Validates fills from a paper-trading bot and stores them via `/journal` |

Setup instructions: [`n8n/README.md`](../../n8n/README.md).

## Assignment

Add an error workflow that alerts you when any CFMAT workflow fails, and a fourth workflow of your own design, such as an end-of-day P&L summary built from the trade journal.

## Readings

- n8n documentation: workflows, expressions, error handling, self-hosting security.
- Telegram Bot API documentation (bots and chat IDs).

## Assessment

Quiz 15; Lab 15; workflow assignment.
