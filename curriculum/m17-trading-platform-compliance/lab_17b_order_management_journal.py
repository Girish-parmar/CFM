# %% [markdown]
# # Lab 17b — Order Management and the Trading Journal (M17)
#
# **Goals**
# 1. Drive orders through an order management system (OMS) and read its state machine and audit trail.
# 2. See how stops, stop-limits, IOC, DAY expiry and amendments behave, including partial fills.
# 3. Protect entries with bracket and OCO orders that resize as fills arrive.
# 4. Catch breaks between the OMS and the broker with reconciliation.
# 5. Trade a week of opening-range breakouts, then review it from the journal: round trips,
#    R-multiples, MAE/MFE, statistics by setup and hour, and charts.
#
# Lab 17a sent orders straight to the paper broker. Here a strategy talks only to
# `OrderManager`, which owns order state; the broker's RMS still checks every order.

# %%
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from cfmat import trading, viz
from cfmat.analytics.indicators import atr
from cfmat.microstructure.costs import IndianCostModel
from cfmat.portfolio.risk import fixed_fractional_qty

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)
pd.set_option("display.max_colwidth", 70)
T0 = pd.Timestamp("2026-01-05 09:15")


def show_events(oms: trading.OrderManager, last: int | None = None) -> None:
    events = oms.events_frame()[["client_id", "event", "status", "detail"]]
    print((events.tail(last) if last else events).to_string())


# %% [markdown]
# ## 1. The OMS and its state machine
# Every order gets a client id. Sending the same id twice (for example, a retry
# after a network timeout) returns the original order and sends nothing: this
# is how an OMS makes submission idempotent.

# %%
broker = trading.PaperBroker(cash=1_000_000, slippage_bps=0)
oms = trading.OrderManager(broker)
oms.on_price("DEMO", 100.0, T0)

first = oms.submit("DEMO", trading.BUY, 50, client_id="orb-2026-01-05-1", timestamp=T0)
retry = oms.submit("DEMO", trading.BUY, 50, client_id="orb-2026-01-05-1", timestamp=T0)
print(f"retry is the same order: {retry is first}; broker orders sent: {len(broker.orders)}; "
      f"position {oms.positions['DEMO']}")
print("\nAllowed transitions:")
for state, nxt in trading.oms.TRANSITIONS.items():
    print(f"  {state:<16} -> {', '.join(sorted(nxt)) or '(terminal)'}")
show_events(oms)

# %% [markdown]
# ## 2. Stops and stop-limits
# The OMS holds a stop until its trigger trades, then sends a market order (stop)
# or a limit order (stop-limit). On a gap through the trigger the stop fills at
# the gap price; the stop-limit does not chase and may not fill at all.
# Exchanges reject a stop whose trigger has already traded, and so does the OMS.

# %%
stop = oms.submit("DEMO", trading.SELL, 25, trading.STOP, stop_price=97.0, tif=trading.GTC)
stop_limit = oms.submit("DEMO", trading.SELL, 25, trading.STOP_LIMIT, stop_price=97.0, limit_price=96.5,
                        tif=trading.GTC)
bad = oms.submit("DEMO", trading.BUY, 10, trading.STOP, stop_price=99.0)
print(f"buy stop below the market: {bad.status} ({bad.reject_reason})")
oms.on_price("DEMO", 95.0, T0 + pd.Timedelta(minutes=1))          # gap down through 97 and 96.5
print(f"after the gap: stop {stop.status} at {stop.avg_fill_price}, "
      f"stop-limit {stop_limit.status} with {stop_limit.filled_qty} filled")
oms.on_price("DEMO", 96.7, T0 + pd.Timedelta(minutes=2))          # bounces back above the limit
print(f"after the bounce: stop-limit {stop_limit.status} at {stop_limit.avg_fill_price}")

# %% [markdown]
# ## 3. Thin liquidity: partial fills, IOC, DAY expiry and amendments
# `max_fill_qty` caps what fills per price update, so large orders fill in parts.
# An IOC order cancels whatever does not fill at once. DAY orders expire at the
# close; GTC orders carry over. An amendment is a cancel/replace at the broker;
# the fill history stays with the OMS order.

