# %% [markdown]
# # Lab 20 — Screeners and Instrument Selection (Module 17)
#
# **Goals**
# 1. Compute 25+ analytics for every instrument in a universe (in parallel).
# 2. Label each instrument's regime: trending up / down, range-bound, squeeze, volatile.
# 3. Filter with preset and custom screens; rank with a composite score.
# 4. Scan for candlestick and chart patterns.
# 5. Pick a diversified shortlist.
# 6. Check that the regime label points to the right *strategy family*.
#
# The 40 instruments are fictional, each built with a known behaviour so you can
# grade the screener. On real data, regimes are less clean and change over time:
# re-screen regularly.

# %%
import time

import matplotlib.pyplot as plt
import pandas as pd

from cfmat import data, parallel
from cfmat import screener as sc
from cfmat import strategy_builder as sb
from cfmat.plotting import savefig

pd.set_option("display.width", 180)
pd.set_option("display.max_columns", 14)
WORKERS = min(4, parallel.available_workers())

universe, meta = data.instrument_universe(40, seed=7)
print(f"{len(universe)} instruments, {len(next(iter(universe.values())))} daily bars each")

# %% [markdown]
# ## 1. Screen the universe (serial vs parallel)

# %%
if __name__ == "__main__":        # process pools need this guard on Windows/macOS
    t0 = time.perf_counter()
    table = sc.screen(universe, workers=1)
    t_serial = time.perf_counter() - t0
    t0 = time.perf_counter()
    table = sc.screen(universe, workers=WORKERS, backend="process")
    t_parallel = time.perf_counter() - t0
    print(f"Screening took {t_serial:.2f}s serially and {t_parallel:.2f}s with {WORKERS} processes")

    cols = ["close", "ret_3m", "ret_6m", "vol_20", "adx", "er_60", "trend_slope_1y", "trend_r2_1y",
            "bb_width_pctile", "turnover_cr", "regime"]
    print(table[cols].head(10).round(3))

# %% [markdown]
# ## 2. How good is the regime label? (graded against the hidden archetype)

# %%
if __name__ == "__main__":
    graded = pd.crosstab(meta["archetype"], table["regime"])
    print(graded)
    truth = {"uptrend": "trending_up", "downtrend": "trending_down", "range": "range_bound",
             "squeeze": "squeeze", "volatile": "volatile"}
    print(f"Accuracy: {(meta['archetype'].map(truth) == table['regime']).mean():.0%}")

    fig, ax = plt.subplots(figsize=(8, 5))
    for regime, grp in table.groupby("regime"):
        ax.scatter(grp["trend_slope_1y"], grp["trend_r2_1y"], label=regime, s=40)
    ax.set(xlabel="1-year trend slope (annualised)", ylabel="1-year trend R²", title="Regime map")
    ax.axvline(0, c="grey", lw=0.8)
    ax.legend()
    print("Chart saved to", savefig(fig, "lab20_regime_map"))

# %% [markdown]
# ## 3. Preset and custom screens

# %%
if __name__ == "__main__":
    for name in ("liquid", "trend_up", "trend_down", "range_bound", "squeeze", "high_volatility", "near_52w_high"):
        hits = sc.apply_filters(table, name)
        print(f"{name:<16} {len(hits):>2}  {', '.join(hits.index[:8])}")
    print("\nPreset definitions are plain query strings, e.g. trend_up =", sc.PRESETS["trend_up"])

    custom = sc.apply_filters(table, ["liquid", "trend_up", "rsi_14 < 70", "dist_52w_high > -0.10"])
    print("\nCustom screen — liquid uptrends, not overbought, within 10% of the 52-week high:")
    print(custom[["close", "ret_6m", "rsi_14", "dist_52w_high", "turnover_cr"]].round(3))

# %% [markdown]
# ## 4. Rank, scan patterns, and pick a diversified shortlist

# %%
if __name__ == "__main__":
    liquid = sc.apply_filters(table, "liquid")
    ranked = sc.rank(liquid, {"ret_6m": 1.0, "trend_r2_1y": 0.5, "vol_60": -0.5, "max_dd_1y": 0.5})
    print(ranked[["regime", "ret_6m", "trend_r2_1y", "vol_60", "max_dd_1y", "score"]].head(8).round(3))

    patterns = sc.pattern_scan(universe, ["bullish_engulfing", "hammer", "morning_star", "bearish_engulfing",
                                          "double_bottom", "squeeze", "inside_bar"], lookback=3)
    print(f"\nPatterns in the last 3 bars ({len(patterns)} instruments):")
    print(patterns.astype(int).head(10))

    returns = pd.DataFrame({s: b["close"].pct_change() for s, b in universe.items()})
    shortlist = sc.diversify(returns, ranked.index, n=6, max_corr=0.5)
    print("\nDiversified shortlist (pairwise |corr| < 0.5):", shortlist)

# %% [markdown]
# ## 5. Does the regime point to the right strategy family?
# Run every strategy template on every instrument (in parallel), then average the
# Sharpe ratio by screener regime × strategy category.

# %%
if __name__ == "__main__":
    specs = {k: sb.TEMPLATES[k] for k in ("trend_up_breakout", "trend_down_breakdown", "trend_supertrend",
                                          "range_bollinger_rsi", "range_box", "either_way_squeeze")}
    t0 = time.perf_counter()
    matrix = sb.strategy_matrix(universe, specs, workers=WORKERS, backend="process")
    print(f"{len(matrix)} backtests in {time.perf_counter() - t0:.1f}s")
    matrix["regime"] = matrix["symbol"].map(table["regime"])
    fit = matrix.pivot_table(index="regime", columns="strategy", values="sharpe", aggfunc="mean")
    print(fit.round(2))
    print("\nTrend templates should shine on trending names and range templates on range-bound ones.")
    print("Regimes here were labelled at the END of the sample; in practice, screen and trade forward in time.")

# %% [markdown]
# ## Exercises
# 1. Download 50 Nifty stocks with `cfmat.data.download_prices` and run the same screen.
# 2. Add a sector-relative momentum metric (return minus sector average) to `instrument_metrics`.
# 3. Re-run section 5 walk-forward: classify at each month end using only past data,
#    then trade the suggested template for the next month.
