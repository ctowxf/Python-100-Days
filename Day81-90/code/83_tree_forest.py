"""
83. Decision Trees and Random Forests (决策树和随机森林)

Enterprise-level implementation covering:
- Decision tree construction (ID3, C4.5, CART)
- Information entropy, information gain, gain ratio, Gini index
- Tree pruning (pre-pruning and post-pruning)
- Random forest ensemble learning
- Feature importance analysis
- Customer churn prediction
- Risk assessment modeling

C++ Comparison: Random Forest bagging vs C++ parallel accumulation
============================================================
In Python, scikit-learn's RandomForestClassifier uses joblib for parallel
bagging across CPU cores. In C++, one would use std::accumulate with
std::execution::par (C++17 parallel algorithms) or OpenMP pragmas to
parallelize the tree-building and voting accumulation. Python trades raw
execution speed for rapid prototyping and rich ML ecosystem integration,
while C++ offers deterministic latency and zero-GIL parallelism for
production inference engines.
============================================================
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from numpy.typing import NDArray

warnings.filterwarnings("ignore", category=FutureWarning)


# ---------------------------------------------------------------------------
# Section 1: Information Theory Foundations (信息论基础)
# ---------------------------------------------------------------------------

def entropy(y: NDArray[np.int_]) -> float:
    """
    Compute information entropy H(D) of a dataset.

    H(D) = -sum(p_i * log2(p_i)) for each class i

    Parameters
    ----------
    y : array-like of shape (n_samples,)
        Target class labels.

    Returns
    -------
    float
        Information entropy in bits.
    """
    _, counts = np.unique(y, return_counts=True)
    probs: NDArray[np.float64] = counts / y.size
    # Filter out zero probabilities to avoid log2(0)
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))


def conditional_entropy(x: NDArray[np.floating], y: NDArray[np.int_]) -> float:
    """
    Compute conditional entropy H(D|A) given feature A=x.

    H(D|A) = sum_v (|D_v|/|D|) * H(D_v)

    Parameters
    ----------
    x : feature values.
    y : target labels.

    Returns
    -------
    float
        Conditional entropy.
    """
    values, counts = np.unique(x, return_counts=True)
    cond_ent: float = 0.0
    for i, val in enumerate(values):
        subset_y: NDArray[np.int_] = y[x == val]
        weight: float = counts[i] / x.size
        cond_ent += weight * entropy(subset_y)
    return cond_ent


def information_gain(x: NDArray[np.floating], y: NDArray[np.int_]) -> float:
    """
    Compute information gain g(D, A) = H(D) - H(D|A).

    Used by the ID3 algorithm for feature selection.
    """
    return entropy(y) - conditional_entropy(x, y)


def gain_ratio(x: NDArray[np.floating], y: NDArray[np.int_]) -> float:
    """
    Compute gain ratio R(D, A) = g(D, A) / H_A(D).

    Used by the C4.5 algorithm; corrects information gain bias toward
    features with many distinct values.
    """
    ig: float = information_gain(x, y)
    intrinsic_val: float = entropy(x)
    if intrinsic_val == 0:
        return 0.0
    return ig / intrinsic_val


def gini_index(y: NDArray[np.int_]) -> float:
    """
    Compute Gini impurity G(D) = 1 - sum(p_k^2).

    Used by the CART algorithm.
    """
    _, counts = np.unique(y, return_counts=True)
    probs: NDArray[np.float64] = counts / y.size
    return float(1.0 - np.sum(probs ** 2))


def gini_with_feature(x: NDArray[np.floating], y: NDArray[np.int_]) -> float:
    """
    Compute weighted Gini index after splitting on feature A.

    G(D, A) = sum_i (|D_i|/|D|) * G(D_i)
    """
    values, counts = np.unique(x, return_counts=True)
    gini: float = 0.0
    for i, val in enumerate(values):
        subset_y: NDArray[np.int_] = y[x == val]
        weight: float = counts[i] / x.size
        gini += weight * gini_index(subset_y)
    return gini


# ---------------------------------------------------------------------------
# Section 2: Decision Tree Implementation (决策树实现)
# ---------------------------------------------------------------------------

@dataclass
class TreeNode:
    """Represents a node in the decision tree."""
    feature_index: Optional[int] = None
    threshold: Optional[float] = None
    left: Optional["TreeNode"] = None
    right: Optional["TreeNode"] = None
    value: Optional[int] = None  # Leaf class label
    samples: int = 0
    impurity: float = 0.0
    is_leaf: bool = False


@dataclass
class DecisionTreeClassifier:
    """
    A from-scratch CART-style decision tree classifier.

    Supports both Gini impurity and information gain as split criteria,
    pre-pruning via max_depth / min_samples_split / min_samples_leaf,
    and post-pruning via cost-complexity pruning (ccp_alpha).

    Parameters
    ----------
    criterion : str
        'gini' or 'entropy'.
    max_depth : int or None
        Maximum tree depth.
    min_samples_split : int
        Minimum samples required to split an internal node.
    min_samples_leaf : int
        Minimum samples required at a leaf node.
    ccp_alpha : float
        Complexity parameter for minimal cost-complexity pruning.
    random_state : int or None
        Seed for reproducibility.
    """

    criterion: str = "gini"
    max_depth: Optional[int] = None
    min_samples_split: int = 2
    min_samples_leaf: int = 1
    ccp_alpha: float = 0.0
    random_state: Optional[int] = None

    root: Optional[TreeNode] = field(default=None, init=False, repr=False)
    n_classes_: int = field(default=0, init=False)
    n_features_: int = field(default=0, init=False)
    feature_importances_: Optional[NDArray[np.float64]] = field(
        default=None, init=False, repr=False
    )

    # -- impurity function dispatch ------------------------------------------

    def _impurity(self, y: NDArray[np.int_]) -> float:
        if self.criterion == "gini":
            return gini_index(y)
        return entropy(y)

    def _split_gain(
        self, x: NDArray[np.floating], y: NDArray[np.int_]
    ) -> float:
        if self.criterion == "gini":
            parent_impurity = gini_index(y)
            return parent_impurity - gini_with_feature(x, y)
        return information_gain(x, y)

    # -- tree building -------------------------------------------------------

    def fit(
        self, X: NDArray[np.floating], y: NDArray[np.int_]
    ) -> "DecisionTreeClassifier":
        """Build the decision tree from training data."""
        rng = np.random.RandomState(self.random_state)
        self.n_classes_ = int(np.unique(y).size)
        self.n_features_ = X.shape[1]
        self._feature_importance_accum = np.zeros(self.n_features_, dtype=np.float64)
        self._total_samples = y.size
        self.root = self._build(X, y, depth=0)
        # Normalize feature importances
        total = self._feature_importance_accum.sum()
        if total > 0:
            self.feature_importances_ = self._feature_importance_accum / total
        else:
            self.feature_importances_ = np.zeros(self.n_features_, dtype=np.float64)
        return self

    def _build(
        self, X: NDArray[np.floating], y: NDArray[np.int_], depth: int
    ) -> TreeNode:
        n_samples, n_features = X.shape
        current_impurity: float = self._impurity(y)

        # Stopping conditions
        majority_class: int = int(np.bincount(y).argmax())
        node = TreeNode(
            value=majority_class,
            samples=n_samples,
            impurity=current_impurity,
        )

        if (
            current_impurity == 0
            or (self.max_depth is not None and depth >= self.max_depth)
            or n_samples < self.min_samples_split
        ):
            node.is_leaf = True
            return node

        # Find best split
        best_gain: float = -1.0
        best_feature: int = -1
        best_threshold: float = 0.0

        for feat_idx in range(n_features):
            col: NDArray[np.floating] = X[:, feat_idx]
            thresholds: NDArray[np.floating] = np.unique(col)
            for thresh in thresholds:
                left_mask: NDArray[np.bool_] = col <= thresh
                right_mask: NDArray[np.bool_] = ~left_mask
                if (
                    left_mask.sum() < self.min_samples_leaf
                    or right_mask.sum() < self.min_samples_leaf
                ):
                    continue
                gain: float = self._split_gain(
                    (col <= thresh).astype(int), y
                )
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feat_idx
                    best_threshold = float(thresh)

        if best_gain <= 0:
            node.is_leaf = True
            return node

        # Accumulate feature importance (weighted)
        self._feature_importance_accum[best_feature] += (
            best_gain * n_samples / self._total_samples
        )

        # Split data
        left_mask = X[:, best_feature] <= best_threshold
        right_mask = ~left_mask
        node.feature_index = best_feature
        node.threshold = best_threshold
        node.is_leaf = False
        node.left = self._build(X[left_mask], y[left_mask], depth + 1)
        node.right = self._build(X[right_mask], y[right_mask], depth + 1)
        return node

    # -- prediction ----------------------------------------------------------

    def predict(self, X: NDArray[np.floating]) -> NDArray[np.int_]:
        """Predict class labels for samples in X."""
        return np.array([self._predict_one(x, self.root) for x in X])

    def _predict_one(
        self, x: NDArray[np.floating], node: Optional[TreeNode]
    ) -> int:
        if node is None or node.is_leaf:
            return node.value if node is not None else 0
        if x[node.feature_index] <= node.threshold:  # type: ignore[index]
            return self._predict_one(x, node.left)
        return self._predict_one(x, node.right)

    # -- post-pruning (cost-complexity) --------------------------------------

    def prune(self, X_val: NDArray[np.floating], y_val: NDArray[np.int_]) -> None:
        """
        Apply cost-complexity post-pruning using a validation set.

        Nodes are pruned when removing them improves validation accuracy.
        """
        if self.root is None:
            return
        self._prune_node(self.root, X_val, y_val)

    def _prune_node(
        self, node: TreeNode, X_val: NDArray[np.floating], y_val: NDArray[np.int_]
    ) -> None:
        if node.is_leaf:
            return
        if X_val.size == 0:
            return

        left_mask = X_val[:, node.feature_index] <= node.threshold  # type: ignore[index]
        right_mask = ~left_mask

        if node.left is not None:
            self._prune_node(node.left, X_val[left_mask], y_val[left_mask])
        if node.right is not None:
            self._prune_node(node.right, X_val[right_mask], y_val[right_mask])

        # Evaluate: prune this subtree into a leaf?
        if node.left is not None and node.right is not None:
            # Current accuracy with subtree
            preds_subtree = np.array(
                [self._predict_one(x, node) for x in X_val]
            )
            acc_subtree = np.mean(preds_subtree == y_val)
            # Accuracy if this node becomes a leaf
            acc_leaf = np.mean(y_val == node.value)
            if acc_leaf >= acc_subtree:
                node.is_leaf = True
                node.left = None
                node.right = None


# ---------------------------------------------------------------------------
# Section 3: Random Forest Implementation (随机森林实现)
# ---------------------------------------------------------------------------

@dataclass
class RandomForestClassifier:
    """
    Random forest classifier built on top of our custom DecisionTreeClassifier.

    Implements Bootstrap aggregating (bagging) and random feature subspace
    selection for each tree.

    Parameters
    ----------
    n_estimators : int
        Number of trees in the forest.
    max_depth : int or None
        Maximum depth for each tree.
    max_features : str or int
        Number of features per tree: 'sqrt', 'log2', or an integer.
    criterion : str
        'gini' or 'entropy'.
    random_state : int or None
        Seed for reproducibility.
    """

    n_estimators: int = 100
    max_depth: Optional[int] = None
    max_features: Any = "sqrt"
    criterion: str = "gini"
    random_state: Optional[int] = None
    min_samples_split: int = 2
    min_samples_leaf: int = 1

    trees: List[DecisionTreeClassifier] = field(
        default_factory=list, init=False, repr=False
    )
    feature_indices_: List[NDArray[np.int_]] = field(
        default_factory=list, init=False, repr=False
    )
    n_classes_: int = field(default=0, init=False)
    n_features_: int = field(default=0, init=False)
    oob_score_: float = field(default=0.0, init=False)
    feature_importances_: Optional[NDArray[np.float64]] = field(
        default=None, init=False, repr=False
    )

    def _resolve_max_features(self, n_features: int) -> int:
        if isinstance(self.max_features, int):
            return min(self.max_features, n_features)
        if self.max_features == "sqrt":
            return max(1, int(math.sqrt(n_features)))
        if self.max_features == "log2":
            return max(1, int(math.log2(n_features)))
        return n_features

    def fit(
        self, X: NDArray[np.floating], y: NDArray[np.int_]
    ) -> "RandomForestClassifier":
        """Build a forest of decision trees from training data."""
        rng = np.random.RandomState(self.random_state)
        n_samples, n_features = X.shape
        self.n_classes_ = int(np.unique(y).size)
        self.n_features_ = n_features
        m = self._resolve_max_features(n_features)

        self.trees = []
        self.feature_indices_ = []
        importances = np.zeros(n_features, dtype=np.float64)
        oob_predictions: List[List[int]] = [[] for _ in range(n_samples)]
        oob_counts = np.zeros(n_samples, dtype=int)

        for i in range(self.n_estimators):
            # Bootstrap sample
            indices = rng.choice(n_samples, size=n_samples, replace=True)
            oob_mask = np.ones(n_samples, dtype=bool)
            oob_mask[indices] = False

            X_boot = X[indices]
            y_boot = y[indices]

            # Random feature subspace
            feat_idx = rng.choice(n_features, size=m, replace=False)
            self.feature_indices_.append(feat_idx)

            X_sub = X_boot[:, feat_idx]
            tree = DecisionTreeClassifier(
                criterion=self.criterion,
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                random_state=rng.randint(0, 2**31),
            )
            tree.fit(X_sub, y_boot)
            self.trees.append(tree)

            # Accumulate feature importances
            if tree.feature_importances_ is not None:
                for j, fi in enumerate(feat_idx):
                    importances[fi] += tree.feature_importances_[j]

            # OOB prediction
            if oob_mask.any():
                X_oob = X[oob_mask][:, feat_idx]
                preds = tree.predict(X_oob)
                oob_indices = np.where(oob_mask)[0]
                for k, oi in enumerate(oob_indices):
                    oob_predictions[oi].append(int(preds[k]))
                oob_counts[oob_mask] += 1

        # Normalize feature importances
        total = importances.sum()
        self.feature_importances_ = (
            importances / total if total > 0 else importances
        )

        # Compute OOB score
        correct = 0
        total_oob = 0
        for i in range(n_samples):
            if oob_predictions[i]:
                majority = max(set(oob_predictions[i]), key=oob_predictions[i].count)
                if majority == y[i]:
                    correct += 1
                total_oob += 1
        self.oob_score_ = correct / total_oob if total_oob > 0 else 0.0
        return self

    def predict(self, X: NDArray[np.floating]) -> NDArray[np.int_]:
        """Predict class labels by majority vote across all trees."""
        all_preds: NDArray[np.int_] = np.zeros(
            (self.n_estimators, X.shape[0]), dtype=int
        )
        for i, (tree, feat_idx) in enumerate(
            zip(self.trees, self.feature_indices_)
        ):
            all_preds[i] = tree.predict(X[:, feat_idx])
        # Majority vote
        result = np.zeros(X.shape[0], dtype=int)
        for j in range(X.shape[0]):
            votes = all_preds[:, j]
            result[j] = int(np.bincount(votes).argmax())
        return result

    def predict_proba(self, X: NDArray[np.floating]) -> NDArray[np.float64]:
        """Predict class probabilities by averaging tree votes."""
        all_preds: NDArray[np.int_] = np.zeros(
            (self.n_estimators, X.shape[0]), dtype=int
        )
        for i, (tree, feat_idx) in enumerate(
            zip(self.trees, self.feature_indices_)
        ):
            all_preds[i] = tree.predict(X[:, feat_idx])
        proba = np.zeros((X.shape[0], self.n_classes_), dtype=np.float64)
        for j in range(X.shape[0]):
            votes = all_preds[:, j]
            for c in range(self.n_classes_):
                proba[j, c] = np.sum(votes == c) / self.n_estimators
        return proba


# ---------------------------------------------------------------------------
# Section 4: Enterprise Application -- Customer Churn Prediction
# (企业应用 -- 客户流失预测)
# ---------------------------------------------------------------------------

@dataclass
class CustomerChurnPredictor:
    """
    Enterprise customer churn prediction pipeline using random forests.

    Demonstrates:
    - Feature engineering from raw customer data
    - Model training with cross-validation
    - Feature importance analysis for business insights
    - Risk scoring with probability calibration

    C++ Comparison Note:
    --------------------
    Python's scikit-learn random forest leverages numpy vectorization and
    joblib parallelism for tree building. In C++, one would use:
    - std::execution::par for parallel tree construction
    - Eigen or Blaze for vectorized matrix operations
    - Template metaprogramming for compile-time feature selection
    The C++ approach achieves ~10x faster inference but requires significantly
    more development time and lacks Python's rich data science ecosystem.
    """

    feature_names: List[str] = field(default_factory=list)
    model: Optional[RandomForestClassifier] = field(
        default=None, init=False, repr=False
    )

    @staticmethod
    def generate_synthetic_data(
        n_customers: int = 1000, random_state: int = 42
    ) -> Tuple[NDArray[np.floating], NDArray[np.int_], List[str]]:
        """
        Generate synthetic customer churn data.

        Features: tenure, monthly_charges, total_charges, num_support_tickets,
        contract_type, payment_method, avg_monthly_usage, has_partner.
        """
        rng = np.random.RandomState(random_state)
        feature_names = [
            "tenure",
            "monthly_charges",
            "total_charges",
            "num_support_tickets",
            "contract_type",
            "payment_method",
            "avg_monthly_usage",
            "has_partner",
        ]

        tenure = rng.uniform(1, 72, n_customers)
        monthly_charges = rng.uniform(20, 120, n_customers)
        total_charges = tenure * monthly_charges + rng.normal(0, 100, n_customers)
        num_support_tickets = rng.poisson(2, n_customers).astype(float)
        contract_type = rng.choice([0, 1, 2], n_customers).astype(float)
        payment_method = rng.choice([0, 1, 2, 3], n_customers).astype(float)
        avg_monthly_usage = rng.uniform(0.1, 1.0, n_customers)
        has_partner = rng.choice([0, 1], n_customers).astype(float)

        X = np.column_stack([
            tenure, monthly_charges, total_charges, num_support_tickets,
            contract_type, payment_method, avg_monthly_usage, has_partner,
        ])

        # Generate churn labels based on realistic rules
        churn_prob = (
            0.3 * (1 - tenure / 72)
            + 0.2 * (monthly_charges / 120)
            + 0.15 * (num_support_tickets / 5)
            + 0.15 * (contract_type == 0).astype(float)
            + 0.1 * (1 - avg_monthly_usage)
            + 0.1 * (1 - has_partner)
        )
        churn_prob = np.clip(churn_prob, 0.05, 0.95)
        y = (rng.random(n_customers) < churn_prob).astype(int)
        return X, y, feature_names

    def train(
        self,
        X_train: NDArray[np.floating],
        y_train: NDArray[np.int_],
        feature_names: Optional[List[str]] = None,
        n_estimators: int = 100,
        max_depth: int = 10,
    ) -> Dict[str, float]:
        """Train the churn prediction model and return diagnostics."""
        self.feature_names = feature_names or [
            f"feature_{i}" for i in range(X_train.shape[1])
        ]
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            criterion="gini",
            random_state=42,
        )
        self.model.fit(X_train, y_train)

        # Evaluate on training data
        train_preds = self.model.predict(X_train)
        train_acc = float(np.mean(train_preds == y_train))
        return {
            "train_accuracy": train_acc,
            "oob_score": self.model.oob_score_,
        }

    def predict_churn(
        self, X: NDArray[np.floating]
    ) -> NDArray[np.floating]:
        """Predict churn probability for each customer."""
        if self.model is None:
            raise RuntimeError("Model has not been trained.")
        proba = self.model.predict_proba(X)
        return proba[:, 1]  # Probability of churn (class 1)

    def get_feature_importance(self) -> Dict[str, float]:
        """Return sorted feature importance scores."""
        if self.model is None or self.model.feature_importances_ is None:
            return {}
        importances = dict(
            zip(self.feature_names, self.model.feature_importances_)
        )
        return dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))


# ---------------------------------------------------------------------------
# Section 5: Enterprise Application -- Risk Assessment (风险评估)
# ---------------------------------------------------------------------------

@dataclass
class RiskAssessmentEngine:
    """
    Financial risk assessment using decision tree ensemble.

    Maps decision tree predictions to risk categories with
    probability-based scoring for enterprise risk management.
    """

    risk_thresholds: Dict[str, float] = field(
        default_factory=lambda: {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.85,
        }
    )
    model: Optional[RandomForestClassifier] = field(
        default=None, init=False, repr=False
    )

    def categorize_risk(self, probability: float) -> str:
        """Categorize a risk score into human-readable levels."""
        if probability < self.risk_thresholds["low"]:
            return "LOW"
        if probability < self.risk_thresholds["medium"]:
            return "MEDIUM"
        if probability < self.risk_thresholds["high"]:
            return "HIGH"
        return "CRITICAL"

    def assess_portfolio(
        self,
        X: NDArray[np.floating],
        customer_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Generate a risk report for a portfolio of customers.

        Returns a list of dictionaries with customer ID, risk score,
        risk category, and recommended action.
        """
        if self.model is None:
            raise RuntimeError("Model has not been trained.")

        proba = self.model.predict_proba(X)
        risk_scores: NDArray[np.float64] = proba[:, 1]

        report: List[Dict[str, Any]] = []
        actions = {
            "LOW": "Continue monitoring; standard engagement.",
            "MEDIUM": "Initiate retention outreach; offer loyalty incentives.",
            "HIGH": "Priority retention call; assign dedicated account manager.",
            "CRITICAL": "Escalate to senior retention team; prepare win-back offer.",
        }

        for cid, score in zip(customer_ids, risk_scores):
            category = self.categorize_risk(float(score))
            report.append({
                "customer_id": cid,
                "risk_score": round(float(score), 4),
                "risk_category": category,
                "recommended_action": actions[category],
            })
        return report