# %%
thin = trading.PaperBroker(cash=1_000_000, slippage_bps=0, max_fill_qty=40)
oms = trading.OrderManager(thin)
oms.on_price("DEMO", 100.0, T0)
ioc = oms.submit("DEMO", trading.BUY, 100, tif=trading.IOC)
print(f"IOC for 100: {ioc.status}, filled {ioc.filled_qty}")
working = oms.submit("DEMO", trading.BUY, 120, trading.LIMIT, limit_price=100.0)
print(f"limit for 120 at 100: {working.status}, filled {working.filled_qty}")
oms.amend(working.client_id, qty=90, limit_price=99.5)
oms.on_price("DEMO", 99.4, T0 + pd.Timedelta(minutes=1))
print(f"after amend to 90 @ 99.5: {working.status}, filled {working.filled_qty} "
      f"at {working.avg_fill_price:.2f}; broker orders {working.broker_ids}")
gtc = oms.submit("DEMO", trading.BUY, 10, trading.LIMIT, limit_price=95.0, tif=trading.GTC)
print("expired at the close:", oms.end_of_day(T0 + pd.Timedelta(hours=6)), "| GTC still", gtc.status)
show_events(oms, last=12)

# %% [markdown]
# ## 4. Bracket and OCO orders
# A bracket is an entry plus a protective stop and a profit target. The exits
# are one-cancels-other and are sized to what the entry has filled, so a
# partial entry is protected at once; a partial exit shrinks the other leg.

# %%
oms = trading.OrderManager(trading.PaperBroker(cash=1_000_000, slippage_bps=0, max_fill_qty=40))
oms.on_price("DEMO", 100.0, T0)
bracket = oms.submit_bracket("DEMO", trading.BUY, 100, stop_loss=97.0, take_profit=104.0)
entry, sl, tp = (oms.get(c) for c in [bracket.parent, *bracket.legs])
print(f"entry filled {entry.filled_qty}/100 → stop {sl.qty} ({sl.status}), target {tp.qty} ({tp.status})")
for minute, price in enumerate([100.4, 100.8, 104.1, 103.0, 96.5, 96.0], start=1):
    oms.on_price("DEMO", price, T0 + pd.Timedelta(minutes=minute))
print(oms.orders_frame()[["role", "side", "qty", "order_type", "status", "filled_qty", "avg_fill_price"]])
print("position:", oms.positions)

# OCO breakout entry: buy above the range or sell below it, never both.
oco = oms.submit_oco([
    {"symbol": "DEMO", "side": trading.BUY, "qty": 30, "order_type": trading.STOP, "stop_price": 98.0},
    {"symbol": "DEMO", "side": trading.SELL, "qty": 30, "order_type": trading.STOP, "stop_price": 94.0},
])
oms.on_price("DEMO", 98.2, T0 + pd.Timedelta(minutes=10))
print({oms.get(c).side: oms.get(c).status for c in oco.legs})

# %% [markdown]
# ## 5. Reconciliation
# Someone places an order from the broker's own terminal and a working order is
# cancelled at the broker (as a broker's auto square-off would). The OMS no
# longer matches reality; `reconcile` lists every break. Run it on a timer and
# before the close in production.

# %%
broker = trading.PaperBroker(cash=1_000_000, slippage_bps=0)
oms = trading.OrderManager(broker)
oms.on_price("DEMO", 100.0, T0)
oms.submit("DEMO", trading.BUY, 20)
resting = oms.submit("DEMO", trading.BUY, 10, trading.LIMIT, limit_price=98.0)
broker.place_order(trading.Order("DEMO", trading.BUY, 7))            # manual order at the terminal
broker.cancel_order(resting.broker_ids[-1])                          # cancelled at the broker
print(oms.reconcile().to_string(index=False))
oms.cancel(resting.client_id)
oms.flatten(T0 + pd.Timedelta(minutes=5))
print("after flatten:", broker.positions() or "flat", "| breaks:", len(oms.reconcile()))

