# Module 10 — Market Microstructure and Execution Algorithms

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 3 · Risk, Portfolio and Execution | 22–23 | 20 | [`lab10_execution_microstructure.py`](../../labs/lab10_execution_microstructure.py) |

## Learning outcomes

1. Explain how a limit order book works, including matching priority, queue position, tick size and depth.
2. Describe the components of the bid–ask spread and the role of informed traders.
3. Estimate market impact with the square-root law and explain temporary vs permanent impact.
4. Implement TWAP, VWAP and POV schedules and the Almgren–Chriss optimal trajectory.
5. Measure execution quality with implementation shortfall and transaction-cost analysis.
6. Describe co-location, latency, HFT and market-making, and the related regulatory concerns.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Order books (Sat, W22) | Matching engines, price–time priority, pre-open auction, tick sizes, iceberg orders, reading market depth |
| L2 | Liquidity and information (Sun, W22) | Spread components; Kyle and Glosten–Milgrom intuition; adverse selection; order-flow imbalance; market impact |
| L3 | Execution algorithms (Sat, W23) | Benchmarks (arrival, VWAP, close); TWAP, VWAP, POV; limit vs market order trade-offs; Almgren–Chriss |
| L4 | TCA and HFT (Sun, W23) | Implementation shortfall; TCA reports; co-location and latency; market making (Avellaneda–Stoikov intuition); HFT debates and regulation |
| C1–C4 | Clinics | Order book simulator; schedules; AC frontier; Lab 10 |

## Assignment

Using historical intraday data, execute a simulated order equal to 10% of average daily volume with TWAP, VWAP and an Almgren–Chriss schedule, and produce a TCA report comparing them.

## Readings

- Larry Harris, *Trading and Exchanges*: chapters on liquidity, dealers and informed traders.
- Cartea, Jaimungal and Penalva, *Algorithmic and High-Frequency Trading*: chapters 1–2, 6–7.
- Almgren and Chriss (2000), "Optimal Execution of Portfolio Transactions".
- Kyle (1985), "Continuous Auctions and Insider Trading".
- Avellaneda and Stoikov (2008), "High-frequency trading in a limit order book".

## Assessment

Quiz 10; Lab 10; TCA assignment.
