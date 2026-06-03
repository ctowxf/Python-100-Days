"""
Day 85 - Regression Models (回归模型)
=====================================

Comprehensive demonstration of regression techniques in Python using scikit-learn,
covering linear regression, polynomial regression, Ridge, Lasso, Elastic Net,
stochastic gradient descent regression, and regularization concepts.

Includes:
    - LinearRegression (OLS closed-form solution)
    - PolynomialFeatures + LinearRegression for nonlinear relationships
    - Ridge (L2 regularization)
    - Lasso (L1 regularization with feature selection)
    - ElasticNet (L1 + L2 combined)
    - SGDRegressor (gradient descent solver)
    - Model evaluation: MSE, RMSE, MAE, R-squared
    - C++ / Eigen comparison note
    - Enterprise examples: price prediction, demand forecasting, trend analysis

References:
    - scikit-learn documentation
    - Day 85 tutorial: 回归模型

Author: Python-100-Days Project
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
#  Suppress convergence warnings for cleaner demo output
# ---------------------------------------------------------------------------
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# =========================================================================
# 1. Data Structures & Helpers
# =========================================================================

@dataclass
class RegressionResult:
    """Container for a trained regression model and its evaluation metrics."""

    model_name: str
    coef: np.ndarray
    intercept: float
    mse: float
    rmse: float
    mae: float
    r2: float
    extra_info: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        lines: List[str] = []
        lines.append(f"{'=' * 60}")
        lines.append(f"  Model: {self.model_name}")
        lines.append(f"{'=' * 60}")
        lines.append(f"  Coefficients : {self.coef}")
        lines.append(f"  Intercept    : {self.intercept:.6f}")
        lines.append(f"  MSE          : {self.mse:.4f}")
        lines.append(f"  RMSE         : {self.rmse:.4f}")
        lines.append(f"  MAE          : {self.mae:.4f}")
        lines.append(f"  R-squared    : {self.r2:.4f}")
        for key, value in self.extra_info.items():
            lines.append(f"  {key:14s}: {value}")
        lines.append(f"{'=' * 60}")
        return "\n".join(lines)


def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_name: str,
    extra_info: Optional[Dict[str, Any]] = None,
) -> RegressionResult:
    """Train a model on (X_train, y_train) and evaluate on (X_test, y_test).

    The model is assumed to already be fitted.  This function generates
    predictions, computes standard regression metrics, and returns a
    ``RegressionResult`` dataclass.

    Parameters
    ----------
    model : fitted scikit-learn estimator
    X_test : test features
    y_test : test target
    model_name : human-readable name for display
    extra_info : optional dict of additional metadata to include in summary

    Returns
    -------
    RegressionResult
    """
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    y_pred: np.ndarray = model.predict(X_test)
    mse: float = mean_squared_error(y_test, y_pred)
    rmse: float = float(np.sqrt(mse))
    mae: float = mean_absolute_error(y_test, y_pred)
    r2: float = r2_score(y_test, y_pred)

    return RegressionResult(
        model_name=model_name,
        coef=np.array(model.coef_),
        intercept=float(model.intercept_),
        mse=mse,
        rmse=rmse,
        mae=mae,
        r2=r2,
        extra_info=extra_info or {},
    )


# =========================================================================
# 2. Dataset Loading & Preprocessing
# =========================================================================

def load_auto_mpg_dataset() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Load and preprocess the UCI Auto MPG dataset.

    Steps:
        1. Download CSV from UCI repository.
        2. Drop the ``car_name`` column (not useful for regression).
        3. Drop rows with missing ``horsepower`` values.
        4. One-hot encode the ``origin`` column (drop first to avoid
           multicollinearity).

    Returns
    -------
    X : ndarray of shape (n_samples, n_features)
    y : ndarray of shape (n_samples,)
    feature_names : list of feature column names
    """
    import pandas as pd
    import ssl

    # Allow unverified HTTPS context (some environments block UCI)
    ssl._create_default_https_context = ssl._create_unverified_context  # type: ignore[attr-defined]

    url: str = "https://archive.ics.uci.edu/static/public/9/data.csv"
    df: pd.DataFrame = pd.read_csv(url)

    # Drop car_name — not useful for numeric regression
    df.drop(columns=["car_name"], inplace=True)

    # Drop rows where horsepower is missing
    df.dropna(inplace=True)

    # One-hot encode origin (1=USA, 2=Europe, 3=Japan)
    df["origin"] = df["origin"].astype("category")
    df = pd.get_dummies(df, columns=["origin"], drop_first=True)

    feature_names: List[str] = [c for c in df.columns if c != "mpg"]
    X: np.ndarray = df.drop(columns=["mpg"]).values.astype(np.float64)
    y: np.ndarray = df["mpg"].values.astype(np.float64)

    return X, y, feature_names


