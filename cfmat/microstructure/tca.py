"""Transaction-cost analysis: market impact and implementation shortfall (Module 15).
"""

from __future__ import annotations

import numpy as np


def square_root_impact_bps(qty: float, adv: float, daily_vol: float, y: float = 1.0) -> float:
    """Empirical square-root law: impact ≈ Y · σ_daily · sqrt(Q / ADV)."""
    return float(y * daily_vol * np.sqrt(qty / adv) * 1e4)


def implementation_shortfall(
    side: str, decision_price: float, fills: list[tuple[int, float]], target_qty: int, final_price: float
) -> dict[str, float]:
    """Perold (1988) shortfall versus the price when the decision was made.

    ``fills`` is a list of (qty, price). Unfilled shares are charged the move
    from decision to ``final_price`` as opportunity cost. Positive = cost.
    """
    sign = 1 if side == "BUY" else -1
    filled = sum(q for q, _ in fills)
    avg = sum(q * p for q, p in fills) / filled if filled else decision_price
    execution = sign * (avg - decision_price) * filled
    opportunity = sign * (final_price - decision_price) * (target_qty - filled)
    notional = decision_price * target_qty
    return {
        "filled_qty": filled,
        "avg_price": avg,
        "execution_cost": execution,
        "opportunity_cost": opportunity,
        "total_cost": execution + opportunity,
        "total_bps": 1e4 * (execution + opportunity) / notional,
    }
