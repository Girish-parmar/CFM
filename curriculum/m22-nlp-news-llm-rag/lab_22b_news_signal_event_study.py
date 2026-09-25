# %% [markdown]
# # Lab 22b — News to Signals (M22)
#
# **Goals**
# 1. Turn timestamped headlines into clean stories: drop re-publications, score the text, and
#    assign each story to the first session that could act on it.
# 2. Find where a lexicon misreads financial headlines, and fix it.
# 3. Measure the price response to news with a pooled event study (HAC t and a permutation test
#    that respects same-day clustering).
# 4. Trade the signal after costs, and watch the edge decay as the publication delay grows —
#    and see how much a look-ahead mistake would have flattered it.
#
# The headlines and prices are synthetic with a planted response, so the answer is known.

# %%
import numpy as np
import pandas as pd

from cfmat import data, nlp
from cfmat.analytics import stats
from cfmat.infra.plotting import plt, savefig

pd.set_option("display.width", 140)
pd.set_option("display.max_colwidth", 60)

# %% [markdown]
# ## 1. Timestamped news
# Two years of headlines for twelve fictional NSE companies. News arrives at any hour, weekends
# included, and about a third of stories are re-published by a second source minutes later.
# Positive and negative stories move the stock when the market can first react, then keep
# drifting with a two-day half-life; routine announcements move nothing.

# %%
news, close, truth = data.news_stream(n_days=500, seed=22)
days = close.index
print(news.head(6).to_string(index=False))
hours = news["ts"].dt.hour + news["ts"].dt.minute / 60
in_session = news["ts"].dt.dayofweek.lt(5) & hours.between(9.25, 15.5)
print(f"\n{len(news)} headlines; {in_session.mean():.0%} during market hours, "
      f"{news['ts'].dt.dayofweek.ge(5).mean():.0%} at weekends; sources: {news['source'].value_counts().to_dict()}")
print("Planted:", truth["params"])

# %% [markdown]
# ## 2. From headlines to a signal
# `news_events` drops re-publications, scores each headline with the lexicon, and assigns it to
# the first session whose close comes after it: a Friday-evening story belongs to Monday.
# Compare the scores with the true direction of each story.

# %%
events = nlp.news_events(news, days)
print(f"{len(news)} headlines → {len(events)} stories after de-duplication (true stories: {len(truth['events'])})")
check = events.merge(truth["events"], on=["ts", "symbol"], suffixes=("", "_true"))
print(f"Session assigned correctly: {(check['session'] == check['session_true']).mean():.0%}")
print("\nLexicon score sign vs true direction:\n", pd.crosstab(check["sign"], np.sign(check["score"]),
                                                             rownames=["true"], colnames=["lexicon"]))
print("\nMisread examples:", check.loc[np.sign(check["score"]) != check["sign"], "headline"].drop_duplicates().head(4).tolist())

# %% [markdown]
# Two misreadings: "downgrades" is not in the lexicon (only "downgrade"), and "record date"
# is not good news — "record" is a positive word only in "record profit". Fix both with a
# scoring function, the way you would extend any dictionary for your own market.

# %%


def better_score(text: str) -> float:
    lowered = text.lower()
    score = nlp.lexicon_sentiment(lowered.replace("record date", "date"))["score"]
    if "downgrades" in lowered:
        score -= 1
    if "upgrades" in lowered:
        score += 1
    return float(np.sign(score))


events = nlp.news_events(news, days, score=better_score)
check = events.merge(truth["events"], on=["ts", "symbol"])
print("After the fix:\n", pd.crosstab(check["sign"], np.sign(check["score"]), rownames=["true"], colnames=["score"]))
signal = nlp.news_signal(events, days, list(close.columns), half_life=2.0)
print("\nSignal on the last five days:\n", signal.tail().round(2).to_string())

# %% [markdown]
# ## 3. Event study: what happens after good and bad news?
# Market-adjusted prices remove the common factor. Events are the sessions each story hit;
# forward returns start at that session's close, so the first-day jump is excluded and only
# the drift a trader could still catch is measured. The permutation test shifts every stock's
# events together, keeping same-day clustering.

# %%
market = close.pct_change().mean(axis=1)
abnormal = (1 + close.pct_change().sub(market, axis=0).fillna(0)).cumprod()


def event_frame(mask: pd.Series) -> pd.DataFrame:
    table = events[mask].pivot_table(index="session", columns="symbol", values="score", aggfunc="size")
    return table.reindex(index=days, columns=close.columns).fillna(0) > 0


p = truth["params"]
planted = {f"{h}d": p["drift"] * sum(0.5 ** (k / p["half_life"]) for k in range(h)) for h in (1, 3, 5, 10)}
for label, mask, sign in (("positive", events["score"] > 0, 1), ("negative", events["score"] < 0, -1)):
    table = stats.event_study(abnormal, event_frame(mask), horizons=(1, 3, 5, 10), n_perm=500)
    table["planted"] = [sign * planted[h] for h in table.index]
    print(f"\nAfter {label} news:\n", table[["events", "excess", "planted", "hit_rate", "t_hac", "p_value"]].round(4).to_string())

# %% [markdown]
# ## 4. Trading the signal, and the cost of waiting
# Hold long the stocks with a positive signal and short those with a negative one, equal weight,
# from the session after the signal is known; 10 bp per side on turnover. Then delay the trade
# by 1–8 sessions, as if the news reached you late. Finally the classic mistake: trading at the
# close of the session the news belongs to, although most of those headlines arrived after it.

# %%
returns = close.pct_change().fillna(0)


def trade(shift: int, cost_bps: float = 10.0) -> pd.Series:
    weights = np.sign(signal).shift(shift).fillna(0)
    weights = weights.div(weights.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    turnover = weights.diff().abs().sum(axis=1).fillna(0)
    return (weights * returns).sum(axis=1) - turnover * cost_bps / 1e4


def sharpe(r: pd.Series) -> float:
    return float(r.mean() / r.std() * np.sqrt(252))


sweep = pd.Series({delay: sharpe(trade(1 + delay)) for delay in (0, 1, 2, 3, 5, 8)}, name="net Sharpe")
sweep.index.name = "delay (sessions)"
print(sweep.round(2).to_string())
print(f"\nLook-ahead (trading the same session's close): Sharpe {sharpe(trade(0)):.2f} — "
      "it pockets the news-day jump it could not have traded.")

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(sweep.index, sweep.values, "o-", color="tab:blue", label="net Sharpe after the delay")
ax.axhline(0, color="grey", lw=0.8)
ax.axvline(p["half_life"], color="tab:red", ls="--", lw=1, label=f"planted half-life ({p['half_life']:g} sessions)")
ax.set_xlabel("publication delay (sessions)")
ax.set_ylabel("Sharpe ratio after costs")
ax.set_title("A news edge decays with every session you wait")
ax.legend()
print("Chart:", savefig(fig, "lab22b_delay_decay"))

# %% [markdown]
# ## Exercises
# 1. Skip de-duplication (`dedupe_window="0s"`). How do the event counts, the signal and the
#    Sharpe ratio change?
# 2. Replace the lexicon with the TF-IDF classifier from Lab 22a trained on `load_headlines()`.
#    Does it read "downgrades" correctly without a hand-made rule?
# 3. Vary `half_life` in `news_signal` (0.5, 2, 5). Which value matches the planted decay best,
#    and how would you choose it without knowing the truth?
# 4. On real data: timestamps from your news source, prices from `python -m cfmat.data.fetch`.
#    What share of headlines arrive after 15:30, and how does that change section 4?