# %% [markdown]
# ## 6. Two weeks of opening-range breakouts through the OMS
# Ten sessions of one-minute bars. After the first 30 minutes, a break of the
# opening range enters with a bracket: stop at the far side of the range (at
# most 1.5 ATR away), target at 2R, size set by risking 0.5% of capital. One
# trade per direction per day; everything is flattened at 15:15. The journal
# listens to the broker and records every fill; we attach the plan to the
# entry fills with `annotate`.

# %%
rng = np.random.default_rng(17)
sessions = []
for day in pd.bdate_range("2026-01-05", periods=10):
    minutes = pd.date_range(day + pd.Timedelta(hours=9, minutes=15), periods=375, freq="1min")
    u = np.linspace(-1, 1, 375)
    sigma = 0.0007 * (1 + 0.8 * u**2)                                  # U-shaped intraday volatility
    drift = rng.choice([-1, 1]) * 0.00004                              # some days trend, some reverse
    close = 2_000 * np.exp(np.cumsum(rng.normal(drift, sigma)))
    sessions.append(pd.Series(close, index=minutes))
close = pd.concat(sessions)
close *= np.repeat(np.exp(np.cumsum(rng.normal(0, 0.006, 10))), 375)  # overnight gaps
noise = np.abs(rng.normal(0, 0.0004, len(close)))
bars = pd.DataFrame({"open": close.shift(1), "close": close})
first_bar = ~bars.index.normalize().duplicated()
bars.loc[first_bar, "open"] = bars.loc[first_bar, "close"] * (1 - rng.normal(0, 0.0005, first_bar.sum()))
bars["high"] = bars[["open", "close"]].max(axis=1) * (1 + noise)
bars["low"] = bars[["open", "close"]].min(axis=1) * (1 - noise)
bars["volume"] = rng.integers(2_000, 20_000, len(bars))

limits = trading.RiskLimits(max_order_qty=5_000, max_order_value=5_000_000, max_position_qty=5_000,
                            max_daily_loss=40_000, max_orders_per_second=20, price_band_pct=0.03)
broker = trading.PaperBroker(cash=2_000_000, risk=trading.RiskManager(limits), slippage_bps=1.0,
                             cost_model=IndianCostModel(), segment="equity_intraday")
oms = trading.OrderManager(broker, id_prefix="ORB")
journal = trading.TradeJournal()
broker.add_fill_listener(journal.record)
capital, risk_fraction = 2_000_000, 0.005
day_atr = atr(bars, 30)
previous_close = bars["close"].shift(1)

for day, session in bars.groupby(bars.index.date):
    opening = session.iloc[:30]
    high, low = opening["high"].max(), opening["low"].min()
    gap = session["open"].iloc[0] / previous_close.loc[session.index[0]] - 1 if day != bars.index[0].date() else 0.0
    gap_tag = "gap-up" if gap > 0.002 else "gap-down" if gap < -0.002 else "flat-open"
    traded = set()
    for ts, bar in session.iloc[30:].iterrows():
        oms.on_price("DEMO", bar["close"], ts)
        if ts.time() >= pd.Timestamp("15:15").time():
            oms.flatten(ts)
            break
        if oms.positions.get("DEMO", 0) or oms.open_orders("DEMO"):
            continue
        a = float(day_atr.loc[ts])
        for side, trigger, far in ((trading.BUY, bar["close"] > high, low), (trading.SELL, bar["close"] < low, high)):
            if not trigger or side in traded:
                continue
            entry = bar["close"]
            stop = max(far, entry - 1.5 * a) if side == trading.BUY else min(far, entry + 1.5 * a)
            target = entry + 2 * (entry - stop)
            qty = fixed_fractional_qty(capital, risk_fraction, entry, stop)
            group = oms.submit_bracket("DEMO", side, qty, stop_loss=round(stop, 2), take_profit=round(target, 2),
                                       tag="ORB", timestamp=ts)
            for broker_id in oms.get(group.parent).broker_ids:
                journal.annotate(broker_id, setup=f"ORB {side.lower()}", stop=round(stop, 2),
                                 target=round(target, 2), tags=[gap_tag])
            traded.add(side)
            break
    oms.end_of_day(session.index[-1])
    broker.start_new_day()

