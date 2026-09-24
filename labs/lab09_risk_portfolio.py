# %% [markdown]
# # Lab 9 — Risk Management and Portfolio Construction (Module 9)
#
# **Goals**
# 1. Measure VaR and expected shortfall three ways and backtest the VaR.
# 2. Size positions from a stop-loss and from ATR; apply volatility targeting.
# 3. Compare equal-weight, minimum-variance, max-Sharpe, risk-parity and HRP
#    portfolios out of sample.
# 4. Run a scenario stress test.

# %%
import pandas as pd

from cfmat import data, portfolio
from cfmat.analytics import indicators, metrics
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

# VaR backtest: a 99% VaR should be breached on ~1% of days.
window = 250
rolling_var = book.rolling(window).quantile(0.01).shift(1)
breaches = (book < rolling_var).iloc[window:]
print(f"Rolling 99% VaR breaches: {breaches.sum()} of {len(breaches)} days ({breaches.mean():.2%}, expected 1.00%)")

# %% [markdown]
# ## 2. Position sizing

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
      f"targeted {metrics.annualized_volatility(targeted.iloc[20:]):.1%}; "
      f"Kelly leverage estimate {risk.kelly_fraction(asset):.2f} (use a fraction of it!)")

# %% [markdown]
# ## 3. Portfolio construction, tested out of sample
# Estimate on 3 years, hold for the next year, roll forward.

# %%
methods = {
    "equal weight": lambda r: pd.Series(1 / r.shape[1], index=r.columns),
    "min variance": lambda r: portfolio.min_variance_weights(r.cov() * 252),
    "max Sharpe": lambda r: portfolio.max_sharpe_weights(r.mean() * 252, r.cov() * 252, rf=0.065),
    "risk parity": lambda r: portfolio.risk_parity_weights(r.cov() * 252),
    "HRP": portfolio.hrp_weights,
}
train, test = 750, 250
oos = {name: [] for name in methods}
for start in range(0, len(rets) - train - test + 1, test):
    est = rets.iloc[start:start + train]
    hold = rets.iloc[start + train:start + train + test]
    for name, fn in methods.items():
        oos[name].append(hold @ fn(est))
summary = pd.DataFrame({name: metrics.performance_summary(pd.concat(parts)) for name, parts in oos.items()})
print(summary.loc[["cagr", "volatility", "sharpe", "max_drawdown"]].T.round(3))

w_hrp = portfolio.hrp_weights(rets)
w_mv = portfolio.min_variance_weights(rets.cov() * 252)
w_ms = portfolio.max_sharpe_weights(rets.mean() * 252, rets.cov() * 252, rf=0.065)
print("\nWeights (full sample):")
print(pd.DataFrame({"HRP": w_hrp, "min variance": w_mv, "max Sharpe": w_ms}).round(3).T)
print("\nMax-Sharpe weights depend on noisy mean estimates — watch how concentrated they get.")

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

# %% [markdown]
# ## Exercises
# 1. Replace the sample covariance with Ledoit–Wolf shrinkage (`sklearn.covariance`). Does min-variance improve?
# 2. Add a 25% single-name cap to max-Sharpe and compare out of sample.
# 3. Write a daily risk report function: VaR, ES, gross/net exposure, top 3 risk contributors.
