# %% [markdown]
# # Lab 16a — Market Data Handler (M16)
#
# **Goals**
# 1. See what a raw tick feed really delivers: duplicates, late ticks, bad prints, a frozen
#    price and an outage — and what each does to your bars if you do not catch it.
# 2. Detect every fault with precision and recall measured against a known answer key.
# 3. Build time, volume and dollar bars, in batch and one tick at a time.
# 4. Keep an instrument master and build continuous futures three ways.
# 5. Store ticks partitioned by date and symbol and replay them deterministically.
#
# Everything is synthetic and seeded: the faults are planted, so we know the truth.

# %%
import tempfile
import time

import numpy as np
import pandas as pd

from cfmat import data
from cfmat.data import handler
from cfmat.infra.plotting import plt, savefig

pd.set_option("display.width", 140)

# %% [markdown]
# ## 1. A tick stream, as the feed delivers it
# One NSE session (09:15–15:30) of trades for a ₹2,000 stock, about one per second, in
# *arrival* order. The feed was faulty: 10 messages were sent twice, 8 arrived late, 6 were
# bad prints, the price froze for 45 seconds and the feed went silent for 90 seconds.
# `truth` is the answer key — a real feed never gives you one.

# %%
ticks, truth = data.tick_stream(seed=16)
print(f"{len(ticks):,} ticks, {ticks['ts'].min():%H:%M:%S} to {ticks['ts'].max():%H:%M:%S}")
print(ticks.head().to_string(index=False))
print("\nPlanted tick-level faults:", truth["flags"].sum().to_dict())
print(truth["periods"].assign(seconds=lambda p: (p.end - p.start).dt.total_seconds()).to_string(index=False))

# %% [markdown]
# ## 2. Bars straight from the raw feed — and what went wrong
# Build one-minute bars without cleaning and compare with bars from validated ticks. A
# single bad print becomes the minute's high or low (and a fake breakout); a duplicated
# message double-counts volume; the outage leaves minutes built from a few seconds of
# trading, which look calm when they were only unobserved.

# %%
dirty_bars = handler.aggregate_bars(ticks, "time", "1min")
report = handler.validate_ticks(ticks)
clean = report.clean()
clean_bars = handler.aggregate_bars(clean, "time", "1min")
range_error = (dirty_bars["high"] - dirty_bars["low"]) - (clean_bars["high"] - clean_bars["low"]).reindex(dirty_bars.index)
print(f"minutes with a corrupted high-low range: {int((range_error.abs() > 1).sum())}; "
      f"largest error ₹{range_error.abs().max():,.2f}")
print(f"volume overstated by duplicates: {int(dirty_bars['volume'].sum() - clean_bars['volume'].sum()):,} shares")
outage = truth["periods"].set_index("kind").loc["outage"]
hit = dirty_bars.loc[outage["start"].floor("1min"):outage["end"].floor("1min"), "ticks"]
print(f"minutes touched by the outage: {', '.join(f'{t:%H:%M}' for t in hit.index)} with {hit.tolist()} ticks "
      f"(a normal minute has about {int(dirty_bars['ticks'].median())})")

# %% [markdown]
# ## 3. Validation: find every fault, raise no false alarms
# `validate_ticks` reads the stream in arrival order, as a live handler would. Scores are
# measured against the answer key: precision is the share of alarms that were real faults,
# recall the share of faults that raised an alarm.

# %%
t0 = time.perf_counter()
report = handler.validate_ticks(ticks)
elapsed = time.perf_counter() - t0
rows = []
for kind in ("duplicate", "out_of_order", "spike"):
    found, true = report.flags[kind], truth["flags"][kind]
    tp = int((found & true).sum())
    rows.append({"fault": kind, "planted": int(true.sum()), "alarms": int(found.sum()),
                 "precision": tp / max(int(found.sum()), 1), "recall": tp / max(int(true.sum()), 1)})
