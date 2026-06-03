"""
Day 81 - 浅谈机器学习 (Machine Learning Overview)

Comprehensive demonstration of machine learning fundamentals using Python scikit-learn.
Covers: ML concepts, supervised/unsupervised learning, train/test split,
        data preprocessing, model evaluation, and enterprise-grade pipelines.

Comparison: Python scikit-learn vs C++ mlpack/dlib
----------------------------------------------------------------------
+---------------------+-----------------------------+----------------------------+
| Feature             | Python scikit-learn         | C++ mlpack / dlib          |
+---------------------+-----------------------------+----------------------------+
| Ease of use         | Very high, Pythonic API     | Moderate, verbose C++ code |
| Ecosystem           | NumPy/SciPy/Pandas/Matplotlib | Limited, manual integration|
| Prototyping speed   | Fast, interactive notebooks | Slower, compile-then-run   |
| Deployment          | Needs serialization (pickle)| Native compiled binaries   |
| Performance         | Good (C/Cython backends)    | Excellent (native speed)   |
| Deep learning       | Not included (use PyTorch)  | dlib has CNN support       |
| GPU acceleration    | Limited (via CuML)          | dlib supports CUDA         |
| Large-scale         | Via Dask / incremental learn| Better memory efficiency   |
| Community / Docs    | Massive, well-documented    | Smaller, growing           |
| Typical use case    | Research, prototyping, ETL  | Embedded / edge / realtime |
+---------------------+-----------------------------+----------------------------+

mlpack (https://www.mlpack.org/):
  - Header-only C++ ML library, emphasis on speed and scalability.
  - Provides similar algorithms: linear regression, SVM, random forests, etc.
  - CLI bindings and Python bindings available.
  - Suitable for resource-constrained environments.

dlib (http://dlib.net/):
  - C++ toolkit with ML, image processing, and numerical algorithms.
  - Strong in face detection, object tracking, and SVM-based classification.
  - Python bindings via pybind11, popular for face recognition pipelines.
  - Optimized for real-time applications.

When to prefer C++ ML:
  - Real-time inference with strict latency requirements.
  - Embedded systems with limited Python runtime availability.
  - Large-scale batch processing where native speed matters most.
  - Security-sensitive environments avoiding Python dependency chains.

When to prefer Python scikit-learn:
  - Rapid prototyping and exploratory data analysis.
  - Rich ecosystem integration (Pandas, Matplotlib, Jupyter).
  - Extensive model selection and hyperparameter tuning tools.
  - Team familiarity and extensive community support.

Key References from the Course Material:
  - Machine learning enables computers to learn patterns from data without
    explicit programming (unlike traditional algorithms).
  - ML categories: Supervised (regression, classification),
    Unsupervised (clustering, dimensionality reduction),
    Semi-supervised, Reinforcement learning.
  - ML pipeline: Define problem -> Collect data -> Clean data -> Split data
    -> Select model -> Train -> Evaluate -> Deploy -> Maintain.
  - Overfitting vs Underfitting: finding the right model complexity.
  - kNN algorithm demonstrated as the simplest ML approach.
  - Linear regression: finding slope (a) and intercept (b) via least squares.
  - Loss function: Mean Squared Error (MSE).
  - Monte Carlo simulation for parameter search vs analytical solutions.
"""

from __future__ import annotations

import statistics
import heapq
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

# ---------------------------------------------------------------------------
# scikit-learn imports
# ---------------------------------------------------------------------------
from sklearn.datasets import (
    load_iris,
    load_wine,
    make_classification,
    make_blobs,
    make_regression,
)
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    silhouette_score,
)

# ---------------------------------------------------------------------------
# scipy for statistical testing (as shown in the course material)
# ---------------------------------------------------------------------------
from scipy import stats


# ============================================================================
# 1. CORE ML CONCEPTS - kNN from scratch (as taught in the course)
# ============================================================================

