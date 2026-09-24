# %% [markdown]
# # Lab 08a — Derivatives, Options Pricing and Volatility (M08)
#
# **Goals**
# 1. Price Nifty-style index options with Black–Scholes and read the Greeks.
# 2. Back out implied volatility and plot a volatility smile.
# 3. Check a binomial tree converges to Black–Scholes; value early exercise.
# 4. Draw payoff diagrams for straddles, iron condors and covered calls.
# 5. Delta-hedge a short option and see that P&L depends on realised vs implied vol.

# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cfmat.derivatives import options as opt
from cfmat.infra.plotting import savefig

S, r, q = 24_500.0, 0.065, 0.012
T = 21 / 365           # three weeks to expiry
LOT = 75               # illustrative lot size

# %% [markdown]
# ## 1. Option chain with Greeks

# %%
rows = []
for K in range(23_500, 25_600, 250):
    for kind in ("call", "put"):
        g = opt.bs_greeks(S, K, T, r, 0.14, kind, q)
        rows.append({"strike": K, "kind": kind, "price": opt.bs_price(S, K, T, r, 0.14, kind, q),
                     "delta": g.delta, "gamma": g.gamma, "vega_1pt": g.vega, "theta_day": g.theta})
chain = pd.DataFrame(rows)
print(chain.pivot(index="strike", columns="kind", values=["price", "delta"]).round(2))
atm = chain[(chain.strike == 24_500) & (chain.kind == "call")].iloc[0]
print(f"\nATM call: one lot loses ₹{-atm.theta_day * LOT:,.0f} a day to theta "
      f"and gains ₹{atm.vega_1pt * LOT:,.0f} per vol point.")

# %% [markdown]
# ## 2. Implied volatility smile
# Market quotes are generated from a skewed vol curve (puts richer than calls,
# as in real index markets); we recover it by inverting Black–Scholes.

# %%
strikes = np.arange(22_500, 26_600, 250)
true_vol = 0.14 + 0.9 * (np.log(strikes / S)) ** 2 - 0.25 * np.log(strikes / S)
quotes = [opt.bs_price(S, K, T, r, v, "put" if K < S else "call", q) for K, v in zip(strikes, true_vol)]
iv = [opt.implied_volatility(p, S, K, T, r, "put" if K < S else "call", q) for p, K in zip(quotes, strikes)]
smile = pd.DataFrame({"strike": strikes, "quote": np.round(quotes, 2), "iv_%": np.round(np.array(iv) * 100, 2)})
print(smile.to_string(index=False))

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(strikes, np.array(iv) * 100, marker="o")
ax.axvline(S, ls="--", c="grey")
ax.set(title="Implied volatility smile (OTM options)", xlabel="Strike", ylabel="IV %")
print("Chart saved to", savefig(fig, "lab08a_smile"))

# %% [markdown]
# ## 3. Binomial tree convergence and early exercise

# %%
bs = opt.bs_price(100, 100, 1, 0.08, 0.25, "put")
for steps in (10, 50, 200, 1000):
    eu = opt.binomial_price(100, 100, 1, 0.08, 0.25, "put", steps)
    am = opt.binomial_price(100, 100, 1, 0.08, 0.25, "put", steps, american=True)
    print(f"steps {steps:>4}: European {eu:.4f} (BS {bs:.4f})  American {am:.4f}  early-exercise premium {am - eu:.4f}")

# %% [markdown]
# ## 4. Strategy payoffs at expiry (per lot)

# %%
spot = np.linspace(22_500, 26_500, 400)
c = lambda K: opt.bs_price(S, K, T, r, 0.14, "call", q)  # noqa: E731
p = lambda K: opt.bs_price(S, K, T, r, 0.14, "put", q)   # noqa: E731
strategies = {
    "long straddle 24500": [{"kind": "call", "strike": 24_500, "qty": 1, "premium": c(24_500)},
                            {"kind": "put", "strike": 24_500, "qty": 1, "premium": p(24_500)}],
    "short iron condor": [{"kind": "put", "strike": 23_800, "qty": 1, "premium": p(23_800)},
                          {"kind": "put", "strike": 24_000, "qty": -1, "premium": p(24_000)},
                          {"kind": "call", "strike": 25_000, "qty": -1, "premium": c(25_000)},
                          {"kind": "call", "strike": 25_200, "qty": 1, "premium": c(25_200)}],
    "covered call (future + short 25000C)": [{"kind": "future", "strike": S, "qty": 1},
                                             {"kind": "call", "strike": 25_000, "qty": -1, "premium": c(25_000)}],
}
fig, ax = plt.subplots(figsize=(9, 5))
for name, legs in strategies.items():
    pnl = opt.strategy_payoff(legs, spot, LOT)
    ax.plot(spot, pnl, label=name)
    breakevens = spot[np.nonzero(np.diff(np.sign(pnl)))[0]]
    print(f"{name:<40} max profit ₹{pnl.max():>10,.0f}  max loss ₹{pnl.min():>10,.0f}  breakevens {np.round(breakevens, -1)}")
ax.axhline(0, c="black", lw=0.8)
ax.set(title="Payoff at expiry per lot", xlabel="Nifty at expiry", ylabel="P&L ₹")
ax.legend()
print("Chart saved to", savefig(fig, "lab08a_payoffs"))

# %% [markdown]
# ## 5. Delta hedging: you earn implied, you pay realised
# Sell one ATM call at 14% implied volatility, hedge daily with the underlying,
# and repeat for markets that realise 10%, 14% and 20% volatility.

# %%
def hedged_short_call_pnl(realised_vol: float, n_paths: int = 300, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    steps, sigma_imp, K = 21, 0.14, S
    dt = T / steps
    results = []
    for _ in range(n_paths):
        s = S
        cash = opt.bs_price(s, K, T, r, sigma_imp, "call", q)   # premium received
        delta = opt.bs_greeks(s, K, T, r, sigma_imp, "call", q).delta
        cash -= delta * s
        for i in range(1, steps + 1):
            s *= np.exp((r - q - 0.5 * realised_vol**2) * dt + realised_vol * np.sqrt(dt) * rng.normal())
            cash *= np.exp(r * dt)
            tau = T - i * dt
            new_delta = opt.bs_greeks(s, K, tau, r, sigma_imp, "call", q).delta if tau > 1e-9 else float(s > K)
            cash -= (new_delta - delta) * s
            delta = new_delta
        results.append((cash + delta * s - max(s - K, 0.0)) * LOT)
    return np.array(results)


for vol in (0.10, 0.14, 0.20):
    pnl = hedged_short_call_pnl(vol)
    print(f"realised {vol:.0%}: mean P&L per lot ₹{pnl.mean():>9,.0f}  std ₹{pnl.std():>8,.0f}")

# %% [markdown]
# ## Exercises
# 1. Price the same chain with the binomial model and American exercise. Where does it differ?
# 2. Rebuild the smile from a real option chain (NSE option chain CSV). Is the skew
#    steeper for weekly or monthly expiries?
# 3. In section 5, hedge only when |delta change| > 0.1. How do cost and P&L variance change?
