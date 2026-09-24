"""Gradient boosting and hyperparameter optimisation for trading models (Module 16).

Hyperparameter search is the easiest way to overfit a trading model: every
extra configuration you try is another chance to find noise that looks like
signal. This module supports the workflow taught in class:

1. ``make_booster``: one interface over scikit-learn's HistGradientBoosting,
   XGBoost and LightGBM.
2. ``random_search`` / ``optuna_search``: score configurations with *purged*
   cross-validation, and keep every trial's out-of-fold predictions.
3. ``nested_walk_forward``: re-tune inside each training window only, then
   trade the next window. This is the honest out-of-sample estimate.
4. ``probability_of_backtest_overfitting``: CSCV test of whether picking the
   best configuration in-sample generalises (Bailey et al., 2017).

XGBoost, LightGBM and Optuna are optional: ``pip install xgboost lightgbm optuna``
(``xgboost-cpu`` is a much smaller CPU-only build on Linux and Windows).
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score

from ..analytics.metrics import TRADING_DAYS
from .validation import purged_kfold, walk_forward_splits

# name -> (kind, low, high); kind is "int", "float" or "log" (log-uniform float)
SEARCH_SPACES: dict[str, dict[str, tuple[str, float, float]]] = {
    "hgb": {
        "learning_rate": ("log", 0.01, 0.3),
        "max_iter": ("int", 50, 300),
        "max_depth": ("int", 2, 6),
        "min_samples_leaf": ("int", 10, 200),
        "l2_regularization": ("log", 1e-4, 10.0),
        "max_features": ("float", 0.3, 1.0),
    },
    "xgboost": {
        "learning_rate": ("log", 0.01, 0.3),
        "n_estimators": ("int", 50, 300),
        "max_depth": ("int", 2, 6),
        "min_child_weight": ("log", 1.0, 50.0),
        "subsample": ("float", 0.5, 1.0),
        "colsample_bytree": ("float", 0.3, 1.0),
        "reg_lambda": ("log", 1e-3, 10.0),
    },
    "lightgbm": {
        "learning_rate": ("log", 0.01, 0.3),
        "n_estimators": ("int", 50, 300),
        "num_leaves": ("int", 4, 48),
        "min_child_samples": ("int", 10, 200),
        "subsample": ("float", 0.5, 1.0),
        "colsample_bytree": ("float", 0.3, 1.0),
        "reg_lambda": ("log", 1e-3, 10.0),
    },
}


def available_boosters() -> list[str]:
    """Booster kinds usable in this environment ("hgb" is always available)."""
    kinds = ["hgb"]
    kinds += [k for k in ("xgboost", "lightgbm") if importlib.util.find_spec(k) is not None]
    return kinds


def make_booster(kind: str = "hgb", random_state: int = 0, **params):
    """A gradient-boosted tree classifier with a scikit-learn interface."""
    if kind == "hgb":
        return HistGradientBoostingClassifier(random_state=random_state, early_stopping=False, **params)
    if kind == "xgboost":
        from xgboost import XGBClassifier

        return XGBClassifier(random_state=random_state, tree_method="hist", eval_metric="logloss",
                             verbosity=0, n_jobs=2, **params)
    if kind == "lightgbm":
        from lightgbm import LGBMClassifier

        if "subsample" in params:
            params.setdefault("subsample_freq", 1)  # LightGBM ignores subsample unless bagging is on
        return LGBMClassifier(random_state=random_state, verbose=-1, n_jobs=2, **params)
    raise ValueError(f"unknown booster kind {kind!r}; choose from {available_boosters()}")


def sample_params(space: dict[str, tuple[str, float, float]], rng: np.random.Generator) -> dict:
    params = {}
    for name, (kind, low, high) in space.items():
        if kind == "int":
            params[name] = int(rng.integers(low, high + 1))
        elif kind == "log":
            params[name] = float(np.exp(rng.uniform(np.log(low), np.log(high))))
        else:
            params[name] = float(rng.uniform(low, high))
    return params


def strategy_returns(proba: pd.Series, fwd_ret: pd.Series, threshold: float = 0.55, cost_bps: float = 0.0) -> pd.Series:
    """Per-period P&L of trading the model: long above ``threshold``, short below
    1 − threshold. ``fwd_ret`` is the return earned by a position taken at each row."""
    pos = pd.Series(np.where(proba > threshold, 1.0, np.where(proba < 1 - threshold, -1.0, 0.0)), index=proba.index)
    pos[proba.isna()] = 0.0
    turnover = pos.diff().abs().fillna(pos.abs())
    return pos * fwd_ret.reindex(proba.index).fillna(0.0) - turnover * cost_bps / 1e4


def _annual_sharpe(r: pd.Series | np.ndarray) -> float:
    r = np.asarray(r, dtype=float)
    sd = r.std(ddof=1)
    return float(r.mean() / sd * np.sqrt(TRADING_DAYS)) if sd > 1e-12 else 0.0


def cv_score(
    make_model,
    X: pd.DataFrame,
    y: pd.Series,
    fwd_ret: pd.Series | None = None,
    metric: str = "log_loss",
    n_splits: int = 4,
    horizon: int = 5,
    embargo: int = 5,
    threshold: float = 0.55,
) -> tuple[float, pd.Series]:
    """Purged K-fold score (higher is better) and the out-of-fold probabilities.

    ``metric``: "log_loss" (negated), "auc", "accuracy", or "sharpe" (needs
    ``fwd_ret``; annualised Sharpe of trading the out-of-fold predictions).
    """
    oof = pd.Series(np.nan, index=X.index)
    fold_scores = []
    for train, test in purged_kfold(len(X), n_splits, horizon=horizon, embargo=embargo):
        if len(np.unique(y.iloc[train])) < 2:
            continue
        model = make_model()
        model.fit(X.iloc[train], y.iloc[train])
        p = model.predict_proba(X.iloc[test])[:, 1]
        oof.iloc[test] = p
        yt = y.iloc[test]
        if metric == "log_loss":
            fold_scores.append(-log_loss(yt, np.clip(p, 1e-6, 1 - 1e-6), labels=[0, 1]))
        elif metric == "auc":
            fold_scores.append(roc_auc_score(yt, p) if yt.nunique() > 1 else 0.5)
        elif metric == "accuracy":
            fold_scores.append(accuracy_score(yt, p > 0.5))
        elif metric == "sharpe":
            if fwd_ret is None:
                raise ValueError("metric='sharpe' needs fwd_ret")
            fold_scores.append(_annual_sharpe(strategy_returns(pd.Series(p, index=yt.index), fwd_ret, threshold)))
        else:
            raise ValueError(f"unknown metric {metric!r}")
    return float(np.mean(fold_scores)), oof


@dataclass
class SearchResult:
    trials: pd.DataFrame     # one row per trial: params and score
    oof: pd.DataFrame        # out-of-fold probabilities, one column per trial
    best_params: dict
    best_score: float


def _finish(rows: list[dict], params: list[dict], oofs: dict[int, pd.Series]) -> SearchResult:
    best = int(np.argmax([row["score"] for row in rows]))
    trials = pd.DataFrame(rows).sort_values("score", ascending=False, ignore_index=True)
    return SearchResult(trials, pd.DataFrame(oofs), params[best], float(rows[best]["score"]))


def random_search(
    X: pd.DataFrame, y: pd.Series, kind: str = "hgb", n_trials: int = 30, seed: int = 0, **cv_kwargs
) -> SearchResult:
    """Random search over ``SEARCH_SPACES[kind]`` scored by purged CV."""
    rng = np.random.default_rng(seed)
    rows, tried, oofs = [], [], {}
    for trial in range(n_trials):
        params = sample_params(SEARCH_SPACES[kind], rng)
        score, oof = cv_score(lambda p=params: make_booster(kind, **p), X, y, **cv_kwargs)
        rows.append({"trial": trial, **params, "score": score})
        tried.append(params)
        oofs[trial] = oof
    return _finish(rows, tried, oofs)


def optuna_search(
    X: pd.DataFrame, y: pd.Series, kind: str = "hgb", n_trials: int = 30, seed: int = 0, **cv_kwargs
) -> SearchResult:
    """Bayesian optimisation (Optuna's TPE sampler) over the same space."""
    try:
        import optuna
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError("pip install optuna") from exc
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    space = SEARCH_SPACES[kind]
    rows, tried, oofs = [], [], {}

    def objective(trial: optuna.Trial) -> float:
        params = {}
        for name, (k, low, high) in space.items():
            if k == "int":
                params[name] = trial.suggest_int(name, int(low), int(high))
            else:
                params[name] = trial.suggest_float(name, low, high, log=(k == "log"))
        score, oof = cv_score(lambda: make_booster(kind, **params), X, y, **cv_kwargs)
        rows.append({"trial": trial.number, **params, "score": score})
        tried.append(params)
        oofs[trial.number] = oof
        return score

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=n_trials)
    return _finish(rows, tried, oofs)