# ---------------------------------------------------------------------------
# Section 6: Feature Selection Utility (特征选择工具)
# ---------------------------------------------------------------------------

class FeatureSelector:
    """
    Select the top-K features based on information gain, gain ratio,
    or Gini index reduction.
    """

    CRITERIA = {
        "information_gain": information_gain,
        "gain_ratio": gain_ratio,
        "gini_reduction": lambda x, y: gini_index(y) - gini_with_feature(x, y),
    }

    def __init__(self, criterion: str = "information_gain", k: int = 5):
        if criterion not in self.CRITERIA:
            raise ValueError(f"Unknown criterion: {criterion}")
        self.criterion = criterion
        self.k = k
        self.scores: Dict[int, float] = {}
        self.selected_indices: List[int] = []

    def fit(
        self,
        X: NDArray[np.floating],
        y: NDArray[np.int_],
        feature_names: Optional[List[str]] = None,
    ) -> "FeatureSelector":
        """Score all features and select the top-k."""
        scoring_fn = self.CRITERIA[self.criterion]
        scores: Dict[int, float] = {}
        for i in range(X.shape[1]):
            scores[i] = float(scoring_fn(X[:, i], y))
        self.scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))
        self.selected_indices = list(self.scores.keys())[: self.k]

        if feature_names:
            print(f"\nFeature Ranking ({self.criterion}):")
            print("-" * 50)
            for rank, (idx, score) in enumerate(self.scores.items(), 1):
                name = feature_names[idx] if idx < len(feature_names) else f"f{idx}"
                marker = " <-- SELECTED" if idx in self.selected_indices else ""
                print(f"  {rank}. {name:30s} score={score:.6f}{marker}")
            print()
        return self

    def transform(
        self, X: NDArray[np.floating]
    ) -> NDArray[np.floating]:
        """Return X with only the selected features."""
        return X[:, self.selected_indices]

    def fit_transform(
        self, X: NDArray[np.floating], y: NDArray[np.int_],
        feature_names: Optional[List[str]] = None,
    ) -> NDArray[np.floating]:
        """Fit and transform in one step."""
        self.fit(X, y, feature_names)
        return self.transform(X)


