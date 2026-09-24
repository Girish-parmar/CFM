# %% [markdown]
# # Lab 2 — Python for Financial Analysis (Module 2)
#
# **Goals**: load prices, compute simple and log returns, resample, measure
# rolling volatility and drawdowns, and build a month-by-year returns table.
#
# Set `USE_REAL_DATA = True` (needs `pip install yfinance` and internet) to use a
# real NSE symbol instead of the synthetic series.

# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cfmat import data, metrics
from cfmat.plotting import savefig

USE_REAL_DATA = False
SYMBOL = "^NSEI"

bars = data.download_prices(SYMBOL, start="2019-01-01") if USE_REAL_DATA else data.ohlcv(1260, seed=42, start="2021-01-01")
close = bars["close"]
print(bars.tail())
print(f"\n{len(bars)} bars from {bars.index[0]:%d-%b-%Y} to {bars.index[-1]:%d-%b-%Y}")

# %% [markdown]
# ## Simple vs log returns
# Simple returns aggregate across assets; log returns aggregate across time.

# %%
simple = metrics.simple_returns(close)
logr = metrics.log_returns(close)
print(f"Sum of log returns     : {logr.sum():.4f} → growth {np.exp(logr.sum()):.4f}")
print(f"Product of simple (1+r): {(1 + simple).prod():.4f}")
print(f"Actual growth          : {close.iloc[-1] / close.iloc[0]:.4f}")

# %% [markdown]
# ## Resampling to weekly and monthly bars

# %%
weekly = bars.resample("W-FRI").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
monthly_ret = close.resample("ME").last().pct_change().dropna()
print(weekly.tail(3))
print(f"\nBest month {monthly_ret.max():.2%} ({monthly_ret.idxmax():%b-%Y}), "
      f"worst {monthly_ret.min():.2%} ({monthly_ret.idxmin():%b-%Y})")

# %% [markdown]
# ## Month × year returns table (a staple of fund factsheets)

# %%
table = monthly_ret.to_frame("ret").assign(year=lambda d: d.index.year, month=lambda d: d.index.strftime("%b"))
pivot = table.pivot(index="year", columns="month", values="ret")
pivot = pivot[[m for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] if m in pivot]]
print((pivot * 100).round(1))

# %% [markdown]
# ## Rolling volatility and drawdown

# %%
roll_vol = logr.rolling(20).std() * np.sqrt(252)
equity = metrics.equity_curve(simple)
dd = metrics.drawdown_series(equity)
print(metrics.performance_summary(simple).round(3))

fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
close.plot(ax=axes[0], title="Close")
roll_vol.plot(ax=axes[1], title="20-day annualised volatility")
dd.plot(ax=axes[2], title="Drawdown", color="tab:red")
print("Chart saved to", savefig(fig, "lab02_price_vol_drawdown"))

# %% [markdown]
# ## Exercises
# 1. Switch to real data for three NSE stocks and compare their volatility.
# 2. Write a function `rolling_beta(stock, index, window)` using pandas only.
# 3. Vectorisation drill: compute a 50-day SMA with a Python loop and with
#    `rolling().mean()`, time both with `%timeit`, and explain the gap.
