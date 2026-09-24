"""Order management, pre-trade risk checks and a paper broker (Module 11).

Real broker APIs (Kite Connect, Upstox, SmartAPI, Interactive Brokers …) are
wrapped behind ``BrokerAdapter`` so a strategy can move from paper to live by
swapping one object. ``RiskManager`` mirrors the checks a broker's RMS and the
exchange framework for retail algos expect: order size and value caps, position
limits, a daily loss limit, an orders-per-second throttle and a kill switch.
"""

from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from .backtest import IndianCostModel

BUY, SELL = "BUY", "SELL"
MARKET, LIMIT = "MARKET", "LIMIT"


@dataclass
class Order:
    symbol: str
    side: str
    qty: int
    order_type: str = MARKET
    limit_price: float | None = None
    algo_id: str = "CFMAT-DEMO"   # exchange-issued algo identifier in live trading
    id: int = 0
    status: str = "NEW"
    reject_reason: str = ""

    def __post_init__(self) -> None:
        if self.side not in (BUY, SELL):
            raise ValueError("side must be BUY or SELL")
        if self.qty <= 0:
            raise ValueError("qty must be positive")
        if self.order_type == LIMIT and self.limit_price is None:
            raise ValueError("limit orders need a limit_price")


@dataclass
class Fill:
    order_id: int
    symbol: str
    side: str
    qty: int
    price: float
    timestamp: datetime | None
    charges: float


@dataclass
class RiskLimits:
    max_order_qty: int = 10_000
    max_order_value: float = 500_000.0
    max_position_qty: int = 20_000
    max_daily_loss: float = 50_000.0
    max_orders_per_second: int = 10
    price_band_pct: float = 0.05          # limit price must be within ±5% of LTP
    allowed_symbols: set[str] | None = None


class RiskManager:
    """Pre-trade checks. ``check`` returns ``(True, "")`` or ``(False, reason)``."""

    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()
        self.kill_switch = False
        self.kill_reason = ""
        self._recent: deque[float] = deque()

    def activate_kill_switch(self, reason: str) -> None:
        self.kill_switch = True
        self.kill_reason = reason

    def reset_kill_switch(self) -> None:
        self.kill_switch = False
        self.kill_reason = ""

    def check(self, order: Order, ltp: float, position_qty: int, day_pnl: float, now: float) -> tuple[bool, str]:
        lim = self.limits
        if self.kill_switch:
            return False, f"kill switch active: {self.kill_reason}"
        if lim.allowed_symbols is not None and order.symbol not in lim.allowed_symbols:
            return False, f"{order.symbol} is not on the approved list"
        if day_pnl <= -lim.max_daily_loss:
            self.activate_kill_switch(f"daily loss limit {lim.max_daily_loss:,.0f} breached")
            return False, f"kill switch active: {self.kill_reason}"
        if order.qty > lim.max_order_qty:
            return False, f"order qty {order.qty} exceeds {lim.max_order_qty}"
        price = order.limit_price if order.order_type == LIMIT else ltp
        if order.qty * price > lim.max_order_value:
            return False, f"order value {order.qty * price:,.0f} exceeds {lim.max_order_value:,.0f}"
        if order.order_type == LIMIT and abs(order.limit_price / ltp - 1.0) > lim.price_band_pct:
            return False, "limit price outside the allowed band (fat-finger check)"
        signed = order.qty if order.side == BUY else -order.qty
        if abs(position_qty + signed) > lim.max_position_qty:
            return False, f"resulting position exceeds {lim.max_position_qty}"
        while self._recent and now - self._recent[0] >= 1.0:
            self._recent.popleft()
        if len(self._recent) >= lim.max_orders_per_second:
            return False, f"throttled: more than {lim.max_orders_per_second} orders per second"
        self._recent.append(now)
        return True, ""


class BrokerAdapter(ABC):
    """The surface every broker integration implements."""

    @abstractmethod
    def place_order(self, order: Order, timestamp: datetime | None = None) -> Order: ...

    @abstractmethod
    def cancel_order(self, order_id: int) -> bool: ...

    @abstractmethod
    def positions(self) -> dict[str, int]: ...

    @abstractmethod
    def equity(self) -> float: ...


@dataclass
class _Position:
    qty: int = 0
    avg_price: float = 0.0