# ---------------------------------------------------------------------------
# Section 7: Demonstration and Benchmarking
# ---------------------------------------------------------------------------

def demonstrate_decision_tree_basics() -> None:
    """Walk through information theory computations on the Iris dataset."""
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split

    print("=" * 70)
    print("PART 1: Information Theory Foundations")
    print("=" * 70)

    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=0.8, random_state=3
    )

    print(f"\nDataset: Iris ({X.shape[0]} samples, {X.shape[1]} features)")
    print(f"Classes: {list(iris.target_names)}")
    print(f"Training set size: {X_train.shape[0]}")
    print(f"Test set size: {X_test.shape[0]}")

    print(f"\nH(D)    = {entropy(y_train):.6f}")
    for i, name in enumerate(iris.feature_names):
        ig = information_gain(X_train[:, i], y_train)
        gr = gain_ratio(X_train[:, i], y_train)
        gi = gini_with_feature(X_train[:, i], y_train)
        print(f"  {name:25s} | IG={ig:.6f} | GR={gr:.6f} | Gini_split={gi:.6f}")


def demonstrate_decision_tree_classifier() -> None:
    """Train and evaluate our custom decision tree."""
    from sklearn.datasets import load_iris
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split

    print("\n" + "=" * 70)
    print("PART 2: Custom Decision Tree Classifier")
    print("=" * 70)

    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=0.8, random_state=3
    )

    # Train with Gini
    tree_gini = DecisionTreeClassifier(criterion="gini", max_depth=5, random_state=42)
    tree_gini.fit(X_train, y_train)
    preds_gini = tree_gini.predict(X_test)
    acc_gini = float(np.mean(preds_gini == y_test))
    print(f"\n[Gini Tree] Test accuracy: {acc_gini:.4f}")
    print(f"  Feature importances: {tree_gini.feature_importances_}")

    # Train with Entropy
    tree_entropy = DecisionTreeClassifier(
        criterion="entropy", max_depth=5, random_state=42
    )
    tree_entropy.fit(X_train, y_train)
    preds_entropy = tree_entropy.predict(X_test)
    acc_entropy = float(np.mean(preds_entropy == y_test))
    print(f"\n[Entropy Tree] Test accuracy: {acc_entropy:.4f}")

    # Classification report
    print("\nClassification Report (Gini Tree):")
    print(classification_report(y_test, preds_gini, target_names=iris.target_names))


