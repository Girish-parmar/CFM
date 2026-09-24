# Module 03 — Quantitative Methods and Financial Statistics

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 1 · Market Foundations | 5–6 | 20 | [`lab03_quant_statistics.py`](../../labs/lab03_quant_statistics.py) |

## Learning outcomes

1. Describe return distributions and measure skew, kurtosis and tail risk.
2. Estimate parameters with confidence intervals and test hypotheses correctly.
3. Fit and interpret linear regressions, including CAPM alpha and beta.
4. Test time series for autocorrelation and stationarity; understand ARMA and GARCH.
5. Test for cointegration and explain why it underpins pairs trading.
6. Use Monte Carlo simulation and the bootstrap to measure uncertainty.
7. Use matrix algebra for portfolio variance and covariance.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Distributions (Sat, W5) | Simple vs log returns, compounding; normal, lognormal, Student-t; skew, kurtosis, Jarque–Bera; fat tails and what they do to risk estimates |
| L2 | Inference and regression (Sun, W5) | Estimation, standard errors, t-tests, p-values and their misuse; OLS, CAPM, multi-factor regression; heteroskedasticity-robust errors |
| C1 | Clinic (Tue, W5) | Monte Carlo and bootstrap exercises |
| C2 | Clinic (Thu, W5) | CAPM betas for a stock universe |
| L3 | Time series (Sat, W6) | Autocorrelation, Ljung–Box; random walks and unit roots; ADF; ARMA; volatility clustering and GARCH(1,1) |
| L4 | Cointegration and linear algebra (Sun, W6) | Engle–Granger and Johansen tests; spreads and half-life; vectors, matrices, covariance, eigen-decomposition and PCA |
| C3 | Clinic (Tue, W6) | Lab 3 |
| C4 | Clinic (Thu, W6) | Quiz review; problem set |

## Assignment

Take five years of daily returns for three stocks and an index. Report distribution statistics, rolling one-year betas, an ADF test on prices and returns, and a bootstrap 95% interval for each stock's Sharpe ratio. Explain in plain language what the intervals imply for anyone claiming a "high Sharpe" strategy.

## Readings

- Ruppert and Matteson, *Statistics and Data Analysis for Financial Engineering*: chapters 2–5, 9, 12.
- Ruey S. Tsay, *Analysis of Financial Time Series*: chapters 1–3.
- Engle and Granger (1987), "Co-integration and Error Correction".

## Assessment

Quiz 3; Lab 3; problem set (part of the lab score).
