"""Macro data without look-ahead: release sessions, data vintages and regime labels (M02).

    release_sessions           the first session whose close comes after each release time
    latest_known               per session: the latest reference period of a series known at
                               that close, its value and its change, from the vintages published
    growth_inflation_regimes   growth x inflation quadrant labels (recovery, overheat,
                               stagflation, reflation) from data known at each close

Macro numbers describe a *reference period* (CPI for August) but become known on a *release
date* (12 September, 16:00 IST, after the NSE close), and are revised later. A label used for
a decision at a session's close may use only releases before that close, and only the
vintage published by then. Row t of every output here obeys that rule: act on it from t + 1.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

REGIMES = {(True, False): "recovery", (True, True): "overheat", (False, True): "stagflation",
           (False, False): "reflation"}


def release_sessions(ts, trading_days: pd.DatetimeIndex, session_close: str = "15:30") -> pd.Series:
    """The first session whose close comes after each timestamp (NaT beyond ``trading_days``).

    A release before the close belongs to that day's session; at or after the close, or on a
    holiday, to the next session. Timestamps are local exchange time (IST for NSE).
    """
    stamps = pd.Series(pd.to_datetime(ts))
    close = pd.Timedelta(f"{session_close}:00")
    same_day = (stamps - stamps.dt.normalize()) < close
    target = stamps.dt.normalize() + pd.to_timedelta(np.where(same_day, 0, 1), unit="D")
    position = trading_days.searchsorted(pd.DatetimeIndex(target))
    inside = position < len(trading_days)
    sessions = pd.Series(pd.NaT, index=stamps.index, dtype="datetime64[ns]")
    sessions[inside] = trading_days[position[inside]]
    return sessions


def latest_known(
    releases: pd.DataFrame,
    trading_days: pd.DatetimeIndex,
    series: str,
    change_periods: int = 3,
    vintage: str = "latest",
    session_close: str = "15:30",
) -> pd.DataFrame:
    """What was known about ``series`` at each close.

    ``releases`` is a vintage table with ``series``, ``reference`` (a pandas Period),
    ``release_ts``, ``vintage`` and ``value``. For each trading day: the latest reference
    period released by that close (``reference``), its value (``value``) and the change from
    the value ``change_periods`` periods earlier (``change``), each value taken from the
    newest vintage published by then. ``vintage="first"`` uses first releases only.
    """
    if vintage not in ("latest", "first"):
        raise ValueError("vintage must be 'latest' or 'first'")
    rel = releases[releases["series"] == series].copy()
    if vintage == "first":
        rel = rel[rel["vintage"] == "first"]
    rel["session"] = release_sessions(rel["release_ts"], trading_days, session_close).to_numpy()
    rel = rel.dropna(subset=["session"]).sort_values(["session", "release_ts"], kind="stable")
    state: dict = {}
    rows = {}
    for session, group in rel.groupby("session", sort=True):
        state.update(zip(group["reference"], group["value"], strict=True))
        latest = max(state)
        before = state.get(latest - change_periods, np.nan)
        rows[session] = {"reference": latest, "value": state[latest], "change": state[latest] - before}
    frame = pd.DataFrame.from_dict(rows, orient="index", columns=["reference", "value", "change"])
    return frame.reindex(trading_days).ffill()


def growth_inflation_regimes(
    releases: pd.DataFrame,
    trading_days: pd.DatetimeIndex,
    growth: str = "IIP",
    inflation: str = "CPI",
    change_periods: int = 3,
    timing: str = "release",
    vintage: str = "latest",
    session_close: str = "15:30",
) -> pd.DataFrame:
    """Growth x inflation regime per trading day.

    Growth (inflation) is *up* when its latest value exceeds the value ``change_periods``
    reference periods earlier. The four quadrants: ``recovery`` (growth up, inflation down),
    ``overheat`` (both up), ``stagflation`` (growth down, inflation up), ``reflation`` (both
    down).

    ``timing="release"`` (default) uses only releases known at each close: causal, trade the
    label from the next session. ``timing="reference"`` labels every day of a reference month
    with that month's final values — hindsight, for comparison only: the numbers were not
    known until weeks later and were revised after that.
    """
    if timing == "release":
        g = latest_known(releases, trading_days, growth, change_periods, vintage, session_close)
        i = latest_known(releases, trading_days, inflation, change_periods, vintage, session_close)
    elif timing == "reference":
        g = _final_by_reference(releases, trading_days, growth, change_periods)
        i = _final_by_reference(releases, trading_days, inflation, change_periods)
    else:
        raise ValueError("timing must be 'release' or 'reference'")
    frame = pd.DataFrame({"growth": g["value"], "growth_change": g["change"],
                          "inflation": i["value"], "inflation_change": i["change"]}, index=trading_days)
    known = frame[["growth_change", "inflation_change"]].notna().all(axis=1)
    labels = [REGIMES[(gc > 0, ic > 0)] for gc, ic in zip(frame["growth_change"], frame["inflation_change"], strict=True)]
    frame["regime"] = pd.Series(labels, index=trading_days).where(known)
    return frame


def _final_by_reference(releases, trading_days, series, change_periods) -> pd.DataFrame:
    rel = releases[releases["series"] == series].sort_values("release_ts", kind="stable")
    final = rel.groupby("reference")["value"].last()
    final.index = pd.PeriodIndex(final.index)
    change = final - final.reindex([p - change_periods for p in final.index]).to_numpy()
    months = trading_days.to_period(final.index.freq)
    return pd.DataFrame({"value": final.reindex(months).to_numpy(), "change": change.reindex(months).to_numpy()},
                        index=trading_days)
