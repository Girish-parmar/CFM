"""Transaction costs for Indian markets: brokerage, STT, exchange fees, SEBI fee,
stamp duty and GST (Modules 1, 11, 15).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

RATES_AS_OF = "2024-10-01"  # the charge sheet the default rates follow


@dataclass
class SegmentRates:
    brokerage_pct: float      # fraction of turnover (inf = always the flat cap)
    brokerage_cap: float      # max rupees per executed order (inf = no cap)
    stt_buy: float
    stt_sell: float
    exchange_txn: float
    stamp_buy: float


@dataclass
class IndianCostModel:
    """Statutory and broker charges for NSE trades.

    The default rates are illustrative, modelled on a typical discount-broker
    charge sheet as of ``RATES_AS_OF`` (after the October 2024 STT and NSE
    transaction-charge revisions). STT, exchange and stamp-duty rates change with
    Union Budgets and exchange circulars — check your broker's current sheet
    before relying on the numbers. For options, ``price`` means the option premium.

    ``dp_charge`` is the flat depository fee a broker levies per delivery sell
    (typically ₹13–16 plus GST); it is 0 by default because it varies by broker.
    Not modelled: STT on exercised in-the-money options, IPFT and clearing fees,
    call-and-trade and auto square-off fees.
    """

    segments: dict[str, SegmentRates] = field(
        default_factory=lambda: {
            "equity_delivery": SegmentRates(0.0, np.inf, 0.001, 0.001, 0.0000297, 0.00015),
            "equity_intraday": SegmentRates(0.0003, 20.0, 0.0, 0.00025, 0.0000297, 0.00003),
            "futures": SegmentRates(0.0003, 20.0, 0.0, 0.0002, 0.0000173, 0.00002),
            "options": SegmentRates(np.inf, 20.0, 0.0, 0.001, 0.0003503, 0.00003),
        }
    )
    sebi_fee: float = 10 / 1e7   # ₹10 per crore of turnover
    gst: float = 0.18            # on brokerage + exchange + SEBI fees (+ DP charge)
    dp_charge: float = 0.0       # ₹ per delivery sell order, before GST

    def charges(self, side: str, qty: float, price: float, segment: str = "equity_intraday") -> dict[str, float]:
        if side not in ("buy", "sell"):
            raise ValueError("side must be 'buy' or 'sell'")
        rates = self.segments[segment]
        turnover = abs(qty) * price
        brokerage = min(turnover * rates.brokerage_pct, rates.brokerage_cap) if turnover > 0 else 0.0
        stt = turnover * (rates.stt_buy if side == "buy" else rates.stt_sell)
        exchange = turnover * rates.exchange_txn
        sebi = turnover * self.sebi_fee
        stamp = turnover * rates.stamp_buy if side == "buy" else 0.0
        dp = self.dp_charge if (side == "sell" and segment == "equity_delivery" and turnover > 0) else 0.0
        gst = self.gst * (brokerage + exchange + sebi + dp)
        total = brokerage + stt + exchange + sebi + stamp + dp + gst
        return {"turnover": turnover, "brokerage": brokerage, "stt": stt, "exchange": exchange,
                "sebi": sebi, "stamp": stamp, "dp": dp, "gst": gst, "total": total}

    def round_trip_bps(self, qty: float, price: float, segment: str = "equity_intraday") -> float:
        """Total buy + sell charges as basis points of one side's turnover."""
        cost = self.charges("buy", qty, price, segment)["total"] + self.charges("sell", qty, price, segment)["total"]
        return 1e4 * cost / (abs(qty) * price)
