# %% [markdown]
# # Lab 09a — Second-order Greeks and P&L Attribution (M09)
#
# **Goals**
# 1. Compute vanna, volga, charm, speed, zomma and colour in closed form and prove them with
#    finite differences.
# 2. See where each Greek lives across spot and time to expiry.
# 3. Explain a short straddle's daily P&L through a sell-off, term by term, with almost nothing
#    left unexplained.
# 4. Show that a delta-hedged long straddle earns realised minus implied variance — and how
#    noisy that is path by path.
#
# Units follow `bs_greeks`: volatility in points (1 point = 1%), time in calendar days.

# %%
import numpy as np
import pandas as pd

from cfmat.derivatives import options as opt
from cfmat.infra.plotting import plt, savefig

pd.set_option("display.width", 150)
R, Q = 0.065, 0.012

# %% [markdown]
# ## 1. Closed forms, checked by finite differences
# Each second-order Greek is the derivative of a first-order one: vanna = ∂delta/∂σ,
# volga = ∂vega/∂σ, charm = ∂delta/∂t, speed = ∂gamma/∂S, zomma = ∂gamma/∂σ, colour = ∂gamma/∂t.
# Bump the first-order Greek and compare.

# %%
S, K, T, SIG = 24_000.0, 24_500.0, 30 / 365, 0.16
closed = opt.bs_second_order_greeks(S, K, T, R, SIG, "call", Q)


def first(**kw):
    return opt.bs_greeks(**{**dict(S=S, K=K, T=T, r=R, sigma=SIG, kind="call", q=Q), **kw})


hs, hv, ht = S * 1e-4, 1e-4, 1e-6
bumped = {
    "vanna": (first(sigma=SIG + hv).delta - first(sigma=SIG - hv).delta) / (2 * hv) / 100,
    "volga": (first(sigma=SIG + hv).vega - first(sigma=SIG - hv).vega) / (2 * hv) / 100,
    "charm": -(first(T=T + ht).delta - first(T=T - ht).delta) / (2 * ht) / 365,
    "speed": (first(S=S + hs).gamma - first(S=S - hs).gamma) / (2 * hs),
    "zomma": (first(sigma=SIG + hv).gamma - first(sigma=SIG - hv).gamma) / (2 * hv) / 100,
    "color": -(first(T=T + ht).gamma - first(T=T - ht).gamma) / (2 * ht) / 365,
}
check = pd.DataFrame({"closed form": pd.Series(closed.__dict__), "finite difference": pd.Series(bumped)})
check["relative error"] = (check["closed form"] / check["finite difference"] - 1).abs()
print(f"30-day {K:,.0f} call on {S:,.0f}, IV {SIG:.0%}:")
print(check.to_string(float_format=lambda v: f"{v: .4e}"))

# %% [markdown]
# **Reading them.** Vanna: how much delta moves when IV moves one point — why a short strangle's
# hedge ratio jumps in a sell-off. Volga: how vega grows as IV moves — convexity in volatility,
# largest for wings. Charm: overnight delta drift — why a delta-neutral book is not neutral next
# morning. Speed, zomma and colour: how gamma itself moves with spot, IV and time — gamma
# explodes near expiry for at-the-money strikes.

# %% [markdown]
# ## 2. Where each Greek lives
# Maps across moneyness (strike / spot) and days to expiry for a call at 16% IV.

# %%
moneyness = np.linspace(0.85, 1.15, 61)
days = np.arange(2, 91, 2)
grids = {name: np.zeros((len(days), len(moneyness))) for name in closed.__dict__}
for i, d in enumerate(days):
    for j, m in enumerate(moneyness):
        g = opt.bs_second_order_greeks(S, S * m, d / 365, R, SIG, "call", Q)
        for name in grids:
            grids[name][i, j] = getattr(g, name)
fig, axes = plt.subplots(2, 3, figsize=(13, 7))
for ax, (name, grid) in zip(axes.ravel(), grids.items(), strict=True):
    limit = np.nanpercentile(np.abs(grid), 98)
    image = ax.imshow(grid, aspect="auto", origin="lower", cmap="RdBu_r", vmin=-limit, vmax=limit,
                      extent=(moneyness[0], moneyness[-1], days[0], days[-1]))
    ax.set_title(name)
    ax.set_xlabel("strike / spot")
    ax.set_ylabel("days to expiry")
    fig.colorbar(image, ax=ax, fraction=0.046)
fig.suptitle("Second-order Greeks of a call (red positive, blue negative)")
print("Chart:", savefig(fig, "lab09a_greek_maps"))
for name, grid in grids.items():
    i, j = np.unravel_index(np.nanargmax(np.abs(grid)), grid.shape)
    print(f"  {name:<6} largest at strike/spot {moneyness[j]:.2f}, {days[i]} days")

# %% [markdown]
# ## 3. Explaining a short straddle through a sell-off
# Sell one lot (50) of the 24,000 straddle with 57 days to expiry. Over three weeks the index
# falls about 17% and IV climbs from 14% to about 30%. Each day, the Greeks at the start of
# the day explain the day's P&L; `residual` is what they miss.

