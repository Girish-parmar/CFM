# %% [markdown]
# # Lab 1 — Markets, Instruments and the Mechanics of a Trade (Module 1)
#
# **Goals**
# 1. Compute contract notional, margin and leverage for an index future.
# 2. Price a future by cost of carry and read the basis.
# 3. Back-adjust a price history for a stock split and a bonus issue.
# 4. Work out T+1 settlement dates around exchange holidays.
#
# Numbers such as lot sizes, margin rates and holidays change through exchange
# circulars. They are parameters here: always check the current NSE/BSE notices.

# %%
import pandas as pd

from cfmat.derivatives.options import futures_fair_value

# %% [markdown]
# ## 1. Contract notional, margin and leverage

# %%
index_level = 24_500.0
lot_size = 75            # illustrative — NSE revises index lot sizes periodically
margin_rate = 0.12       # illustrative SPAN + exposure margin as a share of notional

notional = index_level * lot_size
margin = notional * margin_rate
print(f"Notional per lot : ₹{notional:,.0f}")
print(f"Margin per lot   : ₹{margin:,.0f}")
print(f"Leverage         : {notional / margin:.1f}x")
for move in (-0.02, -0.01, 0.01, 0.02):
    pnl = notional * move
    print(f"Index {move:+.0%} → P&L ₹{pnl:+,.0f} = {pnl / margin:+.1%} of margin")

# %% [markdown]
# ## 2. Futures fair value and basis
# F = S·e^{(r−q)T}. When the market future trades above fair value, a cash-and-carry
# arbitrageur buys spot and sells the future.

# %%
r, q = 0.065, 0.013  # risk-free rate and dividend yield (annual, continuous)
for days in (7, 30, 60, 90):
    fair = futures_fair_value(index_level, days / 365, r, q)
    print(f"{days:>3} days: fair value {fair:,.1f}  basis {fair - index_level:+.1f} points")

market_future = 24_720.0
fair_30 = futures_fair_value(index_level, 30 / 365, r, q)
print(f"\nMarket future {market_future:,.0f} vs fair {fair_30:,.1f}: mispricing {market_future - fair_30:+.1f} points")
print("Before trading it, subtract costs: STT, brokerage, impact and the funding spread.")

# %% [markdown]
# ## 3. Corporate actions: back-adjusting history
# A 1:2 split halves the price. Without adjustment, a backtest sees a fake 50% crash.

# %%
dates = pd.bdate_range("2026-01-05", periods=10)
raw = pd.Series([1000, 1010, 1005, 1020, 510, 515, 512, 520, 346, 350], index=dates, dtype=float)
actions = pd.DataFrame(
    {"ex_date": [dates[4], dates[8]], "factor": [0.5, 2 / 3], "type": ["1:2 split", "1:2 bonus"]}
)
# Bonus 1:2 = one new share for every two held, so price × 2/3.
adjusted = raw.copy()
for _, act in actions.iterrows():
    adjusted[adjusted.index < act["ex_date"]] *= act["factor"]
table = pd.DataFrame({"raw": raw, "adjusted": adjusted.round(2),
                      "raw_ret": raw.pct_change().round(4), "adj_ret": adjusted.pct_change().round(4)})
print(table)

# %% [markdown]
# ## 4. T+1 settlement
# Indian equities settle T+1: shares and funds move on the next *settlement* day.

# %%
holidays = pd.to_datetime(["2026-01-26", "2026-03-04"])  # illustrative subset
bday = pd.offsets.CustomBusinessDay(holidays=holidays)
for trade_date in pd.to_datetime(["2026-01-22", "2026-01-23", "2026-03-03"]):
    print(f"Trade {trade_date:%a %d-%b} → settles {trade_date + bday:%a %d-%b}")

# %% [markdown]
# ## Exercises
# 1. Recompute section 1 for Bank Nifty with its current lot size and margin.
# 2. Find a real split or bonus from an exchange announcement and check that your
#    adjusted series has no artificial jump.
# 3. Add brokerage, STT and exchange charges (see `cfmat.backtest.IndianCostModel`)
#    to the cash-and-carry trade in section 2. Is it still profitable?
