# %% [markdown]
# # Lab 06a — Indicators, Candlesticks and Chart Patterns as Testable Hypotheses (M06)
#
# **Goals**
# 1. Build an indicator dashboard (trend, momentum, volatility, efficiency) from first principles.
# 2. See that many indicators measure the same thing: check their correlations.
# 3. Test a chart rule as a hypothesis with an event study, using standard errors that
#    respect overlapping forward returns (Newey–West / HAC).
# 4. Scan 20 candlestick and chart patterns, test them all, and control the false-discovery
#    rate with Benjamini–Hochberg.
#
# The price series is synthetic with a small, known amount of short-term momentum (AR(1)
# coefficient 0.05), so most patterns *should* fail. Re-run on real data in the exercises.

# %%
import matplotlib.pyplot as plt
import pandas as pd

from cfmat import data
from cfmat.analytics import indicators as ind
from cfmat.analytics import patterns as pt
from cfmat.analytics import stats
from cfmat.infra.plotting import savefig

pd.set_option("display.width", 160)
bars = data.ohlcv_from_close(data.ar1_prices(1500, phi=0.05, seed=12), seed=12)
close = bars["close"]

# %% [markdown]
# ## 1. Indicator dashboard

# %%
supertrend = ind.supertrend(bars, 10, 3.0)
dash = pd.DataFrame({
    "close": close,
    "sma_50": ind.sma(close, 50),
    "ema_20": ind.ema(close, 20),
    "rsi_14": ind.rsi(close, 14),
    "atr_14": ind.atr(bars, 14),
    "er_20": ind.efficiency_ratio(close, 20),
    "supertrend_dir": supertrend["direction"],
}).join(ind.macd(close)).join(ind.bollinger_bands(close).add_prefix("bb_")).join(ind.adx(bars, 14))
print(dash.tail(3).round(2).T)

fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
view = dash.iloc[-250:]
view[["close", "bb_upper", "bb_lower", "sma_50"]].plot(ax=axes[0], title="Price, Bollinger bands, SMA 50")
view["rsi_14"].plot(ax=axes[1], title="RSI 14")
axes[1].axhline(70, ls="--", c="grey")
axes[1].axhline(30, ls="--", c="grey")
view["histogram"].plot(ax=axes[2], title="MACD histogram")
view[["adx", "plus_di", "minus_di"]].plot(ax=axes[3], title="ADX and directional indicators")
print("Chart saved to", savefig(fig, "lab06a_indicators"))

# %% [markdown]
# ## 2. Redundancy: many indicators, few independent ideas
# Momentum oscillators and trend distances move together. Adding five of them to a rule
# (or a model) adds parameters, not information.

# %%
features = pd.DataFrame({
    "rsi_14": dash["rsi_14"],
    "macd_hist": dash["histogram"],
    "stoch_k": ind.stochastic(bars)["k"],
    "roc_10": ind.rate_of_change(close, 10),
    "dist_sma50": close / dash["sma_50"] - 1,
    "bb_pos": (close - dash["bb_lower"]) / (dash["bb_upper"] - dash["bb_lower"]),
    "atr_pct": dash["atr_14"] / close,
    "adx": dash["adx"],
}).dropna()
print(features.corr(method="spearman").round(2))

# %% [markdown]
# ## 3. Event studies with honest standard errors
# Forward returns over *h* days overlap when sampled daily, so the ordinary t-statistic
# overstates significance. `stats.event_study` reports a Newey–West t-statistic (h − 1 lags)
# and, as the p-value, a *random-date* permutation test: shift the events to random dates
# 1,000 times and see how often chance produces an edge as large. With few events the
# permutation p-value is the one to trust.

# %%
def first_day(signal: pd.Series) -> pd.Series:
    """Keep the first day of each spell so one long spell is not counted many times."""
    return signal & ~signal.shift(1, fill_value=False)


rules = {
    "RSI(14) < 30": first_day(dash["rsi_14"] < 30),
    "close > upper Bollinger": first_day(close > dash["bb_upper"]),
    "Supertrend turns up": (dash["supertrend_dir"] == 1) & (dash["supertrend_dir"].shift(1) == -1),
}
tests = []
for name, events in rules.items():
    table = stats.event_study(close, events, horizons=(5, 10, 20))
    print(f"\n{name}: {int(events.sum())} events")
    print(table.round(4).to_string())
    tests += [{"rule": name, "horizon": h, "p_value": p} for h, p in table["p_value"].items()]

tests = pd.DataFrame(tests)
tests["q_value"] = stats.benjamini_hochberg(tests["p_value"])
print("\nAll 9 tests with false-discovery control:")
print(tests.round(3).to_string(index=False))
print("A p-value below 0.05 in one of nine tests is expected by chance; look at the q-values.")

# %% [markdown]
# ## 4. Candlestick and chart patterns
# Swing-based patterns (swing highs/lows, double bottoms) are only *known* k bars after the
# swing point. `cfmat.analytics.patterns` flags them on the confirmation bar, so the scan is
# causal. Every pattern gets the same 10-day event study, then Benjamini–Hochberg.

# %%
scan = pt.scan(bars)
print("Pattern counts:\n", scan.sum().sort_values(ascending=False).to_string())

rows = []
for name in scan.columns:
    events = first_day(scan[name])
    if events.sum() < 10:
        continue
    r = stats.event_study(close, events, horizons=(10,)).iloc[0]
    rows.append({"pattern": name, "events": int(r["events"]), "excess_10d_%": 100 * r["excess"],
                 "hit_rate": r["hit_rate"], "t_hac": r["t_hac"], "p_value": r["p_value"]})
patterns = pd.DataFrame(rows).set_index("pattern")
patterns["q_value"] = stats.benjamini_hochberg(patterns["p_value"])
print(patterns.sort_values("p_value").round(3).to_string())
print(f"\n{(patterns['p_value'] < 0.05).sum()} of {len(patterns)} patterns have p < 0.05; "
      f"{(patterns['q_value'] < 0.10).sum()} survive a 10% false-discovery rate.")

fig, ax = plt.subplots(figsize=(9, 4))
patterns["excess_10d_%"].sort_values().plot.barh(ax=ax, title="10-day excess return after each pattern (%)")
ax.axvline(0, c="black", lw=0.8)
print("Chart saved to", savefig(fig, "lab06a_pattern_edges"))

# %% [markdown]
# ## Exercises
# 1. Re-run sections 3–4 on ten real NSE stocks (`cfmat.data.download_prices`). Pre-register
#    which pattern you expect to work *before* you look.
# 2. Change `phi` in `data.ar1_prices` to −0.10 (short-term reversal) and to +0.15. Which rules
#    change sign, and why?
# 3. Count how many tests you ran in this lab in total. What family-wise error rate would a
#    single 5% test per rule imply?