def knn_predict_from_scratch(
    history_data: dict[float, float],
    query: float,
    k: int = 5,
) -> float:
    """Predict using k-Nearest Neighbors implemented from scratch.

    This mirrors the course material's demonstration of kNN without
    relying on any ML library.  The algorithm finds the k closest
    keys in the history_data dictionary (by squared distance) and
    returns the mean of their corresponding values.

    Parameters
    ----------
    history_data : dict[float, float]
        Mapping from feature value (monthly income) to target (online spend).
    query : float
        The input feature for which to predict the target.
    k : int
        Number of nearest neighbors to consider.

    Returns
    -------
    float
        Predicted target value (mean of k nearest neighbor targets).
    """
    neighbors = heapq.nsmallest(
        k, history_data, key=lambda key: (key - query) ** 2
    )
    return statistics.mean([history_data[n] for n in neighbors])


def mse_loss_from_scratch(
    X: list[float],
    y: list[float],
    a: float,
    b: float,
) -> float:
    """Compute Mean Squared Error (MSE) for a linear model y = a*X + b.

    This is the loss function described in the course material.

    Parameters
    ----------
    X : list[float]
        Input features.
    y : list[float]
        True target values.
    a : float
        Slope of the linear model.
    b : float
        Intercept of the linear model.

    Returns
    -------
    float
        The MSE value.
    """
    y_hat = [a * xi + b for xi in X]
    return statistics.mean([(yi - yi_hat) ** 2 for yi, yi_hat in zip(y, y_hat)])


def monte_carlo_regression(
    X: list[float],
    y: list[float],
    n_trials: int = 100_000,
    a_range: tuple[float, float] = (0.0, 1.0),
    b_range: tuple[float, float] = (-2000.0, 2000.0),
) -> tuple[float, float, float]:
    """Find regression parameters via Monte Carlo simulation.

    Brute-force random search as demonstrated in the course material
    to illustrate the concept of optimization / loss minimization.

    Parameters
    ----------
    X : list[float]
        Input features.
    y : list[float]
        True target values.
    n_trials : int
        Number of random trials.
    a_range : tuple[float, float]
        Range for sampling slope values.
    b_range : tuple[float, float]
        Range for sampling intercept values.

    Returns
    -------
    tuple[float, float, float]
        (best_a, best_b, min_mse)
    """
    import random

    min_mse: float = 1e12
    best_a: float = 0.0
    best_b: float = 0.0

    for _ in range(n_trials):
        candidate_a = random.uniform(*a_range)
        candidate_b = random.uniform(*b_range)
        current_mse = mse_loss_from_scratch(X, y, candidate_a, candidate_b)
        if current_mse < min_mse:
            min_mse = current_mse
            best_a = candidate_a
            best_b = candidate_b

    return best_a, best_b, min_mse


def least_squares_analytical(
    X: np.ndarray,
    y: np.ndarray,
) -> tuple[float, float]:
    """Compute linear regression parameters via the closed-form least-squares solution.

    Uses the formulas derived from setting partial derivatives of the
    MSE loss to zero, as presented in the course material.

    a = sum((x_i - x_bar)(y_i - y_bar)) / sum((x_i - x_bar)^2)
    b = y_bar - a * x_bar

    Parameters
    ----------
    X : np.ndarray
        Input features (1-D array).
    y : np.ndarray
        True target values (1-D array).

    Returns
    -------
    tuple[float, float]
        (slope a, intercept b)
    """
    x_bar = np.mean(X)
    y_bar = np.mean(y)
    a = np.dot(X - x_bar, y - y_bar) / np.sum((X - x_bar) ** 2)
    b = y_bar - a * x_bar
    return float(a), float(b)


# ============================================================================
# 2. DATA PREPROCESSING PIPELINE (Enterprise-Grade)
# ============================================================================

