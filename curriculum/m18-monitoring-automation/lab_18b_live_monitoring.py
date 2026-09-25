# %% [markdown]
# # Lab 18b — Live Monitoring (M18)
#
# **Goals**
# 1. Catch a dead strategy process and a stale feed from timestamps alone.
# 2. Tell whether paper trading is still the strategy you backtested — and know how often a
#    healthy strategy will look drifted by chance.
# 3. Split each day's P&L into signal, execution and costs, and see an execution problem appear.
# 4. Turn metrics into alerts with severity, de-duplication and resolution, delivered to a webhook
#    the way n8n receives them — with no alerts at all on a clean day.
#
# Incidents are planted in synthetic data, so every alert can be checked against the truth.

# %%
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import pandas as pd

from cfmat import data, trading
from cfmat.automation import monitoring as mon
from cfmat.microstructure.costs import IndianCostModel

pd.set_option("display.width", 140)
DAY = pd.Timestamp("2026-01-05")
OPEN, CLOSE = DAY + pd.Timedelta("09:15:00"), DAY + pd.Timedelta("15:30:00")

# %% [markdown]
# ## 1. Heartbeats and stale data
# The strategy process writes a heartbeat every 10 seconds; it crashed at 11:02 and was
# restarted at 11:06. The feed comes from `data.tick_stream`, which plants an outage and a
# frozen price. A clean day has neither.

# %%
beats = pd.date_range(OPEN, CLOSE, freq="10s")
beats = beats[(beats < DAY + pd.Timedelta("11:02:00")) | (beats > DAY + pd.Timedelta("11:06:00"))]
print("Heartbeat gaps:\n", mon.heartbeat_gaps(beats, every="10s", tolerance=3, start=OPEN, end=CLOSE).to_string(index=False))

ticks, truth = data.tick_stream(seed=18)
incidents = mon.staleness(ticks, check_every="5s", max_age="30s", frozen_after="30s")
print("\nFeed incidents found:\n", incidents.to_string(index=False))
print("\nPlanted:\n", truth["periods"].to_string(index=False))
clean_ticks, _ = data.tick_stream(seed=18, faults=False)
clean_beats = pd.date_range(OPEN, CLOSE, freq="10s")
print(f"\nClean day: {len(mon.staleness(clean_ticks))} feed incidents, "
      f"{len(mon.heartbeat_gaps(clean_beats, start=OPEN, end=CLOSE))} heartbeat gaps")

# %% [markdown]
# ## 2. Drift: is paper trading still the backtested strategy?
# A short-term trend strategy (price against its 5-day average, about five trades a month)
# is backtested with 2 bp of slippage. Paper trading matches it for six months; then a code
# change delays signals by a day and fills get worse. Each month, `drift_report` compares
# the month's paper returns, signals and fills with the backtest.

# %%
close = data.gbm_prices(252, s0=1000, mu=0.12, sigma=0.20, seed=18, start="2026-01-01")
signal = np.sign(close - close.rolling(5).mean()).fillna(0)
market = close.pct_change().fillna(0)
backtest = signal.shift(1).fillna(0) * market - signal.diff().abs().fillna(0) / 2 * 2e-4
bug_from = close.index[126]
paper_signal = signal.where(signal.index < bug_from, signal.shift(1)).fillna(0)       # the delayed-signal bug
slip = pd.Series(np.where(close.index < bug_from, 2.0, 9.0), close.index)
paper = paper_signal.shift(1).fillna(0) * market - paper_signal.diff().abs().fillna(0) / 2 * slip / 1e4
rng = np.random.default_rng(18)
trade_days = close.index[paper_signal.diff().fillna(0) != 0]
fills = pd.DataFrame({"side": np.where(paper_signal.loc[trade_days] > 0, "BUY", "SELL"),
                      "model_price": close.loc[trade_days]}, index=trade_days)
cost_bps = slip.loc[trade_days] + rng.normal(0, 1.5, len(fills))
fills["fill_price"] = fills["model_price"] * (1 + np.where(fills["side"] == "BUY", 1, -1) * cost_bps / 1e4)

