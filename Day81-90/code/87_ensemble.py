"""
Day 87 - Ensemble Learning Algorithms
======================================
Comprehensive demonstration of ensemble learning methods including:
  - Bagging (Bootstrap Aggregating)
  - Boosting (AdaBoost, Gradient Boosting, XGBoost)
  - Stacking (Meta-learning)
  - C++ Committee Pattern comparison
  - Enterprise production examples

Ensemble learning combines multiple weak learners to build a strong learner
with better generalization than any single model alone.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence

import numpy as np
from numpy.typing import NDArray

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
ArrayLike = NDArray[np.floating] | Sequence[float]
Labels = NDArray[np.integer] | Sequence[int]


# ===========================================================================
# 1. BAGGING — Bootstrap Aggregating
# ===========================================================================

class SupportsFitPredict(Protocol):
    """Protocol for models that support fit / predict."""
    def fit(self, X: NDArray[Any], y: NDArray[Any]) -> "SupportsFitPredict": ...
    def predict(self, X: NDArray[Any]) -> NDArray[Any]: ...


@dataclass
class ManualBaggingClassifier:
    """
    Hand-coded Bagging classifier that illustrates the core idea:
      1. Draw *n_estimators* bootstrap samples from the training set.
      2. Train one base estimator on each sample.
      3. Aggregate predictions via majority vote.

    Attributes:
        base_estimator_class: The class of the weak learner (must accept
            ``**estimator_params`` in its constructor).
        n_estimators: Number of base estimators.
        estimator_params: Keyword arguments forwarded to the base estimator.
        random_state: Seed for reproducibility.
    """

    base_estimator_class: type
    n_estimators: int = 10
    estimator_params: dict[str, Any] = field(default_factory=dict)
    random_state: int = 42

    # Fitted estimators stored after ``fit``
    estimators_: list[SupportsFitPredict] = field(
        default_factory=list, init=False, repr=False
    )

    def fit(self, X: NDArray[Any], y: NDArray[Any]) -> "ManualBaggingClassifier":
        rng = np.random.RandomState(self.random_state)
        n_samples: int = X.shape[0]
        self.estimators_ = []
        for _ in range(self.n_estimators):
            indices = rng.choice(n_samples, size=n_samples, replace=True)
            X_boot, y_boot = X[indices], y[indices]
            est = self.base_estimator_class(**self.estimator_params)  # type: ignore[call-arg]
            est.fit(X_boot, y_boot)
            self.estimators_.append(est)
        return self

    def predict(self, X: NDArray[Any]) -> NDArray[Any]:
        # Collect predictions from every estimator
        all_preds = np.array([est.predict(X) for est in self.estimators_])
        # Majority vote along axis 0
        from scipy.stats import mode
        result = mode(all_preds, axis=0, keepdims=False)
        return result.mode.ravel() if hasattr(result, "mode") else result[0].ravel()


def demo_bagging() -> None:
    """Demonstrate Bagging with RandomForest and a hand-coded version."""
    from sklearn.datasets import load_iris
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeClassifier

    print("=" * 70)
    print("1. BAGGING DEMO")
    print("=" * 70)

    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=3
    )

    # --- scikit-learn RandomForest (canonical Bagging with decision trees) ---
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    print("\n[RandomForest - sklearn Bagging]")
    print(classification_report(y_test, rf.predict(X_test)))

    # --- Manual Bagging to expose the algorithm ---
    manual = ManualBaggingClassifier(
        base_estimator_class=DecisionTreeClassifier,
        n_estimators=50,
        estimator_params={"max_depth": 5},
        random_state=42,
    )
    manual.fit(X_train, y_train)
    print("[Manual Bagging Classifier]")
    print(classification_report(y_test, manual.predict(X_test)))


# ===========================================================================
# 2. ADABOOST — Adaptive Boosting
# ===========================================================================

def demo_adaboost() -> None:
    """
    AdaBoost trains weak learners sequentially.

    Key idea:
      - Increase weights of misclassified samples after each round.
      - Better weak learners receive higher weight in the final vote.

    Mathematically:
      alpha_t = 0.5 * ln((1 - eps_t) / eps_t)
      w_i^(t+1) = w_i^(t) * exp(-alpha_t * y_i * h_t(x_i))
      H(x) = sign( sum_t alpha_t * h_t(x) )
    """
    from sklearn.datasets import load_iris
    from sklearn.ensemble import AdaBoostClassifier
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeClassifier

    print("=" * 70)
    print("2. ADABOOST DEMO")
    print("=" * 70)

    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=3
    )

    # Decision stump (depth-1 tree) is the classic weak learner
    base = DecisionTreeClassifier(max_depth=1)
    model = AdaBoostClassifier(
        estimator=base,
        n_estimators=50,
        learning_rate=1.0,
        algorithm="SAMME",
        random_state=42,
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"\nEstimators used  : {model.n_estimators}")
    print(f"Estimator weights: {model.estimator_weights_}")
    print(classification_report(y_test, y_pred))


# ===========================================================================
# 3. GRADIENT BOOSTING (GBDT)
# ===========================================================================

def demo_gradient_boosting() -> None:
    """
    GBDT fits each new tree to the *residuals* (negative gradient) of the
    loss function from the previous ensemble, using a learning rate eta:

      F_{m+1}(x) = F_m(x) + eta * h_m(x)

    Regression uses MSE; classification uses log-loss.
    """
    from sklearn.datasets import load_iris
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.metrics import classification_report
    from sklearn.model_selection import GridSearchCV, train_test_split

    print("=" * 70)
    print("3. GRADIENT BOOSTING (GBDT) DEMO")
    print("=" * 70)

    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=3
    )

    # Basic GBDT
    gbdt = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        subsample=0.8,
        random_state=42,
    )
    gbdt.fit(X_train, y_train)
    print("\n[GradientBoostingClassifier]")
    print(classification_report(y_test, gbdt.predict(X_test)))

    # Hyperparameter tuning with GridSearchCV
    param_grid: dict[str, list[Any]] = {
        "n_estimators": [50, 100, 200],
        "learning_rate": [0.01, 0.1, 0.2],
        "max_depth": [2, 3, 4],
    }
    grid = GridSearchCV(
        GradientBoostingClassifier(random_state=42),
        param_grid,
        cv=5,
        scoring="accuracy",
        n_jobs=-1,
    )
    grid.fit(X_train, y_train)
    print(f"Best params : {grid.best_params_}")
    print(f"Best CV acc : {grid.best_score_:.4f}")
    print(f"Test acc    : {grid.best_estimator_.score(X_test, y_test):.4f}")


# ===========================================================================
# 4. XGBOOST
# ===========================================================================

def demo_xgboost() -> None:
    """
    XGBoost extends GBDT with:
      - Second-order Taylor expansion of the loss (uses Hessian).
      - Regularization (L1 / L2) on leaf weights.
      - Column subsampling, shrinkage (eta), gamma for pruning.
      - Sparsity-aware split finding and cache-optimised training.
    """
    try:
        import xgboost as xgb
    except ImportError:
        print("\n[SKIP] xgboost is not installed.  pip install xgboost")
        return

    from sklearn.datasets import load_iris
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split

    print("=" * 70)
    print("4. XGBOOST DEMO")
    print("=" * 70)

    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=3
    )

    # XGBoost native API uses DMatrix for efficiency
    dm_train = xgb.DMatrix(X_train, label=y_train)
    dm_test = xgb.DMatrix(X_test)

    params: dict[str, Any] = {
        "booster": "gbtree",
        "objective": "multi:softmax",
        "num_class": 3,
        "max_depth": 6,
        "eta": 0.05,
        "gamma": 0.1,
        "lambda": 2,            # L2 regularization
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "seed": 42,
        "nthread": 4,
    }

    model = xgb.train(
        params,
        dm_train,
        num_boost_round=200,
        evals=[(dm_train, "train"), (dm_test, "test")],
        verbose_eval=False,
    )
    y_pred = model.predict(dm_test)
    print("\n[XGBoost native API]")
    print(classification_report(y_test, y_pred.astype(int)))

    # XGBoost scikit-learn wrapper
    xgb_clf = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42,
    )
    xgb_clf.fit(X_train, y_train)
    print("[XGBoost sklearn wrapper]")
    print(classification_report(y_test, xgb_clf.predict(X_test)))


# ===========================================================================
# 5. LIGHTGBM (bonus — covered in the document)
# ===========================================================================

def demo_lightgbm() -> None:
    """
    LightGBM adds histogram-based splitting, GOSS, EFB, and leaf-wise
    growth on top of GBDT for faster training on large datasets.
    """
    try:
        import lightgbm as lgb
    except ImportError:
        print("\n[SKIP] lightgbm is not installed.  pip install lightgbm")
        return

    from sklearn.datasets import load_iris
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split

    print("=" * 70)
    print("5. LIGHTGBM DEMO")
    print("=" * 70)

    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=3
    )

    train_data = lgb.Dataset(X_train, label=y_train)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

    params: dict[str, Any] = {
        "objective": "multiclass",
        "num_class": 3,
        "metric": "multi_logloss",
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.75,
        "verbose": -1,
    }
    model = lgb.train(
        params,
        train_data,
        num_boost_round=200,
        valid_sets=[test_data],
        callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)],
    )
    y_pred = np.argmax(model.predict(X_test, num_iteration=model.best_iteration), axis=1)
    print("\n[LightGBM]")
    print(classification_report(y_test, y_pred))


# ===========================================================================
# 6. STACKING — Meta-Learning
# ===========================================================================

def demo_stacking() -> None:
    """
    Stacking trains *base learners* on the training set, then uses their
    out-of-fold predictions as features for a *meta-learner* (level-1 model).

    This allows the meta-learner to discover how to best combine the
    strengths of heterogeneous base models.
    """
    from sklearn.datasets import load_iris
    from sklearn.ensemble import (
        GradientBoostingClassifier,
        RandomForestClassifier,
        StackingClassifier,
    )
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split
    from sklearn.svm import SVC

    print("=" * 70)
    print("6. STACKING DEMO")
    print("=" * 70)

    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=3
    )

    # Level-0: heterogeneous base learners
    base_estimators: list[tuple[str, Any]] = [
        ("rf", RandomForestClassifier(n_estimators=100, random_state=42)),
        ("gbdt", GradientBoostingClassifier(n_estimators=100, random_state=42)),
        ("svc", SVC(kernel="rbf", probability=True, random_state=42)),
    ]

    # Level-1: meta-learner (logistic regression is a common choice)
    meta_learner = LogisticRegression(max_iter=1000, random_state=42)

    stack = StackingClassifier(
        estimators=base_estimators,
        final_estimator=meta_learner,
        cv=5,
        stack_method="predict_proba",
        n_jobs=-1,
    )
    stack.fit(X_train, y_train)
    print("\n[StackingClassifier]")
    print(f"Base learners   : {[name for name, _ in base_estimators]}")
    print(f"Meta-learner    : {type(meta_learner).__name__}")
    print(classification_report(y_test, stack.predict(X_test)))


# ===========================================================================
# 7. C++ COMPARISON — Ensemble vs Committee Pattern
# ===========================================================================

def demo_cpp_comparison() -> None:
    """
    In C++ (and other systems languages) the *Committee Pattern* is a
    design pattern where multiple independent "expert" objects each
    produce a result, and a committee object aggregates them.

    Comparison with Python ensemble learning:
    ┌──────────────────────┬────────────────────────────────────────┐
    │ Aspect               │ C++ Committee / Python Ensemble        │
    ├──────────────────────┼────────────────────────────────────────┤
    │ Binding              │ Compile-time (templates, CRTP)         │
    │                      │ vs. Runtime (duck typing, protocols)   │
    │ Composition          │ Manual (std::vector<Expert*>)          │
    │                      │ vs. sklearn Pipelines / Stacking       │
    │ Aggregation          │ Hand-coded voting / averaging          │
    │                      │ vs. built-in BaggingClassifier, etc.   │
    │ Parallelism          │ std::thread / OpenMP / TBB             │
    │                      │ vs. joblib n_jobs parameter            │
    │ Memory management    │ RAII, smart pointers                   │
    │                      │ vs. GC / reference counting            │
    │ Hot-path performance │ Typically faster for small models      │
    │                      │ vs. NumPy/Cython backends for large    │
    └──────────────────────┴────────────────────────────────────────┘

    The C++ equivalent is roughly:
        template<typename Expert>
        class Committee {
            std::vector<Expert> experts;
            Aggregator agg;
        public:
            auto vote(const Input& in) { return agg(in, experts); }
        };
    """
    print("=" * 70)
    print("7. C++ COMMITTEE PATTERN vs PYTHON ENSEMBLE")
    print("=" * 70)

    cpp_code = r"""