@dataclass
class DataPreprocessor:
    """Encapsulates common data preprocessing steps for ML pipelines.

    Attributes
    ----------
    scaler : str
        Scaling strategy: 'standard' (z-score) or 'minmax' (0-1 range).
    handle_missing : bool
        Whether to impute missing values with column means.
    verbose : bool
        Print progress information.
    """

    scaler: str = "standard"
    handle_missing: bool = True
    verbose: bool = True
    _scaler_obj: Any = field(default=None, repr=False, init=False)

    def fit_transform(
        self,
        X_train: np.ndarray,
        X_test: Optional[np.ndarray] = None,
    ) -> tuple[np.ndarray, Optional[np.ndarray]]:
        """Fit scaler on training data and transform both train and test sets.

        Parameters
        ----------
        X_train : np.ndarray
            Training feature matrix.
        X_test : np.ndarray or None
            Test feature matrix (optional).

        Returns
        -------
        tuple[np.ndarray, Optional[np.ndarray]]
            Scaled training (and optionally test) feature matrices.
        """
        if self.handle_missing:
            col_means = np.nanmean(X_train, axis=0)
            nan_mask_train = np.isnan(X_train)
            X_train = X_train.copy()
            for j in range(X_train.shape[1]):
                X_train[nan_mask_train[:, j], j] = col_means[j]
            if X_test is not None:
                X_test = X_test.copy()
                nan_mask_test = np.isnan(X_test)
                for j in range(X_test.shape[1]):
                    X_test[nan_mask_test[:, j], j] = col_means[j]
            if self.verbose:
                print("[Preprocessor] Missing values imputed with column means.")

        if self.scaler == "standard":
            self._scaler_obj = StandardScaler()
        elif self.scaler == "minmax":
            self._scaler_obj = MinMaxScaler()
        else:
            raise ValueError(f"Unknown scaler type: {self.scaler!r}")

        X_train_scaled = self._scaler_obj.fit_transform(X_train)
        if self.verbose:
            print(f"[Preprocessor] Applied {self.scaler} scaling to training data.")

        X_test_scaled: Optional[np.ndarray] = None
        if X_test is not None:
            X_test_scaled = self._scaler_obj.transform(X_test)
            if self.verbose:
                print("[Preprocessor] Applied same scaling to test data.")

        return X_train_scaled, X_test_scaled


# ============================================================================
# 3. SUPERVISED LEARNING - CLASSIFICATION
# ============================================================================

class ClassificationPipeline:
    """Enterprise-style classification pipeline with train/evaluate/compare.

    Demonstrates the complete ML workflow:
        data loading -> preprocessing -> train/test split -> model training
        -> evaluation -> model comparison.

    C++ comparison note:
        The same workflow in C++ (mlpack) would require:
        - Manual matrix loading (arma::mat)
        - Explicit template instantiation for each model type
        - Manual metric computation loops
        - Verbose serialization for model persistence
        In scikit-learn, each step is a concise method call.
    """

    CLASSIFIERS: dict[str, Any] = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
        "KNN(k=5)": KNeighborsClassifier(n_neighbors=5),
        "DecisionTree": DecisionTreeClassifier(random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
        "SVM(RBF)": SVC(kernel="rbf", random_state=42),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=100, random_state=42
        ),
    }

    def __init__(
        self,
        dataset_name: str = "iris",
        test_size: float = 0.2,
        random_state: int = 42,
        scaler: str = "standard",
    ) -> None:
        self.dataset_name = dataset_name
        self.test_size = test_size
        self.random_state = random_state
        self.scaler_type = scaler
        self.X_train: np.ndarray
        self.X_test: np.ndarray
        self.y_train: np.ndarray
        self.y_test: np.ndarray
        self.results: dict[str, dict[str, float]] = {}

    def load_data(self) -> None:
        """Load a built-in dataset or generate synthetic data."""
        if self.dataset_name == "iris":
            data = load_iris()
        elif self.dataset_name == "wine":
            data = load_wine()
        elif self.dataset_name == "synthetic":
            data = make_classification(
                n_samples=1000,
                n_features=20,
                n_informative=10,
                n_classes=3,
                random_state=self.random_state,
            )
            # make_classification returns (X, y) directly
            X, y = data
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                X, y,
                test_size=self.test_size,
                random_state=self.random_state,
                stratify=y,
            )
            # Apply preprocessing
            preprocessor = DataPreprocessor(
                scaler=self.scaler_type, verbose=False
            )
            self.X_train, self.X_test = preprocessor.fit_transform(
                self.X_train, self.X_test
            )
            return
        else:
            raise ValueError(f"Unknown dataset: {self.dataset_name!r}")

        X, y = data.data, data.target
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y,
        )

        preprocessor = DataPreprocessor(scaler=self.scaler_type, verbose=False)
        self.X_train, self.X_test = preprocessor.fit_transform(
            self.X_train, self.X_test
        )

    def train_and_evaluate(self) -> dict[str, dict[str, float]]:
        """Train all classifiers and collect evaluation metrics."""
        self.results.clear()
        for name, clf in self.CLASSIFIERS.items():
            clf.fit(self.X_train, self.y_train)
            y_pred = clf.predict(self.X_test)

            acc = accuracy_score(self.y_test, y_pred)
            prec = precision_score(self.y_test, y_pred, average="weighted")
            rec = recall_score(self.y_test, y_pred, average="weighted")
            f1 = f1_score(self.y_test, y_pred, average="weighted")

            self.results[name] = {
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1_score": f1,
            }
        return self.results

    def print_results(self) -> None:
        """Print a formatted comparison table of all classifiers."""
        header = f"{'Model':<25} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}"
        print(f"\n{'=' * len(header)}")
        print(f"Classification Results  (dataset={self.dataset_name!r})")
        print(header)
        print("-" * len(header))
        for name, metrics in sorted(self.results.items(), key=lambda kv: -kv[1]["f1_score"]):
            print(
                f"{name:<25} "
                f"{metrics['accuracy']:>10.4f} "
                f"{metrics['precision']:>10.4f} "
                f"{metrics['recall']:>10.4f} "
                f"{metrics['f1_score']:>10.4f}"
            )
        print("=" * len(header))

    def detailed_report(self, model_name: str = "RandomForest") -> None:
        """Print a full classification report for a specific model."""
        clf = self.CLASSIFIERS[model_name]
        y_pred = clf.predict(self.X_test)
        print(f"\nDetailed Classification Report for {model_name}:")
        print(classification_report(self.y_test, y_pred))
        print("Confusion Matrix:")
        print(confusion_matrix(self.y_test, y_pred))

    def cross_validate(self, model_name: str = "RandomForest", cv: int = 5) -> None:
        """Perform k-fold cross-validation on a specific model."""
        # Re-load fresh data without the train/test split for CV
        if self.dataset_name == "iris":
            data = load_iris()
        elif self.dataset_name == "wine":
            data = load_wine()
        else:
            data = make_classification(
                n_samples=1000, n_features=20, n_informative=10,
                n_classes=3, random_state=self.random_state,
            )

        X, y = (data.data, data.target) if hasattr(data, "data") else data

        clf = self.CLASSIFIERS[model_name]
        scores = cross_val_score(clf, X, y, cv=cv, scoring="accuracy")
        print(f"\nCross-Validation ({model_name}, {cv}-fold):")
        print(f"  Scores: {scores}")
        print(f"  Mean:   {scores.mean():.4f} (+/- {scores.std() * 2:.4f})")


