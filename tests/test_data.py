"""Tests for cfmat.data: synthetic generators, loaders, broker/vendor providers and the fetch command."""

import datetime as dt
import enum
import sys
import types

import numpy as np
import pandas as pd
import pytest

from cfmat import data
from cfmat.analytics import metrics
from cfmat.data import fetch as fetch_cli
from cfmat.data import loaders, providers


def test_regime_generator_labels_states():
    m = data.regime_prices(3000, seed=1)
    calm = metrics.simple_returns(m["close"])[m["regime"].iloc[1:] == 0]
    wild = metrics.simple_returns(m["close"])[m["regime"].iloc[1:] == 1]
    assert wild.std() > 2 * calm.std()


def test_gbm_is_reproducible_and_positive():
    a = data.gbm_prices(500, seed=7)
    b = data.gbm_prices(500, seed=7)
    pd.testing.assert_series_equal(a, b)
    assert (a > 0).all() and len(a) == 500 and a.iloc[0] == 100.0


def test_gbm_volatility_is_close_to_input():
    close = data.gbm_prices(5000, sigma=0.25, seed=1)
    vol = metrics.annualized_volatility(metrics.log_returns(close))
    assert vol == pytest.approx(0.25, rel=0.05)


def test_ohlcv_bars_are_consistent():
    bars = data.ohlcv(300, seed=3)
    assert (bars["high"] >= bars[["open", "close"]].max(axis=1)).all()
    assert (bars["low"] <= bars[["open", "close"]].min(axis=1)).all()
    assert (bars["volume"] > 0).all()


def test_volume_profile_sums_to_one_and_is_u_shaped():
    p = data.intraday_volume_profile(25)
    assert p.sum() == pytest.approx(1.0)
    assert p[0] > p[12] < p[-1]


def test_universe_can_draw_a_volatility_per_stock():
    def vol_ratio(prices):
        vol = np.log(prices).diff().std() * np.sqrt(252)
        return vol.max() / vol.min()

    assert vol_ratio(data.universe(20, 1000, idio_vol=(0.10, 0.50), seed=1)) > 2.0
    assert vol_ratio(data.universe(20, 1000, idio_vol=0.20, seed=1)) < 1.6


def test_brownian_ohlc_is_consistent_and_carries_the_true_volatility():
    sigma = np.r_[np.full(50, 0.1), np.full(50, 0.4)]
    bars = data.brownian_ohlc(100, sigma=sigma, seed=7)
    assert (bars["high"] >= bars[["open", "close"]].max(axis=1)).all()
    assert (bars["low"] <= bars[["open", "close"]].min(axis=1)).all()
    assert bars["true_vol"].tolist() == sigma.tolist()
    no_gaps = data.brownian_ohlc(100, overnight_share=0.0, seed=7)
    assert np.allclose(no_gaps["open"].iloc[1:].to_numpy(), no_gaps["close"].iloc[:-1].to_numpy())
    assert not np.allclose(bars["open"].iloc[1:].to_numpy(), bars["close"].iloc[:-1].to_numpy())
    with pytest.raises(ValueError):
        data.brownian_ohlc(10, overnight_share=1.0)


# -- loaders, providers and the fetch command -----------------------------------------------------

def test_standardize_ohlcv_cleans_and_converts_time_zones():
    idx = pd.DatetimeIndex(["2024-01-03 04:00", "2024-01-02 04:00", "2024-01-02 04:00"], tz="UTC")
    raw = pd.DataFrame({"Open": [1, 2, 3], "High": [2, 3, 4], "Low": [0.5, 1, 2], "Close": [1.5, 2.5, 3.5],
                        "Volume": [10, 20, 30], "vwap": [1, 2, 3]}, index=idx)
    out = loaders.standardize_ohlcv(raw, tz="Asia/Kolkata")
    assert list(out.columns) == loaders.OHLCV and out.index.tz is None and out.index.name == "date"
    assert out.index[0] == pd.Timestamp("2024-01-02 09:30") and len(out) == 2
    assert out.iloc[0]["close"] == 3.5                          # the last duplicate wins
    with pytest.raises(ValueError, match="missing columns"):
        loaders.standardize_ohlcv(raw.drop(columns="Volume"))