def generate_synthetic_regression_data(
    n_samples: int = 200,
    n_features: int = 5,
    noise: float = 10.0,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate a synthetic regression dataset for quick demos.

    Parameters
    ----------
    n_samples : number of samples
    n_features : number of informative features
    noise : standard deviation of Gaussian noise added to target
    random_state : seed for reproducibility

    Returns
    -------
    X : feature matrix
    y : target vector
    """
    from sklearn.datasets import make_regression

    X, y = make_regression(
        n_samples=n_samples,
        n_features=n_features,
        noise=noise,
        random_state=random_state,
    )
    return X, y


# =========================================================================
# 3. Linear Regression (OLS)
# =========================================================================

def demo_linear_regression(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
) -> RegressionResult:
    """Ordinary Least Squares linear regression.

    Solves:  beta = (X^T X)^{-1} X^T y

    This is the closed-form (analytic) solution.  scikit-learn's
    ``LinearRegression`` uses LAPACK internally (similar to C++ Eigen's
    ``ColPivHouseholderQR`` decomposition).
    """
    from sklearn.linear_model import LinearRegression

    model = LinearRegression()
    model.fit(X_train, y_train)
    result = evaluate_model(model, X_test, y_test, "LinearRegression (OLS)")
    return result


# =========================================================================
# 4. Polynomial Regression
# =========================================================================

def demo_polynomial_regression(
    degree: int = 2,
    n_samples: int = 150,
) -> RegressionResult:
    """Polynomial regression: y = x^2 - 4x + 3 + noise.

    Demonstrates how ``PolynomialFeatures`` transforms a single feature
    into [1, x, x^2] so that a linear model can fit a quadratic curve.

    Parameters
    ----------
    degree : polynomial degree (default 2)
    n_samples : number of data points to generate
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.preprocessing import PolynomialFeatures

    rng = np.random.RandomState(42)
    x = np.linspace(0, 6, n_samples)
    y_true = x**2 - 4 * x + 3
    y = y_true + rng.normal(1, 1, n_samples)

    x_2d = x.reshape(-1, 1)

    # --- Baseline: plain linear regression (underfits) ---
    lr = LinearRegression()
    lr.fit(x_2d, y)
    y_pred_linear = lr.predict(x_2d)
    r2_linear: float = r2_score(y, y_pred_linear)

    # --- Polynomial features + linear regression ---
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    x_poly = poly.fit_transform(x_2d)

    lr_poly = LinearRegression()
    lr_poly.fit(x_poly, y)
    y_pred_poly = lr_poly.predict(x_poly)
    mse_poly: float = mean_squared_error(y, y_pred_poly)
    r2_poly: float = r2_score(y, y_pred_poly)

    return RegressionResult(
        model_name=f"PolynomialRegression (degree={degree})",
        coef=np.array(lr_poly.coef_),
        intercept=float(lr_poly.intercept_),
        mse=mse_poly,
        rmse=float(np.sqrt(mse_poly)),
        mae=float(np.mean(np.abs(y - y_pred_poly))),
        r2=r2_poly,
        extra_info={
            "linear_R2": f"{r2_linear:.4f} (underfit baseline)",
            "poly_R2": f"{r2_poly:.4f} (polynomial fit)",
        },
    )


# =========================================================================
# 5. Ridge Regression (L2 Regularization)
# =========================================================================

def demo_ridge_regression(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    alpha: float = 1.0,
) -> RegressionResult:
    """Ridge regression with L2 penalty.

    Loss = ||y - X*beta||^2 + alpha * ||beta||^2

    The L2 penalty shrinks coefficients toward zero but never sets them
    exactly to zero — it handles multicollinearity but does NOT perform
    feature selection.

    Parameters
    ----------
    alpha : regularization strength (default 1.0)
    """
    from sklearn.linear_model import Ridge

    model = Ridge(alpha=alpha)
    model.fit(X_train, y_train)
    result = evaluate_model(
        model, X_test, y_test,
        f"Ridge (alpha={alpha})",
        extra_info={"regularization": "L2"},
    )
    return result


# =========================================================================
# 6. Lasso Regression (L1 Regularization)
# =========================================================================

def demo_lasso_regression(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    alpha: float = 1.0,
) -> RegressionResult:
    """Lasso regression with L1 penalty.

    Loss = ||y - X*beta||^2 + alpha * ||beta||_1

    The L1 penalty drives some coefficients to exactly zero, effectively
    performing automatic feature selection — especially useful for
    high-dimensional data.

    Parameters
    ----------
    alpha : regularization strength (default 1.0)
    """
    from sklearn.linear_model import Lasso

    model = Lasso(alpha=alpha, max_iter=10000)
    model.fit(X_train, y_train)

    n_zero: int = int(np.sum(np.abs(model.coef_) < 1e-10))
    result = evaluate_model(
        model, X_test, y_test,
        f"Lasso (alpha={alpha})",
        extra_info={
            "regularization": "L1",
            "zero_coefficients": f"{n_zero} / {len(model.coef_)}",
        },
    )
    return result


# =========================================================================
# 7. ElasticNet Regression (L1 + L2)
# =========================================================================

def demo_elasticnet_regression(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    alpha: float = 1.0,
    l1_ratio: float = 0.5,
) -> RegressionResult:
    """ElasticNet regression combining L1 and L2 penalties.

    Loss = ||y - X*beta||^2
         + alpha * l1_ratio * ||beta||_1
         + 0.5 * alpha * (1 - l1_ratio) * ||beta||^2

    Parameters
    ----------
    alpha    : overall regularization strength
    l1_ratio : mixing parameter; 0 = pure Ridge, 1 = pure Lasso
    """
    from sklearn.linear_model import ElasticNet

    model = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=10000)
    model.fit(X_train, y_train)

    n_zero: int = int(np.sum(np.abs(model.coef_) < 1e-10))
    result = evaluate_model(
        model, X_test, y_test,
        f"ElasticNet (alpha={alpha}, l1_ratio={l1_ratio})",
        extra_info={
            "regularization": "L1 + L2",
            "zero_coefficients": f"{n_zero} / {len(model.coef_)}",
        },
    )
    return result


