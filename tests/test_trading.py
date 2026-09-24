"""Tests for cfmat.trading: orders, risk checks, paper broker, order management and journal."""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from cfmat import trading


def test_paper_broker_accounting_round_trip():
    b = trading.PaperBroker(cash=100_000, slippage_bps=0)
    b.update_price("ABC", 100.0)
    b.place_order(trading.Order("ABC", trading.BUY, 100))
    b.update_price("ABC", 110.0)
    assert b.equity() == pytest.approx(101_000)
    b.place_order(trading.Order("ABC", trading.SELL, 150))  # close 100, open short 50
    assert b.realized_pnl == pytest.approx(1_000) and b.position("ABC") == -50
    b.update_price("ABC", 100.0)
    assert b.equity() == pytest.approx(101_500)


def test_limit_orders_rest_then_fill():
    b = trading.PaperBroker(cash=100_000, slippage_bps=0)
    b.update_price("ABC", 100.0)
    o = b.place_order(trading.Order("ABC", trading.BUY, 10, trading.LIMIT, 98.0))
    assert o.status == "OPEN"
    b.update_price("ABC", 97.5)
    assert o.status == "FILLED" and b.fills[-1].price == 98.0


def test_risk_manager_blocks_bad_orders():
    limits = trading.RiskLimits(max_order_qty=100, max_order_value=50_000, max_position_qty=150,
                            max_orders_per_second=2, max_daily_loss=1_000)
    b = trading.PaperBroker(cash=1_000_000, risk=trading.RiskManager(limits), slippage_bps=0)
    b.update_price("ABC", 100.0)
    ts = datetime(2026, 1, 5, 10, 0, 0)
    assert "exceeds" in b.place_order(trading.Order("ABC", trading.BUY, 101), ts).reject_reason
    assert "fat-finger" in b.place_order(trading.Order("ABC", trading.BUY, 10, trading.LIMIT, 120.0), ts).reject_reason
    assert b.place_order(trading.Order("ABC", trading.BUY, 100), ts).status == "FILLED"
    assert b.place_order(trading.Order("ABC", trading.BUY, 40), ts).status == "FILLED"
    assert "throttled" in b.place_order(trading.Order("ABC", trading.BUY, 5), ts).reject_reason
    b.update_price("ABC", 90.0)  # loss of 1,400 > limit
    later = datetime(2026, 1, 5, 10, 0, 5)
    assert "kill switch" in b.place_order(trading.Order("ABC", trading.SELL, 10), later).reject_reason
    b.square_off_all()
    assert b.positions() == {}


def test_marketable_limit_fills_at_the_market_not_at_its_limit():
    b = trading.PaperBroker(cash=100_000, slippage_bps=0)
    b.update_price("ABC", 100.0)
    o = b.place_order(trading.Order("ABC", trading.BUY, 10, trading.LIMIT, 102.0))
    assert o.status == "FILLED" and b.fills[-1].price == 100.0


def test_thin_liquidity_gives_partial_fills_and_publishes_each_fill():
    b = trading.PaperBroker(cash=100_000, slippage_bps=0, max_fill_qty=30)
    seen = []
    b.add_fill_listener(seen.append)
    b.update_price("ABC", 100.0)
    o = b.place_order(trading.Order("ABC", trading.BUY, 70))
    assert (o.status, o.filled_qty, b.open_order_ids()) == ("PARTIAL", 30, {o.id})
    b.update_price("ABC", 101.0)
    b.update_price("ABC", 102.0)
    assert o.status == "FILLED" and [f.qty for f in seen] == [30, 30, 10]
    assert o.avg_fill_price == pytest.approx((30 * 100 + 30 * 101 + 10 * 102) / 70)
    assert b.position("ABC") == 70 and b.open_order_ids() == set()


def test_broker_order_rejects_stop_types():
    with pytest.raises(ValueError, match="OMS"):
        trading.Order("ABC", trading.SELL, 10, trading.STOP)


# -- order management system ----------------------------------------------------------------

T0 = datetime(2026, 1, 5, 9, 15)


def _oms(price=100.0, **broker_kwargs):
    broker = trading.PaperBroker(cash=1_000_000, slippage_bps=0, **broker_kwargs)
    oms = trading.OrderManager(broker)
    oms.on_price("ABC", price, T0)
    return oms, broker


def _statuses(oms):
    return {cid: o.status for cid, o in oms.orders.items()}


def test_every_transition_the_oms_takes_is_allowed_by_the_state_machine():
    from cfmat.trading import oms as oms_module

    assert all(not oms_module.TRANSITIONS[s] for s in oms_module.TERMINAL)
    oms, _ = _oms()
    order = oms.submit("ABC", trading.BUY, 10)
    with pytest.raises(trading.InvalidTransition):
        oms._set_status(order, oms_module.OPEN)       # FILLED is terminal


