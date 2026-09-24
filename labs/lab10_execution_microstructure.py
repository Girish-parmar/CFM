# %% [markdown]
# # Lab 10 — Market Microstructure and Execution Algorithms (Module 10)
#
# **Goals**
# 1. Operate a price–time-priority limit order book and watch the spread form.
# 2. Build TWAP, VWAP and POV schedules for a large order.
# 3. Trace the Almgren–Chriss cost/risk trade-off.
# 4. Estimate market impact and measure implementation shortfall.

# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cfmat import data, microstructure
from cfmat.infra.plotting import savefig

rng = np.random.default_rng(10)
TICK = 0.05


def to_tick(price: float) -> float:
    return round(round(price / TICK) * TICK, 2)

# %% [markdown]
# ## 1. A limit order book with random order flow

# %%
book = microstructure.OrderBook()
for i in range(1, 6):                      # seed five levels either side of 1,000
    book.add_limit("BUY", to_tick(1000 - TICK * i), int(rng.integers(50, 300)))
    book.add_limit("SELL", to_tick(1000 + TICK * i), int(rng.integers(50, 300)))
print("Initial book:\n", book.depth(5))

spreads, mids = [], []
for _ in range(2000):
    mid = book.mid() or 1000.0
    u = rng.random()
    if u < 0.45:        # passive limit order near the touch
        side = "BUY" if rng.random() < 0.5 else "SELL"
        offset = TICK * int(rng.integers(1, 6))
        price = to_tick(mid - offset if side == "BUY" else mid + offset)
        book.add_limit(side, price, int(rng.integers(10, 200)))
    elif u < 0.75:      # aggressive market order
        book.add_market("BUY" if rng.random() < 0.5 else "SELL", int(rng.integers(10, 150)))
    else:               # cancellation of a random resting order
        resting = book.resting_order_ids()
        if resting:
            book.cancel(int(rng.choice(resting)))
    if book.spread() is not None:
        spreads.append(book.spread())
        mids.append(book.mid())
print(f"\n{len(book.trades)} trades. Median spread {np.median(spreads):.2f}, "
      f"mid moved {mids[0]:.2f} → {mids[-1]:.2f}")
print("Final top of book:\n", book.depth(3))

# %% [markdown]
# ## 2. Execution schedules for 2,00,000 shares over one session (25 × 15-min buckets)

# %%
qty = 200_000
profile = data.intraday_volume_profile(25)
market_volume = profile * 4_000_000        # forecast daily volume 40 lakh shares
sched = pd.DataFrame({
    "TWAP": microstructure.twap_schedule(qty, 25),
    "VWAP": microstructure.vwap_schedule(qty, profile),
    "POV 10%": microstructure.pov_schedule(qty, market_volume, 0.10),
}, index=pd.date_range("2026-01-05 09:15", periods=25, freq="15min").strftime("%H:%M"))
print(sched.head(4), "\n...\n", sched.tail(2))
print("Totals:", sched.sum().to_dict())
print(f"Peak participation — TWAP {(sched['TWAP'] / market_volume).max():.1%}, "
      f"VWAP {(sched['VWAP'] / market_volume).max():.1%}")

# %% [markdown]
# ## 3. Almgren–Chriss: faster is costlier, slower is riskier

# %%
X, horizon, n = 1_000_000, 1.0, 20        # sell 10 lakh shares over one day in 20 steps
sigma, eta, gamma = 0.95, 2.5e-6, 2.5e-7  # impact parameters from the paper's worked example
frontier = []
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for lam in (0.0, 1e-7, 1e-6, 1e-5):
    path = microstructure.almgren_chriss_trajectory(X, horizon, n, sigma, eta, gamma, lam)
    cost = microstructure.almgren_chriss_cost(path, horizon, sigma, eta, gamma)
    frontier.append({"lambda": lam, **cost})
    ax[0].plot(np.linspace(0, horizon, n + 1), path, label=f"λ={lam:g}")
print(pd.DataFrame(frontier).to_string(index=False, formatters={
    "lambda": "{:g}".format, "expected_cost": "₹{:,.0f}".format, "variance": "{:.3g}".format, "std": "₹{:,.0f}".format}))
ax[0].set(title="Holdings over time", xlabel="time (days)", ylabel="shares")
ax[0].legend()
fdf = pd.DataFrame(frontier)
ax[1].plot(fdf["std"], fdf["expected_cost"], marker="o")
ax[1].set(title="Efficient frontier of execution", xlabel="std of cost (₹)", ylabel="expected cost (₹)")
print("Chart saved to", savefig(fig, "lab10_almgren_chriss"))

# %% [markdown]
# ## 4. Impact estimate and implementation shortfall

# %%
adv, daily_vol = 4_000_000, 0.018
for q in (20_000, 200_000, 800_000):
    print(f"Order {q:>7,} shares ({q / adv:5.1%} of ADV) → expected impact "
          f"{microstructure.square_root_impact_bps(q, adv, daily_vol):5.1f} bps")

decision = 1_000.0
path = decision * np.exp(np.cumsum(rng.normal(0.0002, 0.0015, 25)))
fills = []
for i, (slice_qty, px) in enumerate(zip(sched["VWAP"], path)):
    if i >= 22:           # pretend the algo stopped early
        break
    # square-root law applied per bucket: bucket volatility and bucket volume
    impact = microstructure.square_root_impact_bps(slice_qty, market_volume[i], daily_vol / np.sqrt(25)) / 1e4
    fills.append((int(slice_qty), px * (1 + impact)))
print(pd.Series(microstructure.implementation_shortfall("BUY", decision, fills, qty, path[-1])).round(2))

# %% [markdown]
# ## Exercises
# 1. Add iceberg orders to `OrderBook` (only part of the quantity is visible).
# 2. Make the VWAP schedule adaptive: re-plan each bucket from actual volume.
# 3. Estimate η for a real stock from its spread and ADV, then re-run section 3.
