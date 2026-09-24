import numpy as np
import pandas as pd
import pytest

from cfmat import data, report
from cfmat import indicators as ind
from cfmat import strategy_builder as sb


def make_bars(opens, highs, lows, closes):
    idx = pd.bdate_range("2026-01-01", periods=len(opens))
    return pd.DataFrame({"open": opens, "high": highs, "low": lows, "close": closes, "volume": 1e6}, index=idx, dtype=float)


def flat_then(path, n_flat=20):
    """n_flat quiet bars (so ATR exists) followed by an explicit OHLC path."""
    base = [(100.0, 100.5, 99.5, 100.0)] * n_flat
    rows = base + path
    return make_bars(*zip(*rows))


@pytest.fixture(scope="module")
def market():
    return data.seasonal_prices(1500, seed=2)


def test_entry_fills_at_next_open_and_returns_compound_to_trade_return():
    bars = flat_then([(101, 102, 100, 101.5), (102, 104, 101, 103), (104, 106, 103, 105), (105.5, 106, 104, 105)])
    signal_bar = bars.index[20]
    spec = sb.StrategySpec("t", long_entry=["close > 101"], long_exit=["close > 104"])
    res = sb.backtest(bars, spec, cost_bps=0, slippage_bps=0)
    trade = res.trades.iloc[0]
    assert trade["entry_time"] == bars.index[21] and trade["entry_price"] == 102      # next open after the signal
    assert trade["exit_time"] == bars.index[23] and trade["exit_price"] == 105.5      # exit signal at bar 22 close
    held = res.returns.loc[trade["entry_time"]: trade["exit_time"]]
    assert np.prod(1 + held) - 1 == pytest.approx(105.5 / 102 - 1)
    assert res.position.loc[signal_bar] == 0


def test_stop_fills_at_stop_or_at_a_gapped_open():
    path = [(100, 101, 99, 100.8), (101, 101.5, 100, 101), (100.5, 100.8, 97, 98)]   # ATR ≈ 1
    spec = sb.StrategySpec("s", long_entry=["close > 100.6"], stop_atr=2.0)
    bars = flat_then(path)
    res = sb.backtest(bars, spec, cost_bps=0, slippage_bps=0)
    t = res.trades.iloc[0]
    atr_at_signal = ind.atr(bars, 14).iloc[20]              # signal at bar 20's close, entry at bar 21's open
    assert t["reason"] == "stop" and t["exit_price"] == pytest.approx(t["entry_price"] - 2 * atr_at_signal)
    gap = [(100, 101, 99, 100.8), (101, 101.5, 100, 101), (95, 96, 94, 95)]          # opens far below the stop
    t2 = sb.backtest(flat_then(gap), spec, cost_bps=0, slippage_bps=0).trades.iloc[0]
    assert t2["reason"] == "stop" and t2["exit_price"] == 95


def test_target_trailing_stop_and_time_exit():
    up = [(100, 101, 99, 100.8)] + [(100 + i, 101 + i, 99.8 + i, 100.9 + i) for i in range(1, 6)]
    target = sb.StrategySpec("t", long_entry=["close > 100.6"], target_atr=2.0)
    assert sb.backtest(flat_then(up), target, cost_bps=0, slippage_bps=0).trades.iloc[0]["reason"] == "target"
    trail_path = up + [(105, 105.2, 101, 101.5)]
    trail = sb.StrategySpec("tr", long_entry=["close > 100.6"], trail_atr=1.5)
    t = sb.backtest(flat_then(trail_path), trail, cost_bps=0, slippage_bps=0).trades.iloc[0]
    assert t["reason"] == "stop" and t["exit_price"] > t["entry_price"]               # stop trailed into profit
    timed = sb.StrategySpec("time", long_entry=["close > 100.6"], max_bars=3)
    assert sb.backtest(flat_then(up), timed, cost_bps=0, slippage_bps=0).trades.iloc[0]["bars"] == 4


def test_reversal_closes_and_opens_at_the_same_open(market):
    spec = sb.TEMPLATES["trend_supertrend"]
    res = sb.backtest(market, spec)
    rev = res.trades[res.trades["reason"] == "reverse"]
    assert len(rev) > 0
    nxt = res.trades.set_index("entry_time")
    for _, t in rev.head(5).iterrows():
        assert t["exit_time"] in nxt.index and nxt.loc[t["exit_time"], "side"] != t["side"]
    assert set(res.position.unique()) <= {-1.0, 0.0, 1.0}