# =========================================================================
# 8. SGDRegressor (Gradient Descent)
# =========================================================================

def demo_sgd_regression(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    penalty: str = "l2",
    alpha: float = 0.0001,
) -> RegressionResult:
    """SGD-based regression using stochastic gradient descent.

    Unlike the closed-form OLS solver, SGDRegressor updates parameters
    iteratively:  beta <- beta - alpha * gradient

    This approach scales to very large datasets because each update only
    requires a single sample (or mini-batch).

    Parameters
    ----------
    penalty : 'l1', 'l2', 'elasticnet', or None
    alpha   : regularization coefficient
    """
    from sklearn.linear_model import SGDRegressor
    from sklearn.preprocessing import StandardScaler

    # SGD is sensitive to feature scaling — standardize first
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = SGDRegressor(
        penalty=penalty,
        alpha=alpha,
        max_iter=1000,
        tol=1e-4,
        random_state=42,
    )
    model.fit(X_train_s, y_train)

    # Evaluate on scaled test data
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    y_pred = model.predict(X_test_s)
    mse = mean_squared_error(y_test, y_pred)
    rmse = float(np.sqrt(mse))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    return RegressionResult(
        model_name=f"SGDRegressor (penalty={penalty})",
        coef=np.array(model.coef_),
        intercept=float(model.intercept_),
        mse=mse,
        rmse=rmse,
        mae=mae,
        r2=r2,
        extra_info={"solver": "Stochastic Gradient Descent", "scaled": True},
    )


