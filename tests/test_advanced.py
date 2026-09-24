import numpy as np
import pandas as pd
import pytest

from cfmat import advanced as adv
from cfmat import data, metrics


def test_kalman_tracks_a_drifting_hedge_ratio():
    pair = data.drifting_pair(1500, beta_start=1.2, beta_end=1.9, seed=1)
    k = adv.kalman_hedge(pair["y"], pair["x"])
    assert (k["beta"] - pair["true_beta"]).abs().iloc[250:].mean() < 0.1
    assert (k["error_std"] > 0).all()


def test_kalman_is_causal():
    pair = data.drifting_pair(600, seed=3)
    full = adv.kalman_hedge(pair["y"], pair["x"])
    part = adv.kalman_hedge(pair["y"].iloc[:400], pair["x"].iloc[:400])
    pd.testing.assert_frame_equal(full.iloc[:400], part)


def test_kalman_pairs_signals_wait_for_warmup():
    pair = data.drifting_pair(500, seed=4)
    legs = adv.kalman_pairs_signals(pair["y"], pair["x"], warmup=100)
    assert (legs[["y", "x"]].iloc[:100] == 0).all().all()
    assert set(legs["y"].unique()) <= {-1.0, 0.0, 1.0}
    assert {"y", "x", "zscore", "beta"} <= set(legs.columns)


def test_garch_recovers_parameters():
    g = data.garch_prices(4000, omega=2e-6, alpha=0.08, beta=0.90, seed=11)
    fit = adv.garch11_fit(metrics.simple_returns(g["close"]))
    assert fit["alpha"] == pytest.approx(0.08, abs=0.04)
    assert fit["beta"] == pytest.approx(0.90, abs=0.04)
    assert fit["alpha"] + fit["beta"] < 1


def test_garch_forecast_is_causal_and_tracks_truth():
    g = data.garch_prices(1500, seed=2)
    rets = metrics.simple_returns(g["close"])
    params = adv.garch11_fit(rets.iloc[:800])
    full = adv.garch11_forecast(rets, params)
    part = adv.garch11_forecast(rets.iloc[:1000], params)
    pd.testing.assert_series_equal(full.iloc[:1000], part)
    assert full.corr(g["sigma"].reindex(rets.index).shift(-1)) > 0.9


def test_vol_target_weights_are_capped():
    w = adv.vol_target_weights(pd.Series([0.001, 0.01, 0.05]), target_vol=0.10, max_leverage=2.0)
    assert w.iloc[0] == 2.0 and w.iloc[2] < w.iloc[1] < 2.0


def test_markov_filter_has_no_look_ahead_but_smoother_does():
    m = data.regime_prices(1600, seed=5)
    rets = metrics.simple_returns(m["close"])
    params = adv.fit_markov_regimes(rets.iloc[:800])
    full = adv.markov_regime_probabilities(rets, params)
    part = adv.markov_regime_probabilities(rets.iloc[:1200], params)
    np.testing.assert_allclose(full["p_turbulent"].iloc[:1200], part["p_turbulent"], atol=1e-10)
    s_full = adv.markov_regime_probabilities(rets, params, smoothed=True)
    s_part = adv.markov_regime_probabilities(rets.iloc[:1200], params, smoothed=True)
    assert (s_full["p_turbulent"].iloc[:1200] - s_part["p_turbulent"]).abs().max() > 1e-4
    truth = m["regime"].reindex(full.index)
    assert ((full["p_turbulent"] > 0.5) == truth).mean() > 0.85
    assert full["vol_turbulent"].iloc[0] > full["vol_calm"].iloc[0]


def test_regime_generator_labels_states():
    m = data.regime_prices(3000, seed=1)
    calm = metrics.simple_returns(m["close"])[m["regime"].iloc[1:] == 0]
    wild = metrics.simple_returns(m["close"])[m["regime"].iloc[1:] == 1]
    assert wild.std() > 2 * calm.std()


def test_meta_labels_follow_trade_direction():
    idx = pd.bdate_range("2024-01-01", periods=60)
    close = pd.Series(100 * np.exp(np.linspace(0, 0.3, 60)) * (1 + 0.001 * np.sin(np.arange(60))), index=idx)
    long_side = pd.Series(1.0, index=idx)
    short_side = pd.Series(-1.0, index=idx)
    from cfmat import ml

    up_long = ml.meta_labels(close, long_side, horizon=5).dropna()
    up_short = ml.meta_labels(close, short_side, horizon=5).dropna()
    assert up_long["label"].mean() > 0.9 and up_short["label"].mean() < 0.1
    flat = ml.meta_labels(close, pd.Series(0.0, index=idx), horizon=5)
    assert flat["label"].isna().all()


def test_bet_size_is_monotonic_and_floored():
    from cfmat import ml

    p = pd.Series([np.nan, 0.2, 0.5, 0.6, 0.8, 0.99])
    size = ml.bet_size(p)
    assert size.iloc[0] == 0 and size.iloc[1] == 0 and size.iloc[2] == 0
    assert 0 < size.iloc[3] < size.iloc[4] < size.iloc[5] <= 1


@pytest.mark.parametrize("method", ["equal", "inverse_vol", "risk_parity", "hrp"])
def test_rolling_allocation_uses_only_past_data(method):
    from cfmat import portfolio

    rng = np.random.default_rng(0)
    rets = pd.DataFrame(rng.normal(0, [0.01, 0.02, 0.005], size=(400, 3)), columns=list("abc"))
    w = portfolio.rolling_allocation(rets, method=method, lookback=100, rebalance=20)
    assert (w.iloc[:99] == 0).all().all()
    assert np.allclose(w.iloc[99:].sum(axis=1), 1.0)
    # changing future returns must not change today's weights
    shocked = rets.copy()
    shocked.iloc[300:] *= 5
    w2 = portfolio.rolling_allocation(shocked, method=method, lookback=100, rebalance=20)
    pd.testing.assert_frame_equal(w.iloc[:300], w2.iloc[:300], check_exact=False, rtol=1e-6, atol=1e-9)
    if method == "inverse_vol":
        assert w.iloc[-1]["c"] > w.iloc[-1]["a"] > w.iloc[-1]["b"]
    combined = portfolio.allocation_returns(rets, w)
    assert combined.iloc[:100].abs().sum() == 0