class PaperBroker(BrokerAdapter):
    """Simulated broker: fills against the last price you feed it.

    Market orders fill immediately at LTP ± ``slippage_bps``. Limit orders fill
    when marketable, otherwise rest until ``update_price`` crosses them.
    """

    def __init__(
        self,
        cash: float = 1_000_000.0,
        risk: RiskManager | None = None,
        slippage_bps: float = 2.0,
        cost_model: IndianCostModel | None = None,
        segment: str = "equity_intraday",
    ) -> None:
        self.cash = cash
        self.risk = risk
        self.slippage_bps = slippage_bps
        self.cost_model = cost_model
        self.segment = segment
        self.last_price: dict[str, float] = {}
        self._positions: dict[str, _Position] = {}
        self.open_orders: dict[int, Order] = {}
        self.orders: list[Order] = []
        self.fills: list[Fill] = []
        self.realized_pnl = 0.0
        self.total_charges = 0.0
        self._ids = itertools.count(1)
        self._clock = 0.0
        self.day_start_equity = cash

    # -- market data -------------------------------------------------------
    def update_price(self, symbol: str, price: float, timestamp: datetime | None = None) -> None:
        self.last_price[symbol] = price
        for order in list(self.open_orders.values()):
            if order.symbol == symbol and self._marketable(order, price):
                self._execute(order, order.limit_price, timestamp)
        # Mark-to-market loss monitoring, as a broker RMS does between orders.
        if self.risk and not self.risk.kill_switch and self.day_pnl() <= -self.risk.limits.max_daily_loss:
            self.risk.activate_kill_switch(f"daily loss limit {self.risk.limits.max_daily_loss:,.0f} breached")

    def start_new_day(self) -> None:
        self.day_start_equity = self.equity()
        if self.risk:
            self.risk.reset_kill_switch()

    # -- orders -------------------------------------------------------------
    def place_order(self, order: Order, timestamp: datetime | None = None) -> Order:
        order.id = next(self._ids)
        self.orders.append(order)
        ltp = self.last_price.get(order.symbol)
        if ltp is None:
            return self._reject(order, "no market price for symbol")
        if self.risk:
            self._clock = timestamp.timestamp() if timestamp else self._clock + 1.0
            ok, reason = self.risk.check(order, ltp, self.position(order.symbol), self.day_pnl(), self._clock)
            if not ok:
                return self._reject(order, reason)
        if order.order_type == MARKET:
            slip = ltp * self.slippage_bps / 1e4
            self._execute(order, ltp + slip if order.side == BUY else ltp - slip, timestamp)
        elif self._marketable(order, ltp):
            self._execute(order, order.limit_price, timestamp)
        else:
            order.status = "OPEN"
            self.open_orders[order.id] = order
        return order

    def cancel_order(self, order_id: int) -> bool:
        order = self.open_orders.pop(order_id, None)
        if order is None:
            return False
        order.status = "CANCELLED"
        return True

    def square_off_all(self, timestamp: datetime | None = None) -> None:
        """Flatten every position with market orders (bypasses the risk throttle)."""
        for order_id in list(self.open_orders):
            self.cancel_order(order_id)
        for symbol, pos in self._positions.items():
            if pos.qty:
                side = SELL if pos.qty > 0 else BUY
                order = Order(symbol, side, abs(pos.qty))
                order.id = next(self._ids)
                self.orders.append(order)
                self._execute(order, self.last_price[symbol], timestamp)

    # -- state ---------------------------------------------------------------
    def position(self, symbol: str) -> int:
        return self._positions.get(symbol, _Position()).qty

    def positions(self) -> dict[str, int]:
        return {s: p.qty for s, p in self._positions.items() if p.qty}

    def equity(self) -> float:
        return self.cash + sum(p.qty * self.last_price.get(s, p.avg_price) for s, p in self._positions.items())

    def day_pnl(self) -> float:
        return self.equity() - self.day_start_equity

    # -- internals -------------------------------------------------------------
    @staticmethod
    def _marketable(order: Order, price: float) -> bool:
        if order.order_type != LIMIT:
            return True
        return price <= order.limit_price if order.side == BUY else price >= order.limit_price

    def _reject(self, order: Order, reason: str) -> Order:
        order.status = "REJECTED"
        order.reject_reason = reason
        return order

    def _execute(self, order: Order, price: float, timestamp: datetime | None) -> None:
        signed = order.qty if order.side == BUY else -order.qty
        charges = 0.0
        if self.cost_model:
            charges = self.cost_model.charges(order.side.lower(), order.qty, price, self.segment)["total"]
        pos = self._positions.setdefault(order.symbol, _Position())
        if pos.qty == 0 or (pos.qty > 0) == (signed > 0):
            pos.avg_price = (pos.avg_price * abs(pos.qty) + price * abs(signed)) / (abs(pos.qty) + abs(signed))
            pos.qty += signed
        else:
            closing = min(abs(signed), abs(pos.qty))
            direction = 1 if pos.qty > 0 else -1
            self.realized_pnl += closing * (price - pos.avg_price) * direction
            pos.qty += signed
            if pos.qty == 0:
                pos.avg_price = 0.0
            elif (pos.qty > 0) != (direction > 0):
                pos.avg_price = price  # flipped through zero
        self.cash -= signed * price + charges
        self.total_charges += charges
        order.status = "FILLED"
        self.open_orders.pop(order.id, None)
        self.fills.append(Fill(order.id, order.symbol, order.side, order.qty, price, timestamp, charges))


@dataclass
class TradeJournal:
    """Collects fills as plain dicts, ready for pandas, SQL or an n8n webhook."""

    rows: list[dict] = field(default_factory=list)

    def record(self, fill: Fill) -> dict:
        row = {
            "order_id": fill.order_id,
            "symbol": fill.symbol,
            "side": fill.side,
            "qty": fill.qty,
            "price": round(fill.price, 4),
            "charges": round(fill.charges, 2),
            "timestamp": fill.timestamp.isoformat() if fill.timestamp else None,
        }
        self.rows.append(row)
        return row
