"""
Day 88 - Neural Network Models
================================

This module demonstrates neural network fundamentals using scikit-learn's
MLPClassifier, a from-scratch NumPy implementation, and digit recognition.

C++ comparison note:
    In C++, a custom neural network requires manually allocating weight
    matrices, implementing matrix multiplication loops, coding each
    activation function, writing the backpropagation chain-rule gradient
    computations, and managing memory for every layer.  Python achieves
    the same result in a few lines via scikit-learn or NumPy vectorised
    operations, trading raw execution speed for dramatically shorter
    development time and fewer bugs.
"""

from __future__ import annotations

import math
import warnings
from typing import Sequence

import numpy as np
from sklearn.datasets import load_digits, load_iris
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# 1. Activation Functions (from scratch, for educational purposes)
# ---------------------------------------------------------------------------
# In C++ you would write each of these as a loop over an array.
# NumPy applies them element-wise in one vectorised call.

def sigmoid(x: np.ndarray) -> np.ndarray:
    """Sigmoid: f(x) = 1 / (1 + exp(-x)).  Output range (0, 1)."""
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))


def sigmoid_derivative(x: np.ndarray) -> np.ndarray:
    """Derivative of sigmoid: f'(x) = f(x) * (1 - f(x))."""
    s = sigmoid(x)
    return s * (1.0 - s)


def relu(x: np.ndarray) -> np.ndarray:
    """ReLU: f(x) = max(0, x).  Most commonly used in deep networks."""
    return np.maximum(0, x)


def relu_derivative(x: np.ndarray) -> np.ndarray:
    """Derivative of ReLU: 1 if x > 0, else 0."""
    return (x > 0).astype(np.float64)


def tanh_activation(x: np.ndarray) -> np.ndarray:
    """Tanh: f(x) = (e^x - e^-x) / (e^x + e^-x).  Output range (-1, 1)."""
    return np.tanh(x)


def tanh_derivative(x: np.ndarray) -> np.ndarray:
    """Derivative of tanh: f'(x) = 1 - tanh(x)^2."""
    return 1.0 - np.tanh(x) ** 2


def leaky_relu(x: np.ndarray, alpha: float = 0.01) -> np.ndarray:
    """Leaky ReLU: x if x > 0, else alpha * x."""
    return np.where(x > 0, x, alpha * x)


def leaky_relu_derivative(x: np.ndarray, alpha: float = 0.01) -> np.ndarray:
    """Derivative of Leaky ReLU."""
    return np.where(x > 0, 1.0, alpha)


# ---------------------------------------------------------------------------
# 2. From-Scratch Neural Network (NumPy only)
# ---------------------------------------------------------------------------
# C++ comparison:
#   A C++ implementation would need explicit loops for forward/backward
#   passes, manual memory management for layer outputs, and careful
#   index bookkeeping for gradient matrices.  NumPy's vectorised dot
#   products and broadcasting eliminate all of that boilerplate.

ACTIVATION_MAP: dict[str, tuple] = {
    "sigmoid": (sigmoid, sigmoid_derivative),
    "relu": (relu, relu_derivative),
    "tanh": (tanh_activation, tanh_derivative),
    "leaky_relu": (leaky_relu, leaky_relu_derivative),
}


