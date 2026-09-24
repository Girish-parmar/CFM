"""Tests for cfmat.econometrics: Kalman filter, GARCH and Markov regimes."""

import numpy as np
import pandas as pd
import pytest

from cfmat import data, econometrics
from cfmat.analytics import metrics


def test_kalman_tracks_a_drifting_hedge_ratio():
    pair = data.drifting_pair(1500, beta_start=1.2, beta_end=1.9, seed=1)
    k = econometrics.kalman_hedge(pair["y"], pair["x"])
    assert (k["beta"] - pair["true_beta"]).abs().iloc[250:].mean() < 0.1
    assert (k["error_std"] > 0).all()


def test_kalman_is_causal():
    pair = data.drifting_pair(600, seed=3)
    full = econometrics.kalman_hedge(pair["y"], pair["x"])
    part = econometrics.kalman_hedge(pair["y"].iloc[:400], pair["x"].iloc[:400])
    pd.testing.assert_frame_equal(full.iloc[:400], part)


def test_kalman_pairs_signals_wait_for_warmup():
    pair = data.drifting_pair(500, seed=4)
    legs = econometrics.kalman_pairs_signals(pair["y"], pair["x"], warmup=100)
    assert (legs[["y", "x"]].iloc[:100] == 0).all().all()
    assert set(legs["y"].unique()) <= {-1.0, 0.0, 1.0}
    assert {"y", "x", "zscore", "beta"} <= set(legs.columns)


def test_garch_recovers_parameters():
    g = data.garch_prices(4000, omega=2e-6, alpha=0.08, beta=0.90, seed=11)
    fit = econometrics.garch11_fit(metrics.simple_returns(g["close"]))
    assert fit["alpha"] == pytest.approx(0.08, abs=0.04)
    assert fit["beta"] == pytest.approx(0.90, abs=0.04)
    assert fit["alpha"] + fit["beta"] < 1


def test_garch_forecast_is_causal_and_tracks_truth():
    g = data.garch_prices(1500, seed=2)
    rets = metrics.simple_returns(g["close"])
    params = econometrics.garch11_fit(rets.iloc[:800])
    full = econometrics.garch11_forecast(rets, params)
    part = econometrics.garch11_forecast(rets.iloc[:1000], params)
    pd.testing.assert_series_equal(full.iloc[:1000], part)
    assert full.corr(g["sigma"].reindex(rets.index).shift(-1)) > 0.9


def test_vol_target_weights_are_capped():
    w = econometrics.vol_target_weights(pd.Series([0.001, 0.01, 0.05]), target_vol=0.10, max_leverage=2.0)
    assert w.iloc[0] == 2.0 and w.iloc[2] < w.iloc[1] < 2.0


def test_markov_filter_has_no_look_ahead_but_smoother_does():
    m = data.regime_prices(1600, seed=5)
    rets = metrics.simple_returns(m["close"])
    params = econometrics.fit_markov_regimes(rets.iloc[:800])
    full = econometrics.markov_regime_probabilities(rets, params)
    part = econometrics.markov_regime_probabilities(rets.iloc[:1200], params)
    np.testing.assert_allclose(full["p_turbulent"].iloc[:1200], part["p_turbulent"], atol=1e-10)
    s_full = econometrics.markov_regime_probabilities(rets, params, smoothed=True)
    s_part = econometrics.markov_regime_probabilities(rets.iloc[:1200], params, smoothed=True)
    assert (s_full["p_turbulent"].iloc[:1200] - s_part["p_turbulent"]).abs().max() > 1e-4
    truth = m["regime"].reindex(full.index)
    assert ((full["p_turbulent"] > 0.5) == truth).mean() > 0.85
    assert full["vol_turbulent"].iloc[0] > full["vol_calm"].iloc[0]


def test_markov_fit_is_reproducible_and_leaves_global_rng_alone():
    rets = data.regime_prices(700, seed=4)["close"].pct_change().dropna().iloc[:500]
    np.random.seed(7)
    expected_next = np.random.random()
    np.random.seed(7)
    first = econometrics.fit_markov_regimes(rets, seed=3)
    assert np.random.random() == expected_next          # the caller's random stream is untouched
    assert np.allclose(first, econometrics.fit_markov_regimes(rets, seed=3))
