"""Order and fill records shared by brokers, risk checks and the OMS (M17).

``Order`` is what a broker receives: MARKET or LIMIT. Stop, stop-limit, bracket
and OCO orders are held by the order management system (``cfmat.trading.oms``)
and reach the broker as MARKET or LIMIT orders when they trigger.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

BUY, SELL = "BUY", "SELL"

MARKET, LIMIT = "MARKET", "LIMIT"
STOP, STOP_LIMIT = "STOP", "STOP_LIMIT"      # held by the OMS until the trigger price trades

DAY, IOC, GTC = "DAY", "IOC", "GTC"          # time in force

ORDER_TYPES = (MARKET, LIMIT, STOP, STOP_LIMIT)
TIME_IN_FORCE = (DAY, IOC, GTC)


def opposite(side: str) -> str:
    """The other side: BUY for SELL and SELL for BUY."""
    return SELL if side == BUY else BUY


@dataclass
class Order:
    """An order as the broker sees it, with its lifecycle status and fill progress."""
    symbol: str
    side: str
    qty: int
    order_type: str = MARKET
    limit_price: float | None = None
    algo_id: str = "CFMAT-DEMO"   # exchange-issued algo identifier in live trading
    id: int = 0
    status: str = "NEW"
    reject_reason: str = ""
    filled_qty: int = 0
    avg_fill_price: float = 0.0

    def __post_init__(self) -> None:
        if self.side not in (BUY, SELL):
            raise ValueError("side must be BUY or SELL")
        if self.qty <= 0:
            raise ValueError("qty must be positive")
        if self.order_type not in (MARKET, LIMIT):
            raise ValueError("a broker order is MARKET or LIMIT; stops are held by the OMS (cfmat.trading.oms)")
        if self.order_type == LIMIT and self.limit_price is None:
            raise ValueError("limit orders need a limit_price")

    @property
    def remaining(self) -> int:
        """Quantity not yet filled."""
        return self.qty - self.filled_qty


@dataclass
class Fill:
    """An execution: price, quantity and charges."""
    order_id: int
    symbol: str
    side: str
    qty: int
    price: float
    timestamp: datetime | None
    charges: float
