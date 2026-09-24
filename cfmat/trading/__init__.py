"""Order management for paper and live trading (M17).

orders        order and fill records, order types and time in force
risk_checks   pre-trade risk management (RMS) and kill switch
paper_broker  broker interface (with a fill stream) and a simulated broker
oms           order management system: state machine, stops, bracket/OCO, audit trail, reconciliation
journal       trade journal: fills, round trips, R-multiples, MAE/MFE, statistics, persistence
"""

from .journal import (
    TradeJournal,
    excursions,
    round_trips,
    trade_breakdown,
    trade_summary,
)
from .oms import (
    InvalidTransition,
    ManagedOrder,
    OrderEvent,
    OrderGroup,
    OrderManager,
)
from .orders import (
    BUY,
    DAY,
    GTC,
    IOC,
    LIMIT,
    MARKET,
    SELL,
    STOP,
    STOP_LIMIT,
    Fill,
    Order,
    opposite,
)
from .paper_broker import (
    BrokerAdapter,
    PaperBroker,
)
from .risk_checks import (
    RiskLimits,
    RiskManager,
)

__all__ = [
    "BUY",
    "DAY",
    "GTC",
    "IOC",
    "LIMIT",
    "MARKET",
    "SELL",
    "STOP",
    "STOP_LIMIT",
    "BrokerAdapter",
    "Fill",
    "InvalidTransition",
    "ManagedOrder",
    "Order",
    "OrderEvent",
    "OrderGroup",
    "OrderManager",
    "PaperBroker",
    "RiskLimits",
    "RiskManager",
    "TradeJournal",
    "excursions",
    "opposite",
    "round_trips",
    "trade_breakdown",
    "trade_summary",
]