print(pd.DataFrame(rows).to_string(index=False))
print(f"\nOutages found:\n{report.gaps.to_string(index=False)}")
print(f"Frozen prices found (alarm raised {pd.Timedelta('30s').seconds} s into the freeze):\n"
      f"{report.stale.to_string(index=False)}")
print(f"Validated {len(ticks):,} ticks in {elapsed:.2f} s")

clean_ticks, _ = data.tick_stream(seed=16, faults=False)
print("\nOn a clean day the same checks raise:", handler.validate_ticks(clean_ticks).summary())
jumped = clean_ticks.copy()
jumped.loc[12_000:, "price"] = (jumped.loc[12_000:, "price"] * 1.03 / 0.05).round() * 0.05
print("After a genuine +3% news jump that holds:", handler.validate_ticks(jumped).summary()["spike"],
      "spikes flagged (the filter accepts a move confirmed by the next ticks)")

# %% [markdown]
# ## 4. Bars: time, volume and dollar — and the same bars built live
# Time bars start at the session open, so 30-minute bars run 09:15–09:45, not 09:00–09:30.
# Volume and dollar bars close after a fixed amount of trading (labelled by their last tick):
# more bars when the market is busy, fewer when it is quiet. `BarBuilder` builds the time bars one tick at a time,
# as a live system must, and must agree with the batch version exactly.

# %%
bars = {"1-min": handler.aggregate_bars(clean, "time", "1min"),
        "30-min": handler.aggregate_bars(clean, "time", "30min"),
        "volume 25k": handler.aggregate_bars(clean, "volume", 25_000),
        "₹5 cr": handler.aggregate_bars(clean, "dollar", 5e7)}
summary = pd.DataFrame({name: {"bars": len(b), "first bar": f"{b.index[0]:%H:%M}", "median ticks": b["ticks"].median(),
                               "median volume": b["volume"].median(), "median value ₹ lakh": round(b["dollar"].median() / 1e5)}
                        for name, b in bars.items()}).T
print(summary.to_string())

builder, live = handler.BarBuilder("1min"), []
for row in clean.itertuples():
    live += builder.update(row.ts, row.price, row.qty)
live = pd.DataFrame(live + builder.flush()).set_index("ts")
print("\nLive BarBuilder equals batch bars:",
      np.allclose(live[handler.BAR_COLUMNS].to_numpy(float), bars["1-min"][handler.BAR_COLUMNS].to_numpy(float)))

spike_time = ticks.loc[truth["flags"]["spike"].to_numpy(), "ts"].iloc[0].floor("1min")
window = slice(spike_time - pd.Timedelta("10min"), spike_time + pd.Timedelta("10min"))
fig, ax = plt.subplots(figsize=(10, 4))
ax.vlines(dirty_bars.loc[window].index, dirty_bars.loc[window, "low"], dirty_bars.loc[window, "high"],
          color="tab:red", lw=3, alpha=0.5, label="raw feed high-low")
ax.vlines(clean_bars.loc[window].index, clean_bars.loc[window, "low"], clean_bars.loc[window, "high"],
          color="black", lw=1.5, label="validated high-low")
ax.set_title("One bad print turns into a fake high or low")
ax.legend()
print("Chart:", savefig(fig, "lab16a_bad_print"))

# %% [markdown]
# ## 5. Instrument master and continuous futures
# The instrument master is the reference table every order checks: lot size, tick size,
# expiry. Futures expire, so a long backtest needs one continuous series. Three choices:
#
# * **none** — raw front-month prices: every roll shows a fake jump (the carry between contracts);
# * **back-adjusted** — add each roll's price gap to history: point changes are right,
#   percentage returns are not, and old prices can drift far from reality;
# * **ratio-adjusted** — scale history by each roll's ratio: percentage returns are right.