# ============================================================================
# 4. SUPERVISED LEARNING - REGRESSION
# ============================================================================

class RegressionPipeline:
    """Demonstrates regression workflow with the course material's data.

    Uses the monthly income vs. online spending dataset from the course
    and compares multiple regression approaches:
    1. kNN regression (from scratch)
    2. Least-squares analytical solution
    3. scikit-learn LinearRegression
    4. scikit-learn Ridge (L2 regularization)
    5. scikit-learn Lasso (L1 regularization)
    6. scikit-learn KNeighborsRegressor
    """

    def __init__(self) -> None:
        # Original dataset from the course material
        self.incomes: list[int] = [
            9558, 8835, 9313, 14990, 5564, 11227, 11806, 10242, 11999, 11630,
            6906, 13850, 7483, 8090, 9465, 9938, 11414, 3200, 10731, 19880,
            15500, 10343, 11100, 10020, 7587, 6120, 5386, 12038, 13360, 10885,
            17010, 9247, 13050, 6691, 7890, 9070, 16899, 8975, 8650, 9100,
            10990, 9184, 4811, 14890, 11313, 12547, 8300, 12400, 9853, 12890,
        ]
        self.spending: list[int] = [
            3171, 2183, 3091, 5928, 182, 4373, 5297, 3788, 5282, 4166,
            1674, 5045, 1617, 1707, 3096, 3407, 4674, 361, 3599, 6584,
            6356, 3859, 4519, 3352, 1634, 1032, 1106, 4951, 5309, 3800,
            5672, 2901, 5439, 1478, 1424, 2777, 5682, 2554, 2117, 2845,
            3867, 2962, 882, 5435, 4174, 4948, 2376, 4987, 3329, 5002,
        ]
        self.X: np.ndarray = np.array(self.incomes, dtype=np.float64)
        self.y: np.ndarray = np.array(self.spending, dtype=np.float64)

    def correlation_analysis(self) -> None:
        """Compute and display Pearson correlation coefficient."""
        print("\n--- Correlation Analysis ---")
        corr_matrix = np.corrcoef(self.X, self.y)
        print(f"Pearson correlation matrix:\n{corr_matrix}")

        corr_result = stats.pearsonr(self.X, self.y)
        print(f"Pearson r = {corr_result.statistic:.8f}")
        print(f"p-value   = {corr_result.pvalue:.2e}")

        if corr_result.statistic > 0.9:
            print("Interpretation: Strong positive correlation between income and spending.")
        elif corr_result.statistic > 0.7:
            print("Interpretation: Moderate positive correlation.")
        else:
            print("Interpretation: Weak or no correlation.")

    def knn_from_scratch_demo(self) -> None:
        """Demonstrate kNN prediction using the course's from-scratch implementation."""
        print("\n--- kNN From Scratch (Course Material Demo) ---")
        sample_data: dict[float, float] = dict(zip(self.incomes, self.spending))
        test_incomes = [1800, 3500, 5200, 6600, 13400, 17800, 20000, 30000]
        for income in test_incomes:
            predicted = knn_predict_from_scratch(sample_data, income, k=5)
            print(f"  Income: {income:>6d} CNY -> Predicted spending: {predicted:>8.1f} CNY")

    def least_squares_demo(self) -> None:
        """Demonstrate analytical least-squares solution from the course."""
        print("\n--- Least Squares (Analytical) ---")
        a, b = least_squares_analytical(self.X, self.y)
        mse = mse_loss_from_scratch(self.X.tolist(), self.y.tolist(), a, b)
        print(f"  Slope (a)     = {a:.6f}")
        print(f"  Intercept (b) = {b:.6f}")
        print(f"  MSE           = {mse:.4f}")

        # Also show NumPy polyfit (as in the course)
        a_np, b_np = np.polyfit(self.X, self.y, deg=1)
        print(f"  np.polyfit:   a = {a_np:.6f}, b = {b_np:.6f}")

    def sklearn_regression_comparison(self) -> None:
        """Compare multiple scikit-learn regression models."""
        print("\n--- Scikit-learn Regression Models Comparison ---")
        X_reshaped = self.X.reshape(-1, 1)
        X_train, X_test, y_train, y_test = train_test_split(
            X_reshaped, self.y, test_size=0.2, random_state=42
        )

        models: dict[str, Any] = {
            "LinearRegression": LinearRegression(),
            "Ridge(alpha=1.0)": Ridge(alpha=1.0),
            "Lasso(alpha=1.0)": Lasso(alpha=1.0),
            "KNN(k=5)": KNeighborsRegressor(n_neighbors=5),
        }

        header = f"{'Model':<25} {'R-squared':>10} {'MAE':>10} {'MSE':>10} {'RMSE':>10}"
        print(header)
        print("-" * len(header))

        for name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            print(
                f"{name:<25} {r2:>10.4f} {mae:>10.2f} {mse:>10.2f} {rmse:>10.2f}"
            )

    def monte_carlo_demo(self, n_trials: int = 50_000) -> None:
        """Demonstrate Monte Carlo parameter search from the course."""
        print(f"\n--- Monte Carlo Simulation ({n_trials} trials) ---")
        start = time.perf_counter()
        best_a, best_b, min_mse = monte_carlo_regression(
            self.X.tolist(), self.y.tolist(), n_trials=n_trials
        )
        elapsed = time.perf_counter() - start
        print(f"  Best slope (a)     = {best_a:.6f}")
        print(f"  Best intercept (b) = {best_b:.6f}")
        print(f"  Minimum MSE        = {min_mse:.4f}")
        print(f"  Time elapsed       = {elapsed:.3f}s")
        print("  Note: Monte Carlo is a brute-force approach; analytical "
              "least-squares is far more efficient.")


