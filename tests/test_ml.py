"""Tests for cfmat.ml: features, labels, validation, sizing, tuning and reinforcement learning."""


import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from cfmat import data, ml
from cfmat.ml import reinforcement, tuning


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


def test_triple_barrier_labels_and_purged_cv():
    close = data.ar1_prices(600, seed=3)
    lab = ml.triple_barrier_labels(close, horizon=10)
    valid = lab.dropna()
    assert set(valid["label"].unique()) <= {-1.0, 1.0}
    assert (valid["exit_pos"] > np.arange(len(close))[lab["label"].notna()]).all()
    n, h, emb = 500, 10, 5
    for train, test in ml.purged_kfold(n, 5, horizon=h, embargo=emb):
        assert len(np.intersect1d(train, test)) == 0
        # no training label may overlap the test window
        assert not np.any((train + h >= test[0]) & (train <= test[-1] + h))


def test_walk_forward_splits_respect_gap():
    for train, test in ml.walk_forward_splits(300, 100, 50, gap=10):
        assert test[0] - train[-1] == 11


def test_ml_pipeline_runs_end_to_end():
    bars = data.ohlcv_from_close(data.ar1_prices(800, phi=0.15, seed=5), seed=5)
    X = ml.make_features(bars)
    lab = ml.triple_barrier_labels(bars["close"], horizon=5)
    df = X.join(lab).dropna()
    y = (df["label"] > 0).astype(int)
    splits = ml.walk_forward_splits(len(df), 300, 100, gap=5)
    proba = ml.out_of_fold_proba(lambda: LogisticRegression(max_iter=500), df[X.columns], y, splits)
    assert proba.notna().sum() == 400
    assert set(ml.proba_to_position(proba.dropna()).unique()) <= {-1.0, 0.0, 1.0}


def test_q_learning_learns_obvious_pattern():
    # Returns alternate sign: after an up day, the next day is down.
    r = pd.Series(np.tile([0.01, -0.01], 300))
    agent = reinforcement.QLearningTrader(n_lags=1, epsilon=0.2, cost=0.0, seed=1).fit(r, episodes=30)
    pos = agent.positions(r)
    earned = (pos.shift(1) * r).sum()
    assert earned > 2.0


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
    for space in tuning.SEARCH_SPACES.values():
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