# %%
spot = data.gbm_prices(500, s0=24_000, mu=0.10, sigma=0.16, seed=16, start="2025-01-01")
prices, table = data.futures_chain(spot, underlying="DEMOIDX", expiry_weekday=1, lot_size=50, seed=16)
master = handler.InstrumentMaster(table)
print(master.table.head(4).to_string())
contract = master.front("DEMOIDX", "2025-06-24", roll_days=2)
print(f"\nFront month on 24 Jun 2025 (roll 2 business days early): {contract}")
print("Order for 75:", master.check_quantity(contract, 75) or "ok", "| price 24,001.03 rounds to",
      master.round_price(contract, 24_001.03))

series = {m: handler.continuous_futures(prices, master, roll_days=2, method=m) for m in ("none", "back", "ratio")}
rolls = series["none"]["roll"]
roll_returns = pd.DataFrame({m: s["price"].pct_change()[rolls] for m, s in series.items()}) * 1e4
print(f"\n{int(rolls.sum())} rolls. Return on roll days (bp): raw shows the carry as a fake move")
print(roll_returns.describe().loc[["mean", "min", "max"]].round(1).to_string())
print(f"Start of history: raw {series['none']['price'].iloc[0]:,.0f}, back-adjusted "
      f"{series['back']['price'].iloc[0]:,.0f}, ratio-adjusted {series['ratio']['price'].iloc[0]:,.0f}")

fig, ax = plt.subplots(figsize=(10, 4))
for m, s in series.items():
    ax.plot(s.index, s["price"], lw=1, label=m)
ax.plot(spot.index, spot, lw=0.8, color="grey", ls=":", label="spot")
ax.set_title("Continuous futures: raw vs back- vs ratio-adjusted")
ax.legend()
print("Chart:", savefig(fig, "lab16a_continuous_futures"))

# %% [markdown]
# ## 6. Storage and deterministic replay
# Store three days of validated ticks partitioned by date and symbol (Parquet when pyarrow
# is installed, CSV otherwise). Loading one day opens only that day's files. Replaying the
# stored ticks through the live bar builder and a toy signal must give exactly the same
# signals every time, and the same as the in-memory run: that is what lets you test live
# code against history.

# %%
root = tempfile.mkdtemp(prefix="ticks_")
three_days, _ = data.tick_stream(n_days=3, seed=61)
validated = handler.validate_ticks(three_days).clean()
paths = handler.store_ticks(validated, root)
print("Partitions:", [str(p.relative_to(root)) for p in paths])
print("One day loaded:", handler.load_ticks(root, start="2026-01-06", end="2026-01-06")["ts"].dt.date.unique())


def run_strategy(source: pd.DataFrame) -> list[tuple]:
    builder, closes, signals = handler.BarBuilder("5min"), [], []

    def on_tick(ts, symbol, price, qty):
        for bar in builder.update(ts, price, qty):
            closes.append(bar["close"])
            if len(closes) > 12:
                signal = "BUY" if closes[-1] > np.mean(closes[-12:]) else "SELL"
                if not signals or signals[-1][1] != signal:
                    signals.append((bar["ts"], signal, bar["close"]))

    handler.replay(source, on_tick)
    return signals


stored = handler.load_ticks(root)
first, second, memory = run_strategy(stored), run_strategy(stored), run_strategy(validated)
print(f"{len(first)} signal changes; replay twice identical: {first == second}; "
      f"stored equals in-memory: {first == memory}")

# %% [markdown]
# ## Exercises
# 1. Lower `spike_z` to 4 and rerun section 3 on the clean day. How many false alarms, and
#    what would each have done to a live stop-loss?
# 2. Set `confirm=1` and rerun the +3% jump. Explain what happens to every price after the jump.
# 3. Build a 5-minute strategy on raw front-month prices and on the ratio-adjusted series.
#    Which trades are caused by rolls rather than by the market?
# 4. Download a day of real bars for one stock (`python -m cfmat.data.fetch yahoo TCS.NS`)
#    and run `data.ohlcv_problems` on them. Report what you find and how you would handle it.
