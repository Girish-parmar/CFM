"""Machine learning for trading (Modules 19-21, 23).

The package namespace re-exports features, labels, validation and sizing
(``from cfmat import ml; ml.purged_kfold(...)``).

    features        leakage-free feature matrix
    labels          triple-barrier labels and meta-labels
    validation      purged K-fold with embargo, walk-forward splits, out-of-fold predictions
    sizing          probabilities to positions and bet sizes
    tuning          gradient boosting, random/Optuna search, nested walk-forward, PBO
    reinforcement   tabular Q-learning trading agent
"""

from . import reinforcement, tuning
from .features import (
    make_features,
)
from .labels import (
    meta_labels,
    triple_barrier_labels,
)
from .sizing import (
    bet_size,
    proba_to_position,
)
from .validation import (
    out_of_fold_proba,
    purged_kfold,
    walk_forward_splits,
)

__all__ = [
    "bet_size",
    "make_features",
    "meta_labels",
    "out_of_fold_proba",
    "proba_to_position",
    "purged_kfold",
    "reinforcement",
    "triple_barrier_labels",
    "tuning",
    "walk_forward_splits",
]