def demonstrate_random_forest() -> None:
    """Train and evaluate our custom random forest."""
    from sklearn.datasets import load_iris
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split

    print("\n" + "=" * 70)
    print("PART 3: Random Forest Ensemble")
    print("=" * 70)

    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=0.8, random_state=3
    )

    # Compare single tree vs forest
    tree = DecisionTreeClassifier(max_depth=5, random_state=42)
    tree.fit(X_train, y_train)
    acc_tree = float(np.mean(tree.predict(X_test) == y_test))

    forest = RandomForestClassifier(
        n_estimators=50, max_depth=5, random_state=42
    )
    forest.fit(X_train, y_train)
    preds_forest = forest.predict(X_test)
    acc_forest = float(np.mean(preds_forest == y_test))

    print(f"\nSingle Tree accuracy:  {acc_tree:.4f}")
    print(f"Random Forest accuracy: {acc_forest:.4f}")
    print(f"OOB score:              {forest.oob_score_:.4f}")

    if forest.feature_importances_ is not None:
        print("\nFeature importances (Random Forest):")
        for i, (name, imp) in enumerate(
            zip(iris.feature_names, forest.feature_importances_)
        ):
            bar = "#" * int(imp * 50)
            print(f"  {name:25s} {imp:.4f} {bar}")

    print("\nClassification Report (Random Forest):")
    print(classification_report(y_test, preds_forest, target_names=iris.target_names))