# ============================================================================
# 5. UNSUPERVISED LEARNING
# ============================================================================

class UnsupervisedLearningDemo:
    """Demonstrates unsupervised learning techniques.

    Covers:
    - Clustering: KMeans, DBSCAN
    - Dimensionality Reduction: PCA

    C++ comparison note:
        In mlpack, KMeans is invoked as:
            mlpack::kmeans::KMeans<> k;
            k.Cluster(data, assignments);
        In dlib, KMeans is available via dlib::kcentroid.
        Both require explicit matrix types (arma::mat / dlib::matrix).
        scikit-learn wraps all of this into a .fit() / .predict() API.
    """

    @staticmethod
    def clustering_demo() -> None:
        """Demonstrate KMeans and DBSCAN clustering."""
        print("\n--- Unsupervised Learning: Clustering ---")

        # Generate synthetic clustered data
        X, y_true = make_blobs(
            n_samples=300, centers=4, cluster_std=0.60, random_state=42
        )

        # KMeans
        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        y_kmeans = kmeans.fit_predict(X)
        kmeans_silhouette = silhouette_score(X, y_kmeans)
        print(f"  KMeans:  silhouette score = {kmeans_silhouette:.4f}")
        print(f"  KMeans:  cluster centers shape = {kmeans.cluster_centers_.shape}")

        # DBSCAN
        dbscan = DBSCAN(eps=0.5, min_samples=5)
        y_dbscan = dbscan.fit_predict(X)
        n_clusters = len(set(y_dbscan)) - (1 if -1 in y_dbscan else 0)
        n_noise = list(y_dbscan).count(-1)
        if n_clusters > 1:
            mask = y_dbscan != -1
            dbscan_silhouette = silhouette_score(X[mask], y_dbscan[mask])
            print(f"  DBSCAN:  silhouette score = {dbscan_silhouette:.4f} "
                  f"(excluding noise)")
        else:
            print("  DBSCAN:  silhouette score N/A (insufficient clusters)")
        print(f"  DBSCAN:  clusters found = {n_clusters}, noise points = {n_noise}")

    @staticmethod
    def dimensionality_reduction_demo() -> None:
        """Demonstrate PCA for dimensionality reduction."""
        print("\n--- Unsupervised Learning: PCA Dimensionality Reduction ---")

        data = load_iris()
        X, y = data.data, data.target

        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # PCA to 2 components
        pca = PCA(n_components=2, random_state=42)
        X_pca = pca.fit_transform(X_scaled)

        print(f"  Original feature dimensions : {X.shape[1]}")
        print(f"  Reduced feature dimensions  : {X_pca.shape[1]}")
        print(f"  Explained variance ratio    : {pca.explained_variance_ratio_}")
        print(f"  Total variance explained    : {sum(pca.explained_variance_ratio_):.4f}")

        # Full PCA to show all components
        pca_full = PCA(random_state=42)
        pca_full.fit(X_scaled)
        cumulative = np.cumsum(pca_full.explained_variance_ratio_)
        print(f"  Cumulative variance (all)   : {cumulative}")


