# %% [markdown]
# # Lab 11 — Trading Infrastructure, Pre-Trade Risk and Paper Trading (Module 11)
#
# **Goals**
# 1. Run an intraday strategy on one-minute bars through a paper broker.
# 2. Configure pre-trade risk limits and watch the RMS reject bad orders.
# 3. Trip the kill switch with a daily-loss limit and square off.
# 4. Journal every fill in a form ready for a database or an n8n webhook.
#
# The same `BrokerAdapter` interface is what you implement for a live broker API;
# see the skeleton at the end.

# %%
from datetime import datetime

import numpy as np
import pandas as pd

from cfmat import backtest as bt
from cfmat import broker as brk

rng = np.random.default_rng(11)

# One session of 1-minute bars, 09:15–15:29 (375 minutes).
minutes = pd.date_range("2026-01-05 09:15", periods=375, freq="1min")
price = 2_000 * np.exp(np.cumsum(rng.normal(0, 0.0006, len(minutes))))
bars = pd.Series(price, index=minutes, name="close")

# %% [markdown]
# ## 1. Risk limits and the paper broker

# %%
limits = brk.RiskLimits(
    max_order_qty=600,
    max_order_value=1_500_000,
    max_position_qty=600,
    max_daily_loss=15_000,
    max_orders_per_second=10,     # keep below your exchange's algo-registration threshold
    price_band_pct=0.02,
    allowed_symbols={"DEMOSTOCK"},
)
rms = brk.RiskManager(limits)
paper = brk.PaperBroker(cash=2_500_000, risk=rms, slippage_bps=1.5,
                        cost_model=bt.IndianCostModel(), segment="equity_intraday")
journal = brk.TradeJournal()

# %% [markdown]
# ## 2. RMS checks in action

# %%
paper.update_price("DEMOSTOCK", bars.iloc[0], minutes[0])
paper.update_price("OTHER", 500.0, minutes[0])
tests = [
    ("unknown symbol", brk.Order("OTHER", brk.BUY, 10)),
    ("too large", brk.Order("DEMOSTOCK", brk.BUY, 800)),
    ("fat finger limit", brk.Order("DEMOSTOCK", brk.BUY, 10, brk.LIMIT, bars.iloc[0] * 1.10)),
]
for label, order in tests:
    result = paper.place_order(order, minutes[0])
    print(f"{label:<18} → {result.status:<8} {result.reject_reason}")

burst_time = datetime(2026, 1, 5, 9, 16, 0)
statuses = [paper.place_order(brk.Order("DEMOSTOCK", brk.BUY, 1), burst_time).status for _ in range(12)]
print(f"12 orders in the same second → {statuses.count('FILLED')} filled, {statuses.count('REJECTED')} throttled")
paper.square_off_all(burst_time)
for fill in paper.fills:
    journal.record(fill)

# %% [markdown]
# ## 3. An intraday momentum strategy with a hard square-off
# Enter on a 15-minute breakout, reverse on the opposite breakout, flatten by
# 15:15. If the mark-to-market loss hits the daily limit, the RMS kill switch
# trips: flatten immediately and stop for the day.

# %%
square_off = pd.Timestamp("2026-01-05 15:15")
for ts, px in bars.iloc[16:].items():
    paper.update_price("DEMOSTOCK", px, ts)
    if rms.kill_switch:
        print(f"{ts:%H:%M} kill switch: {rms.kill_reason} → squaring off, no more trades today")
        paper.square_off_all(ts)
        break
    if ts >= square_off:
        paper.square_off_all(ts)
        break
    window = bars.loc[:ts].iloc[-16:-1]
    pos = paper.position("DEMOSTOCK")
    if px > window.max() and pos <= 0:
        paper.place_order(brk.Order("DEMOSTOCK", brk.BUY, 300 - pos), ts)
    elif px < window.min() and pos >= 0:
        paper.place_order(brk.Order("DEMOSTOCK", brk.SELL, 300 + pos), ts)

for fill in paper.fills[len(journal.rows):]:
    journal.record(fill)
fills = pd.DataFrame(journal.rows)
rejected = pd.Series([o.reject_reason for o in paper.orders if o.status == "REJECTED"])
print(f"Fills: {len(fills)}, rejected orders: {len(rejected)}")
print(rejected.value_counts().to_string())
print(f"Realised P&L ₹{paper.realized_pnl:,.0f}, charges ₹{paper.total_charges:,.0f}, "
      f"day P&L ₹{paper.day_pnl():,.0f}, open positions: {paper.positions() or 'none'}")
print(fills.tail(4).to_string(index=False))

# %% [markdown]
# ## 4. Kill switch
# A shock drops the price 3%. The next order trips the daily-loss limit, the RMS
# blocks all further trading, and the desk squares off.

# %%
paper.start_new_day()
t0 = pd.Timestamp("2026-01-06 09:15")
paper.update_price("DEMOSTOCK", bars.iloc[-1], t0)
paper.place_order(brk.Order("DEMOSTOCK", brk.BUY, 500), t0)
paper.update_price("DEMOSTOCK", bars.iloc[-1] * 0.97, t0 + pd.Timedelta(minutes=1))
blocked = paper.place_order(brk.Order("DEMOSTOCK", brk.BUY, 10), t0 + pd.Timedelta(minutes=1))
print(f"Day P&L ₹{paper.day_pnl():,.0f} → order {blocked.status}: {blocked.reject_reason}")
paper.square_off_all(t0 + pd.Timedelta(minutes=2))
print(f"After square-off: positions {paper.positions() or 'none'}, kill switch on = {rms.kill_switch}")

# %% [markdown]
# ## 5. From paper to live: implementing a `BrokerAdapter`
#
# ```python
# class KiteAdapter(BrokerAdapter):
#     def __init__(self, kite):              # an authenticated KiteConnect client
#         self.kite = kite
#     def place_order(self, order, timestamp=None):
#         order.id = self.kite.place_order(variety="regular", exchange="NSE",
#             tradingsymbol=order.symbol, transaction_type=order.side, quantity=order.qty,
#             order_type=order.order_type, price=order.limit_price, product="MIS",
#             tag=order.algo_id)
#         return order
#     ...
# ```
# Read your broker's API documentation for exact parameters, and keep the
# `RiskManager` check in front of every call: the broker's RMS is the last line
# of defence, not the first.

# %% [markdown]
# ## Exercises
# 1. Add a "max open orders" limit and a check that blocks new entries after 15:00.
# 2. Persist `journal.rows` to SQLite and compute per-trade P&L with SQL.
# 3. Implement a `BrokerAdapter` for your broker's sandbox and run section 3 against it.
