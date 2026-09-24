# %% [markdown]
# # Lab 5 — Technical, Fundamental and Quantamental Analysis (Module 5)
#
# **Goals**
# 1. Compute the standard indicators from first principles.
# 2. Test a technical rule as a hypothesis with an event study, not a chart.
# 3. Build a multi-factor (value + quality + momentum) stock screen.

# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cfmat import data
from cfmat.analytics import indicators as ind
from cfmat.infra.plotting import savefig

bars = data.ohlcv_from_close(data.ar1_prices(1500, phi=0.05, seed=12), seed=12)
close = bars["close"]

# %% [markdown]
# ## 1. Indicator dashboard

# %%
dash = pd.DataFrame({
    "close": close,
    "sma_50": ind.sma(close, 50),
    "ema_20": ind.ema(close, 20),
    "rsi_14": ind.rsi(close, 14),
    "atr_14": ind.atr(bars, 14),
}).join(ind.macd(close)).join(ind.bollinger_bands(close).add_prefix("bb_"))
print(dash.tail(3).round(2).T)

fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
view = dash.iloc[-250:]
view[["close", "bb_upper", "bb_lower", "sma_50"]].plot(ax=axes[0], title="Price, Bollinger bands, SMA 50")
view["rsi_14"].plot(ax=axes[1], title="RSI 14")
axes[1].axhline(70, ls="--", c="grey")
axes[1].axhline(30, ls="--", c="grey")
view["histogram"].plot(ax=axes[2], kind="line", title="MACD histogram")
print("Chart saved to", savefig(fig, "lab05_indicators"))

# %% [markdown]
# ## 2. Event study: does "RSI below 30" predict a bounce?
# Compare forward returns after the signal with forward returns on all days.

# %%
fwd = pd.DataFrame({f"fwd_{h}d": close.shift(-h) / close - 1 for h in (1, 5, 10, 20)})
events = dash["rsi_14"] < 30
events = events & ~events.shift(1, fill_value=False)   # first day of each oversold spell
study = pd.DataFrame({
    "after RSI<30": fwd[events].mean(),
    "all days": fwd.mean(),
    "hit rate after signal": (fwd[events] > 0).mean(),
})
study["edge"] = study["after RSI<30"] - study["all days"]
print(f"{events.sum()} signal days")
print((study * 100).round(2).rename(columns=lambda c: c + " (%)"))
print("\nWith so few events, check the standard error before believing any edge.")

# %% [markdown]
# ## 3. Quantamental screen
# Fictional fundamentals for 30 companies. We z-score each factor across the
# universe, flip signs where lower is better, and rank on the composite.

# %%
rng = np.random.default_rng(5)
n = 30
fund = pd.DataFrame({
    "company": [f"Company {chr(65 + i // 26)}{chr(65 + i % 26)}" for i in range(n)],
    "pe": rng.lognormal(3.1, 0.4, n).round(1),
    "roe": rng.normal(0.15, 0.06, n).round(3),
    "debt_equity": rng.lognormal(-0.7, 0.6, n).round(2),
    "ret_12m": rng.normal(0.12, 0.25, n).round(3),
}).set_index("company")


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()


factors = pd.DataFrame({
    "value": zscore(-np.log(fund["pe"])),        # cheap = high earnings yield
    "quality": zscore(fund["roe"]) - 0.5 * zscore(fund["debt_equity"]),
    "momentum": zscore(fund["ret_12m"]),
})
fund["composite"] = factors.mean(axis=1)
fund["rank"] = fund["composite"].rank(ascending=False).astype(int)
print(fund.sort_values("rank").head(8))
print("\nFactor correlations:\n", factors.corr().round(2))

# %% [markdown]
# ## Exercises
# 1. Repeat the event study for "close crosses above the upper Bollinger band".
# 2. Winsorise the fundamentals at the 5th/95th percentiles before z-scoring. Does the top 10 change?
# 3. Download real financial statements for 20 Nifty stocks and run the screen.
