"""
Day 82 - k-Nearest Neighbors (kNN) Algorithm
==============================================
Comprehensive demonstration of KNN covering:
  1. Distance metrics (Euclidean, Manhattan, Chebyshev, Minkowski, Cosine)
  2. Manual KNN implementation from scratch (NumPy + SciPy)
  3. sklearn KNeighborsClassifier with cross-validation & grid search
  4. KNN regression with KNeighborsRegressor
  5. Model evaluation (confusion matrix, classification report, ROC/AUC)
  6. C++ analogy: brute-force search vs KD-tree (std::priority_queue)
  7. Enterprise examples:
     - Recommendation system (user-based collaborative filtering)
     - Anomaly detection (distance-based outlier scoring)
     - Multi-class classification on the Iris dataset

Requirements:
    pip install numpy scipy scikit-learn matplotlib
"""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence

import numpy as np
from numpy.typing import NDArray
from scipy import stats
from sklearn.datasets import load_iris
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.preprocessing import StandardScaler


# ============================================================================
# 1. Distance Metrics
# ============================================================================

def minkowski_distance(
    u: NDArray[np.floating],
    v: NDArray[np.floating],
    p: float = 2.0,
) -> float:
    """Generalized Minkowski distance.

    Special cases:
        p=1  -> Manhattan (L1) distance
        p=2  -> Euclidean (L2) distance
        p->inf -> Chebyshev (L-inf) distance

    C++ analogy:
        In C++ you might compute this with a loop over std::valarray or
        Eigen::VectorXd.  The formula is the same; Python just broadcasts
        element-wise subtraction via NumPy.

    Parameters
    ----------
    u, v : 1-D arrays of the same length.
    p    : order of the norm (>= 1).

    Returns
    -------
    Scalar distance value.
    """
    if p < 1:
        raise ValueError("p must be >= 1 for a valid metric")
    diff = np.abs(u - v)
    if np.isinf(p):
        return float(np.max(diff))
    return float(np.sum(diff ** p) ** (1.0 / p))


def euclidean_distance(u: NDArray[np.floating], v: NDArray[np.floating]) -> float:
    """Euclidean (L2) distance -- the default for KNN."""
    return minkowski_distance(u, v, p=2)


def manhattan_distance(u: NDArray[np.floating], v: NDArray[np.floating]) -> float:
    """Manhattan (L1 / city-block) distance."""
    return minkowski_distance(u, v, p=1)


def chebyshev_distance(u: NDArray[np.floating], v: NDArray[np.floating]) -> float:
    """Chebyshev (L-inf) distance -- max absolute difference."""
    return minkowski_distance(u, v, p=np.inf)


def cosine_distance(u: NDArray[np.floating], v: NDArray[np.floating]) -> float:
    """Cosine distance = 1 - cosine_similarity.

    Useful when direction matters more than magnitude (e.g. text TF-IDF).
    """
    dot = np.dot(u, v)
    denom = np.linalg.norm(u) * np.linalg.norm(v)
    if denom == 0:
        return 1.0
    return 1.0 - dot / denom


def demonstrate_distance_metrics() -> None:
    """Print distances between two sample vectors under various metrics."""
    a = np.array([1.0, 2.0, 3.0])
    b = np.array([4.0, 6.0, 3.0])

    print("=" * 60)
    print("Distance Metrics Demo")
    print("=" * 60)
    print(f"  Vector a = {a}")
    print(f"  Vector b = {b}")
    print(f"  Euclidean  (p=2)  : {euclidean_distance(a, b):.4f}")
    print(f"  Manhattan  (p=1)  : {manhattan_distance(a, b):.4f}")
    print(f"  Chebyshev  (p=inf): {chebyshev_distance(a, b):.4f}")
    print(f"  Minkowski  (p=3)  : {minkowski_distance(a, b, p=3):.4f}")
    print(f"  Cosine            : {cosine_distance(a, b):.4f}")
    print()


# ============================================================================
# 2. Manual KNN Implementation (NumPy / SciPy)
# ============================================================================

class DistanceFunc(Protocol):
    """Protocol for distance callables used by the manual KNN."""
    def __call__(self, u: NDArray[np.floating], v: NDArray[np.floating]) -> float: ...