def test_ohlcv_problems_names_each_kind_of_bad_bar():
    idx = pd.bdate_range("2024-01-01", periods=4)
    bad = pd.DataFrame({"open": [10, 10, 10, 10], "high": [11, 9, 11, 11], "low": [9, 9.5, 9, 9],
                        "close": [10, 10, 10, 20], "volume": [1, 1, -1, 1]}, index=idx)
    text = " | ".join(loaders.ohlcv_problems(bad))
    for phrase in ("high below low", "outside the high-low range", "negative volume", "over 25%"):
        assert phrase in text
    assert loaders.ohlcv_problems(data.ohlcv(200, seed=1)) == []


def test_parse_timeframe():
    assert providers.parse_timeframe("1Day") == (1, "Day")
    assert providers.parse_timeframe("15Min") == (15, "Minute")
    assert providers.parse_timeframe("1 h") == (1, "Hour")
    with pytest.raises(ValueError, match="timeframe"):
        providers.parse_timeframe("daily")


@pytest.fixture
def fake_alpaca(monkeypatch):
    """Stand-ins for the alpaca-py modules the provider imports; the real SDK is optional."""
    enums = types.ModuleType("alpaca.data.enums")
    enums.Adjustment = enum.Enum("Adjustment", {"RAW": "raw", "SPLIT": "split", "DIVIDEND": "dividend", "ALL": "all"})
    enums.DataFeed = enum.Enum("DataFeed", {"IEX": "iex", "SIP": "sip"})
    requests_mod = types.ModuleType("alpaca.data.requests")
    requests_mod.StockBarsRequest = type("StockBarsRequest", (), {"__init__": lambda self, **kw: self.__dict__.update(kw)})
    timeframe = types.ModuleType("alpaca.data.timeframe")
    timeframe.TimeFrameUnit = enum.Enum("TimeFrameUnit", {"Minute": "Min", "Hour": "Hour", "Day": "Day",
                                                          "Week": "Week", "Month": "Month"})
    timeframe.TimeFrame = type("TimeFrame", (), {"__init__": lambda self, n, unit: self.__dict__.update(n=n, unit=unit)})

    created = []

    class Client:
        def __init__(self, key, secret):
            self.key, self.secret, self.requests = key, secret, []
            created.append(self)

        def get_stock_bars(self, request):
            self.requests.append(request)
            stamps = pd.DatetimeIndex(["2024-01-02 05:00", "2024-01-03 05:00"], tz="UTC")
            frames = [pd.DataFrame({"open": [10.0, 11], "high": [12.0, 12], "low": [9.0, 10], "close": [11.0, 11.5],
                                    "volume": [100, 200], "trade_count": [5, 6], "vwap": [10.5, 11]},
                                   index=pd.MultiIndex.from_product([[s], stamps], names=["symbol", "timestamp"]))
                      for s in request.symbol_or_symbols if s != "NOPE"]
            return types.SimpleNamespace(df=pd.concat(frames) if frames else pd.DataFrame())

    historical = types.ModuleType("alpaca.data.historical")
    Client.created = created
    historical.StockHistoricalDataClient = Client
    modules = {"alpaca": types.ModuleType("alpaca"), "alpaca.data": types.ModuleType("alpaca.data"),
               "alpaca.data.enums": enums, "alpaca.data.requests": requests_mod,
               "alpaca.data.timeframe": timeframe, "alpaca.data.historical": historical}
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setenv("ALPACA_API_KEY", "test-key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "test-secret")
    return Client


def test_alpaca_bars_builds_the_request_and_returns_standard_frames(fake_alpaca):
    bars = providers.alpaca_bars(["AAPL", "MSFT"], start="2024-01-01", timeframe="15Min")
    client = fake_alpaca.created[-1]
    request = client.requests[-1]
    assert (client.key, client.secret) == ("test-key", "test-secret")
    assert request.timeframe.n == 15 and request.timeframe.unit.name == "Minute"
    assert request.adjustment.name == "ALL" and request.feed.name == "SIP"
    assert request.end <= dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=15)   # free plan delays SIP
    assert set(bars) == {"AAPL", "MSFT"} and bars["AAPL"].index[0] == pd.Timestamp("2024-01-02")
    single = providers.alpaca_bars("AAPL", start="2024-01-01", feed="iex", client=client)
    assert isinstance(single, pd.DataFrame) and client.requests[-1].end is None
    with pytest.raises(ValueError, match="no bars for 'NOPE'"):
        providers.alpaca_bars("NOPE", start="2024-01-01", client=client)