# =========================================================================
# 9. Regularization Strength Comparison
# =========================================================================

def regularization_comparison(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
) -> str:
    """Compare Ridge and Lasso across multiple alpha values.

    Returns a formatted table showing how R-squared and the number of
    non-zero coefficients change with regularization strength.
    """
    from sklearn.linear_model import Lasso, Ridge
    from sklearn.metrics import r2_score

    alphas: List[float] = [0.01, 0.1, 1.0, 10.0, 100.0]
    lines: List[str] = []
    lines.append("")
    lines.append(f"{'Alpha':>8s} | {'Ridge R2':>10s} | {'Lasso R2':>10s} | "
                 f"{'Lasso NZ':>10s}")
    lines.append("-" * 55)

    for a in alphas:
        ridge = Ridge(alpha=a)
        ridge.fit(X_train, y_train)
        r2_ridge = r2_score(y_test, ridge.predict(X_test))

        lasso = Lasso(alpha=a, max_iter=10000)
        lasso.fit(X_train, y_train)
        y_pred_lasso = lasso.predict(X_test)
        r2_lasso = r2_score(y_test, y_pred_lasso)
        n_nonzero = int(np.sum(np.abs(lasso.coef_) > 1e-10))

        lines.append(
            f"{a:>8.2f} | {r2_ridge:>10.4f} | {r2_lasso:>10.4f} | "
            f"{n_nonzero:>10d}"
        )

    lines.append("-" * 55)
    lines.append("NZ = number of non-zero coefficients (feature selection)")
    return "\n".join(lines)


# =========================================================================
# 10. C++ Eigen Comparison Note
# =========================================================================

CPP_EIGEN_COMPARISON: str = """
================================================================
  C++ Eigen Least-Squares vs Python scikit-learn LinearRegression
================================================================

Both solve the same ordinary least squares problem:

    beta = (X^T X)^{-1} X^T y

C++ Eigen implementation (ColPivHouseholderQR decomposition):

    // g++ -O2 -I /path/to/eigen main.cpp -o regression
    #include <Eigen/Dense>
    #include <iostream>

    int main() {
        // Design matrix X (m x n) and target vector y (m x 1)
        Eigen::MatrixXd X(m, n);
        Eigen::VectorXd y(m);

        // ... fill X and y with data ...

        // Solve via column-pivoted QR (numerically stable)
        Eigen::VectorXd beta =
            X.colPivHouseholderQr().solve(y);

        std::cout << "Coefficients:\\n" << beta << std::endl;
        return 0;
    }

Python scikit-learn implementation:

    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(X_train, y_train)
    print("Coefficients:", model.coef_)
    print("Intercept:", model.intercept_)

Key differences:
  - Eigen uses LAPACK-level QR decomposition (ColPivHouseholderQR)
    directly in compiled C++, yielding lower latency per call.
  - scikit-learn wraps the same LAPACK routines via NumPy/SciPy;
    the numerical result is identical up to floating-point precision.
  - For production latency-critical services, a C++ Eigen solver
    embedded in a microservice can reduce per-prediction overhead.
  - For rapid prototyping, EDA, and model selection, Python is
    significantly faster to develop and iterate.
================================================================
"""


# =========================================================================
# 11. Enterprise Application Examples
# =========================================================================