# ============================================================================
# 6. ENTERPRISE PIPELINE - HYPERPARAMETER TUNING
# ============================================================================

class HyperparameterTuningDemo:
    """Demonstrates GridSearchCV for hyperparameter optimization.

    In enterprise ML workflows, manual tuning is impractical.
    GridSearchCV automates cross-validated grid search.

    C++ comparison note:
        mlpack does not have built-in grid search; you would loop
        over parameter combinations manually and track results.
        dlib provides some optimization utilities but not a full
        grid search framework comparable to scikit-learn's.
    """

    @staticmethod
    def run() -> None:
        """Run GridSearchCV on a RandomForest classifier."""
        print("\n--- Hyperparameter Tuning with GridSearchCV ---")

        data = load_wine()
        X_train, X_test, y_train, y_test = train_test_split(
            data.data, data.target, test_size=0.2, random_state=42
        )

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(random_state=42)),
        ])

        param_grid = {
            "clf__n_estimators": [50, 100, 200],
            "clf__max_depth": [None, 5, 10],
            "clf__min_samples_split": [2, 5],
        }

        grid_search = GridSearchCV(
            pipeline,
            param_grid,
            cv=5,
            scoring="accuracy",
            n_jobs=-1,
            verbose=0,
        )

        start = time.perf_counter()
        grid_search.fit(X_train, y_train)
        elapsed = time.perf_counter() - start

        print(f"  Best parameters : {grid_search.best_params_}")
        print(f"  Best CV score   : {grid_search.best_score_:.4f}")
        print(f"  Test score      : {grid_search.score(X_test, y_test):.4f}")
        print(f"  Search time     : {elapsed:.2f}s")
        print(f"  Total fits      : {len(grid_search.cv_results_['params'])}")


