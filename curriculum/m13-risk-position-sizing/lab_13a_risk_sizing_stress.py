# %% [markdown]
# # Lab 13a — Measuring Risk, Sizing Positions and Stress Testing (M13)
#
# **Goals**
# 1. Measure VaR and expected shortfall three ways, and backtest the VaR with Kupiec's test.
# 2. See why a VaR that ignores volatility clustering fails in clusters, and how a GARCH
#    forecast fixes it.
# 3. Size positions from a stop-loss, from ATR and by volatility targeting; see what Kelly implies.
# 4. Run a scenario stress test on a derivatives book.

# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

from cfmat import data, econometrics
from cfmat.analytics import indicators, metrics
from cfmat.infra.plotting import savefig
from cfmat.portfolio import risk

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 12)

prices = data.universe(10, 1500, seed=30)
rets = metrics.simple_returns(prices)
book = rets.mean(axis=1)                    # an equal-weight book
book_value = 10_000_000                     # ₹1 crore

# %% [markdown]
# ## 1. VaR and expected shortfall

# %%
for alpha in (0.95, 0.99):
    print(f"{alpha:.0%} 1-day  historical VaR ₹{risk.historical_var(book, alpha) * book_value:>9,.0f} | "
          f"parametric ₹{risk.parametric_var(book, alpha) * book_value:>9,.0f} | "
          f"bootstrap ₹{risk.monte_carlo_var(book, alpha, seed=1) * book_value:>9,.0f} | "
          f"ES ₹{risk.expected_shortfall(book, alpha) * book_value:>9,.0f}")
print(f"10-day 99% VaR (√t rule): ₹{risk.scale_var(risk.historical_var(book, 0.99), 10) * book_value:,.0f}")

# %% [markdown]
# ## 2. Backtesting VaR when volatility clusters
# Real returns have calm and turbulent spells. A 250-day historical VaR reacts slowly; a
# GARCH(1,1) forecast reacts the next day. Both are fitted or estimated on past data only.

# %%
garchy = data.garch_prices(2500, seed=11)
r = metrics.simple_returns(garchy["close"])
train = r.iloc[:1000]
params = econometrics.garch11_fit(train)
sigma_next = econometrics.garch11_forecast(r, params)          # known at t's close, for day t+1
var_garch = -(params["mu"] + norm.ppf(0.01) * sigma_next).shift(1)   # a positive loss number
var_hist = -r.rolling(250).quantile(0.01).shift(1)
test = r.index[1000:]
rows = {}
for name, var in (("historical 250-day", var_hist), ("GARCH(1,1)", var_garch)):
    breaches = (r.loc[test] < -var.loc[test])
    rows[name] = risk.kupiec_test(breaches, 0.99)
    rows[name]["breaches in worst 50 days"] = int(breaches.rolling(50).sum().max())
print(pd.DataFrame(rows).T.round(3).to_string())
print("\nKupiec checks the breach *rate*. Also look at clustering: several breaches in a few weeks")
print("means the model was slow to see risk rising, exactly when it mattered.")

fig, ax = plt.subplots(figsize=(10, 4))
(-r.loc[test]).clip(lower=0).plot(ax=ax, color="grey", lw=0.6, label="daily loss")
var_hist.loc[test].plot(ax=ax, label="historical VaR 99%")
var_garch.loc[test].plot(ax=ax, label="GARCH VaR 99%")
ax.set_title("Losses vs 99% VaR (test period)")
ax.legend()
print("Chart saved to", savefig(fig, "lab13a_var_backtest"))

# %% [markdown]
# ## 3. Position sizing

# %%
capital = 2_500_000
entry, stop = 1_480.0, 1_440.0
print(f"Risk 1% of ₹{capital:,} with a stop ₹{entry - stop:.0f} away → buy "
      f"{risk.fixed_fractional_qty(capital, 0.01, entry, stop)} shares")

bars = data.ohlcv_from_close(prices["SYN01"], seed=1)
atr_now = indicators.atr(bars).iloc[-1]
print(f"ATR ₹{atr_now:.2f}: 2-ATR stop sizing → {risk.atr_stop_qty(capital, 0.01, atr_now, 2.0)} shares")

asset = rets["SYN01"]
lev = risk.volatility_target_leverage(asset, target_vol=0.12, lookback=20)
targeted = asset * lev
print(f"Vol targeting to 12%: raw vol {metrics.annualized_volatility(asset):.1%} → "
      f"targeted {metrics.annualized_volatility(targeted.iloc[20:]):.1%}")

kelly = risk.kelly_fraction(asset)
print(f"Kelly leverage estimate {kelly:.2f}. With a Sharpe estimated from {len(asset)} days, its standard")
sr = metrics.sharpe_ratio(asset)
se = np.sqrt((1 + sr**2 / 2) / (len(asset) / 252))
print(f"error is ≈ {se:.2f} on a Sharpe of {sr:.2f}: full Kelly could easily be 2–3× too big. Use ¼–½ Kelly.")

# Risk of ruin by simulation: how often does a 30% drawdown happen within 2 years?
rng = np.random.default_rng(3)
mu, sd = asset.mean(), asset.std()
for frac in (0.25, 0.5, 1.0, 2.0):
    lev_k = frac * kelly
    paths = np.cumprod(1 + lev_k * rng.normal(mu, sd, size=(2000, 504)), axis=1)
    dd = 1 - paths / np.maximum.accumulate(paths, axis=1)
    print(f"{frac:>4} × Kelly (leverage {lev_k:4.1f}): P(30% drawdown within 2 years) = {(dd.max(axis=1) > 0.3).mean():.0%}")

# %% [markdown]
# ## 4. Stress test

# %%
positions = {"NIFTY_FUT": 5_000_000, "BANKNIFTY_FUT": 3_000_000, "IT_BASKET": 2_000_000, "GOLD_ETF": 1_000_000}
scenarios = {
    "Covid crash (Mar-2020 style)": {"NIFTY_FUT": -0.23, "BANKNIFTY_FUT": -0.33, "IT_BASKET": -0.18, "GOLD_ETF": 0.03},
    "Rate shock +200bp": {"NIFTY_FUT": -0.08, "BANKNIFTY_FUT": -0.12, "IT_BASKET": -0.05, "GOLD_ETF": -0.04},
    "Rupee depreciation 10%": {"NIFTY_FUT": -0.05, "BANKNIFTY_FUT": -0.06, "IT_BASKET": 0.07, "GOLD_ETF": 0.09},
}
print((risk.stress_test(positions, scenarios) / 1e5).round(1).rename(columns=lambda c: f"{c} (₹ lakh)"))
print("\nCompare the worst scenario with the 99% 1-day VaR: stress losses are several times larger.")

# %% [markdown]
# ## Exercises
# 1. Add a Christoffersen independence test: are breaches on consecutive days more likely than chance?
# 2. Replace the Gaussian GARCH VaR with a filtered historical simulation (standardised residuals).
# 3. Write a daily risk report function: VaR, ES, gross/net exposure, top 3 risk contributors,
#    limit utilisation with red/amber/green flags.