def enterprise_price_prediction_demo() -> str:
    """Simulated enterprise example: real-estate price prediction.

    Mirrors the Zillow Zestimate approach described in the tutorial:
    features include area, age, location score, school rating, etc.
    """
    from sklearn.linear_model import Ridge
    from sklearn.metrics import r2_score
    from sklearn.model_selection import train_test_split

    rng = np.random.RandomState(42)
    n: int = 500

    # Features: area (sqft), house_age, location_score, school_rating,
    #           crime_rate, distance_to_center (km)
    area = rng.normal(1800, 400, n).clip(500, 5000)
    age = rng.uniform(0, 50, n)
    location = rng.uniform(1, 10, n)
    school = rng.uniform(1, 10, n)
    crime = rng.uniform(0, 10, n)
    distance = rng.exponential(10, n).clip(1, 50)

    # Simulated price formula (in $1000s)
    price = (
        0.15 * area
        - 0.8 * age
        + 12 * location
        + 8 * school
        - 5 * crime
        - 2 * distance
        + rng.normal(0, 30, n)
    )

    X = np.column_stack([area, age, location, school, crime, distance])
    X_train, X_test, y_train, y_test = train_test_split(
        X, price, test_size=0.2, random_state=42
    )

    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)

    feature_names = [
        "area", "house_age", "location_score",
        "school_rating", "crime_rate", "distance_to_center",
    ]
    coef_lines = "\n".join(
        f"    {name:>22s}: {c:+.4f}" for name, c in zip(feature_names, model.coef_)
    )

    return f"""
----------------------------------------------------------------
  Enterprise Example 1: Real-Estate Price Prediction (Zillow-style)
----------------------------------------------------------------
  Features: area, house_age, location_score, school_rating,
            crime_rate, distance_to_center
  Model   : Ridge Regression (alpha=1.0)
  R-squared on holdout: {r2:.4f}

  Feature contributions:
{coef_lines}
  Intercept: {model.intercept_:+.4f}
  Interpretation: each additional sqft adds ~$150 to predicted price.
----------------------------------------------------------------
"""


def enterprise_demand_forecasting_demo() -> str:
    """Simulated enterprise example: retail demand forecasting.

    Mirrors the Amazon demand prediction approach from the tutorial:
    features include historical sales, price, discount, seasonality.
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import PolynomialFeatures

    rng = np.random.RandomState(123)
    n: int = 600

    historical_sales = rng.normal(500, 150, n).clip(50, 1500)
    price = rng.uniform(10, 100, n)
    discount = rng.uniform(0, 0.5, n)
    month = rng.randint(1, 13, n)
    is_holiday = rng.choice([0, 1], n, p=[0.85, 0.15])

    # Demand formula: nonlinear price effect + seasonality
    demand = (
        0.6 * historical_sales
        - 2.5 * price
        + 200 * discount
        + 50 * np.sin(2 * np.pi * month / 12)
        + 150 * is_holiday
        + rng.normal(0, 40, n)
    ).clip(0, None)

    X = np.column_stack([
        historical_sales, price, discount, month, is_holiday,
    ])
    X_train, X_test, y_train, y_test = train_test_split(
        X, demand, test_size=0.2, random_state=42
    )

    # Polynomial features to capture nonlinear price-discount interaction
    poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
    X_train_p = poly.fit_transform(X_train)
    X_test_p = poly.transform(X_test)

    model = LinearRegression()
    model.fit(X_train_p, y_train)
    y_pred = model.predict(X_test_p)
    r2 = r2_score(y_test, y_pred)

    return f"""
----------------------------------------------------------------
  Enterprise Example 2: Retail Demand Forecasting (Amazon-style)
----------------------------------------------------------------
  Features: historical_sales, price, discount, month, is_holiday
  Model   : LinearRegression + PolynomialFeatures (degree=2,
            interaction_only=True — captures price*discount effect)
  R-squared on holdout: {r2:.4f}

  Note: Polynomial features capture the interaction between
  price and discount — a 10% discount on a $50 item has a
  different marginal effect than on a $200 item.