def test_client_order_id_makes_submission_idempotent():
    oms, broker = _oms()
    first = oms.submit("ABC", trading.BUY, 10, client_id="strat-1")
    again = oms.submit("ABC", trading.BUY, 10, client_id="strat-1")   # e.g. a retry after a timeout
    assert again is first and len(broker.orders) == 1 and oms.positions["ABC"] == 10
    assert oms.events_frame()["event"].tolist().count("DUPLICATE") == 1


def test_stop_waits_for_its_trigger_and_is_rejected_if_already_crossed():
    oms, _ = _oms()
    stop = oms.submit("ABC", trading.SELL, 10, trading.STOP, stop_price=97.0)
    assert stop.status == "TRIGGER_PENDING"
    oms.on_price("ABC", 98.0)
    assert stop.status == "TRIGGER_PENDING"
    oms.on_price("ABC", 96.5)                          # trades through the trigger
    assert stop.status == "FILLED" and stop.avg_fill_price == 96.5
    late = oms.submit("ABC", trading.BUY, 10, trading.STOP, stop_price=95.0)   # buy stop below the market
    assert late.status == "REJECTED" and "already crossed" in late.reject_reason


def test_stop_limit_does_not_chase_a_gap():
    oms, _ = _oms()
    order = oms.submit("ABC", trading.SELL, 10, trading.STOP_LIMIT, limit_price=96.5, stop_price=97.0, tif=trading.GTC)
    oms.on_price("ABC", 94.0)                          # gaps through trigger and limit
    assert order.status == "OPEN" and order.filled_qty == 0
    oms.on_price("ABC", 96.8)
    assert order.status == "FILLED" and order.avg_fill_price == 96.5


def test_ioc_cancels_the_unfilled_remainder():
    oms, _ = _oms(max_fill_qty=25)
    order = oms.submit("ABC", trading.BUY, 60, tif=trading.IOC)
    assert (order.status, order.filled_qty) == ("CANCELLED", 25)
    passive = oms.submit("ABC", trading.BUY, 10, trading.LIMIT, limit_price=99.0, tif=trading.IOC)
    assert (passive.status, passive.filled_qty) == ("CANCELLED", 0)


def test_day_orders_expire_at_the_close_and_gtc_orders_carry_over():
    oms, broker = _oms()
    day = oms.submit("ABC", trading.BUY, 10, trading.LIMIT, limit_price=98.0)
    gtc = oms.submit("ABC", trading.BUY, 10, trading.LIMIT, limit_price=97.0, tif=trading.GTC)
    assert oms.end_of_day() == [day.client_id]
    assert day.status == "EXPIRED" and gtc.status == "OPEN"
    assert broker.open_order_ids() == {gtc.broker_ids[-1]}


def test_amend_is_a_cancel_replace_that_keeps_the_fill_history():
    oms, broker = _oms(max_fill_qty=10)
    order = oms.submit("ABC", trading.BUY, 30, trading.LIMIT, limit_price=100.0)
    assert order.filled_qty == 10
    oms.amend(order.client_id, qty=20, limit_price=99.0)
    assert len(order.broker_ids) == 2 and broker.orders[0].status == "CANCELLED"
    assert broker.orders[-1].qty == 10 and broker.orders[-1].limit_price == 99.0
    oms.on_price("ABC", 98.5)
    assert order.status == "FILLED" and order.filled_qty == 20
    with pytest.raises(ValueError, match="only active"):
        oms.amend(order.client_id, qty=40)


def test_bracket_exits_track_partial_entry_fills_and_cancel_each_other():
    oms, broker = _oms(max_fill_qty=40)
    group = oms.submit_bracket("ABC", trading.BUY, 100, stop_loss=96.0, take_profit=106.0)
    entry, stop, target = (oms.get(c) for c in [group.parent, *group.legs])
    assert entry.filled_qty == 40 and stop.qty == 40 and target.qty == 40      # protected at once
    for price in (100.5, 101.0):
        oms.on_price("ABC", price)
    assert entry.status == "FILLED" and stop.qty == 100 and target.qty == 100
    for price in (106.2, 106.5, 107.0):
        oms.on_price("ABC", price)
    assert target.status == "FILLED" and stop.status == "CANCELLED"
    assert oms.positions == {"ABC": 0} and broker.positions() == {}
    assert oms.reconcile().empty


def test_bracket_stop_exits_and_cancels_the_target_at_the_broker():
    oms, broker = _oms()
    group = oms.submit_bracket("ABC", trading.BUY, 50, stop_loss=97.0, take_profit=104.0)
    oms.on_price("ABC", 96.0)
    stop, target = (oms.get(c) for c in group.legs)
    assert stop.status == "FILLED" and target.status == "CANCELLED"
    assert broker.open_order_ids() == set() and oms.reconcile().empty


