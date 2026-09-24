# %% [markdown]
# # Lab 22 — Futures and Options Strategies (Module 17)
#
# **Goals**
# 1. Build a futures curve with monthly expiries, and see basis and carry.
# 2. Trade a Strategy Creator signal on index futures: lots, margin, rollovers, charges.
# 3. Test cash-and-carry arbitrage and find what it needs to beat costs.
# 4. Backtest seven option structures (in parallel) across bull, bear, range
#    and volatile conditions, with profit targets and stops.
# 5. Use the screener's regime logic as an entry filter for each option structure.
#
# Expiry weekday, lot size, strike step and margin rates are parameters; set them
# from the current exchange circulars. Option prices here come from Black–Scholes
# on a synthetic implied-volatility index, not from a real option chain.

# %%
import numpy as np
import pandas as pd

from cfmat import data, studio
from cfmat.analytics import metrics
from cfmat.derivatives import futures as fu
from cfmat.derivatives import option_strategies
from cfmat.infra import parallel
from cfmat.infra.plotting import plt, savefig

pd.set_option("display.width", 180)
pd.set_option("display.max_columns", 14)
WORKERS = min(4, parallel.available_workers())
LOT, STEP, EXPIRY_WEEKDAY = 75, 50, 1          # illustrative: lot size, strike step, expiry weekday (0 = Mon)

market = data.regime_prices(1500, seed=5)       # calm bull regimes and turbulent bear regimes
scale = 24_000 / market["close"].iloc[0]
bars = data.ohlcv_from_close(market["close"] * scale, seed=5)   # an index-like series around 24,000
spot = bars["close"]
iv = data.implied_vol_series(spot, premium=0.15, seed=1)
print(f"Index from {spot.iloc[0]:,.0f} to {spot.iloc[-1]:,.0f}; implied vol {iv.min():.0%}–{iv.max():.0%} "
      f"(median {iv.median():.0%})")

# %% [markdown]
# ## 1. Futures curve: basis, carry and expiry

# %%
curve = fu.futures_curve(spot, r=0.065, q=0.012, expiry_weekday=EXPIRY_WEEKDAY, seed=1)
view = curve.assign(basis=curve["near"] - curve["spot"], calendar_spread=curve["next"] - curve["near"])
print(view[["spot", "near", "next", "dte", "basis", "calendar_spread"]].iloc[:3].round(1))
print(f"\n{int(curve['is_expiry'].sum())} monthly expiries; average basis {view['basis'].mean():.1f} points, "
      f"average calendar spread {view['calendar_spread'].mean():.1f} points")

# %% [markdown]
# ## 2. A trend strategy on index futures

# %%
capital = 2_000_000
signal = studio.backtest(bars, studio.TEMPLATES["trend_supertrend"]).position          # +1 / −1 / 0, decided the day before
lots_per_signal = fu.lots_for_capital(capital, curve["near"].iloc[0], LOT, margin_rate=0.12, max_margin_use=0.3)
daily, summary = fu.backtest_futures(curve, signal * lots_per_signal, lot_size=LOT, capital=capital, margin_rate=0.12)
print(f"Trading {lots_per_signal} lot(s) per signal on ₹{capital:,.0f} capital")
print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in summary.items()})
fut_r = daily["return"]
print(f"Futures strategy: CAGR {metrics.cagr(fut_r):.1%}, Sharpe {metrics.sharpe_ratio(fut_r):.2f}, "
      f"max drawdown {metrics.max_drawdown(daily['equity']):.1%}")
print(f"Buy & hold the index: Sharpe {metrics.sharpe_ratio(spot.pct_change().dropna()):.2f}, "
      f"max drawdown {metrics.max_drawdown(spot):.1%}")

# %% [markdown]
# ## 3. Cash-and-carry arbitrage: can it beat costs?

# %%
from cfmat.microstructure.costs import IndianCostModel, SegmentRates

free = IndianCostModel(segments={k: SegmentRates(0, 0, 0, 0, 0, 0) for k in
                                 ("equity_delivery", "equity_intraday", "futures", "options")}, sebi_fee=0, gst=0)
for label, model in (("before costs", free), ("after Indian retail costs", IndianCostModel())):
    d, trades = fu.basis_trade(curve, entry_bps=15, exit_bps=3, cost_model=model)
    print(f"{label:<26} trades {len(trades):3d}  win rate {(trades['pnl'] > 0).mean():.0%}  "
          f"total ₹{trades['pnl'].sum():>10,.0f}")
round_trip = IndianCostModel().round_trip_bps(LOT, spot.iloc[0], "equity_delivery") + \
    IndianCostModel().round_trip_bps(LOT, spot.iloc[0], "futures")