// ---- C++ Committee Pattern (conceptual) ----
#include <vector>
#include <algorithm>
#include <numeric>

template <typename Expert, typename Aggregator>
class Committee {
    std::vector<Expert> experts_;
    Aggregator agg_;
public:
    Committee(std::vector<Expert> experts, Aggregator agg)
        : experts_(std::move(experts)), agg_(std::move(agg)) {}

    auto vote(const auto& input) const {
        std::vector<typename Expert::result_type> results;
        results.reserve(experts_.size());
        for (const auto& e : experts_) {
            results.push_back(e.predict(input));
        }
        return agg_(results);   // majority vote, weighted average, etc.
    }
};

// Usage:
// Committee<DecisionTree, MajorityVote> forest(trees, MajorityVote{});
// auto label = forest.vote(sample);
"""
    print(cpp_code)

    # Python equivalent in ~15 lines
    print("--- Python equivalent (runtime, duck-typed) ---")
    print(
        "class Committee:\n"
        "    def __init__(self, experts, aggregator):\n"
        "        self.experts = experts\n"
        "        self.agg = aggregator\n"
        "    def vote(self, X):\n"
        "        preds = [e.predict(X) for e in self.experts]\n"
        "        return self.agg(preds)\n"
    )
    print(
        "Key difference: C++ resolves types at compile time and manages\n"
        "memory manually (RAII).  Python binds at runtime and delegates\n"
        "heavy lifting to NumPy/Cython, making rapid prototyping easy\n"
        "while C++ excels at latency-critical, embedded deployments."
    )


# ===========================================================================
# 8. ENTERPRISE EXAMPLE — Competition Stacking Pipeline
# ===========================================================================

def demo_enterprise_competition_stacking() -> None:
    """
    Real-world Kaggle / data-science competition pipeline:
      1. Train diverse base learners with cross-validated out-of-fold (OOF)
         predictions to prevent leakage.
      2. Stack OOF predictions as new features for a meta-learner.
      3. Optionally blend with a weighted average.

    This pattern is battle-tested in winning solutions.
    """
    from sklearn.datasets import load_iris
    from sklearn.ensemble import (
        ExtraTreesClassifier,
        GradientBoostingClassifier,
        RandomForestClassifier,
    )
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import KFold, train_test_split
    from sklearn.svm import SVC

    print("=" * 70)
    print("8. ENTERPRISE: COMPETITION STACKING PIPELINE")
    print("=" * 70)

    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=3
    )

    # Level-0 base learners
    base_models: dict[str, Any] = {
        "rf": RandomForestClassifier(n_estimators=200, random_state=42),
        "et": ExtraTreesClassifier(n_estimators=200, random_state=42),
        "gbdt": GradientBoostingClassifier(n_estimators=200, random_state=42),
        "svc": SVC(kernel="rbf", probability=True, random_state=42),
    }

    n_folds: int = 5
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)

    # Generate out-of-fold predictions for training meta-features
    oof_train: dict[str, NDArray[np.floating]] = {}
    oof_test: dict[str, NDArray[np.floating]] = {}
    oof_test_mean: dict[str, NDArray[np.floating]] = {}

    for name, model in base_models.items():
        print(f"  Generating OOF predictions for: {name}")
        oof_train_np = np.zeros((X_train.shape[0],))  # class labels
        oof_test_np = np.zeros((n_folds, X_test.shape[0]))

        for fold_idx, (trn_idx, val_idx) in enumerate(kf.split(X_train)):
            X_tr, X_val = X_train[trn_idx], X_train[val_idx]
            y_tr, _ = y_train[trn_idx], y_train[val_idx]

            model.fit(X_tr, y_tr)
            oof_train_np[val_idx] = model.predict(X_val)
            oof_test_np[fold_idx] = model.predict(X_test)

        oof_train[name] = oof_train_np
        oof_test_mean[name] = oof_test_np.mean(axis=0)

    # Build meta-features: stack OOF predictions from all base models
    meta_X_train = np.column_stack([oof_train[n] for n in base_models])
    meta_X_test = np.column_stack([oof_test_mean[n] for n in base_models])

    # Level-1 meta-learner
    meta_model = LogisticRegression(max_iter=1000, random_state=42)
    meta_model.fit(meta_X_train, y_train)
    y_pred = meta_model.predict(meta_X_test)

    print(f"\n  Stacking accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"  Individual model accuracies:")
    for name in base_models:
        acc = accuracy_score(y_test, oof_test_mean[name].round().astype(int))
        print(f"    {name:>6s}: {acc:.4f}")


# ===========================================================================
# 9. ENTERPRISE EXAMPLE — Production Ensemble Model
# ===========================================================================

@dataclass
class ProductionEnsembleConfig:
    """Configuration for a production ensemble model."""
    model_names: list[str] = field(
        default_factory=lambda: ["rf", "gbdt", "xgb", "lgb"]
    )
    voting: str = "soft"  # 'soft' (probabilities) or 'hard' (labels)
    weights: list[float] | None = None
    n_jobs: int = -1
    cv_folds: int = 5


class ProductionEnsemble:
    """
    Enterprise-grade ensemble that:
      - Supports hard and soft voting.
      - Accepts pre-fitted models or builds them from config.
      - Provides predict and predict_proba for deployment.
      - Logs model contributions for interpretability.

    Typical deployment:
      model = ProductionEnsemble(config)
      model.fit(X_train, y_train)
      predictions = model.predict(X_test)
    """

    def __init__(self, config: ProductionEnsembleConfig | None = None) -> None:
        self.config = config or ProductionEnsembleConfig()
        self.models: dict[str, Any] = {}
        self._is_fitted: bool = False

    def _build_models(self) -> dict[str, Any]:
        from sklearn.ensemble import (
            GradientBoostingClassifier,
            RandomForestClassifier,
        )

        builders: dict[str, Any] = {
            "rf": lambda: RandomForestClassifier(
                n_estimators=300, max_depth=10, random_state=42
            ),
            "gbdt": lambda: GradientBoostingClassifier(
                n_estimators=300, learning_rate=0.05, max_depth=4, random_state=42
            ),
        }
        # Optionally add XGBoost / LightGBM
        try:
            import xgboost as xgb
            builders["xgb"] = lambda: xgb.XGBClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                use_label_encoder=False,
                eval_metric="mlogloss",
                random_state=42,
            )
        except ImportError:
            pass
        try:
            import lightgbm as lgb
            builders["lgb"] = lambda: lgb.LGBMClassifier(
                n_estimators=300,
                learning_rate=0.05,
                num_leaves=31,
                random_state=42,
                verbose=-1,
            )
        except ImportError:
            pass

        return {
            name: builders[name]()
            for name in self.config.model_names
            if name in builders
        }

    def fit(self, X: NDArray[Any], y: NDArray[Any]) -> "ProductionEnsemble":
        self.models = self._build_models()
        for name, model in self.models.items():
            print(f"  [ProductionEnsemble] Fitting {name}...")
            model.fit(X, y)
        self._is_fitted = True
        return self

    def predict_proba(self, X: NDArray[Any]) -> NDArray[np.floating]:
        if not self._is_fitted:
            raise RuntimeError("Model must be fitted before prediction.")
        probas: list[NDArray[np.floating]] = []
        for name, model in self.models.items():
            probas.append(model.predict_proba(X))
        weights = self.config.weights or [1.0] * len(probas)
        weighted = sum(w * p for w, p in zip(weights, probas))
        return weighted / sum(weights)

    def predict(self, X: NDArray[Any]) -> NDArray[np.integer]:
        if self.config.voting == "soft":
            return np.argmax(self.predict_proba(X), axis=1)
        # Hard voting
        preds = np.array([m.predict(X) for m in self.models.values()])
        from scipy.stats import mode
        result = mode(preds, axis=0, keepdims=False)
        return result.mode.ravel() if hasattr(result, "mode") else result[0].ravel()

    def score(self, X: NDArray[Any], y: NDArray[Any]) -> float:
        from sklearn.metrics import accuracy_score
        return float(accuracy_score(y, self.predict(X)))


def demo_production_ensemble() -> None:
    """End-to-end production ensemble example."""
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split

    print("=" * 70)
    print("9. ENTERPRISE: PRODUCTION ENSEMBLE MODEL")
    print("=" * 70)

    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=3
    )

    config = ProductionEnsembleConfig(
        model_names=["rf", "gbdt"],
        voting="soft",
        weights=[1.0, 1.5],  # GBDT weighted slightly higher
    )
    model = ProductionEnsemble(config)
    model.fit(X_train, y_train)

    accuracy = model.score(X_test, y_test)
    print(f"\n  Production Ensemble Accuracy: {accuracy:.4f}")
    print(f"  Models used: {list(model.models.keys())}")
    print(f"  Voting method: {config.voting}")
    print(f"  Weights: {config.weights}")


# ===========================================================================
# 10. BONUS — Manual AdaBoost from scratch (educational)
# ===========================================================================

class ManualAdaBoost:
    """
    Minimal AdaBoost.SAMME implementation from scratch.

    Follows the mathematical formulation from the document:
      1. Initialize uniform sample weights.
      2. For each round:
         a. Fit a weak learner on weighted samples.
         b. Compute weighted error eps_t.
         c. Compute learner weight alpha_t = 0.5 * ln((1-eps)/eps).
         d. Update sample weights: w *= exp(-alpha * y * h(x)).
         e. Normalize weights.
      3. Final prediction: sign( sum_t alpha_t * h_t(x) ).
    """

    def __init__(self, n_estimators: int = 50, random_state: int = 42) -> None:
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.alphas: list[float] = []
        self.stumps: list[Any] = []
        self.classes_: NDArray[Any] | None = None

    def fit(self, X: NDArray[Any], y: NDArray[Any]) -> "ManualAdaBoost":
        from sklearn.tree import DecisionTreeClassifier

        self.classes_ = np.unique(y)
        n_samples: int = X.shape[0]
        weights = np.ones(n_samples) / n_samples
        rng = np.random.RandomState(self.random_state)

        for _ in range(self.n_estimators):
            stump = DecisionTreeClassifier(max_depth=1)
            stump.fit(X, y, sample_weight=weights)
            preds = stump.predict(X)

            misclassified = preds != y
            eps: float = np.dot(weights, misclassified)
            eps = np.clip(eps, 1e-10, 1 - 1e-10)  # avoid log(0)

            alpha: float = 0.5 * np.log((1 - eps) / eps)

            weights *= np.exp(-alpha * y * preds * np.sign(y))
            weights /= weights.sum()

            self.alphas.append(alpha)
            self.stumps.append(stump)

        return self

    def predict(self, X: NDArray[Any]) -> NDArray[Any]:
        # Weighted vote
        votes = sum(
            alpha * stump.predict(X)
            for alpha, stump in zip(self.alphas, self.stumps)
        )
        return np.sign(votes).astype(int)


def demo_manual_adaboost() -> None:
    """Run the from-scratch AdaBoost on a toy dataset."""
    from sklearn.datasets import make_classification
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split

    print("=" * 70)
    print("10. MANUAL ADABOOST FROM SCRATCH")
    print("=" * 70)

    X, y = make_classification(
        n_samples=500, n_features=10, n_informative=5, random_state=42
    )
    y = np.where(y == 0, -1, 1)  # convert to {-1, +1}
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = ManualAdaBoost(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)
    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"\n  Manual AdaBoost accuracy: {acc:.4f}")
    print(f"  Number of stumps: {len(model.stumps)}")


# ===========================================================================
# MAIN
# ===========================================================================

def main() -> None:
    """Run all ensemble learning demonstrations."""
    warnings.filterwarnings("ignore", category=FutureWarning)

    demos: list[tuple[str, Any]] = [
        ("Bagging", demo_bagging),
        ("AdaBoost", demo_adaboost),
        ("GradientBoosting", demo_gradient_boosting),
        ("XGBoost", demo_xgboost),
        ("LightGBM", demo_lightgbm),
        ("Stacking", demo_stacking),
        ("C++ Comparison", demo_cpp_comparison),
        ("Competition Stacking", demo_enterprise_competition_stacking),
        ("Production Ensemble", demo_production_ensemble),
        ("Manual AdaBoost", demo_manual_adaboost),
    ]

    for title, func in demos:
        try:
            func()
        except Exception as exc:
            print(f"\n[ERROR in {title}] {exc}")
        print()  # blank line separator


if __name__ == "__main__":
    main()
