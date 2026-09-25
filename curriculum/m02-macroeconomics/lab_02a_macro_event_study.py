# %% [markdown]
# # Lab 02a — RBI Policy Days, CPI Surprises and the Yield Curve (M02)
#
# **Goals**
# 1. Read a macro calendar: reference period, release time, and the first session a release can move.
# 2. Measure volatility and returns on announcement days with honest tests (HAC and permutation),
#    measure the response to surprises, and test "the market already priced it in".
# 3. Fit Nelson–Siegel curves, track level, slope and curvature, and find inversions.
# 4. Label growth × inflation regimes with only the data known at each close, prove it with a
#    truncation test, and see how much hindsight flatters a regime study.
#
# The economy is synthetic with planted effects (`truth`), so every answer can be checked.
# Times are IST; the NSE closes at 15:30.

# %%
import numpy as np
import pandas as pd

from cfmat import data
from cfmat.analytics import macro, rates, stats
from cfmat.infra.plotting import plt, savefig
from cfmat.research.segments import segment_stats

pd.set_option("display.width", 150)

# %% [markdown]
# ## 1. The macro calendar
# Ten years of scheduled events. The RBI announces at 10:00, during the session; CPI, IIP and
# GDP come out at 16:00 and the FOMC at 23:30 IST, after the close — so their first tradable
# session is the next one. A Budget on a Saturday moves Monday here (NSE would open a special
# session). A data release also names a *reference period*: CPI for August arrives on 12 September.

# %%
calendar, releases, market, curves, truth = data.macro_calendar(seed=7)
days = market.index
calendar["session"] = macro.release_sessions(calendar["release_ts"], days)
print(calendar.dropna(subset=["surprise"]).groupby("event").head(2).sort_values("release_ts").to_string(index=False))
summary = calendar.assign(time=calendar["release_ts"].dt.strftime("%H:%M"),
                          next_session=calendar["session"] > calendar["release_ts"].dt.normalize())
print("\n", summary.groupby("event").agg(events=("event", "size"), time=("time", "first"),
                                         moves_next_session=("next_session", "mean"),
                                         surprise_sd=("surprise", "std")).round(2).to_string())
print("\nSessions match the answer key:", bool((calendar["session"] == truth["sessions"]).all()))

# %% [markdown]
# **Vintages.** Each CPI and IIP month is published once and revised a month later. IIP
# revisions are large enough to flip the direction of growth.

# %%
iip = (releases[releases["series"] == "IIP"].astype({"reference": "period[M]"})
       .pivot_table(index="reference", columns="vintage", values="value"))
iip["revision"] = iip["revised"] - iip["first"]
flips = (np.sign(iip["first"].diff(3)) != np.sign(iip["revised"].diff(3))).mean()
print(iip.tail(4).to_string())
print(f"IIP revisions: sd {iip['revision'].std():.2f} pp; the three-month change of growth flips sign "
      f"between first and revised data in {flips:.0%} of months")

# %% [markdown]
# ## 2. Announcement days
# **Volatility and returns.** Compare each event's sessions with all other days, for the absolute
# return (volatility) and the return itself. HAC standard errors respect volatility clustering;
# the permutation test shifts the event dates around the sample.

# %%
ret = market["equity"].pct_change().iloc[1:]
flags = {event: pd.Series(ret.index.isin(group["session"]), index=ret.index)
         for event, group in calendar.groupby("event")}
rows = {}
for event, flag in flags.items():
    vol = stats.event_day_effect(ret.abs(), flag, n_perm=1000)
    mean = stats.event_day_effect(ret, flag, n_perm=1000)
    rows[event] = {"events": int(vol["events"]), "abs_ratio": vol["ratio"], "abs_t_hac": vol["t_hac"],
                   "abs_p_perm": vol["p_value"], "planted_vol": truth["params"]["event_vol"][event],
                   "mean_bp": 1e4 * mean["mean_event"], "other_bp": 1e4 * mean["mean_other"], "mean_p_perm": mean["p_value"]}
print(pd.DataFrame(rows).T.round(2).to_string())

# %% [markdown]
# Compare the ratios with the planted multipliers. Only the RBI's extra volatility clears the 1%
# level; the Budget's ratio is the largest but rests on ten days; CPI and GDP (planted 1.3 and 1.2)
# sit at the edge of significance and FOMC (1.3) is missed. A 20–30% rise in volatility needs
# more than ten years of events to show reliably. No mean return is significant — including the
# planted RBI-day premium, which is real. How many meetings would it take to see it?

