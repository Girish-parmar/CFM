# Module 11 — Trading Infrastructure, Broker APIs and Compliance

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 3 · Risk, Portfolio and Execution | 24–25 | 20 | [`lab11_paper_trading_rms.py`](../../labs/lab11_paper_trading_rms.py) |

## Learning outcomes

1. Design the architecture of an automated trading system: market data, signal, order management (OMS), risk management (RMS), execution, storage and monitoring.
2. Integrate with broker APIs through an adapter interface, and describe FIX at a conceptual level.
3. Implement order state machines, pre-trade risk checks, a kill switch and position reconciliation.
4. Deploy a strategy on a cloud server with a static IP, secrets management, logging and alerting.
5. Explain SEBI's retail algo framework and the research-analyst and investment-adviser rules as they apply to algo builders.
6. Keep audit trails suitable for broker and exchange review.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Architecture (Sat, W24) | Components and data flow; event loops; latency budgets; failure modes; the `cfmat.broker` and `cfmat.engine` design |
| L2 | Broker APIs and OMS (Sun, W24) | REST and WebSocket APIs (Kite Connect, Upstox, Angel SmartAPI, Interactive Brokers); authentication and session handling; rate limits; order states; FIX concepts |
| L3 | RMS and operations (Sat, W25) | Pre-trade checks (size, value, price bands, position, loss, orders-per-second); kill switches; reconciliation; cloud deployment, static IP, secrets, monitoring, incident runbooks |
| L4 | Regulation (Sun, W25) | SEBI retail algo framework (algo IDs, broker as principal, empanelled providers, OPS thresholds, white-box vs black-box); RA and IA regulations; market-abuse rules; audit trails. Guest: a broker's compliance head |
| C1–C4 | Clinics | Broker adapter skeleton; RMS configuration; deployment on a VM; Lab 11 |

See [../../docs/09-compliance-and-disclaimers.md](../../docs/09-compliance-and-disclaimers.md) for how the program applies these rules.

## Assignment

Implement a `BrokerAdapter` for one broker's paper or sandbox environment (or a mock of its documented API), put `RiskManager` in front of it, and write an incident runbook: what happens and who does what if the strategy sends runaway orders, the API disconnects, or positions do not reconcile.

## Readings

- SEBI circular of 4 February 2025 on safer participation of retail investors in algorithmic trading, and NSE/BSE implementation standards.
- Your chosen broker's API documentation.
- Rishi K. Narang, *Inside the Black Box*: chapters on execution and infrastructure.

## Assessment

Quiz 11; Lab 11; adapter and runbook assignment; Term exam 2 and Mini-project 2 (Week 26).