def knn_predict_single(
    X_train: NDArray[np.floating],
    y_train: NDArray[np.int_],
    x_new: NDArray[np.floating],
    k: int,
    dist_fn: DistanceFunc = euclidean_distance,
) -> int:
    """Predict the label for a single sample using KNN.

    Uses np.argpartition (analogous to C++ std::nth_element) to find the k
    smallest distances in O(n) average time instead of a full O(n log n) sort.

    C++ analogy:
        std::nth_element distances.begin(), distances.begin()+k, distances.end()
        selects the k-th smallest element in-place without fully sorting.
    """
    distances = np.array([dist_fn(x_new, x_i) for x_i in X_train])
    k_nearest_idx = np.argpartition(distances, k)[:k]
    k_nearest_labels = y_train[k_nearest_idx]
    mode_result = stats.mode(k_nearest_labels, keepdims=True)
    return int(mode_result.mode[0])


def knn_predict(
    X_train: NDArray[np.floating],
    y_train: NDArray[np.int_],
    X_new: NDArray[np.floating],
    k: int = 5,
    dist_fn: DistanceFunc = euclidean_distance,
) -> NDArray[np.int_]:
    """Predict labels for an array of samples using the manual KNN."""
    return np.array([
        knn_predict_single(X_train, y_train, x, k, dist_fn) for x in X_new
    ])


def demonstrate_manual_knn(
    X_train: NDArray[np.floating],
    X_test: NDArray[np.floating],
    y_train: NDArray[np.int_],
    y_test: NDArray[np.int_],
) -> NDArray[np.bool_]:
    """Run the hand-built KNN on the Iris split and print accuracy."""
    print("=" * 60)
    print("Manual KNN Implementation (NumPy + SciPy)")
    print("=" * 60)

    y_pred = knn_predict(X_train, y_train, X_test, k=5)
    correct = y_pred == y_test
    accuracy = np.mean(correct)
    print(f"  Predictions match test labels : {correct}")
    print(f"  Accuracy                      : {accuracy:.4f}")
    print()
    return correct


# ============================================================================
# 3. C++ Analogy: Brute-Force vs KD-Tree Search
# ============================================================================

@dataclass(order=True)
class DistanceItem:
    """Heap element for the brute-force KNN -- pairs distance with index.

    C++ analogy:
        struct Item { double dist; size_t idx; };
        std::priority_queue<Item, vector<Item>, greater<Item>> minHeap;
    """
    dist: float
    idx: int = field(compare=False)


def knn_brute_force(
    X_train: NDArray[np.floating],
    query: NDArray[np.floating],
    k: int,
) -> list[int]:
    """Brute-force KNN using a min-heap (priority queue).

    Time complexity: O(n * d + n log k)  where n=#samples, d=dimensions.

    C++ analogy:
        This mirrors a C++ implementation that pushes all distances onto a
        std::priority_queue<Item, vector<Item>, greater<Item>> (min-heap)
        and pops the k smallest.  In C++ you would write:

            std::priority_queue<Item, std::vector<Item>, std::greater<>> pq;
            for (size_t i = 0; i < n; ++i) {
                pq.push({euclidean(X_train[i], query), i});
            }
            for (int j = 0; j < k; ++j) {
                result.push_back(pq.top().idx);
                pq.pop();
            }

    Python's heapq module implements the same binary min-heap.
    """
    heap: list[DistanceItem] = []
    for i, train_row in enumerate(X_train):
        dist = euclidean_distance(train_row, query)
        heapq.heappush(heap, DistanceItem(dist=dist, idx=i))

    nearest: list[int] = []
    for _ in range(k):
        item = heapq.heappop(heap)
        nearest.append(item.idx)
    return nearest


def knn_kdtree_search(
    X_train: NDArray[np.floating],
    query: NDArray[np.floating],
    k: int,
) -> list[int]:
    """Simulated KD-tree search.

    A real KD-tree partitions space by cycling through dimensions at each
    level.  At query time it prunes branches whose bounding box is farther
    than the current k-th nearest distance.

    C++ analogy:
        In C++ one might implement a KD-tree with:
            struct KDNode {
                KDNode* left;
                KDNode* right;
                size_t point_idx;
                int split_dim;
            };
        Search uses a std::priority_queue to maintain the k nearest neighbors
        and prunes subtrees when the split-plane distance exceeds the worst
        neighbor.  Libraries like FLANN or nanoflann provide production-grade
        implementations.

    This simplified version uses sklearn's BallTree internally to show the
    same idea without writing the tree from scratch.
    """
    from sklearn.neighbors import BallTree

    tree = BallTree(X_train)
    dist, ind = tree.query(query.reshape(1, -1), k=k)
    return ind[0].tolist()


