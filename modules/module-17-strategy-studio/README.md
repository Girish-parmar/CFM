# Module 17 — Strategy Studio: Screeners, Strategy Creator, F&O Backtesting and Parallel Research

| Term | Weeks | Hours | Labs |
|---|---|---|---|
| 5 · Strategy Studio, Capstone and Career | 37–38 | 20 (4 live × 3 h + 4 clinics × 2 h) | [`lab20_screener_instrument_selection.py`](../../labs/lab20_screener_instrument_selection.py), [`lab21_strategy_creator_parallel.py`](../../labs/lab21_strategy_creator_parallel.py), [`lab22_futures_options_strategies.py`](../../labs/lab22_futures_options_strategies.py) |

This module turns everything before it into a working research toolkit that learners then use for their capstone. Code: `cfmat.screener`, `cfmat.patterns`, `cfmat.strategy_builder`, `cfmat.report`, `cfmat.futures`, `cfmat.options_backtest`, `cfmat.parallel`.

## Learning outcomes

1. Screen a universe with 25+ analytics (returns, trend strength and fit, volatility, squeeze, liquidity, beta, drawdown), label each instrument's regime, and build preset and custom screens, composite rankings, pattern scans and diversified shortlists.
2. Detect candlestick patterns (engulfing, hammer, doji, stars, soldiers/crows…) and chart structures (swing highs/lows, higher highs and lows, double tops/bottoms, consolidation, squeeze) without look-ahead.
3. Write strategies as readable rules over indicators, prices, patterns and parameters. Use the library of trend-up, trend-down, both-way trend, range-bound, either-way breakout and pattern strategies.
4. Backtest with realistic execution (next-open fills, slippage, ATR stops, targets, trailing stops, time exits, reversals) and read a full report: trade list, win rate, payoff, expectancy, streaks, exposure, monthly table.
5. Backtest futures strategies with lots, margin, monthly rollover and charges, and test cash-and-carry arbitrage against real costs.
6. Backtest option structures (straddles, strangles, iron condors, debit spreads) with daily re-pricing, Greeks, profit targets, stops and regime-based entry filters.
7. Speed up research with process and thread pools, explain why threads don't help Python-heavy loops, and search parameters smarter (coarse-to-fine) instead of brute force, then validate walk-forward.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Screeners and instrument selection (Sat, W37) | What makes an instrument tradable (liquidity, impact, costs); trend strength (ADX, efficiency ratio, regression slope and R², Hurst); volatility squeezes; regime labels and their error rates; composite ranking; correlation-aware shortlists; pattern scanners; compliance: screener output is research, not a recommendation |
| L2 | The Strategy Creator (Sun, W37) | Strategy families and when each works; rules, parameters and patterns; the execution model (why fills happen at the next open); stops, targets, trailing stops and time exits; reading a trade-level report; strategy-instrument fit |
| C1 | Clinic (Tue, W37) | Lab 20: screen a universe, grade the regime labels, strategy-fit matrix |
| C2 | Clinic (Thu, W37) | Lab 21 part 1: build, save and backtest your own strategy from rules |
| L3 | Faster and smarter research (Sat, W38) | Processes vs threads and the GIL; sharing data with workers; chunking; reproducibility; coarse-to-fine search; walk-forward; charging for trials (Deflated Sharpe) |
| L4 | Futures and options strategy backtesting (Sun, W38) | Lots, margin and rollover; basis and calendar spread; cash-and-carry arbitrage after STT and charges; option structures by market view; re-pricing and Greeks; profit targets and stops for credit and debit trades; tail risk behind high win rates; regime filters |
| C3 | Clinic (Tue, W38) | Lab 21 part 2: parallel sweep benchmark, coarse-to-fine, walk-forward |
| C4 | Clinic (Thu, W38) | Lab 22: futures trend strategy, basis trade, seven option structures with regime filters |

## What the labs show

| Lab | Result you should reproduce |
|---|---|
| 20 | The regime labels are correct for roughly three-quarters of instruments; running every template on every instrument shows trend strategies earning on trending names and losing on range-bound ones, and the reverse for range strategies |
| 21 | A custom rule-based strategy is saved to JSON, reloaded and backtested with a full report; 216-combination sweeps run about 3–4× faster on 4 processes while threads are *slower* (GIL); coarse-to-fine finds the grid winner with fewer than half the evaluations; walk-forward Sharpe is below the best in-sample Sharpe |
| 22 | A Supertrend signal on index futures survives rollovers and charges; cash-and-carry arbitrage wins almost always before costs and mostly loses after retail charges; option sellers earn the volatility premium with large worst-case losses, buyers pay it; regime filters raise average trades and cut worst losses |

## Assignment

Build a complete screen → strategy → backtest pipeline for one idea of your choice: a screen that selects instruments, a strategy written in the rule language, a walk-forward backtest run in parallel, and either a futures or an options implementation of the same view. Report the number of configurations you tried and the Deflated Sharpe Ratio. This pipeline usually becomes the starting point of the capstone.

## Readings

- Andreas Clenow, *Following the Trend* and *Trading Evolved* (systematic trend following and backtesting practice).
- Steve Nison, *Japanese Candlestick Charting Techniques* (read alongside Aronson's *Evidence-Based Technical Analysis*).
- Sheldon Natenberg, *Option Volatility and Pricing*, chapters on spreads and volatility trading.
- Python documentation: `concurrent.futures`; David Beazley's talks on the GIL.
- NSE/BSE circulars on F&O contract specifications (lot sizes, expiry days) and SPAN margins; your broker's charge sheet.

## Assessment

Quiz 17; Labs 20–22; the pipeline assignment feeds the capstone pre-registration.