def test_alpaca_credentials_must_come_from_the_environment(monkeypatch):
    for name in (*providers.ALPACA_KEY_VARS, *providers.ALPACA_SECRET_VARS):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError, match="ALPACA_API_KEY"):
        providers.alpaca_credentials()
    monkeypatch.setenv("APCA_API_KEY_ID", "k")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "s")
    assert providers.alpaca_credentials() == ("k", "s")


class _FakeIB:
    """A connected ib_async.IB stand-in that serves older 5-minute bars on each request."""

    def __init__(self, known=True, pages=2):
        self.known, self.pages, self.requests = known, pages, []

    def qualifyContracts(self, contract):
        contract.conId = 101 if self.known else 0
        return [contract]

    def reqHistoricalData(self, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate):
        self.requests.append(endDateTime)
        page = len(self.requests) - 1
        if page >= self.pages:
            return []
        start = dt.datetime(2024, 1, 5, 4, 0, tzinfo=dt.timezone.utc) - dt.timedelta(minutes=10 * page)
        return [types.SimpleNamespace(date=start + dt.timedelta(minutes=5 * k), open=100, high=101, low=99,
                                      close=100.5, volume=10) for k in range(3)]


@pytest.fixture
def fake_ib_async(monkeypatch):
    module = types.ModuleType("ib_async")
    module.Contract = type("Contract", (), {"__init__": lambda self, **kw: self.__dict__.update(kw)})
    module.IB = object
    monkeypatch.setitem(sys.modules, "ib_async", module)


def test_ibkr_bars_pages_back_in_time_with_pacing(fake_ib_async):
    ib, pauses = _FakeIB(pages=2), []
    bars = providers.ibkr_bars("RELIANCE", bar_size="5 mins", duration="1 D", chunks=3, ib=ib, pause_s=10.5,
                               sleep=pauses.append)
    assert ib.requests[0] == "" and ib.requests[1] == dt.datetime(2024, 1, 5, 4, 0, tzinfo=dt.timezone.utc)
    assert pauses == [10.5, 10.5] and len(ib.requests) == 3            # the third page was empty: stop
    assert bars.index[0] == pd.Timestamp("2024-01-05 09:20") and bars.index[-1] == pd.Timestamp("2024-01-05 09:40")
    assert bars.index.is_unique and len(bars) == 5                      # overlapping bar kept once


def test_ibkr_bars_explains_bad_requests(fake_ib_async):
    with pytest.raises(ValueError, match="does not recognise"):
        providers.ibkr_bars("NOSUCH", ib=_FakeIB(known=False))
    with pytest.raises(ValueError, match="ADJUSTED_LAST"):
        providers.ibkr_bars("RELIANCE", what_to_show="ADJUSTED_LAST", chunks=2, ib=_FakeIB())
    with pytest.raises(ValueError, match="no bars"):
        providers.ibkr_bars("RELIANCE", ib=_FakeIB(pages=0))


def test_fetch_command_saves_checked_csv_files(fake_alpaca, tmp_path, capsys):
    assert fetch_cli.main(["alpaca", "AAPL", "NOPE", "--start", "2024-01-01", "--out", str(tmp_path)]) == 1
    saved = loaders.load_ohlcv_csv(tmp_path / "AAPL.csv")
    assert list(saved.columns) == loaders.OHLCV and len(saved) == 2
    out = capsys.readouterr()
    assert "OK   AAPL: 2 bars" in out.out and "FAIL NOPE" in out.err
    assert fetch_cli.file_name("^nsei") == "NSEI" and fetch_cli.file_name("tcs.ns") == "TCS.NS"