def demonstrate_brute_vs_kdtree(
    X_train: NDArray[np.floating],
    X_test: NDArray[np.floating],
) -> None:
    """Compare brute-force and KD-tree/BallTree neighbor search times."""
    print("=" * 60)
    print("Brute-Force vs KD-tree (C++ analogy: std::priority_queue)")
    print("=" * 60)

    query = X_test[0]
    k = 5

    t0 = time.perf_counter()
    bf_indices = knn_brute_force(X_train, query, k)
    t_bf = time.perf_counter() - t0

    t0 = time.perf_counter()
    kd_indices = knn_kdtree_search(X_train, query, k)
    t_kd = time.perf_counter() - t0

    print(f"  Query point          : {query}")
    print(f"  k                    : {k}")
    print(f"  Brute-force indices  : {bf_indices}  ({t_bf*1e6:.1f} us)")
    print(f"  BallTree   indices   : {kd_indices}  ({t_kd*1e6:.1f} us)")
    print()
    print("  C++ analogy:")
    print("    Brute-force uses std::priority_queue (min-heap) on all distances.")
    print("    KD-tree prunes branches -- like std::nth_element + bounding-box")
    print("    checks.  Libraries: FLANN, nanoflann, mlpack.")
    print()


# ============================================================================
# 4. sklearn KNeighborsClassifier + Cross-Validation + Grid Search
# ============================================================================

