"""Live monitoring for a trading process: heartbeats, stale data, drift, P&L attribution and alerts (M18).

    heartbeat_gaps     silences in a process's heartbeat longer than a tolerance
    staleness          timed feed checks: no updates at all, or updates whose price stopped moving
    drift_report       live (or paper) trading against its backtest: tracking, return
                       distribution, signal agreement and slippage
    pnl_attribution    daily P&L split into signal, execution and costs, which add up exactly
    AlertRule, AlertManager, webhook_sink
                       threshold rules with severity, de-duplication, reminders and resolution
                       notices, delivered to any callable such as an n8n webhook

Every check has a false-alarm budget: thresholds and test levels decide how often a
healthy system pages someone. Measure it on clean days before trusting an alert.
"""

from __future__ import annotations

import json
import operator
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field
from itertools import pairwise

import numpy as np
import pandas as pd
from scipy import stats

from ..data.synthetic import NSE_SESSION

SEVERITY = {"info": 0, "warning": 1, "critical": 2}
_OPS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le, "==": operator.eq}


# -- heartbeats and staleness ---------------------------------------------------------------

def heartbeat_gaps(
    beats: Iterable,
    every: str = "10s",
    tolerance: float = 3.0,
    start: str | pd.Timestamp | None = None,
    end: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Silences longer than ``tolerance`` × ``every`` in a process's heartbeat.

    Pass ``start`` and ``end`` (for example the session open and the time of the check) so a
    process that never started, or died before the last check, is caught too. Columns:
    ``start`` (last beat heard), ``end`` (next beat, or ``end``), ``seconds``, ``missed``
    (beats not received) and ``detected_at`` (when an alert could first fire).
    """
    period = pd.Timedelta(every)
    limit = tolerance * period
    stamps = pd.DatetimeIndex(sorted(pd.to_datetime(list(beats))))
    edges = [pd.Timestamp(start)] if start is not None else []
    stamps = pd.DatetimeIndex([*edges, *stamps, *([pd.Timestamp(end)] if end is not None else [])])
    rows = []
    for a, b in pairwise(stamps):
        if b - a > limit:
            rows.append({"start": a, "end": b, "seconds": (b - a).total_seconds(),
                         "missed": int((b - a) / period) - 1, "detected_at": a + limit})
    return pd.DataFrame(rows, columns=["start", "end", "seconds", "missed", "detected_at"])


def staleness(
    updates: pd.DataFrame,
    check_every: str = "5s",
    max_age: str = "30s",
    frozen_after: str = "30s",
    min_updates: int = 5,
    session: tuple[str, str] = NSE_SESSION,
) -> pd.DataFrame:
    """Feed checks on a timer, per symbol: ``no_updates`` or ``frozen`` incidents.

    ``updates`` has ``ts``, ``symbol`` and ``price``. At each check inside the session, a
    symbol is ``no_updates`` when nothing arrived for ``max_age``, and ``frozen`` when at
    least ``min_updates`` updates arrived since the price last changed, ``frozen_after`` ago
    (a feed repeating its last value; a silent feed is ``no_updates``, not frozen).
    Consecutive failing checks form one incident: ``start`` is the first failing check,
    ``end`` the first passing one. Set thresholds per instrument: an illiquid stock can
    legitimately go quiet for minutes.
    """
    open_, close = (pd.Timedelta(f"{t}:00") for t in session)
    step, age_limit, frozen_limit = pd.Timedelta(check_every), pd.Timedelta(max_age), pd.Timedelta(frozen_after)
    rows = []
    for (day, symbol), group in updates.sort_values("ts").groupby([updates["ts"].dt.normalize(), "symbol"]):
        checks = pd.date_range(day + open_ + step, day + close, freq=step, inclusive="left")
        ts = group["ts"].to_numpy()
        price = group["price"].to_numpy()
        change_pos = np.flatnonzero(np.r_[True, price[1:] != price[:-1]])
        n_seen = np.searchsorted(ts, checks.to_numpy(), side="right")
        n_changes = np.searchsorted(ts[change_pos], checks.to_numpy(), side="right")
        opened = np.datetime64(day + open_)
        last_update = np.where(n_seen > 0, ts[np.maximum(n_seen - 1, 0)], opened)
        last_pos = np.where(n_changes > 0, change_pos[np.maximum(n_changes - 1, 0)], -1)
        last_change = np.where(last_pos >= 0, ts[np.maximum(last_pos, 0)], opened)
        since_change = n_seen - 1 - last_pos                        # updates that repeated the price
        age = checks.to_numpy() - last_update
        still = checks.to_numpy() - last_change
        frozen = (still > frozen_limit) & (since_change >= min_updates)
        kinds = np.where(age > age_limit, "no_updates", np.where(frozen, "frozen", ""))
        current, began = "", None
        for when, kind in zip(checks, kinds, strict=True):
            if kind != current:
                if current:
                    rows.append({"symbol": symbol, "kind": current, "start": began, "end": when})
                current, began = kind, when
        if current:
            rows.append({"symbol": symbol, "kind": current, "start": began, "end": pd.NaT})
    return pd.DataFrame(rows, columns=["symbol", "kind", "start", "end"])


# -- drift -------------------------------------------------------------------------------------

def drift_report(
    live_returns: pd.Series,
    backtest_returns: pd.Series,
    live_signals: pd.Series | None = None,
    backtest_signals: pd.Series | None = None,
    fills: pd.DataFrame | None = None,
    expected_slippage_bps: float = 0.0,
    alpha: float = 0.01,
    min_agreement: float = 0.95,
) -> pd.Series:
    """Is live (or paper) trading still the strategy that was backtested?

    * tracking: mean daily difference live − backtest over common days, with a t-statistic;
    * distribution: two-sample Kolmogorov–Smirnov test of the daily returns;
    * signals: share of bars where live and backtest wanted the same position;
    * slippage: from ``fills`` (``side``, ``fill_price``, ``model_price``), the cost in bp
      against the model price, tested against ``expected_slippage_bps``.

    Each check has a ``*_drift`` flag; ``alpha`` is the false-alarm rate per statistical test.
    Every field is always present: checks without data read NaN and do not flag drift.
    """
    common = live_returns.dropna().index.intersection(backtest_returns.dropna().index)
    diff = (live_returns.loc[common] - backtest_returns.loc[common]).astype(float)
    critical = stats.norm.ppf(1 - alpha / 2)
    t_track = diff.mean() / (diff.std(ddof=1) / np.sqrt(len(diff))) if len(diff) > 2 and diff.std() > 0 else 0.0
    ks = stats.ks_2samp(live_returns.dropna(), backtest_returns.dropna())
    out = {
        "days": float(len(common)),
        "tracking_bps_per_day": float(diff.mean() * 1e4),
        "tracking_tstat": float(t_track),
        "tracking_drift": bool(abs(t_track) > critical),
        "ks_stat": float(ks.statistic),
        "ks_pvalue": float(ks.pvalue),
        "distribution_drift": bool(ks.pvalue < alpha),
    }
    out.update({"signal_agreement": float("nan"), "signal_drift": False,
                "slippage_bps": float("nan"), "slippage_tstat": float("nan"), "slippage_drift": False})
    if live_signals is not None and backtest_signals is not None:
        both = pd.concat([live_signals, backtest_signals], axis=1, join="inner").dropna()
        if len(both):
            agreement = float((both.iloc[:, 0] == both.iloc[:, 1]).mean())
            out.update({"signal_agreement": agreement, "signal_drift": bool(agreement < min_agreement)})
    if fills is not None and len(fills):
        sign = np.where(fills["side"].str.upper() == "BUY", 1.0, -1.0)
        slip = sign * (fills["fill_price"] - fills["model_price"]) / fills["model_price"] * 1e4
        excess = slip - expected_slippage_bps
        t_slip = excess.mean() / (excess.std(ddof=1) / np.sqrt(len(excess))) if len(excess) > 2 and excess.std() > 0 else 0.0
        out.update({"slippage_bps": float(slip.mean()), "slippage_tstat": float(t_slip),
                    "slippage_drift": bool(t_slip > stats.norm.ppf(1 - alpha))})
    out["drift"] = any(v for k, v in out.items() if k.endswith("_drift"))
    return pd.Series(out, dtype=object)


# -- P&L attribution ---------------------------------------------------------------------------------

def pnl_attribution(trades: pd.DataFrame, closes: pd.Series | pd.DataFrame) -> pd.DataFrame:
    """Daily P&L split into signal, execution and costs; the three add up to the true P&L.

    ``trades``: ``ts``, ``symbol``, ``side``, ``qty``, ``decision_price`` (the price the
    signal saw), ``fill_price`` and ``charges``. ``closes``: daily closing prices, one column
    per symbol (a Series for one symbol). Per day:

    * signal = positions carried × close-to-close move + trades × (close − decision price):
      what the strategy would have made with perfect fills and no costs;
    * execution = trades × (decision price − fill price): what slippage and timing cost;
    * costs = − charges.
    """
    closes = closes.to_frame(trades["symbol"].iloc[0]) if isinstance(closes, pd.Series) else closes
    days = closes.index
    parts = []
    for symbol, group in trades.groupby("symbol"):
        close = closes[symbol]
        signed = np.where(group["side"].str.upper() == "BUY", 1.0, -1.0) * group["qty"].to_numpy()
        day = pd.DatetimeIndex(group["ts"]).normalize()
        per_day = pd.DataFrame({
            "qty": signed,
            "vs_close": signed * (close.reindex(day).to_numpy() - group["decision_price"].to_numpy()),
            "execution": signed * (group["decision_price"].to_numpy() - group["fill_price"].to_numpy()),
            "costs": -group["charges"].to_numpy(dtype=float),
        }, index=day).groupby(level=0).sum().reindex(days, fill_value=0.0)
        carried = per_day["qty"].cumsum().shift(fill_value=0.0)
        signal = carried * close.diff().fillna(0.0) + per_day["vs_close"]
        parts.append(pd.DataFrame({"signal": signal, "execution": per_day["execution"], "costs": per_day["costs"]}))
    total = sum(parts[1:], parts[0]) if parts else pd.DataFrame(0.0, index=days, columns=["signal", "execution", "costs"])
    total["total"] = total[["signal", "execution", "costs"]].sum(axis=1)
    return total


# -- alerts ------------------------------------------------------------------------------------

@dataclass
class AlertRule:
    """Fire when ``metric`` ``op`` ``threshold`` holds, at most once per ``cooldown`` while it lasts."""
    name: str
    metric: str
    op: str
    threshold: float
    severity: str = "warning"
    cooldown: str = "15min"
    message: str = "{name}: {metric} = {value:.4g} (rule: {op} {threshold:g})"

    def __post_init__(self) -> None:
        if self.op not in _OPS:
            raise ValueError(f"op must be one of {sorted(_OPS)}")
        if self.severity not in SEVERITY:
            raise ValueError(f"severity must be one of {sorted(SEVERITY, key=SEVERITY.get)}")

    def breached(self, value: float) -> bool:
        """True when the value breaks the rule (missing values never do)."""
        return value is not None and not (isinstance(value, float) and np.isnan(value)) and \
            bool(_OPS[self.op](value, self.threshold))


@dataclass
class Alert:
    """One notification: ``status`` is firing, reminder or resolved."""
    ts: pd.Timestamp
    rule: str
    severity: str
    status: str
    value: float
    message: str


@dataclass
class AlertManager:
    """Evaluate rules on each batch of metrics, de-duplicate, and deliver alerts to ``sinks``.

    A rule fires once when first breached, reminds after each ``cooldown`` while still
    breached, and sends one ``resolved`` notice when it clears. Alerts go out most severe
    first. A sink that raises does not stop monitoring: the error is kept in ``failures``.
    """
    rules: list[AlertRule]
    sinks: list[Callable[[Alert], None]] = field(default_factory=list)
    history: list[Alert] = field(default_factory=list, init=False)
    failures: list[tuple[Alert, str]] = field(default_factory=list, init=False)
    _active: dict[str, pd.Timestamp] = field(default_factory=dict, init=False, repr=False)

    def evaluate(self, metrics: dict[str, float], now) -> list[Alert]:
        """Check every rule against ``metrics`` at time ``now``; returns the alerts sent."""
        now = pd.Timestamp(now)
        out = []
        for rule in self.rules:
            value = metrics.get(rule.metric)
            text = rule.message.format(name=rule.name, metric=rule.metric, value=np.nan if value is None else value,
                                       op=rule.op, threshold=rule.threshold)
            if rule.breached(value):
                last = self._active.get(rule.name)
                if last is None:
                    status = "firing"
                elif now - last >= pd.Timedelta(rule.cooldown):
                    status = "reminder"
                else:
                    continue
                self._active[rule.name] = now
                out.append(Alert(now, rule.name, rule.severity, status, float(value), text))
            elif rule.name in self._active:
                del self._active[rule.name]
                out.append(Alert(now, rule.name, rule.severity, "resolved",
                                 float("nan") if value is None else float(value), f"resolved: {text}"))
        out.sort(key=lambda a: -SEVERITY[a.severity])
        for alert in out:
            for sink in self.sinks:
                try:
                    sink(alert)
                except Exception as exc:   # a broken sink must not stop monitoring
                    self.failures.append((alert, repr(exc)))
        self.history += out
        return out

    def history_frame(self) -> pd.DataFrame:
        """Every alert sent so far, one row each."""
        return pd.DataFrame([asdict(a) for a in self.history], columns=list(Alert.__dataclass_fields__))


def webhook_sink(url: str, timeout: float = 5.0) -> Callable[[Alert], None]:
    """A sink that POSTs each alert as JSON to ``url`` (for example an n8n webhook).

    Keep the URL in configuration, add header authentication on the n8n side, and never
    expose the webhook to the internet without it.
    """
    def send(alert: Alert) -> None:
        payload = {**asdict(alert), "ts": pd.Timestamp(alert.ts).isoformat()}
        request = urllib.request.Request(url, data=json.dumps(payload, default=str).encode(), method="POST",
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read()

    return send