rows = {}
for month, days in close.groupby(close.index.to_period("M")).groups.items():
    report = mon.drift_report(paper.loc[days], backtest.loc[days], paper_signal.loc[days], signal.loc[days],
                              fills[fills.index.isin(days)], expected_slippage_bps=2.0)
    rows[str(month)] = report[["tracking_bps_per_day", "tracking_tstat", "signal_agreement", "slippage_bps",
                               "slippage_tstat", "drift"]]
print(pd.DataFrame(rows).T.astype({"drift": bool}).round(2).to_string())
print(f"(the bug went live on {bug_from:%d %b})")

# %% [markdown]
# Read the columns. The tracking t-statistic never reaches significance: daily return
# differences are too noisy for a month of data. Signal agreement and slippage catch the
# problem at once — compare the things the strategy controls, not just its returns. And a
# month with only a couple of trades can slip through: small samples hide drift.

# %% [markdown]
# **The false-alarm budget.** Each statistical check alarms with probability `alpha` on a
# healthy system. Run the monthly report on 300 faithful copies (paper = backtest plus tiny
# noise) and count how many would have paged you.

# %%
false_alarms = 0
for trial in range(300):
    noise = np.random.default_rng(trial).normal(0, 2e-4, 21)
    window = backtest.iloc[40:61]
    false_alarms += bool(mon.drift_report(window + noise, window, alpha=0.01)["drift"])
print(f"Faithful copies flagged: {false_alarms}/300 ({false_alarms / 3:.1f}%) with alpha = 1% per test")

# %% [markdown]
# ## 3. P&L attribution: signal, execution, costs
# Paper-trade 40 days through `PaperBroker` with Indian costs. Slippage is 2 bp until day
# 20, then 12 bp (a new, worse execution route). The attribution adds up exactly to the
# broker's equity change and shows where the money went.

# %%
prices = data.gbm_prices(40, s0=1500, seed=19, start="2026-02-02")
rng = np.random.default_rng(19)
rows, equity = [], []
broker = trading.PaperBroker(cash=2_000_000, slippage_bps=2, cost_model=IndianCostModel())
for i, (day, px) in enumerate(prices.items()):
    broker.slippage_bps = 2 if i < 20 else 12
    decision = px * (1 + rng.normal(0, 0.003))
    ts = day + pd.Timedelta("10:30:00")
    broker.update_price("DEMO", decision, ts)
    side = "BUY" if rng.random() < 0.5 else "SELL"
    qty = int(rng.integers(50, 200))
    broker.place_order(trading.Order("DEMO", side, qty), ts)
    fill = broker.fills[-1]
    rows.append({"ts": ts, "symbol": "DEMO", "side": side, "qty": qty, "decision_price": decision,
                 "fill_price": fill.price, "charges": fill.charges})
    broker.update_price("DEMO", px, day + pd.Timedelta("15:29:00"))
    equity.append(broker.equity())
attribution = mon.pnl_attribution(pd.DataFrame(rows), prices.rename("DEMO"))
change = pd.Series(equity, index=prices.index).diff().fillna(equity[0] - 2_000_000)
print("Adds up to the broker's equity change:", bool(np.allclose(attribution["total"], change)))
halves = attribution.groupby(np.where(np.arange(len(attribution)) < 20, "days 1-20", "days 21-40")).sum()
print(halves.round(0).to_string())

# %% [markdown]
# ## 4. Alerts: rules, severity, de-duplication and a webhook
# Every 15 seconds the monitor computes four metrics (feed age, how long the price has not
# moved, heartbeat age and the day's P&L) and hands them to an `AlertManager`.
# Alerts go to a webhook server started here, standing in for n8n's Webhook node. A rule
# fires once, reminds after its cool-down if the problem persists, and resolves once.

# %%
received = []


class FakeN8n(BaseHTTPRequestHandler):
    def do_POST(self):
        received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), FakeN8n)
