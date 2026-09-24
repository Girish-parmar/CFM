"""Tests for cfmat.microstructure: order book, schedules, impact and costs."""

import pytest

from cfmat import data, microstructure
from cfmat.microstructure.costs import RATES_AS_OF, IndianCostModel


def test_order_book_price_time_priority():
    book = microstructure.OrderBook()
    first, _ = book.add_limit("SELL", 101.0, 30)
    second, _ = book.add_limit("SELL", 101.0, 30)
    book.add_limit("SELL", 102.0, 50)
    book.add_limit("BUY", 99.0, 40)
    assert book.spread() == pytest.approx(2.0)
    trades = book.add_market("BUY", 45)
    assert [(t["maker_id"], t["qty"]) for t in trades] == [(first, 30), (second, 15)]
    assert book.cancel(second) and book.best_ask() == 102.0
    _, crossed = book.add_limit("SELL", 98.0, 60)  # sweeps the 99 bid, rests at 98
    assert crossed[0]["price"] == 99.0 and book.best_ask() == 98.0


def test_schedules_sum_exactly():
    assert microstructure.twap_schedule(1003, 10).sum() == 1003
    v = microstructure.vwap_schedule(50_000, data.intraday_volume_profile())
    assert v.sum() == 50_000 and v[0] > v[12]


def test_almgren_chriss_limits():
    twap = microstructure.almgren_chriss_trajectory(1e6, 1.0, 10, 0.95, 2.5e-6, risk_aversion=0)
    urgent = microstructure.almgren_chriss_trajectory(1e6, 1.0, 10, 0.95, 2.5e-6, risk_aversion=1e-5)
    assert twap[0] == urgent[0] == 1e6 and abs(urgent[-1]) < 1e-6
    assert urgent[1] < twap[1]  # risk-averse trader sells faster early
    c_twap = microstructure.almgren_chriss_cost(twap, 1.0, 0.95, 2.5e-6)
    c_urgent = microstructure.almgren_chriss_cost(urgent, 1.0, 0.95, 2.5e-6)
    assert c_urgent["expected_cost"] > c_twap["expected_cost"] and c_urgent["variance"] < c_twap["variance"]


def test_implementation_shortfall():
    res = microstructure.implementation_shortfall("BUY", 100.0, [(600, 100.5), (200, 101.0)], 1000, 102.0)
    assert res["avg_price"] == pytest.approx(100.625)
    assert res["execution_cost"] == pytest.approx(500.0)
    assert res["opportunity_cost"] == pytest.approx(400.0)
    assert res["total_bps"] == pytest.approx(90.0)


def test_indian_cost_model_components():
    model = IndianCostModel()
    buy = model.charges("buy", 100, 1000, "equity_delivery")
    sell = model.charges("sell", 100, 1000, "equity_delivery")
    assert buy["stt"] == pytest.approx(100) and sell["stt"] == pytest.approx(100)
    assert buy["stamp"] == pytest.approx(15) and sell["stamp"] == 0
    assert buy["brokerage"] == 0
    intraday = model.charges("buy", 1000, 2000, "equity_intraday")
    assert intraday["brokerage"] == 20  # capped at ₹20
    assert 0 < model.round_trip_bps(1000, 2000, "equity_intraday") < 10


def test_dp_charge_applies_only_to_delivery_sells():
    model = IndianCostModel(dp_charge=15.93)
    sell = model.charges("sell", 10, 500, "equity_delivery")
    assert sell["dp"] == 15.93 and sell["gst"] == pytest.approx(0.18 * (sell["exchange"] + sell["sebi"] + 15.93))
    assert model.charges("buy", 10, 500, "equity_delivery")["dp"] == 0
    assert model.charges("sell", 10, 500, "equity_intraday")["dp"] == 0
    assert IndianCostModel().charges("sell", 10, 500, "equity_delivery")["dp"] == 0   # off by default
    assert RATES_AS_OF >= "2024-10-01"