# %%
dates = pd.bdate_range("2026-03-02", periods=16)
rng = np.random.default_rng(9)
path = pd.DataFrame({"spot": 24_000 * np.exp(np.cumsum(np.r_[0, rng.normal(-0.012, 0.006, 15)])),
                     "iv": 0.14 + np.cumsum(np.r_[0, rng.normal(0.01, 0.004, 15)])}, index=dates)
legs = [{"kind": k, "strike": 24_000, "qty": -50, "expiry": "2026-04-28"} for k in ("call", "put")]
attribution = opt.greek_pnl_attribution(legs, path, r=R, q=Q)
terms = ["delta", "gamma", "vega", "theta", "vanna", "volga", "charm", "speed"]
gross = attribution[terms].abs().sum(axis=1)
print(path.assign(iv=lambda p: (100 * p["iv"]).round(1)).iloc[[0, 5, 10, 15]].round(0).to_string())
print("\nDaily attribution (₹):")
print(attribution[terms + ["actual", "residual"]].round(0).to_string())
totals = attribution[terms + ["actual", "residual"]].sum()
print("\nTotals (₹):", totals.round(0).to_dict())
print(f"Largest daily residual: {100 * (attribution['residual'].abs() / gross).max():.1f}% of that day's gross "
      f"Greek P&L; over the period {100 * attribution['residual'].abs().sum() / attribution['actual'].abs().sum():.1f}%"
      f" of the P&L is unexplained")

fig, ax = plt.subplots(figsize=(11, 4.5))
bottom_pos = np.zeros(len(attribution))
bottom_neg = np.zeros(len(attribution))
for name in terms + ["residual"]:
    values = attribution[name].to_numpy()
    bottom = np.where(values >= 0, bottom_pos, bottom_neg)
    ax.bar(attribution.index, values, bottom=bottom, label=name, width=0.8)
    bottom_pos += np.clip(values, 0, None)
    bottom_neg += np.clip(values, None, 0)
ax.plot(attribution.index, attribution["actual"], "ko-", ms=3, lw=1, label="actual")
ax.set_title("Short straddle through a sell-off: daily P&L by Greek (₹)")
ax.legend(ncol=5, fontsize=8)
print("Chart:", savefig(fig, "lab09a_attribution"))

# %% [markdown]
# Delta, gamma and vega do the damage; theta pays a little; vanna matters because IV rises as
# spot falls. A risk report that shows only delta, gamma, vega and theta leaves the cross terms
# unexplained on exactly the days they matter.

# %% [markdown]
# ## 4. Gamma scalping: a hedged long straddle earns realised − implied variance
# Buy the straddle at 16% IV and delta-hedge with futures at every close. The hedged P&L is,
# to first order, the sum of ½ · gamma · S² · (realised² − implied²) · dt. Repeat on 40 paths
# for each realised volatility.

# %%


def hedged_straddle(realised: float, implied: float = 0.16, n_days: int = 30, seed: int = 0) -> float:
    """P&L of a long ATM straddle (1 unit) held n_days, delta-hedged daily, IV held at `implied`."""
    rng = np.random.default_rng(seed)
    dt = 1 / 365
    spot = 24_000 * np.exp(np.cumsum(np.r_[0, rng.normal(-0.5 * realised**2 * dt, realised * np.sqrt(dt), n_days)]))
    strike, expiry = 24_000.0, 45 / 365
    pnl, hedge = 0.0, 0.0
    for t in range(n_days):
        tau0, tau1 = expiry - t * dt, expiry - (t + 1) * dt
        value0 = sum(opt.bs_price(spot[t], strike, tau0, R, implied, k) for k in ("call", "put"))
        value1 = sum(opt.bs_price(spot[t + 1], strike, tau1, R, implied, k) for k in ("call", "put"))
        hedge = -sum(opt.bs_greeks(spot[t], strike, tau0, R, implied, k).delta for k in ("call", "put"))
        pnl += (value1 - value0) + hedge * (spot[t + 1] - spot[t])
    return pnl


rows = []
for realised in (0.10, 0.16, 0.22, 0.28):
    outcomes = np.array([hedged_straddle(realised, seed=s) for s in range(40)])
    rows.append({"realised vol": f"{realised:.0%}", "mean P&L": outcomes.mean(), "st. dev.": outcomes.std(),
                 "share of paths profitable": (outcomes > 0).mean()})
scalp = pd.DataFrame(rows).set_index("realised vol")
print(scalp.round(1).to_string())
print("\nBought at 16%: the hedged straddle loses when the market realises less, breaks even on average "
      "at 16% — where half the paths win and half lose — and wins above. The spread across paths grows "
      "with volatility: when the big moves come, relative to where gamma is high, matters as well as their size.")

# %% [markdown]
# ## Exercises
# 1. Rerun section 3 for a short 25-delta strangle. Which Greek's share of the loss grows, and why?
# 2. Drop the vanna and volga terms from the explanation. On which days does the residual jump?
# 3. In section 4, hedge every 5 days instead of daily. What happens to the mean and to the spread?
# 4. Using `charm`, estimate how many futures a delta-neutral short straddle must trade at the next
#    open if spot does not move, and check it against a full reprice.