class SimpleNeuralNetwork:
    """
    A minimal fully-connected neural network trained with backpropagation.

    Architecture: input -> [hidden layers] -> output (sigmoid for binary,
    softmax for multi-class).

    Parameters
    ----------
    layer_sizes : tuple[int, ...]
        Number of neurons per layer, e.g. (4, 32, 3) for 4 inputs,
        one hidden layer of 32 neurons, and 3 output classes.
    activation : str
        Activation function for hidden layers ('sigmoid', 'relu', 'tanh',
        'leaky_relu').
    learning_rate : float
        Step size for gradient descent updates.
    epochs : int
        Number of full passes over the training data.
    random_state : int | None
        Seed for reproducible weight initialisation.
    """

    def __init__(
        self,
        layer_sizes: tuple[int, ...],
        activation: str = "relu",
        learning_rate: float = 0.01,
        epochs: int = 1000,
        random_state: int | None = None,
    ) -> None:
        self.layer_sizes = layer_sizes
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.rng = np.random.RandomState(random_state)

        act_func, act_deriv = ACTIVATION_MAP.get(activation, ACTIVATION_MAP["relu"])
        self._activation = act_func
        self._activation_derivative = act_deriv

        # Xavier / He initialisation for weights
        self.weights: list[np.ndarray] = []
        self.biases: list[np.ndarray] = []
        for i in range(len(layer_sizes) - 1):
            scale = np.sqrt(2.0 / layer_sizes[i])
            w = self.rng.randn(layer_sizes[i], layer_sizes[i + 1]) * scale
            b = np.zeros((1, layer_sizes[i + 1]))
            self.weights.append(w)
            self.biases.append(b)

    # -- forward propagation ------------------------------------------------

    def _forward(self, X: np.ndarray) -> tuple[list[np.ndarray], list[np.ndarray]]:
        """
        Compute forward propagation through all layers.

        Returns
        -------
        activations : list of layer outputs (a^[0] .. a^[L])
        zs          : list of pre-activation values (z^[1] .. z^[L])
        """
        activations = [X]
        zs: list[np.ndarray] = []
        a = X
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            z = a @ w + b
            zs.append(z)
            if i < len(self.weights) - 1:
                a = self._activation(z)
            else:
                # Output layer: softmax for multi-class
                exp_z = np.exp(z - np.max(z, axis=1, keepdims=True))
                a = exp_z / np.sum(exp_z, axis=1, keepdims=True)
            activations.append(a)
        return activations, zs

    # -- backpropagation ----------------------------------------------------

    def _backward(
        self,
        activations: list[np.ndarray],
        zs: list[np.ndarray],
        y_true: np.ndarray,
    ) -> tuple[list[np.ndarray], list[np.ndarray]]:
        """
        Compute gradients via backpropagation (chain rule).

        In C++ this requires explicit nested loops over every neuron and
        every weight.  Here, NumPy matrix operations handle it in bulk.
        """
        m = y_true.shape[0]
        num_layers = len(self.weights)
        dw_list: list[np.ndarray] = [None] * num_layers  # type: ignore[list-item]
        db_list: list[np.ndarray] = [None] * num_layers  # type: ignore[list-item]

        # Output layer error (softmax + cross-entropy simplification)
        delta = activations[-1] - y_true
        for i in reversed(range(num_layers)):
            dw_list[i] = (activations[i].T @ delta) / m
            db_list[i] = np.sum(delta, axis=0, keepdims=True) / m
            if i > 0:
                delta = (delta @ self.weights[i].T) * self._activation_derivative(zs[i - 1])

        return dw_list, db_list

    # -- training -----------------------------------------------------------

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SimpleNeuralNetwork":
        """
        Train the network using mini-batch gradient descent.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
        y : ndarray of shape (n_samples,) with integer class labels
        """
        n_classes = self.layer_sizes[-1]
        y_one_hot = np.eye(n_classes)[y]

        for epoch in range(self.epochs):
            activations, zs = self._forward(X)
            dw_list, db_list = self._backward(activations, zs, y_one_hot)
            for i in range(len(self.weights)):
                self.weights[i] -= self.learning_rate * dw_list[i]
                self.biases[i] -= self.learning_rate * db_list[i]

            if (epoch + 1) % 200 == 0:
                loss = -np.mean(
                    np.sum(
                        y_one_hot * np.log(np.clip(activations[-1], 1e-12, 1.0)),
                        axis=1,
                    )
                )
                print(f"  Epoch {epoch + 1:>5d}/{self.epochs}  loss={loss:.4f}")

        return self

    # -- prediction ---------------------------------------------------------

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return class probabilities for each sample."""
        activations, _ = self._forward(X)
        return activations[-1]

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return predicted class labels."""
        return np.argmax(self.predict_proba(X), axis=1)


# ---------------------------------------------------------------------------
# 3. Enterprise Example A -- Digit Recognition with MLPClassifier
# ---------------------------------------------------------------------------
# C++ comparison:
#   Building a digit recogniser in C++ from scratch means writing matrix
#   multiplication, activation, loss computation, and optimiser loops.
#   With scikit-learn, the entire pipeline fits in ~20 lines.

