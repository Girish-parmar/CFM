# Module 09 — Risk Management and Portfolio Construction

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 3 · Risk, Portfolio and Execution | 20–21 | 20 | [`lab09_risk_portfolio.py`](../../labs/lab09_risk_portfolio.py) |

## Learning outcomes

1. Measure VaR (historical, parametric, Monte Carlo) and expected shortfall, and backtest a VaR model.
2. Design and run stress and scenario tests.
3. Size positions with fixed-fractional, ATR, Kelly and volatility-targeting methods, and set drawdown controls.
4. Build mean–variance, minimum-variance, risk-parity and HRP portfolios and compare them out of sample.
5. Explain estimation error and use shrinkage to reduce it.
6. Write a daily risk report for a trading book.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Measuring risk (Sat, W20) | Volatility, VaR, expected shortfall; square-root-of-time and its limits; VaR backtesting (Kupiec test) |
| L2 | Stress testing (Sun, W20) | Historical scenarios (2008, 2013 taper tantrum, 2016 demonetisation, 2020 Covid), hypothetical shocks, liquidity risk, margin calls, correlation breakdown |
| L3 | Sizing and drawdowns (Sat, W21) | Fixed fractional, ATR stops, Kelly and fractional Kelly, volatility targeting, drawdown-based de-risking, risk of ruin |
| L4 | Portfolio construction (Sun, W21) | Markowitz and its instability; minimum variance; risk parity; Hierarchical Risk Parity; Ledoit–Wolf shrinkage; constraints and turnover |
| C1–C4 | Clinics | Risk report builder; VaR backtest; optimiser comparison; Lab 9 |

## Assignment

Build a one-page daily risk report for a multi-strategy paper book: gross and net exposure, VaR and ES, top risk contributors, stress-test table, and limit utilisation with red/amber/green flags.

## Readings

- Philippe Jorion, *Value at Risk*: chapters 1–5.
- Grinold and Kahn, *Active Portfolio Management*: chapters on risk.
- López de Prado (2016), "Building Diversified Portfolios that Outperform Out of Sample" (HRP).
- Ledoit and Wolf (2004), "Honey, I Shrunk the Sample Covariance Matrix".

## Assessment

Quiz 9; Lab 9; risk report assignment.
