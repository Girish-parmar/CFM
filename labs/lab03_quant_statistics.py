# %% [markdown]
# # Lab 3 — Quantitative Methods and Financial Statistics (Module 3)
#
# **Goals**
# 1. Show that returns have fat tails, and what that does to risk estimates.
# 2. Test for autocorrelation and stationarity (Ljung–Box, ADF).
# 3. Estimate CAPM alpha and beta by regression.
# 4. Test a pair for cointegration (Engle–Granger).
# 5. Put a confidence interval on a Sharpe ratio with the bootstrap.

# %%
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import adfuller, coint

from cfmat import data, metrics

rng = np.random.default_rng(7)


def adf_pvalue(series) -> float:
    with warnings.catch_warnings():  # statsmodels 0.15 announces a return-type change
        warnings.simplefilter("ignore", FutureWarning)
        return adfuller(series)[1]

# %% [markdown]
# ## 1. Fat tails
# Real daily returns look more like a Student-t with 3–5 degrees of freedom than
# a normal distribution. We simulate both with the same volatility.

# %%
n = 5000
normal = pd.Series(rng.normal(0, 0.01, n))
t3 = pd.Series(rng.standard_t(3, n) * 0.01 / np.sqrt(3))  # scaled to the same std
for name, r in [("normal", normal), ("student-t(3)", t3)]:
    jb = stats.jarque_bera(r)
    beyond_4sd = (r.abs() > 4 * r.std()).sum()
    print(f"{name:>13}: excess kurtosis {stats.kurtosis(r):6.2f}  JB p-value {jb.pvalue:.3g}  "
          f"days beyond 4σ: {beyond_4sd} (normal theory expects {n * 2 * stats.norm.sf(4):.2f})")

# %% [markdown]
# ## 2. Autocorrelation and stationarity
# Prices wander (non-stationary); returns fluctuate around a mean (stationary).
# The AR(1) series has planted momentum that Ljung–Box should detect.

# %%
close = data.ar1_prices(1500, phi=0.12, seed=3)
rets = metrics.log_returns(close)
print(f"ADF on prices : p = {adf_pvalue(close):.3f}  (high → unit root, non-stationary)")
print(f"ADF on returns: p = {adf_pvalue(rets):.3g}  (low → stationary)")
lb = acorr_ljungbox(rets, lags=[1, 5, 10])
print("Ljung–Box on AR(1) returns:\n", lb.round(4))
print(f"Lag-1 autocorrelation: {rets.autocorr(1):.3f} (planted phi = 0.12)")

# %% [markdown]
# ## 3. CAPM regression: r_stock − r_f = α + β (r_market − r_f) + ε

# %%
prices = data.universe(5, 1000, seed=11)
rets_u = metrics.simple_returns(prices)
market = rets_u.mean(axis=1)            # equal-weight proxy for the index
rf_daily = 0.065 / 252
y = rets_u["SYN01"] - rf_daily
X = sm.add_constant((market - rf_daily).rename("market"))
capm = sm.OLS(y, X).fit()
print(capm.summary().tables[1])
print(f"Annualised alpha: {capm.params['const'] * 252:.2%}, beta: {capm.params['market']:.2f}, R²: {capm.rsquared:.2f}")

# %% [markdown]
# ## 4. Cointegration: the statistical basis of pairs trading

# %%
pair = data.cointegrated_pair(1000, seed=5)
unrelated = data.gbm_prices(1000, seed=99)
print(f"Cointegrated pair  : Engle–Granger p = {coint(pair['y'], pair['x'])[1]:.4f}")
print(f"Unrelated random walk: Engle–Granger p = {coint(pair['y'], unrelated.to_numpy())[1]:.4f}")

# %% [markdown]
# ## 5. How sure are we about a Sharpe ratio?

# %%
strategy = pd.Series(rng.normal(0.0004, 0.01, 750))  # three years of a modest strategy
point = metrics.sharpe_ratio(strategy)
boot = [metrics.sharpe_ratio(pd.Series(rng.choice(strategy, len(strategy)))) for _ in range(2000)]
lo, hi = np.percentile(boot, [2.5, 97.5])
t_stat, p_value = stats.ttest_1samp(strategy, 0.0)
print(f"Sharpe {point:.2f}, 95% bootstrap CI [{lo:.2f}, {hi:.2f}]")
print(f"t-test of mean > 0: t = {t_stat:.2f}, one-sided p = {p_value / 2:.3f}")
print(f"Probabilistic Sharpe Ratio (true SR > 0): {metrics.probabilistic_sharpe_ratio(strategy):.2%}")

# %% [markdown]
# ## Exercises
# 1. Download Nifty 50 returns and repeat section 1. How many 4σ days since 2008?
# 2. Estimate rolling 1-year betas for five stocks; plot how unstable they are.
# 3. How many years of data would the strategy in section 5 need before its
#    bootstrap interval excludes zero?