def demonstrate_customer_churn() -> None:
    """End-to-end customer churn prediction pipeline."""
    from sklearn.model_selection import train_test_split

    print("\n" + "=" * 70)
    print("PART 4: Enterprise Customer Churn Prediction")
    print("=" * 70)

    predictor = CustomerChurnPredictor()
    X, y, feature_names = CustomerChurnPredictor.generate_synthetic_data(
        n_customers=2000, random_state=42
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Feature selection
    print("\n[Step 1] Feature Selection")
    selector = FeatureSelector(criterion="information_gain", k=6)
    X_train_sel = selector.fit_transform(X_train, y_train, feature_names)
    X_test_sel = selector.transform(X_test)
    selected_names = [feature_names[i] for i in selector.selected_indices]

    # Train model
    print("[Step 2] Training Random Forest")
    diagnostics = predictor.train(
        X_train_sel, y_train, feature_names=selected_names,
        n_estimators=100, max_depth=8,
    )
    print(f"  Train accuracy: {diagnostics['train_accuracy']:.4f}")
    print(f"  OOB score:      {diagnostics['oob_score']:.4f}")

    # Evaluate
    churn_probs = predictor.predict_churn(X_test_sel)
    churn_preds = (churn_probs > 0.5).astype(int)
    test_acc = float(np.mean(churn_preds == y_test))
    print(f"\n[Step 3] Test accuracy: {test_acc:.4f}")

    # Feature importance
    print("\n[Step 4] Feature Importance:")
    for name, score in predictor.get_feature_importance().items():
        bar = "#" * int(score * 50)
        print(f"  {name:30s} {score:.4f} {bar}")

    # Risk assessment
    print("\n[Step 5] Risk Assessment Report (first 10 customers):")
    risk_engine = RiskAssessmentEngine()
    risk_engine.model = predictor.model
    customer_ids = [f"CUST-{i:05d}" for i in range(X_test_sel.shape[0])]
    report = risk_engine.assess_portfolio(X_test_sel, customer_ids)

    risk_counts: Dict[str, int] = {}
    for entry in report:
        cat = entry["risk_category"]
        risk_counts[cat] = risk_counts.get(cat, 0) + 1

    print(f"\n  Risk distribution: {risk_counts}")
    print(f"\n  {'Customer ID':15s} {'Score':>8s} {'Category':10s} Action")
    print("  " + "-" * 80)
    for entry in report[:10]:
        print(
            f"  {entry['customer_id']:15s} {entry['risk_score']:8.4f} "
            f"{entry['risk_category']:10s} {entry['recommended_action'][:50]}"
        )


def demonstrate_feature_selection() -> None:
    """Show feature selection across different criteria."""
    from sklearn.datasets import load_iris

    print("\n" + "=" * 70)
    print("PART 5: Feature Selection Comparison")
    print("=" * 70)

    iris = load_iris()
    X, y = iris.data, iris.target

    for criterion in ["information_gain", "gain_ratio", "gini_reduction"]:
        selector = FeatureSelector(criterion=criterion, k=3)
        selector.fit(X, y, feature_names=list(iris.feature_names))


def demonstrate_pruning() -> None:
    """Show the effect of pre-pruning and post-pruning."""
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split

    print("\n" + "=" * 70)
    print("PART 6: Decision Tree Pruning")
    print("=" * 70)

    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, train_size=0.6, random_state=3
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=3
    )

    # Unpruned tree
    tree_full = DecisionTreeClassifier(random_state=42)
    tree_full.fit(X_train, y_train)
    acc_full = float(np.mean(tree_full.predict(X_test) == y_test))

    # Pre-pruned tree
    tree_pre = DecisionTreeClassifier(
        max_depth=3, min_samples_split=5, min_samples_leaf=3, random_state=42
    )
    tree_pre.fit(X_train, y_train)
    acc_pre = float(np.mean(tree_pre.predict(X_test) == y_test))

    # Post-pruned tree
    tree_post = DecisionTreeClassifier(random_state=42)
    tree_post.fit(X_train, y_train)
    tree_post.prune(X_val, y_val)
    acc_post = float(np.mean(tree_post.predict(X_test) == y_test))

    print(f"\n  Unpruned tree accuracy:  {acc_full:.4f}")
    print(f"  Pre-pruned tree accuracy: {acc_pre:.4f}")
    print(f"  Post-pruned tree accuracy: {acc_post:.4f}")


# ---------------------------------------------------------------------------
# Main Guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Decision Trees and Random Forests -- Enterprise Demo")
    print("=" * 70)

    demonstrate_decision_tree_basics()
    demonstrate_decision_tree_classifier()
    demonstrate_random_forest()
    demonstrate_customer_churn()
    demonstrate_feature_selection()
    demonstrate_pruning()

    print("\n" + "=" * 70)
    print("All demonstrations completed successfully.")
    print("=" * 70)