def digit_recognition_demo() -> None:
    """Train an MLPClassifier on the sklearn digits dataset (8x8 images)."""
    print("=" * 70)
    print("  Enterprise Example A: Handwritten Digit Recognition (MLP)")
    print("=" * 70)

    digits = load_digits()
    X, y = digits.data, digits.target
    print(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features (8x8 pixel images)")
    print(f"Classes: {digits.target_names.tolist()}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Three hidden layers with 128, 64, and 32 neurons
    model = MLPClassifier(
        hidden_layer_sizes=(128, 64, 32),
        activation="relu",
        solver="adam",
        learning_rate="adaptive",
        learning_rate_init=0.001,
        max_iter=500,
        alpha=1e-4,  # L2 regularisation
        batch_size="auto",
        random_state=42,
        tol=1e-4,
        early_stopping=True,
        validation_fraction=0.1,
    )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nTest accuracy: {acc:.4f}")
    print(f"Iterations to converge: {model.n_iter_}")
    print(f"Loss at convergence: {model.loss_:.6f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))
    print()


# ---------------------------------------------------------------------------
# 4. Enterprise Example B -- Iris Classification with from-scratch NN
# ---------------------------------------------------------------------------

def iris_scratch_nn_demo() -> None:
    """Classify Iris species using our from-scratch SimpleNeuralNetwork."""
    print("=" * 70)
    print("  Enterprise Example B: Iris Classification (from-scratch NN)")
    print("=" * 70)

    iris = load_iris()
    X, y = iris.data, iris.target

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    nn = SimpleNeuralNetwork(
        layer_sizes=(4, 32, 16, 3),
        activation="relu",
        learning_rate=0.05,
        epochs=2000,
        random_state=42,
    )

    print("\nTraining from-scratch neural network ...")
    nn.fit(X_train_scaled, y_train)

    y_pred = nn.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nTest accuracy: {acc:.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, target_names=iris.target_names))
    print()


# ---------------------------------------------------------------------------
# 5. Enterprise Example C -- Iris with MLPClassifier (hyperparameter study)
# ---------------------------------------------------------------------------

def iris_mlpclassifier_demo() -> None:
    """Compare different MLPClassifier architectures on the Iris dataset."""
    print("=" * 70)
    print("  Enterprise Example C: Iris MLPClassifier Hyperparameter Study")
    print("=" * 70)

    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=3, stratify=y,
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    configs: list[dict[str, object]] = [
        {"hidden_layer_sizes": (1,), "label": "1 neuron"},
        {"hidden_layer_sizes": (10,), "label": "10 neurons"},
        {"hidden_layer_sizes": (32, 32, 32), "label": "3x32 neurons"},
        {"hidden_layer_sizes": (64, 64), "label": "2x64 neurons"},
    ]

    print(f"\n{'Architecture':<25s} {'Accuracy':>10s} {'Iterations':>12s}")
    print("-" * 50)

    for cfg in configs:
        model = MLPClassifier(
            hidden_layer_sizes=cfg["hidden_layer_sizes"],  # type: ignore[arg-type]
            activation="relu",
            solver="lbfgs",
            learning_rate="adaptive",
            random_state=42,
            max_iter=2000,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            model.fit(X_train_s, y_train)

        acc = accuracy_score(y_test, model.predict(X_test_s))
        print(f"{str(cfg['label']):<25s} {acc:>10.4f} {model.n_iter_:>12d}")

    print()


# ---------------------------------------------------------------------------
# 6. Activation function visualisation (text-based)
# ---------------------------------------------------------------------------

def activation_function_comparison() -> None:
    """Print a small table comparing activation functions at key points."""
    print("=" * 70)
    print("  Activation Function Comparison")
    print("=" * 70)

    test_values = np.array([-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0])
    funcs = {
        "Sigmoid": sigmoid,
        "Tanh": tanh_activation,
        "ReLU": relu,
        "Leaky ReLU (a=0.01)": lambda x: leaky_relu(x, 0.01),
    }

    header = f"{'x':>7s}"
    for name in funcs:
        header += f" {name:>20s}"
    print(f"\n{header}")
    print("-" * (7 + 21 * len(funcs)))

    for x_val in test_values:
        row = f"{x_val:>7.2f}"
        for func in funcs.values():
            row += f" {func(np.array([x_val]))[0]:>20.6f}"
        print(row)

    print(
        "\nNotes:\n"
        "  - Sigmoid outputs (0,1); good for probabilities but suffers from\n"
        "    vanishing gradients at extremes.\n"
        "  - Tanh outputs (-1,1); zero-centred, better gradient symmetry.\n"
        "  - ReLU is the default for hidden layers; simple and effective.\n"
        "  - Leaky ReLU avoids 'dead neurons' by allowing small negative values."
    )
    print()


# ---------------------------------------------------------------------------
# 7. Educational: single neuron forward & backward pass
# ---------------------------------------------------------------------------

def single_neuron_demo() -> None:
    """
    Walk through the forward and backward pass for a single neuron.

    This mirrors what a C++ tutorial would demonstrate with explicit loops,
    but here NumPy handles the arithmetic in vectorised form.
    """
    print("=" * 70)
    print("  Educational: Single Neuron Forward & Backward Pass")
    print("=" * 70)

    # Two inputs, one output neuron with sigmoid activation
    X = np.array([[0.5, 0.3], [0.9, 0.1], [0.4, 0.8]])
    y = np.array([[0], [1], [1]])

    rng = np.random.RandomState(42)
    w = rng.randn(2, 1) * 0.5
    b = np.zeros((1, 1))
    lr = 0.5

    print(f"\nInitial weights:\n{w.ravel()}")
    print(f"Initial bias: {b.ravel()}")

    for step in range(1, 6):
        # Forward
        z = X @ w + b
        a = sigmoid(z)
        # Binary cross-entropy loss
        loss = -np.mean(y * np.log(a + 1e-12) + (1 - y) * np.log(1 - a + 1e-12))

        # Backward
        dz = a - y  # derivative of BCE + sigmoid simplifies to this
        dw = X.T @ dz / len(X)
        db = np.mean(dz, axis=0, keepdims=True)

        # Update
        w -= lr * dw
        b -= lr * db

        print(f"  Step {step}: loss={loss:.6f}  preds={a.ravel().round(3)}")

    print(f"\nFinal weights: {w.ravel().round(4)}")
    print(f"Final bias:    {b.ravel().round(4)}")
    print()


# ---------------------------------------------------------------------------
# 8. Performance comparison note
# ---------------------------------------------------------------------------

def performance_comparison_note() -> None:
    """Print a summary comparing Python vs C++ for neural network tasks."""
    print("=" * 70)
    print("  Python Neural Net vs C++ Custom Neural Network Implementation")
    print("=" * 70)
    print("""
    Aspect                  Python (NumPy/sklearn)        C++ (from scratch)
    ----------------------  ----------------------------  -----------------------------
    Development time        Very short (hours)            Long (days to weeks)
    Lines of code           ~50-200                       ~500-2000+
    Matrix operations       Vectorised (BLAS/LAPACK)      Manual loops or Eigen/etc.
    Activation functions    One-liner (np.maximum, etc.)  Per-element loops
    Backpropagation         Automatic or a few lines      Manual chain-rule loops
    Memory management       Garbage collected             Manual new/delete, RAII
    GPU acceleration        Easy (PyTorch/TensorFlow)     CUDA / OpenCL (complex)
    Runtime speed           Slower (interpreter overhead) Faster (compiled, optimised)
    Debugging ease          High (REPL, rich tooling)     Lower (gdb, sanitizers)
    Ecosystem               Massive (sklearn, torch, ..)  Limited, must build or bind

    Bottom line: Python excels for prototyping, research, and most production
    ML tasks.  C++ wins when you need ultra-low-latency inference on embedded
    or edge devices, or when every microsecond counts in a hot loop.
    """)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all demonstrations."""
    activation_function_comparison()
    single_neuron_demo()
    iris_scratch_nn_demo()
    iris_mlpclassifier_demo()
    digit_recognition_demo()
    performance_comparison_note()


if __name__ == "__main__":
    main()
