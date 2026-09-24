"""Order management system (OMS): the layer between a strategy and the broker (M17).

A strategy asks the OMS for orders. The OMS

* validates them and gives each a client order id (resubmitting an id returns
  the original order, so a retry after a timeout cannot double the position);
* holds what the broker does not take: stop and stop-limit orders until their
  trigger trades, and bracket exits until the entry fills;
* sends the rest through the broker, whose risk checks still apply;
* tracks every order through an explicit state machine and applies time in
  force (DAY orders expire at ``end_of_day``, IOC remainders are cancelled);
* links OCO and bracket legs, resizing or cancelling siblings as fills arrive;
* writes an audit trail of every event, and ``reconcile`` compares what it
  believes with what the broker reports.

States (terminal states in capitals on the right)::

    NEW ─┬─► HELD ───────────┐
         ├─► TRIGGER_PENDING ┼─► OPEN ─► PARTIAL ─► FILLED
         └───────────────────┘      any active state ─► CANCELLED / REJECTED / EXPIRED

``HELD`` is a bracket exit waiting for its entry; ``TRIGGER_PENDING`` is a stop
waiting for its trigger price.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import datetime

import pandas as pd

from .orders import (
    BUY,
    DAY,
    GTC,
    IOC,
    LIMIT,
    MARKET,
    ORDER_TYPES,
    SELL,
    STOP,
    STOP_LIMIT,
    TIME_IN_FORCE,
    Fill,
    Order,
    opposite,
)
from .paper_broker import BrokerAdapter

NEW, HELD, TRIGGER_PENDING, OPEN, PARTIAL = "NEW", "HELD", "TRIGGER_PENDING", "OPEN", "PARTIAL"
FILLED, CANCELLED, REJECTED, EXPIRED = "FILLED", "CANCELLED", "REJECTED", "EXPIRED"
TERMINAL = frozenset({FILLED, CANCELLED, REJECTED, EXPIRED})
_ENDS = {CANCELLED, REJECTED, EXPIRED}

TRANSITIONS: dict[str, frozenset[str]] = {
    NEW: frozenset({HELD, TRIGGER_PENDING, OPEN, *_ENDS}),
    HELD: frozenset({TRIGGER_PENDING, OPEN, *_ENDS}),
    TRIGGER_PENDING: frozenset({OPEN, *_ENDS}),
    OPEN: frozenset({PARTIAL, FILLED, *_ENDS}),
    PARTIAL: frozenset({FILLED, CANCELLED, EXPIRED}),
    FILLED: frozenset(),
    CANCELLED: frozenset(),
    REJECTED: frozenset(),
    EXPIRED: frozenset(),
}

BRACKET, OCO = "BRACKET", "OCO"


class InvalidTransition(RuntimeError):
    """Raised when code tries to move an order along an edge the state machine does not allow."""


@dataclass
class ManagedOrder:
    """One order as the OMS tracks it; the broker may see several orders over its life (cancel/replace)."""
    client_id: str
    symbol: str
    side: str
    qty: int
    order_type: str = MARKET
    limit_price: float | None = None
    stop_price: float | None = None
    tif: str = DAY
    tag: str = ""
    group_id: str = ""
    role: str = ""                  # entry / stop / target in a bracket, leg in an OCO
    status: str = NEW
    filled_qty: int = 0
    avg_fill_price: float = 0.0
    reject_reason: str = ""
    broker_ids: list[int] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def remaining(self) -> int:
        """Quantity still to fill."""
        return self.qty - self.filled_qty

    @property
    def is_active(self) -> bool:
        """True until the order reaches a terminal state."""
        return self.status not in TERMINAL

    @property
    def at_broker(self) -> bool:
        """True while a broker order is working for it."""
        return self.status in (OPEN, PARTIAL)


@dataclass
class OrderGroup:
    """Linked orders: a bracket (entry + stop + target) or a one-cancels-other set."""
    group_id: str
    kind: str
    legs: list[str]
    parent: str | None = None       # bracket entry; exits protect what it has filled
    qty: int = 0                    # OCO: the quantity the legs share


@dataclass
class OrderEvent:
    """One row of the audit trail."""
    seq: int
    timestamp: datetime | None
    client_id: str
    event: str
    status: str
    detail: str = ""


class OrderManager:
    """Order management system in front of a ``BrokerAdapter``.

    Feed prices with ``on_price``: it forwards them to a paper broker (anything
    with ``update_price``) so working orders can fill, then triggers stops.
    Fills reach the OMS through the broker's fill listener and are applied in
    arrival order.
    """

    def __init__(self, broker: BrokerAdapter, id_prefix: str = "CFM") -> None:
        self.broker = broker
        self.id_prefix = id_prefix
        self.orders: dict[str, ManagedOrder] = {}
        self.groups: dict[str, OrderGroup] = {}
        self.events: list[OrderEvent] = []
        self.positions: dict[str, int] = {}
        self.last_price: dict[str, float] = {}
        self.now: datetime | None = None
        self._by_broker_id: dict[int, str] = {}
        self._inbox: list[Fill] = []
        self._seq = itertools.count(1)
        self._order_seq = itertools.count(1)
        self._group_seq = itertools.count(1)
        self._squaring_off = False
        broker.add_fill_listener(self._inbox.append)

    # -- requests from the strategy -------------------------------------------------
    def submit(
        self,
        symbol: str,
        side: str,
        qty: int,
        order_type: str = MARKET,
        limit_price: float | None = None,
        stop_price: float | None = None,
        tif: str = DAY,
        client_id: str | None = None,
        tag: str = "",
        timestamp: datetime | None = None,
    ) -> ManagedOrder:
        """Create and route one order; resubmitting a ``client_id`` returns the original order."""
        self._tick(timestamp)
        if client_id is not None and client_id in self.orders:
            original = self.orders[client_id]
            self._log(original, "DUPLICATE", "client_id already used; original order returned, nothing sent")
            return original
        order = self._create(symbol, side, qty, order_type, limit_price, stop_price, tif, tag, client_id)
        self._route(order)
        self._drain()
        return order

    def submit_bracket(
        self,
        symbol: str,
        side: str,
        qty: int,
        stop_loss: float,
        take_profit: float,
        entry_type: str = MARKET,
        entry_price: float | None = None,
        tif: str = DAY,
        client_id: str | None = None,
        tag: str = "",
        timestamp: datetime | None = None,
    ) -> OrderGroup:
        """Entry plus a protective stop and a profit target that activate as the entry fills.

        The exits are an OCO pair sized to the filled entry quantity: a partial
        entry fill is protected at once, and a fill on one exit shrinks or
        cancels the other.
        """
        self._tick(timestamp)
        if client_id is not None and client_id in self.orders:
            self._log(self.orders[client_id], "DUPLICATE", "client_id already used; original bracket returned")
            return self.groups[self.orders[client_id].group_id]
        if entry_type not in (MARKET, LIMIT):
            raise ValueError("a bracket entry is MARKET or LIMIT")
        if tif == IOC:
            raise ValueError("bracket exits must stay working; use DAY or GTC")
        low, high = (stop_loss, take_profit) if side == BUY else (take_profit, stop_loss)
        reference = entry_price if entry_type == LIMIT else self.last_price.get(symbol)
        if not low < high or (reference is not None and not low < reference < high):
            raise ValueError("a long bracket needs stop < entry < target; a short one target < entry < stop")
        gid = f"{self.id_prefix}-G{next(self._group_seq):04d}"
        entry = self._create(symbol, side, qty, entry_type, entry_price, None, tif, tag, client_id, gid, "entry")
        exit_side = opposite(side)
        stop = self._create(symbol, exit_side, qty, STOP, None, stop_loss, tif, tag,
                            f"{entry.client_id}-SL", gid, "stop")
        target = self._create(symbol, exit_side, qty, LIMIT, take_profit, None, tif, tag,
                              f"{entry.client_id}-TP", gid, "target")
        for leg in (stop, target):
            self._set_status(leg, HELD, "waiting for the entry to fill")
        group = OrderGroup(gid, BRACKET, [stop.client_id, target.client_id], parent=entry.client_id)
        self.groups[gid] = group
        self._route(entry)
        self._drain()
        self._sync_group(group)
        return group

    def submit_oco(
        self,
        legs: Iterable[dict],
        tif: str = GTC,
        tag: str = "",
        timestamp: datetime | None = None,
    ) -> OrderGroup:
        """One-cancels-other: when one leg fills, the others shrink to what is left or cancel.

        Each leg is a dict of ``submit`` arguments (``side``, ``order_type``,
        ``limit_price``, ``stop_price`` ...). All legs share one symbol and one
        quantity, e.g. a stop below and a target above an existing long, or a
        buy stop above a range and a sell stop below it.
        """
        self._tick(timestamp)
        specs = [dict(leg) for leg in legs]
        if len(specs) < 2:
            raise ValueError("an OCO needs at least two legs")
        symbols, qtys = {s["symbol"] for s in specs}, {s["qty"] for s in specs}
        if len(symbols) != 1 or len(qtys) != 1:
            raise ValueError("OCO legs must share one symbol and one quantity")
        for s in specs:     # validate every leg before creating any, so a bad leg leaves no orphans
            self._validate(s["side"], s["qty"], s.get("order_type", LIMIT), s.get("limit_price"),
                           s.get("stop_price"), s.get("tif", tif))
        gid = f"{self.id_prefix}-G{next(self._group_seq):04d}"
        orders = [
            self._create(s["symbol"], s["side"], s["qty"], s.get("order_type", LIMIT), s.get("limit_price"),
                         s.get("stop_price"), s.get("tif", tif), s.get("tag", tag), s.get("client_id"), gid, "leg")
            for s in specs
        ]
        group = OrderGroup(gid, OCO, [o.client_id for o in orders], qty=qtys.pop())
        self.groups[gid] = group
        for order in orders:
            if order.is_active:
                self._route(order)
            self._drain()
        self._sync_group(group)
        return group

    def cancel(self, client_id: str, reason: str = "cancelled by user", timestamp: datetime | None = None) -> bool:
        """Cancel an active order (the unfilled part); False if it had already finished."""
        self._tick(timestamp)
        order = self.orders[client_id]
        if not order.is_active:
            return False
        if order.at_broker and not self.broker.cancel_order(order.broker_ids[-1]):
            self._drain()                    # the broker filled it before the cancel arrived
            if not order.is_active:
                return False
        self._set_status(order, CANCELLED, reason)
        if order.group_id:
            self._sync_group(self.groups[order.group_id])
        return True

    def cancel_group(self, group_id: str, reason: str = "group cancelled by user",
                     timestamp: datetime | None = None) -> int:
        """Cancel every active order of a bracket or OCO; returns how many were cancelled."""
        group = self.groups[group_id]
        ids = ([group.parent] if group.parent else []) + group.legs
        return sum(self.cancel(cid, reason, timestamp) for cid in ids)

    def amend(
        self,
        client_id: str,
        qty: int | None = None,
        limit_price: float | None = None,
        stop_price: float | None = None,
        timestamp: datetime | None = None,
    ) -> ManagedOrder:
        """Change quantity or prices of an active order (cancel/replace at the broker).

        A replaced order joins the back of the queue at its price on a real
        exchange; only a quantity decrease keeps queue priority there.
        """
        self._tick(timestamp)
        order = self.orders[client_id]
        if not order.is_active:
            raise ValueError(f"{client_id} is {order.status}; only active orders can be amended")
        if qty is not None and qty <= order.filled_qty:
            raise ValueError(f"new qty {qty} must exceed the filled qty {order.filled_qty}")
        if limit_price is not None and order.order_type not in (LIMIT, STOP_LIMIT):
            raise ValueError(f"{order.order_type} orders have no limit price")
        if stop_price is not None and order.order_type not in (STOP, STOP_LIMIT):
            raise ValueError(f"{order.order_type} orders have no stop price")
        if stop_price is not None and order.status == TRIGGER_PENDING and self._crossed(
                order.side, stop_price, self.last_price.get(order.symbol)):
            raise ValueError("the new trigger price has already traded; it would fire at once")
        changes = {k: v for k, v in (("qty", qty), ("limit_price", limit_price), ("stop_price", stop_price))
                   if v is not None and v != getattr(order, k)}
        if not changes:
            return order
        return self._replace(order, changes, "amended by user")

    def on_price(self, symbol: str, price: float, timestamp: datetime | None = None) -> None:
        """New last price: the paper broker fills working orders, then pending stops trigger."""
        self._tick(timestamp)
        self.last_price[symbol] = price
        update = getattr(self.broker, "update_price", None)
        if update is not None:
            update(symbol, price, timestamp)
        self._drain()
        for order in list(self.orders.values()):
            if order.symbol == symbol and order.status == TRIGGER_PENDING and self._crossed(
                    order.side, order.stop_price, price):
                self._trigger(order, f"last price {price:.2f} reached trigger {order.stop_price:.2f}")

    def end_of_day(self, timestamp: datetime | None = None) -> list[str]:
        """Expire every active DAY order; GTC orders carry over. Returns the expired ids."""
        self._tick(timestamp)
        expired = []
        for order in list(self.orders.values()):
            if not order.is_active or order.tif != DAY:
                continue
            if order.at_broker and not self.broker.cancel_order(order.broker_ids[-1]):
                self._drain()
                if not order.is_active:
                    continue
            self._set_status(order, EXPIRED, "DAY order expired at the close")
            expired.append(order.client_id)
        for group in self.groups.values():
            self._sync_group(group)
        return expired

    def flatten(self, timestamp: datetime | None = None) -> None:
        """Cancel every active order, then close all positions (the broker's square-off if it has one)."""
        self._tick(timestamp)
        for order in list(self.orders.values()):
            if order.is_active:
                self.cancel(order.client_id, "flatten: all orders cancelled")
        square_off = getattr(self.broker, "square_off_all", None)
        if square_off is not None:
            self._squaring_off = True
            try:
                square_off(timestamp)
                self._drain()
            finally:
                self._squaring_off = False
            return
        for symbol, qty in list(self.positions.items()):
            if qty:
                self.submit(symbol, SELL if qty > 0 else BUY, abs(qty), tag="flatten")

    # -- views ---------------------------------------------------------------------
    def get(self, client_id: str) -> ManagedOrder:
        """The order with this client id."""
        return self.orders[client_id]

    def open_orders(self, symbol: str | None = None) -> list[ManagedOrder]:
        """Active orders, optionally for one symbol."""
        return [o for o in self.orders.values() if o.is_active and (symbol is None or o.symbol == symbol)]

    def orders_frame(self) -> pd.DataFrame:
        """Every order as one row (the order book of the OMS)."""
        rows = [asdict(o) for o in self.orders.values()]
        return pd.DataFrame(rows).set_index("client_id") if rows else pd.DataFrame()

    def events_frame(self) -> pd.DataFrame:
        """The audit trail: one row per event, in order."""
        return pd.DataFrame([asdict(e) for e in self.events]).set_index("seq") if self.events else pd.DataFrame()

    def reconcile(self) -> pd.DataFrame:
        """Differences between the OMS and the broker; an empty frame means they agree.

        Checks positions by symbol and, when the broker reports them, working
        orders: an order the OMS thinks is working but the broker does not (it
        was cancelled or filled behind the OMS's back), and the reverse.
        """
        rows = []
        broker_pos = self.broker.positions()
        for symbol in sorted(set(self.positions) | set(broker_pos)):
            ours, theirs = self.positions.get(symbol, 0), broker_pos.get(symbol, 0)
            if ours != theirs:
                rows.append({"kind": "position", "ref": symbol, "oms": ours, "broker": theirs})
        working = self.broker.open_order_ids()
        if working is not None:
            ours = {o.broker_ids[-1]: o.client_id for o in self.orders.values() if o.at_broker}
            for bid in sorted(set(ours) - working):
                rows.append({"kind": "order", "ref": ours[bid], "oms": "working", "broker": "not working"})
            for bid in sorted(working - set(ours)):
                rows.append({"kind": "order", "ref": f"broker#{bid}", "oms": "unknown", "broker": "working"})
        return pd.DataFrame(rows, columns=["kind", "ref", "oms", "broker"])

    # -- internals: creation and routing -------------------------------------------------
    def _tick(self, timestamp: datetime | None) -> None:
        if timestamp is not None:
            self.now = timestamp

    @staticmethod
    def _validate(side, qty, order_type, limit_price, stop_price, tif) -> None:
        """Raise ``ValueError`` for a request no market would accept."""
        if side not in (BUY, SELL):
            raise ValueError("side must be BUY or SELL")
        if int(qty) != qty or qty <= 0:
            raise ValueError("qty must be a positive whole number")
        if order_type not in ORDER_TYPES:
            raise ValueError(f"order_type must be one of {ORDER_TYPES}")
        if tif not in TIME_IN_FORCE:
            raise ValueError(f"tif must be one of {TIME_IN_FORCE}")
        if order_type in (LIMIT, STOP_LIMIT) and limit_price is None:
            raise ValueError(f"{order_type} orders need a limit_price")
        if order_type in (STOP, STOP_LIMIT) and stop_price is None:
            raise ValueError(f"{order_type} orders need a stop_price")
        if order_type in (STOP, STOP_LIMIT) and tif == IOC:
            raise ValueError("IOC applies to orders that reach the market at once, not to stops")
        if order_type == STOP_LIMIT and (limit_price < stop_price if side == BUY else limit_price > stop_price):
            raise ValueError("a buy stop-limit needs limit >= stop; a sell stop-limit needs limit <= stop")

    def _create(self, symbol, side, qty, order_type, limit_price, stop_price, tif, tag, client_id,
                group_id: str = "", role: str = "") -> ManagedOrder:
        self._validate(side, qty, order_type, limit_price, stop_price, tif)
        cid = client_id or f"{self.id_prefix}-{next(self._order_seq):06d}"
        if cid in self.orders:
            raise ValueError(f"client_id {cid} is already in use")
        order = ManagedOrder(cid, symbol, side, int(qty), order_type, limit_price, stop_price, tif, tag,
                             group_id, role, created_at=self.now, updated_at=self.now)
        self.orders[cid] = order
        price = {LIMIT: f" @ {limit_price}", STOP: f" stop {stop_price}",
                 STOP_LIMIT: f" stop {stop_price} limit {limit_price}"}.get(order_type, "")
        self._log(order, "CREATED", f"{side} {qty} {symbol} {order_type}{price} {tif}")
        return order

    def _route(self, order: ManagedOrder) -> None:
        """Hold a stop until it triggers; send anything else to the broker."""
        if order.order_type not in (STOP, STOP_LIMIT):
            self._send(order)
            return
        last = self.last_price.get(order.symbol)
        if last is None:
            self._set_status(order, REJECTED, "no market price: cannot check the trigger")
        elif self._crossed(order.side, order.stop_price, last) and order.role != "stop":
            # exchanges reject a stop whose trigger has already traded
            self._set_status(order, REJECTED, f"trigger {order.stop_price} already crossed (last {last})")
        elif self._crossed(order.side, order.stop_price, last):
            # a bracket stop activated after a gap through it: exit now rather than stay unprotected
            self._set_status(order, TRIGGER_PENDING, "activated")
            self._trigger(order, f"trigger {order.stop_price} already crossed on activation (last {last})")
        else:
            self._set_status(order, TRIGGER_PENDING, f"waiting for {order.stop_price}")

    def _trigger(self, order: ManagedOrder, why: str) -> None:
        self._log(order, "TRIGGERED", why)
        self._send(order)

    def _send(self, order: ManagedOrder) -> None:
        """Send the unfilled quantity to the broker as MARKET or LIMIT, then apply IOC."""
        kind = LIMIT if order.order_type in (LIMIT, STOP_LIMIT) else MARKET
        sent = self.broker.place_order(
            Order(order.symbol, order.side, order.remaining, kind, order.limit_price if kind == LIMIT else None),
            self.now)
        order.broker_ids.append(sent.id)
        self._by_broker_id[sent.id] = order.client_id
        if sent.status == "REJECTED":
            if order.filled_qty:
                self._set_status(order, CANCELLED, f"replacement rejected by broker: {sent.reject_reason}")
            else:
                self._set_status(order, REJECTED, f"broker: {sent.reject_reason}")
            return
        self._log(order, "SENT", f"broker order #{sent.id}: {kind} {order.remaining}")
        if order.status != PARTIAL:
            self._set_status(order, OPEN, f"working at broker as #{sent.id}")
        self._drain()
        if order.tif == IOC and order.is_active:
            self.broker.cancel_order(sent.id)
            self._set_status(order, CANCELLED, f"IOC: unfilled {order.remaining} cancelled")

    def _replace(self, order: ManagedOrder, changes: dict, why: str) -> ManagedOrder:
        """Apply changes; an order working at the broker is cancelled and re-sent."""
        if order.at_broker and not self.broker.cancel_order(order.broker_ids[-1]):
            self._drain()
            if not order.is_active:
                self._log(order, "AMEND_FAILED", "filled before the amendment reached the broker")
                return order
        detail = ", ".join(f"{k} {getattr(order, k)} -> {v}" for k, v in changes.items())
        for k, v in changes.items():
            setattr(order, k, v)
        order.updated_at = self.now
        self._log(order, "AMENDED", f"{detail} ({why})")
        if order.at_broker:
            self._send(order)
        return order

    # -- internals: fills and linked orders ------------------------------------------------
    def _drain(self) -> None:
        while self._inbox:
            self._apply_fill(self._inbox.pop(0))

    def _apply_fill(self, fill: Fill) -> None:
        signed = fill.qty if fill.side == BUY else -fill.qty
        self.positions[fill.symbol] = self.positions.get(fill.symbol, 0) + signed
        cid = self._by_broker_id.get(fill.order_id)
        if cid is None:
            event, source = (("SQUARE_OFF_FILL", "broker square-off") if self._squaring_off
                             else ("EXTERNAL_FILL", "not placed by this OMS"))
            self.events.append(OrderEvent(next(self._seq), self.now, "", event, "",
                                          f"broker #{fill.order_id} {fill.side} {fill.qty} {fill.symbol} "
                                          f"@ {fill.price:.2f} ({source})"))
            return
        order = self.orders[cid]
        order.avg_fill_price = ((order.avg_fill_price * order.filled_qty + fill.price * fill.qty)
                                / (order.filled_qty + fill.qty))
        order.filled_qty += fill.qty
        order.updated_at = self.now
        if not order.is_active:
            self._log(order, "LATE_FILL", f"{fill.qty} @ {fill.price:.2f} after the order was {order.status}")
        else:
            self._log(order, "FILL", f"{fill.qty} @ {fill.price:.2f} ({order.filled_qty}/{order.qty})")
            self._set_status(order, FILLED if order.remaining <= 0 else PARTIAL)
        if order.group_id:
            group = self.groups[order.group_id]
            if self._exposure(group) < 0:
                self._log(order, "OVERFILL", f"legs closed {-self._exposure(group)} more than the exposure")
            self._sync_group(group)

    def _exposure(self, group: OrderGroup) -> int:
        """Quantity the group's legs still have to close (bracket) or share (OCO)."""
        protect = self.orders[group.parent].filled_qty if group.kind == BRACKET else group.qty
        return protect - sum(self.orders[cid].filled_qty for cid in group.legs)

    def _sync_group(self, group: OrderGroup) -> None:
        """Keep every active leg sized to the exposure still open; cancel the rest when none is."""
        if group.kind == BRACKET:
            parent = self.orders[group.parent]
            if parent.filled_qty == 0:
                if not parent.is_active:
                    for cid in group.legs:
                        if self.orders[cid].is_active:
                            self._set_status(self.orders[cid], CANCELLED,
                                             f"entry {parent.status.lower()} without a fill")
                return
        for cid in group.legs:
            leg = self.orders[cid]
            if not leg.is_active:
                continue
            exposure = self._exposure(group)    # recomputed: activating a leg can fill it at once
            if exposure <= 0:
                if leg.at_broker and not self.broker.cancel_order(leg.broker_ids[-1]):
                    self._drain()
                    if not leg.is_active:
                        continue
                self._set_status(leg, CANCELLED, "OCO: the exposure is closed")
                continue
            wanted = leg.filled_qty + exposure
            if leg.status == HELD:
                leg.qty = wanted
                self._route(leg)
            elif wanted != leg.qty:
                self._replace(leg, {"qty": wanted}, "resized to the open exposure")

    # -- internals: helpers ----------------------------------------------------------
    @staticmethod
    def _crossed(side: str, stop_price: float, price: float | None) -> bool:
        if price is None:
            return False
        return price >= stop_price if side == BUY else price <= stop_price

    def _set_status(self, order: ManagedOrder, status: str, detail: str = "") -> None:
        if status == order.status:
            return
        if status not in TRANSITIONS[order.status]:
            raise InvalidTransition(f"{order.client_id}: {order.status} -> {status} is not allowed")
        order.status = status
        order.updated_at = self.now
        if status == REJECTED:
            order.reject_reason = detail
        self._log(order, status, detail)

    def _log(self, order: ManagedOrder, event: str, detail: str = "") -> None:
        self.events.append(OrderEvent(next(self._seq), self.now, order.client_id, event, order.status, detail))