# ============================================================================
# 7. COMPLETE ENTERPRISE ML PIPELINE
# ============================================================================

class EnterpriseMLPipeline:
    """End-to-end enterprise ML pipeline demonstrating best practices.

    Steps (mirroring the course material's 9-step ML process):
    1. Define problem
    2. Collect data
    3. Clean data (preprocessing)
    4. Split data (train/test)
    5. Select model
    6. Train model
    7. Evaluate model
    8. (Simulated) Deploy model
    9. (Simulated) Monitor and maintain

    In production, this pipeline would integrate with:
    - Feature stores for consistent feature engineering
    - MLflow / Weights & Biases for experiment tracking
    - Model registries for version control
    - CI/CD pipelines for automated retraining
    - A/B testing frameworks for gradual rollouts
    """

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose
        self.pipeline: Optional[Pipeline] = None
        self.best_model: Optional[Any] = None
        self.metrics: dict[str, float] = {}

    def run(self) -> dict[str, float]:
        """Execute the complete pipeline."""
        if self.verbose:
            print("\n" + "=" * 60)
            print("  ENTERPRISE ML PIPELINE - FULL EXECUTION")
            print("=" * 60)

        # Step 1: Define problem (classification on synthetic data)
        if self.verbose:
            print("\n[Step 1] Problem: Binary classification on synthetic data")

        # Step 2: Collect data
        X, y = make_classification(
            n_samples=2000,
            n_features=15,
            n_informative=8,
            n_redundant=3,
            n_classes=2,
            flip_y=0.05,  # 5% label noise to simulate real-world data
            random_state=42,
        )
        if self.verbose:
            print(f"[Step 2] Data collected: {X.shape[0]} samples, {X.shape[1]} features")

        # Step 3: Clean data (check for NaN, outliers)
        nan_count = np.isnan(X).sum()
        if self.verbose:
            print(f"[Step 3] Data cleaning: {nan_count} NaN values found")

        # Step 4: Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        if self.verbose:
            print(f"[Step 4] Train size: {X_train.shape[0]}, Test size: {X_test.shape[0]}")

        # Step 5: Select model (use pipeline with preprocessing)
        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=3,
                random_state=42,
            )),
        ])
        if self.verbose:
            print("[Step 5] Model: GradientBoostingClassifier with StandardScaler")

        # Step 6: Train
        start = time.perf_counter()
        self.pipeline.fit(X_train, y_train)
        train_time = time.perf_counter() - start
        if self.verbose:
            print(f"[Step 6] Training completed in {train_time:.4f}s")

        # Step 7: Evaluate
        y_pred = self.pipeline.predict(X_test)
        self.metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1_score": f1_score(y_test, y_pred),
        }
        if self.verbose:
            print("[Step 7] Evaluation results:")
            for metric, value in self.metrics.items():
                print(f"         {metric:<12} = {value:.4f}")

        # Step 8: Simulate deployment
        if self.verbose:
            print("[Step 8] Model serialized and ready for deployment (simulation)")

        # Step 9: Simulate monitoring
        if self.verbose:
            print("[Step 9] Model monitoring active (simulation)")
            print("         Drift detection, performance tracking scheduled.")

        return self.metrics

    def predict_new(self, X_new: np.ndarray) -> np.ndarray:
        """Use the trained pipeline to predict on new data.

        Parameters
        ----------
        X_new : np.ndarray
            New feature matrix for prediction.

        Returns
        -------
        np.ndarray
            Predicted class labels.
        """
        if self.pipeline is None:
            raise RuntimeError("Pipeline has not been trained yet. Call run() first.")
        return self.pipeline.predict(X_new)


# ============================================================================
# 8. MAIN ENTRY POINT
# ============================================================================

