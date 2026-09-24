"""Pre-trade risk management (RMS): size, value, price band, position, daily loss,
orders-per-second throttle and kill switch (M17).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .orders import BUY, LIMIT, Order


@dataclass
class RiskLimits:
    """Pre-trade limits a broker RMS enforces for one account."""
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
        """Block all new orders until reset."""
        self.kill_switch = True
        self.kill_reason = reason

    def reset_kill_switch(self) -> None:
        """Allow orders again (for example at the start of a new day)."""
        self.kill_switch = False
        self.kill_reason = ""

    def check(self, order: Order, ltp: float, position_qty: int, day_pnl: float, now: float) -> tuple[bool, str]:
        """Run every pre-trade check; returns (allowed, reason)."""
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