# %%
sd_rbi = ret[flags["RBI policy"]].std()
mde = 2.8 * sd_rbi / np.sqrt(flags["RBI policy"].sum())      # 5% test, 80% power
premium = truth["params"]["rbi_day_premium"]
print(f"Planted RBI-day premium {1e4 * premium:.0f} bp; minimum detectable effect with "
      f"{flags['RBI policy'].sum()} meetings {1e4 * mde:.0f} bp; meetings needed ≈ "
      f"{(2.8 * sd_rbi / premium) ** 2:,.0f} ({(2.8 * sd_rbi / premium) ** 2 / 6:,.0f} years)")

# %% [markdown]
# **Surprises.** Regress the event session's return (%) on the surprise (actual − consensus, pp).
# Then repeat on the *release date*: for after-close releases that is the day before the market
# could react — the most common timing mistake in macro event studies. The RBI announces during
# the session, so both columns agree.

# %%


def slope_t(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    keep = ~np.isnan(y)
    x, y = x[keep], y[keep]
    slope, intercept = np.polyfit(x, y, 1)
    resid = y - (slope * x + intercept)
    return slope, slope / (resid.std(ddof=2) / np.sqrt(((x - x.mean()) ** 2).sum()))


rows = {}
for event in ["RBI policy", "CPI", "IIP", "GDP"]:
    ev = calendar[(calendar["event"] == event) & calendar["session"].isin(ret.index)]
    x = ev["surprise"].to_numpy()
    on_session = slope_t(x, 100 * ret.reindex(ev["session"]).to_numpy())
    on_release = slope_t(x, 100 * ret.reindex(ev["release_ts"].dt.normalize()).to_numpy())
    rows[event] = {"events": len(ev), "slope_session": on_session[0], "t_session": on_session[1],
                   "slope_release_date": on_release[0], "t_release_date": on_release[1],
                   "planted": truth["params"]["surprise_response_pct_per_pp"][event]}
print(pd.DataFrame(rows).T.round(2).to_string())
print("(RBI surprises are ±25 bp: a hawkish surprise moves the index by about "
      f"{0.25 * rows['RBI policy']['slope_session']:.2f}%)")

# %% [markdown]
# **"Already priced in" is testable.** After a hawkish CPI surprise (above consensus by more
# than 0.1 pp), does the index keep falling? Forward returns start at the close of the event
# session, so the event-day move is excluded. Then the look-ahead version: the same study
# started one day earlier, as if the sign of the surprise were known before the release.

# %%
cpi = calendar[(calendar["event"] == "CPI") & calendar["session"].isin(days)]
hawkish = pd.Series(days.isin(cpi.loc[cpi["surprise"] > 0.1, "session"]), index=days)
after = stats.event_study(market["equity"], hawkish, horizons=(1, 5, 10, 20), n_perm=1000)
before = stats.event_study(market["equity"], hawkish.shift(-1, fill_value=False), horizons=(1, 5), n_perm=1000)
print("From the event session's close (tradable):\n", after[["events", "excess", "t_hac", "p_value"]].round(4).to_string())
print("\nFrom the day before (look-ahead):\n", before[["events", "excess", "t_hac", "p_value"]].round(4).to_string())

# %% [markdown]
# No drift after the event: the price adjusts on the session and stops. The only "profitable"
# CPI trade is the one that needs tomorrow's number today.

# %% [markdown]
# ## 3. The yield curve
# Fit Nelson–Siegel to single days, then to every day with a fixed decay `tau` (Diebold–Li).
# In the fitted factors, level = b0, slope = long − short = −b1, and b2 is curvature.

# %%
maturities = curves.columns.to_numpy(dtype=float)
spread = curves[10.0] - curves[0.25]
picks = {"steepest": spread.idxmax(), "most inverted": spread.idxmin(), "median slope": (spread - spread.median()).abs().idxmin()}
for name, day in picks.items():
    fit = rates.nelson_siegel_fit(maturities, curves.loc[day])
    true = truth["factors"].loc[day]
    print(f"{name:<14} {day:%d %b %Y}: fitted b0 {fit.beta0:.2f} b1 {fit.beta1:+.2f} b2 {fit.beta2:+.2f} tau {fit.tau:.2f} "
          f"(rmse {100 * fit.rmse:.1f} bp) · true {true['beta0']:.2f} {true['beta1']:+.2f} {true['beta2']:+.2f} "
          f"{true['tau']:.2f}")

free = rates.nelson_siegel_panel(curves.iloc[::21])                  # about monthly, tau free on each date
tau = rates.nelson_siegel_tau(curves)                                 # one tau that fits the whole panel best
factors = rates.nelson_siegel_panel(curves, tau=tau)
compare = pd.DataFrame({
    "corr with truth": [factors[b].corr(truth["factors"][b]) for b in ("beta0", "beta1", "beta2")],
    "mean abs error (bp)": [100 * (factors[b] - truth["factors"][b]).abs().mean() for b in ("beta0", "beta1", "beta2")],
    "tau-free monthly sd of change": [free[b].diff().std() for b in ("beta0", "beta1", "beta2")],
    "fixed-tau monthly sd of change": [factors[b].iloc[::21].diff().std() for b in ("beta0", "beta1", "beta2")],
}, index=["level b0", "b1 (short − long)", "curvature b2"])
print(f"\nPanel tau = {tau:.2f} years (planted {truth['params']['tau']}); free per-date fits range "
      f"{free['tau'].quantile(0.1):.2f}–{free['tau'].quantile(0.9):.2f} (10th–90th percentile)")
print(compare.round(3).to_string())
proxies = pd.DataFrame({"level ≈ 10y": curves[10.0], "slope ≈ 10y − 3m": spread,
                        "curvature ≈ 2·2y − 3m − 10y": 2 * curves[2.0] - curves[0.25] - curves[10.0]})
print("\nCorrelation of the simple proxies with the fitted factors:",
      {name: round(float(np.corrcoef(p, f)[0, 1]), 3) for (name, p), f in
       zip(proxies.items(), (factors["beta0"], -factors["beta1"], factors["beta2"]), strict=True)})

# %% [markdown]
# **Inversions.** When the repo climbs above the long end, the curve inverts. Episodes of at
# least 20 sessions in the 10y − 3m spread:

# %%
episodes = rates.inversion_episodes(spread, min_days=20, merge_gap=10)
episodes["repo_at_start"] = market["repo"].reindex(episodes["start"]).to_numpy()
episodes["growth_regime_at_start"] = truth["daily_regime"].reindex(episodes["start"]).to_numpy()
print(episodes.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
print(f"{len(episodes)} episodes in ten years: far too few to estimate how reliably, or how far "
      "ahead, an inversion predicts a slowdown.")

# %% [markdown]
# **What a level shift does to a 10-year G-sec.** Duration and convexity from `bond_risk`,
# against a full reprice, for a 50 bp rise in yield.

# %%
y10 = float(curves[10.0].iloc[-1])
risk = rates.bond_risk(y10, coupon=y10, maturity=10)
full = rates.bond_price(y10 + 0.5, y10, 10) / risk["price"] - 1
print(f"10y at {y10:.2f}%: modified duration {risk['modified']:.2f}, convexity {risk['convexity']:.1f}, "
      f"DV01 ₹{risk['dv01']:.3f} per ₹100")
print(f"+50 bp: full reprice {full:.2%} · duration {-risk['modified'] * 0.005:.2%} · "
      f"duration + convexity {-risk['modified'] * 0.005 + 0.5 * risk['convexity'] * 0.005 ** 2:.2%}")

fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
grid = np.linspace(0.1, 30, 200)
for name, day in picks.items():
    fit = rates.nelson_siegel_fit(maturities, curves.loc[day])
    line = axes[0].plot(grid, fit.yields(grid), label=f"{name} ({day:%b %Y})")[0]
    axes[0].plot(maturities, curves.loc[day], "o", color=line.get_color(), ms=4)
axes[0].set_xlabel("maturity (years)")
axes[0].set_ylabel("yield (%)")
axes[0].set_title("G-sec curves (dots) and Nelson–Siegel fits")
axes[0].legend(fontsize=8)
axes[1].plot(factors.index, factors["beta0"], label="level b0")
axes[1].plot(factors.index, -factors["beta1"], label="slope −b1 (long − short)")
axes[1].plot(market.index, market["repo"], color="black", lw=1, label="repo")
for row in episodes.itertuples():
    axes[1].axvspan(row.start, row.end, color="tab:red", alpha=0.15)
axes[1].axhline(0, color="grey", lw=0.8)
axes[1].set_title("Level, slope and the repo (inversions shaded)")
axes[1].legend(fontsize=8)
print("Chart:", savefig(fig, "lab02a_yield_curve"))

# %% [markdown]
# ## 4. Growth × inflation regimes without look-ahead
# Three labels: *hindsight* (each month labelled with its final, revised numbers — not known
# until weeks later), *causal* (the latest vintage known at each close) and *first release*
# (first prints only). Then the truncation test: rerun the causal label on data cut off at a
# date; up to that date nothing may change. The hindsight label fails it.

# %%
labels = {
    "hindsight": macro.growth_inflation_regimes(releases, days, timing="reference")["regime"],
    "causal": macro.growth_inflation_regimes(releases, days)["regime"],
    "first release": macro.growth_inflation_regimes(releases, days, vintage="first")["regime"],
}
true_regime = truth["daily_regime"]
print({name: f"{(label == true_regime).mean():.0%} of days match the true regime" for name, label in labels.items()})

cutoff = days[1500]
cut_releases = releases[releases["release_ts"] <= cutoff + pd.Timedelta("23:59:59")]
cut_days = days[days <= cutoff]
for name, timing in (("causal", "release"), ("hindsight", "reference")):
    again = macro.growth_inflation_regimes(cut_releases, cut_days, timing=timing)["regime"]
    changed = (again.fillna("") != labels[name].loc[cut_days].fillna("")).sum()
    print(f"Truncation test at {cutoff:%d %b %Y}, {name}: {changed} of {len(cut_days)} labels change "
          f"→ {'PASS' if changed == 0 else 'FAIL (uses data published after the date)'}")

# %% [markdown]
# **Returns by regime.** A causal label known at the close of day t is used for day t + 1's
# return. Count observations per regime before looking at the means.

# %%
frame = pd.DataFrame({"hindsight": labels["hindsight"], "causal": labels["causal"].shift(1),
                      "first release": labels["first release"].shift(1)}).reindex(ret.index)
table = segment_stats(ret, frame, min_obs=60)
table["annual_mean"] = table["mean_bp"] * 252 / 1e4
table["planted"] = table["segment"].map(truth["params"]["regime_drift"])
view = table.pivot_table(index="segment", columns="family", values="annual_mean")
view["planted"] = view.index.map(truth["params"]["regime_drift"])
print("Annualised index return by regime:\n", view[["hindsight", "causal", "first release", "planted"]].round(2).to_string())
print("\nDays per regime:\n", table.pivot_table(index="segment", columns="family", values="n").astype(int).to_string())
spread_by = {f: view[f].max() - view[f].min() for f in ("hindsight", "causal", "first release")}
print("\nBest − worst regime:", {k: f"{v:.0%}" for k, v in spread_by.items()})

# %% [markdown]
# **Strategy attribution.** A 200-day trend rule (long above the average, flat below): which
# causal regimes did it make its money in?

# %%
position = (market["equity"] > market["equity"].rolling(200).mean()).astype(float)
trend = (position.shift(1) * market["equity"].pct_change()).reindex(ret.index).iloc[200:]
by_regime = segment_stats(trend, frame[["causal"]], min_obs=60)
by_regime["share_of_pnl"] = (by_regime["mean_bp"] * by_regime["n"]) / (by_regime["mean_bp"] * by_regime["n"]).sum()
columns = ["segment", "n", "mean_bp", "hit_rate", "sharpe", "p_value", "q_value", "share_of_pnl"]
print(by_regime[columns].round(3).to_string(index=False))

fig, ax = plt.subplots(figsize=(12, 3.8))
colours = {"recovery": "tab:green", "overheat": "tab:orange", "stagflation": "tab:red", "reflation": "tab:blue"}
for row, (name, label) in enumerate((("true", true_regime), ("causal", labels["causal"]))):
    codes = label.reindex(days)
    for regime, colour in colours.items():
        ax.fill_between(days, row, row + 0.8, where=(codes == regime).to_numpy(), color=colour, step="post",
                        label=regime if row == 0 else None)
ax.set_yticks([0.4, 1.4], ["true", "causal"])
ax.set_title("Growth × inflation regime: the truth and what could be known at each close")
ax.legend(ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.1))
print("Chart:", savefig(fig, "lab02a_regimes"))

# %% [markdown]
# Hindsight labels match the truth almost perfectly and make the regime effect look large. The
# causal label arrives one to two months late and uses first prints that are later revised, so
# it matches the truth less often and the spread between regimes you could have traded shrinks.
# That smaller number is the one to report — with the days per regime next to it: from 300 days
# the standard error of an annualised mean is about 13 percentage points.

# %% [markdown]
# ## Exercises
# 1. Change the hawkish threshold in section 2 to 0.2 pp. How many events remain, and what
#    happens to the p-values? Write one sentence on power.
# 2. Fit the panel with `tau=0.5` and `tau=5`. Which factors change meaning, and why does a
#    fixed tau make day-to-day factor changes comparable?
# 3. Use `change_periods=1` and `6` in `growth_inflation_regimes`. How often does the label
#    switch, and what does that do to trading costs of a regime-filtered strategy?
# 4. On real data: RBI policy dates and MOSPI CPI release dates for the last eight years,
#    Nifty closes from `python -m cfmat.data.fetch yahoo ^NSEI`. Repeat the section 2 tables and
#    report the number of events next to every p-value.