def nested_walk_forward(
    X: pd.DataFrame,
    y: pd.Series,
    kind: str = "hgb",
    search: str = "random",
    n_trials: int = 10,
    train_size: int = 1000,
    test_size: int = 250,
    gap: int = 5,
    seed: int = 0,
    inner_splits: int = 3,
    **cv_kwargs,
) -> tuple[pd.Series, pd.DataFrame]:
    """Tune on each (expanding) training window only, then predict the next window.

    Returns out-of-sample probabilities (NaN where never tested) and a table of
    the parameters chosen for each window. Nothing from a test window is ever
    seen by the search that picks the model used on it.
    """
    search_fn = {"random": random_search, "optuna": optuna_search}[search]
    proba = pd.Series(np.nan, index=X.index)
    chosen = []
    fwd_ret = cv_kwargs.pop("fwd_ret", None)
    for fold, (train, test) in enumerate(walk_forward_splits(len(X), train_size, test_size, gap=gap)):
        inner_kwargs = dict(cv_kwargs, n_splits=inner_splits)
        if fwd_ret is not None:
            inner_kwargs["fwd_ret"] = fwd_ret.iloc[train]
        result = search_fn(X.iloc[train], y.iloc[train], kind, n_trials, seed + fold, **inner_kwargs)
        model = make_booster(kind, **result.best_params).fit(X.iloc[train], y.iloc[train])
        proba.iloc[test] = model.predict_proba(X.iloc[test])[:, 1]
        chosen.append({"test_start": X.index[test[0]], **result.best_params, "inner_score": result.best_score})
    return proba, pd.DataFrame(chosen)


