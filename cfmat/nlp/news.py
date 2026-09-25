"""From timestamped headlines to a tradable signal (M22).

    news_events   de-duplicate, score each headline, and assign it to the first session whose
                  close can act on it (after-hours and weekend news go to the next session)
    news_signal   per stock and day: the sum of scores, decayed with a half-life, known at the
                  close of each day — trade it from the next session

The two most common mistakes this avoids are counting a syndicated story twice and
trading at the close of the day on news that arrived after that close.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from ..analytics.macro import release_sessions
from .sentiment import lexicon_sentiment


def news_events(
    news: pd.DataFrame,
    trading_days: pd.DatetimeIndex,
    session_close: str = "15:30",
    dedupe_window: str = "30min",
    score: Callable[[str], float] | None = None,
) -> pd.DataFrame:
    """Clean, scored news: one row per story, with the session it belongs to.

    ``news`` has ``ts``, ``symbol`` and ``headline``. The same headline for the same symbol
    within ``dedupe_window`` of its previous appearance is dropped as a re-publication; the
    same words weeks later are a new story.
    ``score`` maps a headline to a number (default: the lexicon score). ``session`` is the
    first trading day whose close comes after the headline.
    """
    score = score or (lambda text: lexicon_sentiment(text)["score"])
    frame = news.sort_values("ts", kind="stable").copy()
    frame["key"] = frame["headline"].str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True).str.strip()
    previous = frame.groupby(["symbol", "key"])["ts"].shift()
    frame = frame[~((frame["ts"] - previous) <= pd.Timedelta(dedupe_window))]   # the same story re-published
    frame["session"] = release_sessions(frame["ts"], trading_days, session_close).to_numpy()
    frame = frame.dropna(subset=["session"]).copy()
    frame["score"] = [float(score(text)) for text in frame["headline"]]
    return frame.drop(columns="key").reset_index(drop=True)


def news_signal(
    events: pd.DataFrame,
    trading_days: pd.DatetimeIndex,
    symbols: list[str] | None = None,
    half_life: float = 2.0,
) -> pd.DataFrame:
    """Per-stock sentiment known at each close: the day's summed scores plus the decayed past.

    s_t = scores_t + 0.5^(1/half_life) · s_{t−1}. Row t uses only news assigned to sessions up
    to t; to trade it without look-ahead, hold the position from session t + 1.
    """
    symbols = symbols or sorted(events["symbol"].unique())
    daily = (events.pivot_table(index="session", columns="symbol", values="score", aggfunc="sum")
             .reindex(index=trading_days, columns=symbols).fillna(0.0))
    keep = 0.5 ** (1.0 / half_life)
    return daily.ewm(alpha=1 - keep, adjust=False).mean() / (1 - keep)
