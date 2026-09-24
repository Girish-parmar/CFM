"""Event-driven backtester (M11).

Unlike the vectorised backtester, this replays bars one at a time through the
same ``PaperBroker`` used for paper trading, so strategy code written here runs
unchanged against a live ``BrokerAdapter`` later.

Timing model: ``on_bar`` sees bar t after its close; orders it submits are
executed at bar t+1's open.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from ..microstructure.costs import IndianCostModel
from ..trading import BUY, SELL, Order, PaperBroker, RiskManager


@dataclass
class Context:
    """What a strategy sees on each bar: its symbol, the broker, and the history so far."""
    symbol: str
    broker: PaperBroker
    history: pd.DataFrame = field(default_factory=pd.DataFrame)
    _pending: list[Order] = field(default_factory=list)

    @property
    def position(self) -> int:
        return self.broker.position(self.symbol)

    def order(self, qty: int) -> None:
        """Queue a market order: positive qty buys, negative sells."""
        if qty:
            self._pending.append(Order(self.symbol, BUY if qty > 0 else SELL, abs(int(qty))))

    def order_target(self, target_qty: int) -> None:
        """Send the order that moves the position to ``target_qty``."""
        self.order(int(target_qty) - self.position)


class Strategy:
    """Subclass and override ``on_bar``."""

    def on_start(self, ctx: Context) -> None:  # pragma: no cover - optional hook
        """Called once before the first bar."""
        pass

    def on_bar(self, ctx: Context, bar: pd.Series) -> None:
        """Called at each bar's close with the history up to and including ``bar``."""
        raise NotImplementedError


class SmaCrossStrategy(Strategy):
    """Reference strategy: hold ``qty`` shares while the fast SMA is above the slow SMA."""

    def __init__(self, fast: int = 20, slow: int = 50, qty: int = 100) -> None:
        self.fast, self.slow, self.qty = fast, slow, qty

    def on_bar(self, ctx: Context, bar: pd.Series) -> None:
        """Hold ``qty`` shares while the fast SMA is above the slow SMA, otherwise flat."""
        close = ctx.history["close"]
        if len(close) < self.slow:
            return
        bullish = close.iloc[-self.fast:].mean() > close.iloc[-self.slow:].mean()
        ctx.order_target(self.qty if bullish else 0)


def run_event_backtest(
    bars: pd.DataFrame,
    strategy: Strategy,
    cash: float = 1_000_000.0,
    symbol: str = "SYN",
    slippage_bps: float = 2.0,
    cost_model: IndianCostModel | None = None,
    segment: str = "equity_delivery",
    risk: RiskManager | None = None,
) -> tuple[pd.DataFrame, PaperBroker]:
    """Replay OHLCV ``bars`` through ``strategy``. Returns (equity table, broker)."""
    broker = PaperBroker(cash, risk, slippage_bps, cost_model, segment)
    ctx = Context(symbol, broker)
    strategy.on_start(ctx)
    records = []
    for i, (ts, bar) in enumerate(bars.iterrows()):
        broker.start_new_day()
        broker.update_price(symbol, float(bar["open"]), ts)
        for order in ctx._pending:
            broker.place_order(order, ts)
        ctx._pending.clear()
        broker.update_price(symbol, float(bar["close"]), ts)
        ctx.history = bars.iloc[: i + 1]
        strategy.on_bar(ctx, bar)
        records.append({"date": ts, "equity": broker.equity(), "cash": broker.cash, "position": ctx.position})
    table = pd.DataFrame(records).set_index("date")
    table["strategy_return"] = table["equity"].pct_change().fillna(0.0)
    return table, broker
