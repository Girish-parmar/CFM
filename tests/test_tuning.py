import numpy as np
import pandas as pd
import pytest

from cfmat import data, ml, tuning


@pytest.fixture(scope="module")
def dataset():
    bars = data.ohlcv_from_close(data.ar1_prices(700, phi=0.2, seed=4), seed=4)
    feats = ml.make_features(bars)
    fwd = bars["close"].pct_change().shift(-1).rename("fwd")
    df = feats.join(fwd).dropna()
    return df[feats.columns], (df["fwd"] > 0).astype(int), df["fwd"]


@pytest.mark.parametrize("kind", tuning.available_boosters())
def test_make_booster_fits_every_available_kind(kind, dataset):
    X, y, _ = dataset
    params = tuning.sample_params(tuning.SEARCH_SPACES[kind], np.random.default_rng(0))
    model = tuning.make_booster(kind, **params).fit(X, y)
    proba = model.predict_proba(X)[:, 1]
    assert proba.shape == (len(X),) and ((proba >= 0) & (proba <= 1)).all()


def test_sample_params_respect_bounds_and_types():
    rng = np.random.default_rng(1)
    for kind, space in tuning.SEARCH_SPACES.items():
        for _ in range(20):
            params = tuning.sample_params(space, rng)
            for name, (k, low, high) in space.items():
                assert low <= params[name] <= high
                assert isinstance(params[name], int) == (k == "int")


def test_random_search_keeps_every_trial(dataset):
    X, y, fwd = dataset
    res = tuning.random_search(X, y, "hgb", n_trials=3, seed=0, fwd_ret=fwd, horizon=1, embargo=2, n_splits=3)
    assert len(res.trials) == 3 and res.oof.shape == (len(X), 3)
    assert res.best_score == res.trials["score"].max()
    assert isinstance(res.best_params["max_iter"], int)
    assert res.oof.notna().all().all()  # every sample lands in exactly one test fold


def test_sharpe_metric_needs_forward_returns(dataset):
    X, y, _ = dataset
    with pytest.raises(ValueError):
        tuning.cv_score(lambda: tuning.make_booster("hgb", max_iter=20), X, y, metric="sharpe")


def test_optuna_search_runs(dataset):
    pytest.importorskip("optuna")
    X, y, fwd = dataset
    res = tuning.optuna_search(X, y, "hgb", n_trials=3, seed=0, fwd_ret=fwd, horizon=1, embargo=2, n_splits=3)
    assert len(res.trials) == 3 and set(res.best_params) == set(tuning.SEARCH_SPACES["hgb"])


def test_nested_walk_forward_only_predicts_test_windows(dataset):
    X, y, fwd = dataset
    proba, chosen = tuning.nested_walk_forward(X, y, "hgb", n_trials=2, train_size=300, test_size=100, gap=2,
                                               fwd_ret=fwd, horizon=1, embargo=2)
    assert proba.iloc[:302].isna().all()
    assert proba.notna().sum() == 100 * len(chosen) and len(chosen) >= 2


def test_strategy_returns_charges_costs():
    idx = pd.RangeIndex(4)
    proba = pd.Series([0.9, 0.9, 0.1, 0.5], index=idx)
    fwd = pd.Series([0.01, 0.02, -0.01, 0.03], index=idx)
    r = tuning.strategy_returns(proba, fwd, threshold=0.55, cost_bps=10)
    assert r.round(6).tolist() == [0.009, 0.02, 0.008, -0.001]


def test_pbo_detects_luck_and_skill():
    rng = np.random.default_rng(0)
    noise = pd.DataFrame(rng.normal(0, 0.01, size=(1000, 20)))
    assert 0.25 <= tuning.probability_of_backtest_overfitting(noise)["pbo"] <= 0.75
    skilled = noise.copy()
    skilled[0] += 0.003  # one configuration with a real, persistent edge
    assert tuning.probability_of_backtest_overfitting(skilled)["pbo"] < 0.05
    with pytest.raises(ValueError):
        tuning.probability_of_backtest_overfitting(noise, n_blocks=5)