def main() -> None:
    """Run all demonstrations in sequence."""
    print("Python 100 Days - Day 81: Machine Learning Overview")
    print("=" * 60)
    print("C++ comparison: scikit-learn vs mlpack/dlib")
    print("- Python scikit-learn: high-level API, rapid prototyping, rich ecosystem")
    print("- C++ mlpack: header-only, fast, suitable for embedded/edge deployment")
    print("- C++ dlib: optimized for real-time CV tasks, native CUDA support")
    print("=" * 60)

    # ---------------------------------------------------------------
    # Part 1: Core Concepts - kNN and Regression from Scratch
    # ---------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# PART 1: CORE ML CONCEPTS (FROM SCRATCH)")
    print("#" * 60)

    reg_pipeline = RegressionPipeline()
    reg_pipeline.correlation_analysis()
    reg_pipeline.knn_from_scratch_demo()
    reg_pipeline.least_squares_demo()
    reg_pipeline.monte_carlo_demo(n_trials=50_000)

    # ---------------------------------------------------------------
    # Part 2: Supervised Learning - Regression with scikit-learn
    # ---------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# PART 2: SUPERVISED LEARNING - REGRESSION (scikit-learn)")
    print("#" * 60)

    reg_pipeline.sklearn_regression_comparison()

    # ---------------------------------------------------------------
    # Part 3: Supervised Learning - Classification
    # ---------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# PART 3: SUPERVISED LEARNING - CLASSIFICATION")
    print("#" * 60)

    for dataset in ("iris", "wine", "synthetic"):
        clf_pipeline = ClassificationPipeline(
            dataset_name=dataset, test_size=0.2, random_state=42
        )
        clf_pipeline.load_data()
        clf_pipeline.train_and_evaluate()
        clf_pipeline.print_results()

    # Detailed report for the best model on iris
    iris_pipeline = ClassificationPipeline(dataset_name="iris")
    iris_pipeline.load_data()
    iris_pipeline.train_and_evaluate()
    iris_pipeline.detailed_report("RandomForest")
    iris_pipeline.cross_validate("RandomForest", cv=5)

    # ---------------------------------------------------------------
    # Part 4: Unsupervised Learning
    # ---------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# PART 4: UNSUPERVISED LEARNING")
    print("#" * 60)

    UnsupervisedLearningDemo.clustering_demo()
    UnsupervisedLearningDemo.dimensionality_reduction_demo()

    # ---------------------------------------------------------------
    # Part 5: Hyperparameter Tuning
    # ---------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# PART 5: HYPERPARAMETER TUNING")
    print("#" * 60)

    HyperparameterTuningDemo.run()

    # ---------------------------------------------------------------
    # Part 6: Enterprise ML Pipeline
    # ---------------------------------------------------------------
    print("\n" + "#" * 60)
    print("# PART 6: ENTERPRISE ML PIPELINE")
    print("#" * 60)

    pipeline = EnterpriseMLPipeline(verbose=True)
    metrics = pipeline.run()

    # Demonstrate prediction on new data
    X_new, _ = make_classification(
        n_samples=5, n_features=15, n_informative=8,
        n_redundant=3, n_classes=2, random_state=99,
    )
    predictions = pipeline.predict_new(X_new)
    print(f"\n  Predictions on new data: {predictions}")

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
Machine learning enables computers to learn from data without explicit
programming. This file demonstrated:

1. k-Nearest Neighbors implemented from scratch (course material)
2. Linear regression via least-squares and Monte Carlo simulation
3. Multiple regression models: Linear, Ridge, Lasso, KNN
4. Classification with 6 algorithms on 3 datasets
5. Unsupervised learning: KMeans, DBSCAN, PCA
6. Hyperparameter tuning with GridSearchCV
7. End-to-end enterprise ML pipeline with 9-step process

Key takeaways from the course:
- Traditional algorithms need explicit rules; ML learns patterns from data.
- GIGO applies: data quality directly impacts model quality.
- Overfitting (complex model, poor generalization) vs
  Underfitting (simple model, poor performance on training data).
- Train/test split is essential to evaluate generalization.
- The ML workflow is iterative: train, evaluate, tune, repeat.

C++ ML comparison summary:
- scikit-learn excels at rapid prototyping and has the richest ecosystem.
- mlpack/dlib offer native performance for production/edge deployment.
- Python ML ecosystem (NumPy, SciPy, Pandas) is unmatched for data work.
- C++ ML libraries require more boilerplate but deliver deterministic
  performance critical for real-time systems.
""")


if __name__ == "__main__":
    main()