print(f"Round-trip cost of both legs ≈ {round_trip:.1f} bp, so a {15}-bp mispricing cannot pay for itself.")
print("Arbitrage desks earn the full carry to expiry with low funding costs; retail traders rarely can.")

# %% [markdown]
# ## 4. Seven option structures, run in parallel

# %%
weekly = fu.weekly_expiries(spot.index, EXPIRY_WEEKDAY)
monthly = fu.monthly_expiries(spot.index, EXPIRY_WEEKDAY)
common = dict(lot_size=LOT, strike_step=STEP)
configs = {
    "short_straddle": dict(strategy="short_straddle", expiries=weekly, profit_take=0.5, stop_loss=1.5, **common),
    "short_strangle": dict(strategy="short_strangle", expiries=weekly, profit_take=0.5, stop_loss=2.0, **common),
    "iron_condor": dict(strategy="iron_condor", expiries=weekly, profit_take=0.5, stop_loss=1.5, **common),
    "long_straddle": dict(strategy="long_straddle", expiries=weekly, profit_take=0.5, **common),
    "long_strangle": dict(strategy="long_strangle", expiries=weekly, profit_take=1.0, **common),
    "bull_call_spread": dict(strategy="bull_call_spread", expiries=monthly, profit_take=0.8, stop_loss=0.5, **common),
    "bear_put_spread": dict(strategy="bear_put_spread", expiries=monthly, profit_take=0.8, stop_loss=0.5, **common),
}
if __name__ == "__main__":        # process pools need this guard on Windows/macOS
    import time

    t0 = time.perf_counter()
    results = option_strategies.run_many(spot, iv, configs, workers=WORKERS, backend="process")
    print(f"7 option backtests in {time.perf_counter() - t0:.1f}s on {WORKERS} processes")
    table = pd.DataFrame({k: r.summary() for k, r in results.items()}).T
    table["view"] = [option_strategies.VIEW[k] for k in table.index]
    print(table[["trades", "win_rate", "total_pnl", "worst_trade", "profit_factor", "avg_return_on_margin", "view"]]
          .round(3).to_string())
    print("\nSellers collect the volatility premium most weeks and give much of it back in turbulent spells;")
    print("buyers pay that premium. Look at worst_trade before falling for a high win rate.")

# %% [markdown]
# ## 5. Regime filters: trade each structure only when its view fits
# The filters use the same rule language as the Strategy Creator, evaluated at the entry close.

# %%
if __name__ == "__main__":
    ev = studio.Evaluator(bars)
    filters = {
        "iron_condor": ev.boolean("adx(14) < 20 and er(20) < 0.3"),                  # range-bound
        "short_straddle": ev.boolean("adx(14) < 20 and vol(20) < 20"),               # quiet market
        "long_straddle": ev.boolean("squeeze(20, 120) or recent(squeeze(20, 120), 5)"),   # compressed volatility
        "bull_call_spread": ev.boolean("close > sma(50) and supertrend_dir(10, 3) == 1"),
        "bear_put_spread": ev.boolean("close < sma(50) and supertrend_dir(10, 3) == -1"),
    }
    filtered_cfg = {f"{k} (filtered)": {**configs[k], "entry_filter": f} for k, f in filters.items()}
    filtered = option_strategies.run_many(spot, iv, filtered_cfg, workers=WORKERS, backend="process")
    rows = []
    for k in filters:
        a, b = results[k].summary(), filtered[f"{k} (filtered)"].summary()
        rows.append({"structure": k, "trades_all": a["trades"], "trades_filtered": b.get("trades", 0),
                     "avg_pnl_all": a["avg_pnl"], "avg_pnl_filtered": b.get("avg_pnl", np.nan),
                     "worst_all": a["worst_trade"], "worst_filtered": b.get("worst_trade", np.nan)})
    print(pd.DataFrame(rows).set_index("structure").round(0))
    print("\nA filter earns its place if it raises the average trade or cuts the worst one, with enough trades left.")

    straddle = results["short_straddle"]
    fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
    axes[0].plot(spot.index, spot, color="black")
    axes[0].set_title("Index")
    axes[1].plot(straddle.daily.index, straddle.daily["realised_pnl"], color="tab:blue")
    axes[1].set_title("Short straddle: cumulative realised P&L (₹)")
    axes[2].plot(iv.index, iv * 100, color="tab:red")
    axes[2].set_title("Implied volatility (%)")
    print("Chart saved to", savefig(fig, "lab22_short_straddle"))

# %% [markdown]
# ## Exercises
# 1. Add a 1-lot long wing to the short straddle (turning it into an iron fly) and
#    compare the worst trade and the return on margin.
# 2. Replace the synthetic IV with a real India VIX history and real expiry dates.
# 3. Size the futures strategy by volatility (fewer lots when ATR is high) and compare drawdowns.
