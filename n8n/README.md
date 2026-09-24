# n8n Workflows (M18)

Three workflows that connect n8n to the CFMAT signal service (`cfmat/automation/signal_service.py`).

| File | Trigger | Flow |
|---|---|---|
| `01_daily_signal_alert.json` | Schedule, weekdays 15:45 IST | Watchlist → `GET /signal` per symbol → IF signal changed → Telegram alert (else no-op) |
| `02_news_sentiment_digest.json` | Schedule, weekdays 08:45 IST | RSS feed → collect headlines → `POST /sentiment` → format ranked digest → Telegram |
| `03_trade_journal_webhook.json` | Webhook `POST /webhook/cfmat-trade-fill` | Validate side/qty/price → `POST /journal` → respond 200, or respond 400 if invalid |

All three were imported into n8n 2.40 and executed against the signal service while this course was built. Workflows 1 and 2 ran with their trigger swapped for a manual trigger and Telegram replaced by a no-op; workflow 3 ran as an active webhook.

## 1. Start the signal service

```bash
pip install -e .
python -m cfmat.automation.signal_service --host 127.0.0.1 --port 8000
curl "http://127.0.0.1:8000/signal?symbol=NIFTYDEMO"
```

If n8n runs in Docker, start the service with `--host 0.0.0.0` and use `http://host.docker.internal:8000` in the HTTP Request nodes (on Linux, add `--add-host=host.docker.internal:host-gateway` to `docker run`). The service has no authentication: keep it on your machine or a private network.

## 2. Start n8n and import

```bash
docker run -it --rm -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n
# or: npx n8n
```

Open http://localhost:5678 → **Workflows → Import from File** → choose each JSON file. From the command line: `n8n import:workflow --input=01_daily_signal_alert.json`.

## 3. Configure

1. **Service URL**: the HTTP Request nodes call `http://localhost:8000`; change it if your service runs elsewhere.
2. **Telegram**: create a bot with @BotFather, add a *Telegram API* credential in n8n with the token, and replace `REPLACE_WITH_YOUR_CHAT_ID` in the Telegram nodes.
3. **RSS feed** (workflow 2): replace the placeholder URL with a feed whose terms allow this use.
4. **Watchlist** (workflow 1): edit the list in the *Watchlist* Code node. Symbols without a `data/<SYMBOL>.csv` file get a synthetic series, which is fine for practice.
5. Timezone is set to Asia/Kolkata in each workflow's settings.

## 4. Test the webhook

Activate workflow 3, then:

```bash
curl -X POST http://localhost:5678/webhook/cfmat-trade-fill \
  -H 'Content-Type: application/json' \
  -d '{"order_id": 7, "symbol": "DEMOSTOCK", "side": "BUY", "qty": 25, "price": 1250.5, "strategy": "demo"}'
# → {"stored": true, "rows": 1}
curl http://127.0.0.1:8000/journal
```

A fill with `"side": "HOLD"` or a non-positive quantity returns HTTP 400.

## Safety notes

- Alerts are for learning and paper trading. The message text says so; keep it that way if you share alerts with anyone.
- Never paste API keys or tokens into workflow JSON. Use n8n credentials.
- Add header authentication to the webhook before exposing n8n to the internet.