def demonstrate_sklearn_knn(
    X_train: NDArray[np.floating],
    X_test: NDArray[np.floating],
    y_train: NDArray[np.int_],
    y_test: NDArray[np.int_],
    feature_names: list[str],
    target_names: list[str],
) -> KNeighborsClassifier:
    """Train a sklearn KNN classifier, evaluate, then tune with GridSearchCV."""
    print("=" * 60)
    print("sklearn KNeighborsClassifier")
    print("=" * 60)

    # --- Basic model --------------------------------------------------------
    model = KNeighborsClassifier()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = model.score(X_test, y_test)

    print(f"  Default KNN accuracy on test set: {accuracy:.4f}")
    print(f"  Predictions == test labels      : {y_pred == y_test}")
    print()

    # --- Classification report & confusion matrix --------------------------
    print("  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=target_names))

    cm = confusion_matrix(y_test, y_pred)
    print("  Confusion Matrix:")
    print(cm)
    print()

    # --- Cross-validation on the full training set --------------------------
    cv_scores = cross_val_score(
        KNeighborsClassifier(), X_train, y_train, cv=5, scoring="accuracy"
    )
    print(f"  5-Fold CV scores : {cv_scores}")
    print(f"  Mean CV accuracy : {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    print()

    # --- Grid search for hyperparameter tuning ------------------------------
    print("  GridSearchCV (k, weights, distance metric) ...")
    param_grid: dict[str, list[Any]] = {
        "n_neighbors": [1, 3, 5, 7, 9, 11, 13, 15],
        "weights": ["uniform", "distance"],
        "p": [1, 2],
    }
    gs = GridSearchCV(
        estimator=KNeighborsClassifier(),
        param_grid=param_grid,
        cv=5,
        scoring="accuracy",
    )
    gs.fit(X_train, y_train)

    print(f"  Best params      : {gs.best_params_}")
    print(f"  Best CV score    : {gs.best_score_:.4f}")
    print(f"  Test set accuracy: {gs.score(X_test, y_test):.4f}")
    print()

    return gs.best_estimator_


# ============================================================================
# 5. Model Evaluation: ROC / AUC (Binary Example)
# ============================================================================

def demonstrate_roc_auc() -> None:
    """Show ROC curve and AUC for a synthetic binary classification."""
    print("=" * 60)
    print("ROC / AUC Evaluation (Binary Example)")
    print("=" * 60)

    y_true = np.array([0, 0, 0, 1, 1, 0, 1, 1, 1, 0])
    y_scores = np.array([0.1, 0.4, 0.35, 0.8, 0.9, 0.2, 0.7, 0.85, 0.6, 0.55])

    auc_value = roc_auc_score(y_true, y_scores)
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)

    print(f"  AUC = {auc_value:.4f}")
    print(f"  FPR points : {np.round(fpr, 3)}")
    print(f"  TPR points : {np.round(tpr, 3)}")
    print()

    # Attempt to plot; skip gracefully if no display is available
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(fpr, tpr, color="coral", lw=2, label=f"ROC (AUC={auc_value:.2f})")
        ax.plot([0, 1], [0, 1], "k--", lw=1, label="Random baseline")
        ax.set_xlabel("False Positive Rate")
        ax.set_ylabel("True Positive Rate")
        ax.set_title("ROC Curve")
        ax.legend(loc="lower right")
        fig.tight_layout()
        fig.savefig("roc_curve_day82.png", dpi=100)
        plt.close(fig)
        print("  ROC curve saved to roc_curve_day82.png")
    except Exception as exc:
        print(f"  (Plotting skipped: {exc})")
    print()


# ============================================================================
# 6. KNN Regression
# ============================================================================

def demonstrate_knn_regression() -> None:
    """KNN regression on the income-vs-online-spending example from the doc."""
    print("=" * 60)
    print("KNN Regression (KNeighborsRegressor)")
    print("=" * 60)

    incomes = np.array([
        9558, 8835, 9313, 14990, 5564, 11227, 11806, 10242, 11999, 11630,
        6906, 13850, 7483, 8090, 9465, 9938, 11414, 3200, 10731, 19880,
        15500, 10343, 11100, 10020, 7587, 6120, 5386, 12038, 13360, 10885,
        17010, 9247, 13050, 6691, 7890, 9070, 16899, 8975, 8650, 9100,
        10990, 9184, 4811, 14890, 11313, 12547, 8300, 12400, 9853, 12890,
    ])
    outcomes = np.array([
        3171, 2183, 3091, 5928, 182, 4373, 5297, 3788, 5282, 4166,
        1674, 5045, 1617, 1707, 3096, 3407, 4674, 361, 3599, 6584,
        6356, 3859, 4519, 3352, 1634, 1032, 1106, 4951, 5309, 3800,
        5672, 2901, 5439, 1478, 1424, 2777, 5682, 2554, 2117, 2845,
        3867, 2962, 882, 5435, 4174, 4948, 2376, 4987, 3329, 5002,
    ])

    order = np.argsort(incomes)
    X = incomes[order].reshape(-1, 1)
    y = outcomes[order]

    model = KNeighborsRegressor(n_neighbors=5, weights="uniform")
    model.fit(X, y)
    y_pred = model.predict(X)

    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - ss_res / ss_tot

    print(f"  Training samples : {len(X)}")
    print(f"  k (neighbors)   : {model.n_neighbors}")
    print(f"  R-squared        : {r_squared:.4f}")
    print(f"  Sample predictions (income -> predicted spend):")
    for inc, pred in zip(X[:5, 0], y_pred[:5]):
        print(f"    {inc:>6.0f} -> {pred:>8.1f}")
    print()

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(X, y, color="navy", s=20, alpha=0.7, label="Actual")
        ax.plot(X, y_pred, color="coral", lw=2, label="KNN prediction")
        ax.set_xlabel("Monthly Income")
        ax.set_ylabel("Online Spending")
        ax.set_title("KNN Regression: Income vs Spending")
        ax.legend()
        fig.tight_layout()
        fig.savefig("knn_regression_day82.png", dpi=100)
        plt.close(fig)
        print("  Regression plot saved to knn_regression_day82.png")
    except Exception as exc:
        print(f"  (Plotting skipped: {exc})")
    print()


# ============================================================================
# 7. Enterprise Example A -- Recommendation System (User-Based CF)
# ============================================================================

def demonstrate_recommendation_system() -> None:
    """User-based collaborative filtering with KNN.

    Scenario: An e-commerce platform predicts how a new user would rate
    products by finding the k most similar users and averaging their ratings.

    Each user is represented by a feature vector of product ratings.
    The system finds nearest neighbors in rating-space, then recommends
    items those neighbors liked but the target user has not rated.
    """
    print("=" * 60)
    print("Enterprise Example: Recommendation System (User-Based CF)")
    print("=" * 60)

    # Rows = users, columns = products (ratings 1-5; 0 = not rated)
    user_product_ratings = np.array([
        [5, 3, 0, 1, 4, 0, 0],
        [4, 0, 0, 1, 5, 0, 2],
        [0, 1, 2, 5, 0, 4, 3],
        [1, 0, 3, 4, 0, 5, 0],
        [0, 2, 4, 0, 3, 1, 5],
        [3, 4, 0, 0, 2, 0, 1],
    ])
    product_names = ["Phone", "Laptop", "Headphones", "Keyboard", "Tablet", "Monitor", "Mouse"]

    # New user's partial ratings (0 = unrated)
    new_user = np.array([4, 0, 0, 2, 5, 0, 0])

    # Build feature vectors from co-rated items only
    def build_features(
        ratings: NDArray[np.floating],
        target: NDArray[np.floating],
    ) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
        """Extract co-rated columns for fair distance comparison."""
        co_rated = (target != 0) & np.all(ratings != 0, axis=0)
        if not np.any(co_rated):
            co_rated = target != 0
        return ratings[:, co_rated], target[co_rated]

    X_users, x_new = build_features(user_product_ratings, new_user)

    k = 3
    tree = KNeighborsClassifier(n_neighbors=k, metric="euclidean")
    # Treat each existing user as a "class" for nearest-neighbor lookup
    tree.fit(X_users, np.arange(len(X_users)))

    neighbor_indices = tree.kneighbors(x_new.reshape(1, -1), return_distance=False)[0]
    print(f"  New user ratings   : {new_user}")
    print(f"  k (neighbors)      : {k}")
    print(f"  Nearest user IDs   : {neighbor_indices.tolist()}")

    # Recommend products the new user has NOT rated, ranked by neighbor avg
    unrated_mask = new_user == 0
    scores: dict[str, float] = {}
    for prod_idx in range(len(product_names)):
        if unrated_mask[prod_idx]:
            neighbor_ratings = user_product_ratings[neighbor_indices, prod_idx]
            avg_rating = float(np.mean(neighbor_ratings))
            scores[product_names[prod_idx]] = avg_rating

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print("  Recommendations (product -> predicted rating):")
    for name, score in ranked:
        print(f"    {name:<15} -> {score:.2f}")
    print()


# ============================================================================
# 8. Enterprise Example B -- Anomaly Detection
# ============================================================================

def demonstrate_anomaly_detection() -> None:
    """Distance-based anomaly detection using KNN.

    Scenario: A server monitoring system uses KNN to flag anomalous metrics.
    A data point is considered anomalous if its average distance to its k
    nearest neighbors exceeds a threshold (e.g. 95th percentile of all
    average distances in the training data).
    """
    print("=" * 60)
    print("Enterprise Example: Anomaly Detection")
    print("=" * 60)

    rng = np.random.RandomState(42)

    # Normal server metrics: [cpu%, memory%, disk_io, network_io]
    normal_data = rng.normal(loc=[40, 55, 30, 25], scale=[8, 10, 5, 5], size=(200, 4))

    # Inject a few anomalies
    anomalies = np.array([
        [95, 98, 90, 85],   # CPU spike, memory exhaustion
        [10, 95, 95, 5],    # Low CPU but disk thrashing
        [85, 80, 10, 95],   # Network saturation
    ])

    # Combine for fitting the reference distribution
    all_data = np.vstack([normal_data, anomalies])

    scaler = StandardScaler()
    normal_scaled = scaler.fit_transform(normal_data)
    all_scaled = scaler.transform(all_data)

    k = 10
    nn = KNeighborsClassifier(n_neighbors=k, metric="euclidean")
    nn.fit(normal_scaled, np.zeros(len(normal_scaled), dtype=int))

    distances, _ = nn.kneighbors(all_scaled, n_neighbors=k, return_distance=True)
    avg_distances = distances.mean(axis=1)

    # Threshold: 95th percentile of normal data's average distances
    normal_avg_dists = avg_distances[: len(normal_data)]
    threshold = np.percentile(normal_avg_dists, 95)

    print(f"  Training samples   : {len(normal_data)} normal + {len(anomalies)} anomalies")
    print(f"  k (neighbors)      : {k}")
    print(f"  Distance threshold : {threshold:.4f} (95th percentile of normal)")

    flagged = avg_distances > threshold
    print(f"  Total flagged      : {flagged.sum()} out of {len(all_data)}")
    for i, (is_anom, avg_d) in enumerate(zip(flagged, avg_distances)):
        if is_anom:
            label = "ANOMALY" if i >= len(normal_data) else "false positive"
            print(f"    Index {i:>3}  avg_dist={avg_d:.4f}  [{label}]  data={all_data[i]}")
    print()


# ============================================================================
# 9. Enterprise Example C -- Full Classification Pipeline
# ============================================================================

def demonstrate_enterprise_classification(
    X_train: NDArray[np.floating],
    X_test: NDArray[np.floating],
    y_train: NDArray[np.int_],
    y_test: NDArray[np.int_],
    target_names: list[str],
) -> None:
    """End-to-end classification pipeline with scaling, tuning, and evaluation.

    This mimics a production workflow where raw features are standardized,
    the model is tuned via cross-validation, and a final evaluation report
    is generated for stakeholders.
    """
    print("=" * 60)
    print("Enterprise Example: Full Classification Pipeline")
    print("=" * 60)

    # Step 1 -- Feature scaling (critical when features have different units)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Step 2 -- Hyperparameter tuning with cross-validation
    param_grid: dict[str, list[Any]] = {
        "n_neighbors": [3, 5, 7, 9],
        "weights": ["uniform", "distance"],
        "p": [1, 2],
        "algorithm": ["auto", "ball_tree", "kd_tree", "brute"],
    }
    gs = GridSearchCV(
        KNeighborsClassifier(),
        param_grid=param_grid,
        cv=5,
        scoring="accuracy",
        n_jobs=-1,
    )
    gs.fit(X_train_scaled, y_train)

    print(f"  Scaler            : StandardScaler (mean-center, unit-variance)")
    print(f"  Best params       : {gs.best_params_}")
    print(f"  Best CV accuracy  : {gs.best_score_:.4f}")

    # Step 3 -- Final evaluation on hold-out test set
    best_model: KNeighborsClassifier = gs.best_estimator_
    y_pred = best_model.predict(X_test_scaled)
    test_acc = best_model.score(X_test_scaled, y_test)

    print(f"  Test set accuracy : {test_acc:.4f}")
    print()
    print("  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=target_names))

    cm = confusion_matrix(y_test, y_pred)
    print("  Confusion Matrix:")
    for row in cm:
        print(f"    {row}")
    print()

    # Step 4 -- Save confusion matrix plot
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 5))
        disp = ConfusionMatrixDisplay(cm, display_labels=target_names)
        disp.plot(ax=ax, cmap="Blues", colorbar=False)
        ax.set_title("KNN Confusion Matrix (Iris)")
        fig.tight_layout()
        fig.savefig("confusion_matrix_day82.png", dpi=100)
        plt.close(fig)
        print("  Confusion matrix saved to confusion_matrix_day82.png")
    except Exception as exc:
        print(f"  (Plotting skipped: {exc})")
    print()


