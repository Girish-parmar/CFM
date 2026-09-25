# ADR 0005 — An order management layer above thin broker adapters

**Status:** accepted (v2.1.0)

## Context

Until v2.0.0 strategies sent orders straight to `PaperBroker`. That left no place for order
types the broker does not take (stops, stop-limits, brackets, OCO), for time in force, for
idempotent retries or for an audit trail, and no way to notice when the broker's state and the
strategy's view diverge. Real broker APIs differ in which of these they support natively.

## Decision

- `cfmat.trading.oms.OrderManager` owns order state. Strategies talk to it, never to the broker.
- Broker adapters stay thin: MARKET and LIMIT orders, cancel, positions, equity, a fill stream
  (`add_fill_listener`) and, where possible, the ids of working orders (`open_order_ids`).
- Stops and bracket exits are held by the OMS and sent as MARKET or LIMIT orders when they
  trigger or activate. The broker's `RiskManager` still checks every order that reaches it.
- Every order moves through an explicit state machine (`TRANSITIONS`); an illegal move raises.
  Every event is appended to an audit trail.
- Fills are queued by the listener and applied in arrival order after each broker call, so a
  fill that arrives while an order is being placed is never lost or applied twice.
- Bracket and OCO legs are sized to the exposure still open, recomputed on every fill.
- `reconcile` compares OMS positions and working orders with the broker's and lists every break.

## Consequences

- The same strategy code runs against the paper broker and against a live adapter; only
  natively supported order types need an adapter change.
- OMS-held stops depend on the OMS receiving prices: if the process stops, the stops stop.
  Live deployments must either use broker-side stop orders (GTT/SL) or run the OMS under
  supervision with reconciliation on restart (M17 runbook).
- A stop held by the OMS is risk-checked only when it triggers; it can be rejected at the
  worst moment (kill switch, price band). Lab 17b shows this and the exercise asks for the
  incident note.
