"""Trade journal: fills as plain records for pandas, SQL or webhooks (M17, M18).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .orders import Fill


@dataclass
class TradeJournal:
    """Collects fills as plain dicts, ready for pandas, SQL or an n8n webhook."""

    rows: list[dict] = field(default_factory=list)

    def record(self, fill: Fill) -> dict:
        """Append a fill as a plain record and return it."""
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