----------------------------------------------------------------
"""


def enterprise_trend_analysis_demo() -> str:
    """Simulated enterprise example: battery degradation trend analysis.

    Mirrors the Tesla battery life prediction approach from the tutorial:
    features include charge cycles, temperature, depth of discharge.
    """
    from sklearn.linear_model import Lasso
    from sklearn.metrics import r2_score
    from sklearn.model_selection import train_test_split

    rng = np.random.RandomState(7)
    n: int = 400

    charge_cycles = rng.uniform(0, 2000, n)
    temperature = rng.normal(25, 10, n)
    depth_of_discharge = rng.uniform(0.2, 1.0, n)
    internal_resistance = rng.uniform(0.01, 0.1, n)
    charge_rate = rng.uniform(0.5, 3.0, n)

    # Battery capacity retention (%)
    retention = (
        100
        - 0.015 * charge_cycles
        - 0.3 * np.abs(temperature - 25)
        - 10 * depth_of_discharge
        - 50 * internal_resistance
        - 2 * charge_rate
        + rng.normal(0, 2, n)
    ).clip(0, 100)

    X = np.column_stack([
        charge_cycles, temperature, depth_of_discharge,
        internal_resistance, charge_rate,
    ])
    X_train, X_test, y_train, y_test = train_test_split(
        X, retention, test_size=0.2, random_state=42
    )

    model = Lasso(alpha=0.1, max_iter=10000)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)

    feature_names = [
        "charge_cycles", "temperature", "depth_of_discharge",
        "internal_resistance", "charge_rate",
    ]
    coef_lines = "\n".join(
        f"    {name:>24s}: {c:+.6f}" for name, c in zip(feature_names, model.coef_)
    )
    n_zero = int(np.sum(np.abs(model.coef_) < 1e-10))

    return f"""
----------------------------------------------------------------
  Enterprise Example 3: Battery Degradation Trend (Tesla-style)
----------------------------------------------------------------
  Features: charge_cycles, temperature, depth_of_discharge,
            internal_resistance, charge_rate
  Model   : Lasso (alpha=0.1) — automatic feature selection
  R-squared on holdout: {r2:.4f}
  Zero coefficients   : {n_zero} / {len(model.coef_)}

  Feature contributions:
{coef_lines}
  Intercept: {model.intercept_:+.4f}

  Lasso identified charge_rate as less important (coefficient
  driven toward zero), simplifying the model for deployment.