def test_bracket_legs_cancel_if_the_entry_never_fills():
    oms, _ = _oms()
    group = oms.submit_bracket("ABC", trading.BUY, 10, stop_loss=95.0, take_profit=105.0,
                               entry_type=trading.LIMIT, entry_price=99.0)
    oms.cancel(group.parent)
    assert {oms.get(c).status for c in group.legs} == {"CANCELLED"}
    with pytest.raises(ValueError, match="stop < entry < target"):
        oms.submit_bracket("ABC", trading.BUY, 10, stop_loss=101.0, take_profit=105.0)


def test_oco_breakout_entry_fills_one_side_only():
    oms, _ = _oms()
    group = oms.submit_oco([
        {"symbol": "ABC", "side": trading.BUY, "qty": 20, "order_type": trading.STOP, "stop_price": 103.0},
        {"symbol": "ABC", "side": trading.SELL, "qty": 20, "order_type": trading.STOP, "stop_price": 97.0},
    ])
    oms.on_price("ABC", 103.5)
    up, down = (oms.get(c) for c in group.legs)
    assert (up.status, down.status) == ("FILLED", "CANCELLED") and oms.positions["ABC"] == 20
    with pytest.raises(ValueError, match="share one symbol"):
        oms.submit_oco([{"symbol": "ABC", "side": "BUY", "qty": 1, "order_type": trading.STOP, "stop_price": 110},
                        {"symbol": "XYZ", "side": "SELL", "qty": 1, "order_type": trading.STOP, "stop_price": 90}])


def test_invalid_oco_leg_leaves_no_orphan_orders():
    oms, _ = _oms()
    before = len(oms.orders)
    with pytest.raises(ValueError, match="stop_price"):
        oms.submit_oco([{"symbol": "ABC", "side": "SELL", "qty": 5, "order_type": trading.LIMIT, "limit_price": 105},
                        {"symbol": "ABC", "side": "SELL", "qty": 5, "order_type": trading.STOP}])
    assert len(oms.orders) == before


def test_broker_rejection_is_recorded_with_its_reason():
    limits = trading.RiskLimits(max_order_qty=50)
    broker = trading.PaperBroker(cash=1_000_000, risk=trading.RiskManager(limits), slippage_bps=0)
    oms = trading.OrderManager(broker)
    oms.on_price("ABC", 100.0, T0)
    order = oms.submit("ABC", trading.BUY, 80, timestamp=T0)
    assert order.status == "REJECTED" and "exceeds 50" in order.reject_reason


def test_reconcile_finds_changes_made_behind_the_oms_and_flatten_clears_them():
    oms, broker = _oms()
    oms.submit("ABC", trading.BUY, 10)
    resting = oms.submit("ABC", trading.BUY, 5, trading.LIMIT, limit_price=95.0)
    broker.place_order(trading.Order("ABC", trading.BUY, 7))       # manual order at the broker terminal
    broker.cancel_order(resting.broker_ids[-1])                     # cancelled outside the OMS
    breaks = oms.reconcile()
    assert set(breaks["kind"]) == {"position", "order"} and resting.client_id in set(breaks["ref"])
    oms.on_price("ABC", 100.0)                                       # the external fill arrives as an event
    assert "EXTERNAL_FILL" in set(oms.events_frame()["event"])
    oms.cancel(resting.client_id)
    oms.flatten()
    assert broker.positions() == {} and oms.reconcile().empty
    assert "SQUARE_OFF_FILL" in set(oms.events_frame()["event"])


# -- trade journal ----------------------------------------------------------------------------

def _fill(oid, side, qty, price, minute, charges=0.0, symbol="ABC"):
    return trading.Fill(oid, symbol, side, qty, price, T0 + timedelta(minutes=minute), charges)


def test_journal_record_keeps_the_original_row_format():
    row = trading.TradeJournal().record(_fill(1, "BUY", 10, 100.123456, 0, 1.234))
    assert row == {"order_id": 1, "symbol": "ABC", "side": "BUY", "qty": 10, "price": 100.1235,
                   "charges": 1.23, "timestamp": "2026-01-05T09:15:00"}


