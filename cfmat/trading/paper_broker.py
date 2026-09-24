"""Broker interface and a simulated (paper) broker (M17).

Real broker APIs (Kite Connect, Upstox, SmartAPI, Interactive Brokers ...) are
wrapped behind ``BrokerAdapter`` so a strategy can move from paper to live by
swapping one object, with ``RiskManager`` in front of every order.
"""

from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from ..microstructure.costs import IndianCostModel
from .orders import BUY, LIMIT, MARKET, SELL, Fill, Order
from .risk_checks import RiskManager


class BrokerAdapter(ABC):
    """The surface every broker integration implements."""

    @abstractmethod
    def place_order(self, order: Order, timestamp: datetime | None = None) -> Order:
        """Send an order; returns it with its id and status."""

    @abstractmethod
    def cancel_order(self, order_id: int) -> bool:
        """Cancel an open order; False if it is not open."""

    @abstractmethod
    def positions(self) -> dict[str, int]:
        """Open positions by symbol."""

    @abstractmethod
    def equity(self) -> float:
        """Cash plus marked-to-market positions."""


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
        """New last price: fill marketable resting orders and run the mark-to-market loss check."""
        self.last_price[symbol] = price
        for order in list(self.open_orders.values()):
            if order.symbol == symbol and self._marketable(order, price):
                self._execute(order, order.limit_price, timestamp)
        # Mark-to-market loss monitoring, as a broker RMS does between orders.
        if self.risk and not self.risk.kill_switch and self.day_pnl() <= -self.risk.limits.max_daily_loss:
            self.risk.activate_kill_switch(f"daily loss limit {self.risk.limits.max_daily_loss:,.0f} breached")

    def start_new_day(self) -> None:
        """Reset the day's P&L baseline and the kill switch."""
        self.day_start_equity = self.equity()
        if self.risk:
            self.risk.reset_kill_switch()

    # -- orders -------------------------------------------------------------
    def place_order(self, order: Order, timestamp: datetime | None = None) -> Order:
        """Risk-check and execute or rest an order at the last price (with slippage)."""
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
        """Cancel an open order; False if it is not open."""
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
        """Signed quantity held in ``symbol``."""
        return self._positions.get(symbol, _Position()).qty

    def positions(self) -> dict[str, int]:
        """Non-zero positions by symbol."""
        return {s: p.qty for s, p in self._positions.items() if p.qty}

    def equity(self) -> float:
        """Cash plus positions marked at the last price."""
        return self.cash + sum(p.qty * self.last_price.get(s, p.avg_price) for s, p in self._positions.items())

    def day_pnl(self) -> float:
        """Equity change since the start of the day."""
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
