# Module 06 — Derivatives, Options Pricing and Volatility

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 2 · Trading and Strategy Design | 12–14 | 30 (6 live × 3 h + 6 clinics × 2 h) | [`lab06_options_derivatives.py`](../../labs/lab06_options_derivatives.py) |

## Learning outcomes

1. Price forwards and futures by cost of carry; analyse basis, rollover and calendar spreads.
2. Explain option payoffs, put–call parity and no-arbitrage bounds.
3. Price options with binomial trees and Black–Scholes–Merton; value early exercise.
4. Compute and interpret delta, gamma, vega, theta and rho, and manage a book by its Greeks.
5. Extract implied volatility and read the smile, skew and term structure.
6. Design and evaluate option strategies with defined risk, including margin requirements.
7. Delta-hedge an option and explain P&L in terms of realised vs implied volatility.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Forwards and futures (Sat, W12) | Cost of carry, basis, convergence; index and stock futures on NSE; rollover; cash-and-carry arbitrage |
| L2 | Option basics (Sun, W12) | Payoffs, moneyness, parity, bounds; binomial model and risk-neutral pricing; American exercise |
| L3 | Black–Scholes–Merton (Sat, W13) | Assumptions, derivation intuition, dividends; the Greeks and their behaviour through time and moneyness |
| L4 | Volatility (Sun, W13) | Historical vs implied volatility; smile and skew; term structure; India VIX; event volatility around results and budgets |
| L5 | Strategies and margins (Sat, W14) | Spreads, straddles, strangles, butterflies, iron condors, calendars, covered calls, protective puts; SPAN and exposure margin for option sellers; weekly expiry dynamics |
| L6 | Hedging and volatility trading (Sun, W14) | Delta and gamma hedging, hedging frequency and costs; gamma scalping; variance and volatility premium; tail risk of short-volatility strategies |
| C1–C6 | Clinics | Futures fair value; parity; binomial convergence; Greeks table; IV surface from an option-chain snapshot; Lab 6 |

## Assignment

Using a historical option-chain snapshot (at least three months old), build the IV smile for two expiries, price an iron condor, compute its Greeks and margin, and stress-test it for ±5% and ±10% index moves with a 5-point rise in implied volatility.

## Readings

- John C. Hull, *Options, Futures, and Other Derivatives*: chapters 2–5, 10–15, 19–20.
- Sheldon Natenberg, *Option Volatility and Pricing*: chapters 5–9, 11.
- NISM Series VIII workbook (Equity Derivatives).
- Black and Scholes (1973), "The Pricing of Options and Corporate Liabilities".

## Assessment

Quiz 6; Lab 6; options assignment; NISM Series VIII exam recommended after this module (voucher included).
