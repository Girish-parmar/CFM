# %% [markdown]
# # Lab 12c — Strategy Creator Signals on Futures and Options (M12)
#
# **Goals**
# 1. Trade a Strategy Creator template on index futures: lots from capital, margin,
#    monthly rollovers and Indian charges.
# 2. Use the rule language as a *regime filter* for option structures: sell premium only in
#    quiet, range-bound markets; buy direction only when the trend agrees.
# 3. Judge a filter properly: it must raise the average trade or cut the worst one while
#    leaving enough trades to trust.
#
# Builds on Lab 09b (futures curve, seven option structures) and Lab 12b (rule language).
# Lot size, strike step, expiry weekday and margin rates are illustrative parameters.

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
bars = data.ohlcv_from_close(market["close"] * scale, seed=5)
spot = bars["close"]
iv = data.implied_vol_series(spot, premium=0.15, seed=1)
curve = fu.futures_curve(spot, r=0.065, q=0.012, expiry_weekday=EXPIRY_WEEKDAY, seed=1)

# %% [markdown]
# ## 1. A trend template on index futures

# %%
capital = 2_000_000
signal = studio.backtest(bars, studio.TEMPLATES["trend_supertrend"]).position   # +1 / −1 / 0, decided the day before
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
# ## 2. Regime filters for option structures
# Each filter is a rule evaluated at the entry day's close. Structures are backtested with
# and without their filter, in parallel.

# %%
weekly = fu.weekly_expiries(spot.index, EXPIRY_WEEKDAY)
monthly = fu.monthly_expiries(spot.index, EXPIRY_WEEKDAY)
common = dict(lot_size=LOT, strike_step=STEP)
configs = {
    "short_straddle": dict(strategy="short_straddle", expiries=weekly, profit_take=0.5, stop_loss=1.5, **common),
    "iron_condor": dict(strategy="iron_condor", expiries=weekly, profit_take=0.5, stop_loss=1.5, **common),
    "long_straddle": dict(strategy="long_straddle", expiries=weekly, profit_take=0.5, **common),
    "bull_call_spread": dict(strategy="bull_call_spread", expiries=monthly, profit_take=0.8, stop_loss=0.5, **common),
    "bear_put_spread": dict(strategy="bear_put_spread", expiries=monthly, profit_take=0.8, stop_loss=0.5, **common),
}
if __name__ == "__main__":        # process pools need this guard on Windows/macOS
    ev = studio.Evaluator(bars)
    filters = {
        "iron_condor": ev.boolean("adx(14) < 20 and er(20) < 0.3"),                  # range-bound
        "short_straddle": ev.boolean("adx(14) < 20 and vol(20) < 20"),               # quiet market
        "long_straddle": ev.boolean("squeeze(20, 120) or recent(squeeze(20, 120), 5)"),   # compressed volatility
        "bull_call_spread": ev.boolean("close > sma(50) and supertrend_dir(10, 3) == 1"),
        "bear_put_spread": ev.boolean("close < sma(50) and supertrend_dir(10, 3) == -1"),
    }
    jobs = {**configs, **{f"{k} (filtered)": {**configs[k], "entry_filter": f} for k, f in filters.items()}}
    results = option_strategies.run_many(spot, iv, jobs, workers=WORKERS, backend="process")
    rows = []
    for k in filters:
        a, b = results[k].summary(), results[f"{k} (filtered)"].summary()
        rows.append({"structure": k, "trades_all": a["trades"], "trades_filtered": b.get("trades", 0),
                     "avg_pnl_all": a["avg_pnl"], "avg_pnl_filtered": b.get("avg_pnl", np.nan),
                     "worst_all": a["worst_trade"], "worst_filtered": b.get("worst_trade", np.nan)})
    table = pd.DataFrame(rows).set_index("structure")
    print(table.round(0).to_string())
    better = (table["avg_pnl_filtered"] > table["avg_pnl_all"]) | (table["worst_filtered"] > table["worst_all"])
    enough = table["trades_filtered"] >= 30
    print(f"\nFilters that improve the average or worst trade: {', '.join(table.index[better]) or 'none'}")
    print(f"...and keep at least 30 trades: {', '.join(table.index[better & enough]) or 'none'}")
    print("A filter with 8 trades left proves nothing; the filter itself is also a parameter you tuned.")

    fig, ax = plt.subplots(figsize=(10, 4))
    for k in ("iron_condor", "iron_condor (filtered)"):
        d = results[k].daily
        ax.plot(d.index, d["realised_pnl"], label=k)
    ax.set_title("Iron condor: cumulative realised P&L (₹), with and without the range filter")
    ax.legend()
    print("Chart saved to", savefig(fig, "lab12c_filtered_condor"))

# %% [markdown]
# ## Exercises
# 1. Replace `trend_supertrend` with your own spec from Lab 12b and size lots by ATR.
# 2. Tune the iron-condor filter thresholds on the first half of the sample only, then test
#    on the second half. Does the improvement survive?
# 3. Add an IV filter (sell premium only when IV is above its 60-day median). You will need to
#    pass the IV series into the rule language with `studio.register`.