threading.Thread(target=server.serve_forever, daemon=True).start()
hook = f"http://127.0.0.1:{server.server_address[1]}/webhook/cfmat-alert"

RULES = [
    mon.AlertRule("feed silent", "feed_age_s", ">", 30, "critical", cooldown="10min"),
    mon.AlertRule("price frozen", "frozen_s", ">", 30, "warning", cooldown="10min"),
    mon.AlertRule("strategy down", "heartbeat_age_s", ">", 30, "critical", cooldown="5min"),
    mon.AlertRule("daily loss limit", "day_pnl", "<", -25_000, "critical", cooldown="30min"),
]


def run_day(feed: pd.DataFrame, heartbeats: pd.DatetimeIndex, pnl: pd.Series, sinks) -> mon.AlertManager:
    manager = mon.AlertManager(RULES, sinks=sinks)
    checks = pd.date_range(OPEN + pd.Timedelta("1min"), CLOSE, freq="15s", inclusive="left")
    ts, px = feed["ts"].sort_values().to_numpy(), feed.sort_values("ts")["price"].to_numpy()
    moved = ts[np.r_[True, px[1:] != px[:-1]]]
    last_tick = ts[np.searchsorted(ts, checks.to_numpy(), side="right") - 1]
    last_move = moved[np.searchsorted(moved, checks.to_numpy(), side="right") - 1]
    last_beat = heartbeats[heartbeats.searchsorted(checks, side="right") - 1]
    for k, now in enumerate(checks):
        age = (now - pd.Timestamp(last_tick[k])).total_seconds()
        manager.evaluate({"feed_age_s": age,
                          "frozen_s": (now - pd.Timestamp(last_move[k])).total_seconds() if age <= 30 else 0.0,
                          "heartbeat_age_s": (now - last_beat[k]).total_seconds(),
                          "day_pnl": float(pnl.asof(now))}, now)
    return manager


minutes = pd.date_range(OPEN, CLOSE, freq="1min")
calm = pd.Series(np.cumsum(np.random.default_rng(20).normal(15, 150, len(minutes))), index=minutes)  # a normal day
after_1330 = np.clip((minutes - (DAY + pd.Timedelta("13:30:00"))).total_seconds() / 60, 0, None)
sliding = calm - after_1330 * 350                                    # from 13:30 a position goes wrong
try:
    incident_day = run_day(ticks, beats, sliding, [mon.webhook_sink(hook)])
    quiet_day = run_day(clean_ticks, clean_beats, calm, [mon.webhook_sink(hook)])
finally:
    server.shutdown()

alerts = incident_day.history_frame()
print(alerts[["ts", "severity", "status", "rule", "message"]].to_string(index=False))
n_checks = len(pd.date_range(OPEN + pd.Timedelta("1min"), CLOSE, freq="15s", inclusive="left")) * len(RULES)
print(f"\n{n_checks:,} rule checks → {len(alerts)} notifications; webhook received {len(received)}; "
      f"delivery failures {len(incident_day.failures)}")
print(f"Clean day: {len(quiet_day.history)} notifications")

# %% [markdown]
# Every planted incident raised exactly one alert and one resolution; the loss-limit rule
# kept reminding every 30 minutes because nothing stopped the slide. In production the
# RMS kill switch (M17) flattens the book at the first breach, and the reminders stop.

# %% [markdown]
# ## Exercises
# 1. Lower the frozen-price threshold to 10 s and run the clean day. How many alerts, and what
#    threshold would you set for a stock that trades once a minute?
# 2. In section 2, change `alpha` to 0.05 and rerun the false-alarm count. What does a desk with
#    20 strategies and monthly reports experience each year at each level?
# 3. Add a rule on execution cost (bp of traded value from section 3) and decide its severity.
# 4. Import the n8n trade-journal workflow, add a Webhook node at `/webhook/cfmat-alert`, route
#    `critical` alerts to Telegram and the rest to a daily digest, and point `webhook_sink` at it.
