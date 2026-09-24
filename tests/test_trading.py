"""Tests for cfmat.trading: orders, risk checks and paper broker."""

from datetime import datetime

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