def test_round_trips_handle_scaling_partial_exits_and_reversals():
    j = trading.TradeJournal()
    j.record(_fill(1, "BUY", 100, 10.0, 0, charges=2.0), setup="breakout", stop=9.0, tags=["trend", "A+"])
    j.record(_fill(2, "SELL", 50, 12.0, 1, charges=1.0))
    j.record(_fill(3, "BUY", 50, 14.0, 2, charges=1.0))
    j.record(_fill(4, "SELL", 150, 13.0, 3, charges=3.0))       # closes 100, opens a 50 short
    j.record(_fill(5, "BUY", 50, 12.0, 4, charges=1.0))
    trips = j.round_trips()
    assert len(trips) == 2
    long, short = trips.iloc[0], trips.iloc[1]
    assert long.direction == "LONG" and long.gross_pnl == pytest.approx(-1000 + 600 - 700 + 1300)
    assert long.charges == pytest.approx(2 + 1 + 1 + 2) and long.net_pnl == pytest.approx(194)
    assert long.setup == "breakout" and long.tags == ("trend", "A+")
    assert long.risk == pytest.approx(abs(1700 / 150 - 9.0) * 150)       # |avg entry − stop| × qty entered
    assert long.r_multiple == pytest.approx(194 / long.risk)
    assert short.direction == "SHORT" and short.gross_pnl == pytest.approx(50) and short.charges == pytest.approx(2)
    assert long.holding == pd.Timedelta(minutes=3)


def test_open_trade_is_reported_only_when_asked():
    j = trading.TradeJournal()
    j.record(_fill(1, "BUY", 10, 100.0, 0))
    j.record(_fill(2, "SELL", 4, 103.0, 1))
    assert j.round_trips().empty
    trip = j.round_trips(include_open=True).iloc[0]
    assert trip.status == "OPEN" and trip.gross_pnl == pytest.approx(12.0) and pd.isna(trip.exit_time)


def test_excursions_and_review_statistics():
    j = trading.TradeJournal()
    j.record(_fill(1, "BUY", 10, 100.0, 0), setup="pullback", stop=98.0)
    j.record(_fill(2, "SELL", 10, 104.0, 30))
    j.record(_fill(3, "SELL", 10, 104.0, 40), setup="fade", stop=105.0)
    j.record(_fill(4, "BUY", 10, 106.0, 50))
    idx = pd.date_range("2026-01-05 09:15", periods=60, freq="min")
    bars = pd.DataFrame({"high": 101.0, "low": 99.0}, index=idx)
    bars.loc["2026-01-05 09:20", ["high", "low"]] = [106.0, 97.0]
    trips = trading.excursions(j.round_trips(), bars)
    long, short = trips.iloc[0], trips.iloc[1]
    assert (long.mae, long.mfe) == (-3.0, 6.0) and long.mae_r == -1.5 and long.exit_efficiency == pytest.approx(4 / 6)
    assert short.r_multiple == pytest.approx(-20 / 10)
    stats = trading.trade_summary(trips)
    assert stats["trades"] == 2 and stats["win_rate"] == 0.5 and stats["expectancy_r"] == pytest.approx((2 - 2) / 2)
    by_setup = trading.trade_breakdown(trips, "setup")
    assert by_setup.loc["pullback", "net_pnl"] == 40 and by_setup.loc["fade", "net_pnl"] == -20
    assert trading.trade_breakdown(trips, "weekday").index.tolist() == ["Monday"]


@pytest.mark.parametrize("suffix", [".csv", ".sqlite"])
def test_journal_round_trips_through_csv_and_sqlite(tmp_path, suffix):
    j = trading.TradeJournal()
    j.record(_fill(1, "BUY", 10, 100.0, 0, 1.5), setup="breakout", stop=98.0, tags=["trend", "news"])
    j.record(_fill(2, "SELL", 10, 103.0, 5, 1.5), note="took profit early")
    loaded = trading.TradeJournal.load(j.save(tmp_path / f"journal{suffix}"))
    before, after = j.round_trips(), loaded.round_trips()
    cols = ["net_pnl", "r_multiple", "setup", "tags", "entry_time", "exit_time"]
    pd.testing.assert_frame_equal(before[cols], after[cols], check_dtype=False)
    assert loaded.rows[1]["note"] == "took profit early"


def test_journal_listens_to_the_broker_and_matches_its_pnl():
    from cfmat.microstructure.costs import IndianCostModel

    broker = trading.PaperBroker(cash=1_000_000, slippage_bps=5, cost_model=IndianCostModel())
    journal = trading.TradeJournal()
    broker.add_fill_listener(journal.record)
    for price, side, qty in [(100.0, "BUY", 60), (104.0, "SELL", 20), (97.0, "SELL", 100), (99.0, "BUY", 60)]:
        broker.update_price("ABC", price)
        broker.place_order(trading.Order("ABC", side, qty))
    trips = journal.round_trips()
    assert broker.position("ABC") == 0 and len(journal.rows) == len(broker.fills) == 4
    assert trips["gross_pnl"].sum() == pytest.approx(broker.realized_pnl, abs=0.01)
    assert trips["charges"].sum() == pytest.approx(broker.total_charges, abs=0.02)