# ============================================================================
# 10. Iris Dataset Loader Helper
# ============================================================================

@dataclass
class IrisSplit:
    """Container for the Iris dataset split into train / test."""
    X_train: NDArray[np.floating]
    X_test: NDArray[np.floating]
    y_train: NDArray[np.int_]
    y_test: NDArray[np.int_]
    feature_names: list[str]
    target_names: list[str]


def load_iris_split(train_ratio: float = 0.8, seed: int = 3) -> IrisSplit:
    """Load the Iris dataset and split into training / test sets."""
    iris = load_iris()
    X: NDArray[np.floating] = iris.data
    y: NDArray[np.int_] = iris.target
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=train_ratio, random_state=seed, stratify=y
    )
    return IrisSplit(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        feature_names=list(iris.feature_names),
        target_names=list(iris.target_names),
    )


# ============================================================================
# Main
# ============================================================================

def main() -> None:
    """Run all KNN demonstrations."""
    print()
    print("*" * 60)
    print("  Day 82 -- k-Nearest Neighbors (kNN) Comprehensive Demo")
    print("*" * 60)
    print()

    # 1. Distance metrics
    demonstrate_distance_metrics()

    # 2. Load Iris dataset
    data = load_iris_split()
    print(f"  Iris dataset: {len(data.X_train)} train / {len(data.X_test)} test samples")
    print(f"  Features    : {data.feature_names}")
    print(f"  Targets     : {data.target_names}")
    print()

    # 3. Manual KNN
    demonstrate_manual_knn(data.X_train, data.X_test, data.y_train, data.y_test)

    # 4. Brute-force vs KD-tree
    demonstrate_brute_vs_kdtree(data.X_train, data.X_test)

    # 5. sklearn KNN + cross-validation + grid search
    demonstrate_sklearn_knn(
        data.X_train, data.X_test, data.y_train, data.y_test,
        data.feature_names, data.target_names,
    )

    # 6. ROC / AUC
    demonstrate_roc_auc()

    # 7. KNN regression
    demonstrate_knn_regression()

    # 8. Enterprise: Recommendation system
    demonstrate_recommendation_system()

    # 9. Enterprise: Anomaly detection
    demonstrate_anomaly_detection()

    # 10. Enterprise: Full classification pipeline
    demonstrate_enterprise_classification(
        data.X_train, data.X_test, data.y_train, data.y_test,
        data.target_names,
    )

    print("=" * 60)
    print("All KNN demonstrations complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