----------------------------------------------------------------
"""


# =========================================================================
# 12. Manual Implementation: Closed-Form OLS with NumPy
# =========================================================================

def manual_ols_demo(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
) -> RegressionResult:
    """Implement OLS regression from scratch using the normal equation.

    beta = (X^T X)^{-1} X^T y

    This mirrors what LinearRegression does internally and is directly
    comparable to the C++ Eigen implementation shown above.
    """
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    # Add bias column (column of ones) to X
    ones_train = np.ones((X_train.shape[0], 1))
    X_train_b = np.hstack([ones_train, X_train])

    ones_test = np.ones((X_test.shape[0], 1))
    X_test_b = np.hstack([ones_test, X_test])

    # Normal equation: beta = (X^T X)^{-1} X^T y
    XtX = X_train_b.T @ X_train_b
    Xty = X_train_b.T @ y_train
    beta = np.linalg.solve(XtX, Xty)  # numerically more stable than inv

    intercept = float(beta[0])
    coef = beta[1:]

    y_pred = X_test_b @ beta
    mse = mean_squared_error(y_test, y_pred)
    rmse = float(np.sqrt(mse))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    return RegressionResult(
        model_name="Manual OLS (Normal Equation)",
        coef=coef,
        intercept=intercept,
        mse=mse,
        rmse=rmse,
        mae=mae,
        r2=r2,
        extra_info={
            "method": "beta = (X^T X)^{-1} X^T y",
            "note": "Comparable to C++ Eigen ColPivHouseholderQR.solve()",
        },
    )


# =========================================================================
# 13. Main Entry Point
# =========================================================================

def main() -> None:
    """Run all regression model demonstrations."""
    from sklearn.model_selection import train_test_split

    print("=" * 70)
    print("  Day 85: Regression Models (回归模型)")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Load real dataset
    # ------------------------------------------------------------------
    print("\n>>> Loading Auto MPG dataset from UCI ...")
    try:
        X, y, feature_names = load_auto_mpg_dataset()
        print(f"    Loaded {X.shape[0]} samples, {X.shape[1]} features")
        print(f"    Features: {feature_names}")
    except Exception as exc:
        print(f"    Could not load UCI dataset ({exc}); using synthetic data.")
        X, y = generate_synthetic_regression_data(n_samples=300, n_features=8)
        feature_names = [f"x{i}" for i in range(X.shape[1])]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=0.8, random_state=3
    )

    # ------------------------------------------------------------------
    # 1. Linear Regression (OLS)
    # ------------------------------------------------------------------
    print("\n--- 1. Linear Regression (OLS) ---")
    result_lr = demo_linear_regression(X_train, X_test, y_train, y_test)
    print(result_lr.summary())

    # ------------------------------------------------------------------
    # 2. Polynomial Regression
    # ------------------------------------------------------------------
    print("\n--- 2. Polynomial Regression ---")
    result_poly = demo_polynomial_regression(degree=2)
    print(result_poly.summary())

    # ------------------------------------------------------------------
    # 3. Ridge Regression (L2)
    # ------------------------------------------------------------------
    print("\n--- 3. Ridge Regression (L2 Regularization) ---")
    result_ridge = demo_ridge_regression(X_train, X_test, y_train, y_test, alpha=1.0)
    print(result_ridge.summary())

    # ------------------------------------------------------------------
    # 4. Lasso Regression (L1)
    # ------------------------------------------------------------------
    print("\n--- 4. Lasso Regression (L1 Regularization) ---")
    result_lasso = demo_lasso_regression(X_train, X_test, y_train, y_test, alpha=1.0)
    print(result_lasso.summary())

    # ------------------------------------------------------------------
    # 5. ElasticNet Regression (L1 + L2)
    # ------------------------------------------------------------------
    print("\n--- 5. ElasticNet Regression (L1 + L2) ---")
    result_en = demo_elasticnet_regression(
        X_train, X_test, y_train, y_test, alpha=1.0, l1_ratio=0.5,
    )
    print(result_en.summary())

    # ------------------------------------------------------------------
    # 6. SGDRegressor (Gradient Descent)
    # ------------------------------------------------------------------
    print("\n--- 6. SGDRegressor (Stochastic Gradient Descent) ---")
    result_sgd = demo_sgd_regression(
        X_train, X_test, y_train, y_test, penalty="l2", alpha=0.0001,
    )
    print(result_sgd.summary())

    # ------------------------------------------------------------------
    # 7. Manual OLS (Normal Equation)
    # ------------------------------------------------------------------
    print("\n--- 7. Manual OLS (Normal Equation) ---")
    result_manual = manual_ols_demo(X_train, X_test, y_train, y_test)
    print(result_manual.summary())

    # ------------------------------------------------------------------
    # 8. Regularization Strength Comparison Table
    # ------------------------------------------------------------------
    print("\n--- 8. Regularization Strength Comparison ---")
    table = regularization_comparison(X_train, X_test, y_train, y_test)
    print(table)

    # ------------------------------------------------------------------
    # 9. C++ Eigen Comparison
    # ------------------------------------------------------------------
    print(CPP_EIGEN_COMPARISON)

    # ------------------------------------------------------------------
    # 10. Enterprise Examples
    # ------------------------------------------------------------------
    print(enterprise_price_prediction_demo())
    print(enterprise_demand_forecasting_demo())
    print(enterprise_trend_analysis_demo())

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  Summary of All Models (sorted by R-squared)")
    print("=" * 70)
    all_results: List[RegressionResult] = [
        result_lr, result_poly, result_ridge, result_lasso,
        result_en, result_sgd, result_manual,
    ]
    for r in sorted(all_results, key=lambda x: x.r2, reverse=True):
        print(f"  {r.model_name:45s}  R2={r.r2:.4f}  RMSE={r.rmse:.4f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
