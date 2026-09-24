"""Order and fill records shared by brokers and risk checks (Module 17).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

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