def probability_of_backtest_overfitting(returns: pd.DataFrame, n_blocks: int = 10) -> dict:
    """Combinatorially symmetric cross-validation (CSCV).

    ``returns`` holds one column of per-period returns for every configuration
    you tried. Time is cut into ``n_blocks`` blocks; for every way of choosing
    half of them as in-sample, the best in-sample configuration is located in the
    out-of-sample ranking. PBO is the share of splits where it lands at or below
    the out-of-sample median. Near 0 is good; around 0.5 means selection is
    no better than chance.
    """
    if n_blocks % 2:
        raise ValueError("n_blocks must be even")
    values = returns.to_numpy(dtype=float)
    n_configs = values.shape[1]
    blocks = np.array_split(np.arange(len(values)), n_blocks)
    logits = []
    for is_blocks in combinations(range(n_blocks), n_blocks // 2):
        is_idx = np.concatenate([blocks[b] for b in is_blocks])
        oos_idx = np.concatenate([blocks[b] for b in range(n_blocks) if b not in is_blocks])
        is_perf = np.array([_annual_sharpe(values[is_idx, j]) for j in range(n_configs)])
        oos_perf = np.array([_annual_sharpe(values[oos_idx, j]) for j in range(n_configs)])
        best = int(np.argmax(is_perf))
        omega = (pd.Series(oos_perf).rank().iloc[best]) / (n_configs + 1)
        logits.append(np.log(omega / (1 - omega)))
    logits = np.array(logits)
    return {"pbo": float(np.mean(logits <= 0)), "logits": logits, "n_splits": len(logits)}