def test_costs_reduce_returns(market):
    spec = sb.TEMPLATES["rsi2_pullback"]
    free = sb.backtest(market, spec, cost_bps=0, slippage_bps=0).returns.sum()
    paid = sb.backtest(market, spec, cost_bps=10, slippage_bps=5).returns.sum()
    assert paid < free


@pytest.mark.parametrize("rule", [
    "__import__('os').system('echo hacked')", "close.values", "[x for x in close]", "lambda: 1",
    "close[0]", "open(1)", "unknown_indicator(3) > 1", "sma(close, window=5)",
])
def test_rule_language_rejects_anything_not_whitelisted(market, rule):
    with pytest.raises(ValueError):
        sb.Evaluator(market)(rule)


def test_rule_language_features(market):
    ev = sb.Evaluator(market)
    assert ev.boolean("rsi(14) > 0 and rsi(14) < 100").iloc[50:].all()
    assert (ev("sma(close, 5)") == ev("sma(5)")).iloc[10:].all()
    assert ev.boolean("30 < rsi(14) < 70").sum() > 0
    both = ev.boolean("bullish_engulfing or hammer")
    assert both.sum() >= ev.boolean("bullish_engulfing").sum()
    assert ev.boolean("recent(cross_above(ema(10), ema(30)), 5)").sum() >= ev.boolean("cross_above(ema(10), ema(30))").sum()
    assert ev.boolean("squeeze(20, 120)").dtype == bool


def test_spec_placeholders_and_json_round_trip(tmp_path):
    spec = sb.TEMPLATES["either_way_squeeze"]
    resolved = spec.resolve(n=30, stop=2)
    assert "highest(high, 30)" in resolved.long_entry[1] and resolved.stop_atr == 2.0
    path = tmp_path / "s.json"
    spec.to_json(str(path))
    assert sb.StrategySpec.from_json(str(path)) == spec
    with pytest.raises(ValueError):
        sb.StrategySpec("x", long_entry=["rsi(2) < {level}"]).resolve()
    with pytest.raises(ValueError):
        sb.StrategySpec.from_dict({"name": "x", "bogus": 1})


def test_parallel_sweep_matches_serial(market):
    spec = sb.TEMPLATES["rsi2_pullback"]
    grid = {"oversold": [5, 10, 15, 20]}
    serial = sb.sweep(market, spec, grid, workers=1)
    procs = sb.sweep(market, spec, grid, workers=2, backend="process")
    threads = sb.sweep(market, spec, grid, workers=2, backend="thread")
    pd.testing.assert_frame_equal(serial, procs)
    pd.testing.assert_frame_equal(serial, threads)


def test_coarse_to_fine_uses_fewer_evaluations(market):
    grid = {"entry": [10, 15, 20, 25, 30, 40], "exit": [5, 10, 15, 20], "trend": [50, 100, 200]}
    full = sb.sweep(market, sb.TEMPLATES["trend_up_breakout"], grid)
    smart, evaluations = sb.coarse_to_fine(market, sb.TEMPLATES["trend_up_breakout"], grid, top_k=3)
    assert evaluations < len(full)
    assert smart["sharpe"].iloc[0] >= full["sharpe"].quantile(0.8)


def test_walk_forward_is_out_of_sample(market):
    oos, chosen = sb.walk_forward(market, sb.TEMPLATES["rsi2_pullback"], {"oversold": [5, 15]}, train=600, test=300)
    assert oos.index[0] == market.index[600] and len(oos) == 900 and len(chosen) == 3
    assert chosen["oversold"].map(type).eq(int).all()


def test_strategy_matrix_and_report(market):
    uni = {"A": market, "B": market.iloc[:800]}
    specs = {k: sb.TEMPLATES[k] for k in ("rsi2_pullback", "trend_supertrend")}
    m = sb.strategy_matrix(uni, specs, workers=2, backend="thread")
    assert len(m) == 4 and set(m["symbol"]) == {"A", "B"}
    res = sb.backtest(market, specs["rsi2_pullback"])
    stats = res.stats()
    assert 0 <= stats["win_rate"] <= 1 and stats["trades"] == len(res.trades)
    table = report.monthly_returns_table(res.returns)
    assert "Year" in table.columns and table.shape[0] == len(set(market.index.year))
