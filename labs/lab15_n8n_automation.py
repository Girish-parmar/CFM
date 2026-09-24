# %% [markdown]
# # Lab 15 — Automation with n8n and AI Agents (Module 15)
#
# **Goals**
# 1. Run the CFMAT signal service that the n8n workflows call.
# 2. Exercise every endpoint from Python exactly as n8n's HTTP Request node will.
# 3. Push paper-trading fills into the trade journal through the webhook path.
# 4. Import the workflows in `n8n/` and wire them to Telegram.
#
# For the n8n part, run the service in a terminal instead:
#     python -m cfmat.automation.signal_service --host 0.0.0.0 --port 8000
# and follow `n8n/README.md`.

# %%
import json
import tempfile
import threading
import urllib.request
from pathlib import Path

from cfmat import nlp, trading
from cfmat.automation.signal_service import make_server

db_path = Path(tempfile.mkdtemp()) / "trade_journal.sqlite"
server = make_server("127.0.0.1", 0, db_path)          # port 0 = pick any free port
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_address[1]}"
print("Signal service running at", BASE)


def call(path: str, payload: dict | None = None):
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


# %% [markdown]
# ## 1. What the "Daily signal alert" workflow sees

# %%
print(call("/health"))
for symbol in ("NIFTYDEMO", "BANKDEMO", "ITDEMO"):
    sig = call(f"/signal?symbol={symbol}&fast=20&slow=50")
    alert = "→ send Telegram alert" if sig["changed"] else "→ no alert"
    print(f"{sig['symbol']:<10} close {sig['close']:>8.2f}  fast {sig['fast_sma']:>8.2f}  slow {sig['slow_sma']:>8.2f}  "
          f"{sig['action']:<11} {alert}")

# %% [markdown]
# ## 2. What the "News sentiment digest" workflow sees

# %%
sample = nlp.load_headlines().headline.head(6).tolist()
digest = call("/sentiment", {"texts": sample})
print(f"{digest['count']} headlines, average score {digest['average_score']:+.2f}")
for item in digest["items"]:
    print(f"  {item['score']:+.2f}  {item['text']}")

# %% [markdown]
# ## 3. What the "Trade journal" webhook stores

# %%
paper = trading.PaperBroker(cash=500_000, slippage_bps=1)
paper.update_price("DEMOSTOCK", 1_250.0)
paper.place_order(trading.Order("DEMOSTOCK", trading.BUY, 100))
paper.update_price("DEMOSTOCK", 1_262.5)
paper.place_order(trading.Order("DEMOSTOCK", trading.SELL, 100))
journal = trading.TradeJournal()
for fill in paper.fills:
    row = journal.record(fill) | {"strategy": "lab15-demo"}
    print("POST /journal", row, "→", call("/journal", row))
print("\nLatest journal rows:")
for row in call("/journal")[:2]:
    print(" ", {k: row[k] for k in ("id", "symbol", "side", "qty", "price", "strategy")})

server.shutdown()
server.server_close()

# %% [markdown]
# ## 4. Now in n8n
# 1. Start n8n (`docker run -it --rm -p 5678:5678 n8nio/n8n` or `npx n8n`).
# 2. Workflows → Import from file → pick each JSON in `n8n/`.
# 3. Create a Telegram bot with @BotFather, add the credential, set your chat ID.
# 4. Point the HTTP Request nodes at your service URL (from Docker use
#    `http://host.docker.internal:8000`).
#
# ## Exercises
# 1. Add an "Error Trigger" workflow that alerts you when any workflow fails.
# 2. Extend the digest: call `nlp.answer_with_claude` through a new `/ask` endpoint
#    and post a one-paragraph morning brief built from the filings.
# 3. Add a shared-secret header check to the service before exposing it beyond localhost.
