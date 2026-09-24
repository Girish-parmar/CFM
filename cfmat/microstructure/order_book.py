"""A price-time-priority limit order book (M15).
"""

from __future__ import annotations

import itertools
from collections import deque

import pandas as pd


class OrderBook:
    """Continuous double auction with price–time priority (like NSE's matching engine).

    >>> book = OrderBook()
    >>> _ = book.add_limit("SELL", 101.0, 50)
    >>> _, trades = book.add_limit("BUY", 101.0, 20)
    >>> trades[0]["qty"], book.best_ask()
    (20, 101.0)
    """

    def __init__(self) -> None:
        self.bids: dict[float, deque] = {}
        self.asks: dict[float, deque] = {}
        self._where: dict[int, tuple[str, float]] = {}
        self._ids = itertools.count(1)
        self.trades: list[dict] = []

    # -- queries -------------------------------------------------------------
    def best_bid(self) -> float | None:
        """Highest resting bid price, or None."""
        return max(self.bids) if self.bids else None

    def best_ask(self) -> float | None:
        """Lowest resting ask price, or None."""
        return min(self.asks) if self.asks else None

    def spread(self) -> float | None:
        """Best ask − best bid, or None if either side is empty."""
        bid, ask = self.best_bid(), self.best_ask()
        return None if bid is None or ask is None else ask - bid

    def resting_order_ids(self) -> list[int]:
        """IDs of orders still resting in the book."""
        return list(self._where)

    def mid(self) -> float | None:
        """Mid price, or None if either side is empty."""
        bid, ask = self.best_bid(), self.best_ask()
        return None if bid is None or ask is None else (bid + ask) / 2

    def depth(self, levels: int = 5) -> pd.DataFrame:
        """Top ``levels`` price levels on each side with their total quantity."""
        bids = sorted(self.bids, reverse=True)[:levels]
        asks = sorted(self.asks)[:levels]
        rows = []
        for i in range(max(len(bids), len(asks))):
            rows.append({
                "bid_qty": sum(q for _, q in self.bids[bids[i]]) if i < len(bids) else None,
                "bid": bids[i] if i < len(bids) else None,
                "ask": asks[i] if i < len(asks) else None,
                "ask_qty": sum(q for _, q in self.asks[asks[i]]) if i < len(asks) else None,
            })
        return pd.DataFrame(rows)

    # -- order entry ---------------------------------------------------------------
    def add_limit(self, side: str, price: float, qty: int) -> tuple[int, list[dict]]:
        """Match a limit order against the book; any remainder rests. Returns (order id, trades)."""
        order_id = next(self._ids)
        remaining, trades = self._match(side, qty, order_id, limit=price)
        if remaining > 0:
            book = self.bids if side == "BUY" else self.asks
            book.setdefault(price, deque()).append([order_id, remaining])
            self._where[order_id] = (side, price)
        return order_id, trades

    def add_market(self, side: str, qty: int) -> list[dict]:
        """Match a market order against the book; any unfilled remainder is dropped. Returns trades."""
        _, trades = self._match(side, qty, next(self._ids), limit=None)
        return trades

    def cancel(self, order_id: int) -> bool:
        """Cancel a resting order; False if it is not in the book."""
        loc = self._where.pop(order_id, None)
        if loc is None:
            return False
        side, price = loc
        book = self.bids if side == "BUY" else self.asks
        queue = book[price]
        for entry in queue:
            if entry[0] == order_id:
                queue.remove(entry)
                break
        if not queue:
            del book[price]
        return True

    def _match(self, side: str, qty: int, taker_id: int, limit: float | None) -> tuple[int, list[dict]]:
        if side not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")
        opposite = self.asks if side == "BUY" else self.bids
        trades = []
        while qty > 0 and opposite:
            best = min(opposite) if side == "BUY" else max(opposite)
            if limit is not None and ((side == "BUY" and best > limit) or (side == "SELL" and best < limit)):
                break
            queue = opposite[best]
            maker = queue[0]
            traded = min(qty, maker[1])
            trade = {"price": best, "qty": traded, "aggressor": side, "maker_id": maker[0], "taker_id": taker_id}
            trades.append(trade)
            self.trades.append(trade)
            qty -= traded
            maker[1] -= traded
            if maker[1] == 0:
                queue.popleft()
                self._where.pop(maker[0], None)
            if not queue:
                del opposite[best]
        return qty, trades