print(f"orders {len(oms.orders)}, broker orders {len(broker.orders)}, fills {len(journal.rows)}, "
      f"events {len(oms.events)}")
print("status counts:", oms.orders_frame()["status"].value_counts().to_dict())
print("reconciliation breaks:", len(oms.reconcile()), "| open positions:", broker.positions() or "none")
rejected = oms.orders_frame().query("status == 'REJECTED'")
print(rejected[["role", "side", "qty", "reject_reason"]].to_string())

# %% [markdown]
# Read the rejections. When the opening range is narrow, the stop is tight and
# risk-based sizing asks for a very large quantity; the broker's order-value
# limit refuses it and the OMS cancels the bracket's exits with it. The RMS is
# the last line of defence: cap the size in the strategy too (exercise 5).

# %% [markdown]
# ## 7. Review from the journal
# Round trips rebuild trades from fills. R-multiples compare each result with
# the risk you planned; MAE and MFE show how far a trade went against you and
# for you before it closed. Two weeks is far too few trades to judge a setup:
# the point is the review process, not this result.

# %%
trips = trading.excursions(journal.round_trips(), bars)
cols = ["symbol", "direction", "entry_time", "exit_time", "qty", "entry_price", "exit_price", "net_pnl",
        "r_multiple", "mae_r", "mfe_r", "setup", "tags"]
table = trips[cols].copy()
table["tags"] = table["tags"].map(", ".join)
numeric = table.select_dtypes("number").columns
table[numeric] = table[numeric].round(2)
print(table.to_string(index=False))
summary = pd.Series(trading.trade_summary(trips))
print("\n", summary.round(3).to_string())
print("\nBy setup:\n", trading.trade_breakdown(trips, "setup").round(2).to_string())
print("\nBy tag:\n", trading.trade_breakdown(trips, "tags").round(2).to_string())
print(f"\nJournal gross P&L ₹{trips['gross_pnl'].sum():,.0f} = broker realised ₹{broker.realized_pnl:,.0f}; "
      f"journal charges ₹{trips['charges'].sum():,.0f} = broker charges ₹{broker.total_charges:,.0f}")

# %% [markdown]
# ## 8. Keep it, chart it
# Save the journal to SQLite (the file an n8n workflow or a dashboard would
# read), load it back and chart the week.

# %%
store = Path(tempfile.mkdtemp()) / "journal.sqlite"
journal.save(store)
reloaded = trading.TradeJournal.load(store)
assert reloaded.round_trips()["net_pnl"].round(6).equals(journal.round_trips()["net_pnl"].round(6))
print(f"saved {len(reloaded.rows)} fills to {store.name} and read them back")

five_min = bars.resample("5min").agg({"open": "first", "high": "max", "low": "min", "close": "last",
                                      "volume": "sum"}).dropna()
print("Charts:",
      viz.savefig(viz.price_chart(five_min, trades=trips, last=375, title="ORB, last 5 sessions, 5-minute bars"),
                  "lab17b_orb_sessions"),
      viz.savefig(viz.trade_chart(trips, title="ORB, two weeks — trade review"), "lab17b_trade_review"))

# %% [markdown]
# ## Exercises
# 1. Replace the fixed 2R target with a trailing stop: on each bar, `amend` the stop leg upward.
#    Compare the R-multiple distribution with the fixed target.
# 2. Set `max_fill_qty=200` on the broker. How do partial entries change the bracket legs and
#    the realised R? Find the events in the audit trail that show the resizing.
# 3. Trip the kill switch mid-trade (lower `max_daily_loss`). What happens to a triggered stop,
#    and why does `flatten` still work? Write the incident note you would file.
# 4. Add a `mistake` note with `annotate` to trades you would not take again, and break down
#    the statistics by it.
# 5. Cap each entry at 20% of capital in the strategy, rerun, and compare the rejections and
#    the R-multiples. Charges took most of the gross P&L here: what minimum R per trade does
#    this setup need to pay its costs?
