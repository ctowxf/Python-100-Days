"""
Day 68 - NumPy Fundamentals: ndarray Creation, Attributes, Indexing, Slicing, Reshape
=======================================================================================

This module provides a comprehensive walkthrough of NumPy's core ndarray operations
with enterprise-grade examples in sensor data processing, image pixel manipulation,
and financial time series analysis.

NumPy vs C++ Comparison Notes (embedded in docstrings and comments):
  - NumPy ndarray  vs  C++ Eigen::Matrix
  - NumPy vectorization  vs  C++ element-wise loops

Requirements:
    pip install numpy

Reference:
    Python-100-Days / Day66-80 / 68.NumPy的应用-1.md
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from typing import Any


# ---------------------------------------------------------------------------
# 1. ndarray Creation
# ---------------------------------------------------------------------------

def demo_array_creation() -> None:
    """Demonstrate the many ways to create NumPy ndarrays.

    C++ Comparison: NumPy ndarray vs C++ Eigen::Matrix
    ---------------------------------------------------
    In C++ with Eigen, you would write:
        Eigen::MatrixXi m(3, 4);           // 3x4 int matrix (uninitialized)
        Eigen::MatrixXd::Zero(3, 4);       // 3x4 double matrix filled with 0
        Eigen::MatrixXd::Ones(3, 4);       // 3x4 double matrix filled with 1
        Eigen::MatrixXd::Identity(4, 4);   // 4x4 identity matrix
    NumPy equivalents:
        np.empty((3, 4), dtype=np.int32)   # uninitialized
        np.zeros((3, 4))                   # filled with 0
        np.ones((3, 4))                    # filled with 1
        np.eye(4)                          # 4x4 identity

    Key difference: Eigen matrices are fixed-size at compile time (or use
    Dynamic), while NumPy ndarrays are always dynamically sized at runtime.
    Eigen performs compile-time template optimization; NumPy delegates to
    optimized C/Fortran BLAS/LAPACK at runtime.
    """
    print("=" * 70)
    print("1. ndarray Creation Methods")
    print("=" * 70)

    # --- Method 1: From Python list ---
    array1: NDArray[np.int_] = np.array([1, 2, 3, 4, 5])
    array2: NDArray[np.int_] = np.array([[1, 2, 3], [4, 5, 6]])
    print(f"From list (1D):  {array1}")
    print(f"From list (2D):\n{array2}")

    # --- Method 2: arange (start, stop, step) ---
    array3: NDArray[np.int_] = np.arange(0, 20, 2)
    print(f"\narange(0, 20, 2): {array3}")

    # --- Method 3: linspace (start, stop, num) -> arithmetic sequence ---
    array4: NDArray[np.float64] = np.linspace(-1, 1, 11)
    print(f"linspace(-1, 1, 11): {array4}")

    # --- Method 4: logspace -> geometric sequence ---
    # 2^1, 2^2, ..., 2^10
    array5: NDArray[np.float64] = np.logspace(1, 10, num=10, base=2)
    print(f"logspace(1, 10, num=10, base=2): {array5}")

    # --- Method 5: fromstring ---
    array6: NDArray[np.int64] = np.fromstring("1, 2, 3, 4, 5", sep=",", dtype="i8")
    print(f"fromstring: {array6}")

    # --- Method 6: fromiter (generator / iterator) ---
    def fib(how_many: int) -> Any:
        """Yield Fibonacci numbers."""
        a, b = 0, 1
        for _ in range(how_many):
            a, b = b, a + b
            yield a

    array7: NDArray[np.int64] = np.fromiter(fib(20), dtype="i8")
    print(f"fromiter (Fibonacci): {array7}")

    # --- Method 7: Random arrays ---
    # Uniform [0, 1)
    array8: NDArray[np.float64] = np.random.rand(10)
    print(f"\nrand(10) [0,1):      {array8.round(4)}")

    # Random integers [1, 100)
    array9: NDArray[np.int_] = np.random.randint(1, 100, 10)
    print(f"randint(1,100,10):   {array9}")

    # Normal distribution: mu=50, sigma=10
    array10: NDArray[np.float64] = np.random.normal(50, 10, 20)
    print(f"normal(50,10,20):    {array10.round(2)}")

    # 2D random float array
    array11: NDArray[np.float64] = np.random.rand(3, 4)
    print(f"rand(3,4):\n{array11.round(4)}")

    # 3D random integer array
    array12: NDArray[np.int_] = np.random.randint(1, 100, (3, 4, 5))
    print(f"randint(1,100,(3,4,5)) shape: {array12.shape}")

    # --- Method 8: zeros, ones, full ---
    array13: NDArray[np.float64] = np.zeros((3, 4))
    array14: NDArray[np.float64] = np.ones((3, 4))
    array15: NDArray[np.int_] = np.full((3, 4), 10)
    print(f"\nzeros(3,4):\n{array13}")
    print(f"ones(3,4):\n{array14}")
    print(f"full((3,4), 10):\n{array15}")

    # --- Method 9: Identity matrix ---
    print(f"\neye(4):\n{np.eye(4)}")

    # --- Method 10: zeros_like / ones_like / full_like ---
    template: NDArray[np.int_] = np.array([[1, 2], [3, 4], [5, 6]])
    print(f"\nzeros_like(template): {np.zeros_like(template).shape}")
    print(f"ones_like(template):  {np.ones_like(template).shape}")
    print(f"full_like(template, 7):\n{np.full_like(template, 7)}")


# ---------------------------------------------------------------------------
# 2. Array Attributes
# ---------------------------------------------------------------------------

def demo_array_attributes() -> None:
    """Inspect fundamental ndarray attributes: size, shape, dtype, ndim, itemsize, nbytes.

    C++ Comparison: NumPy ndarray vs C++ Eigen::Matrix
    ---------------------------------------------------
    NumPy attribute        | Eigen equivalent
    -----------------------|---------------------------------------
    arr.shape              | m.rows(), m.cols()  (or m.size() for vector)
    arr.size               | m.size()            (total element count)
    arr.dtype              | template param, e.g. MatrixXd (double)
    arr.ndim               | always 2 for Eigen matrices
    arr.itemsize           | sizeof(Scalar)
    arr.nbytes             | m.size() * sizeof(Scalar)
    arr.strides            | no direct equivalent; Eigen uses column-major
    """
    print("\n" + "=" * 70)
    print("2. Array Attributes")
    print("=" * 70)

    arr_1d: NDArray[np.int_] = np.arange(1, 100, 2)
    arr_2d: NDArray[np.float64] = np.random.rand(3, 4)
    arr_3d: NDArray[np.uint8] = np.random.randint(0, 256, (100, 80, 3), dtype=np.uint8)

    for name, arr in [("1D arange", arr_1d), ("2D rand", arr_2d), ("3D image-like", arr_3d)]:
        print(f"\n--- {name} ---")
        print(f"  .size      = {arr.size}       (total elements)")
        print(f"  .shape     = {arr.shape}      (dimension tuple)")
        print(f"  .dtype     = {arr.dtype}      (element type)")
        print(f"  .ndim      = {arr.ndim}       (number of axes)")
        print(f"  .itemsize  = {arr.itemsize} byte(s) per element")
        print(f"  .nbytes    = {arr.nbytes} bytes total")
        print(f"  .strides   = {arr.strides} (bytes to step along each axis)")


# ---------------------------------------------------------------------------
# 3. Indexing
# ---------------------------------------------------------------------------

def demo_indexing() -> None:
    """Demonstrate basic (integer), fancy, and boolean indexing.

    C++ Comparison: NumPy vectorization vs C++ loops
    -------------------------------------------------
    Boolean filtering in C++ (manual loop):
        std::vector<int> result;
        for (int i = 0; i < n; ++i) {
            if (arr[i] > 5 && arr[i] % 2 == 0)
                result.push_back(arr[i]);
        }

    NumPy vectorized equivalent (single expression, runs in C under the hood):
        arr[(arr > 5) & (arr % 2 == 0)]

    The NumPy version is not only shorter but typically 10-100x faster for
    large arrays because the loop runs entirely in optimized C without
    per-element Python interpreter overhead.
    """
    print("\n" + "=" * 70)
    print("3. Indexing")
    print("=" * 70)

    # --- Basic (integer) indexing ---
    arr_1d: NDArray[np.int_] = np.arange(1, 10)
    arr_2d: NDArray[np.int_] = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

    print("--- Basic Indexing ---")
    print(f"arr_1d[0]={arr_1d[0]}, arr_1d[-1]={arr_1d[-1]}")
    print(f"arr_2d[2] (row 2):         {arr_2d[2]}")
    print(f"arr_2d[0][0]={arr_2d[0][0]}, arr_2d[-1][-1]={arr_2d[-1][-1]}")
    print(f"arr_2d[1, 1] (comma form): {arr_2d[1, 1]}")

    # Modify via indexing
    arr_2d[1, 1] = 10
    print(f"After arr_2d[1,1]=10:\n{arr_2d}")
    arr_2d[1] = [10, 11, 12]
    print(f"After arr_2d[1]=[10,11,12]:\n{arr_2d}")

    # --- Fancy indexing (integer array as index) ---
    print("\n--- Fancy Indexing ---")
    arr_1d = np.arange(1, 10)  # reset
    print(f"arr_1d[[0, 1, 1, -1, 4, -1]]: {arr_1d[[0, 1, 1, -1, 4, -1]]}")
    print(f"arr_2d[[0, 2]] (rows 0 and 2):\n{arr_2d[[0, 2]]}")
    print(f"arr_2d[[0, 2], [1, 2]] (pairs): {arr_2d[[0, 2], [1, 2]]}")
    print(f"arr_2d[[0, 2], 1] (col 1 of rows 0,2): {arr_2d[[0, 2], 1]}")

    # --- Boolean indexing ---
    print("\n--- Boolean Indexing ---")
    mask: NDArray[np.bool_] = np.array(
        [True, True, False, False, True, False, False, True, True]
    )
    print(f"arr_1d[bool_mask]: {arr_1d[mask]}")
    print(f"arr_1d > 5:        {arr_1d > 5}")
    print(f"arr_1d[arr_1d > 5]: {arr_1d[arr_1d > 5]}")
    print(f"Even numbers:       {arr_1d[arr_1d % 2 == 0]}")

    combined: NDArray[np.bool_] = (arr_1d > 5) & (arr_1d % 2 == 0)
    print(f">5 AND even:        {arr_1d[combined]}")
    combined_or: NDArray[np.bool_] = (arr_1d > 5) | (arr_1d % 2 == 0)
    print(f">5 OR even:         {arr_1d[combined_or]}")


# ---------------------------------------------------------------------------
# 4. Slicing
# ---------------------------------------------------------------------------

def demo_slicing() -> None:
    """Demonstrate slice indexing on 1D and 2D arrays.

    Important: Slice views share memory with the original array.
    Fancy and boolean indices create copies.

    C++ Comparison:
        In C++ with Eigen, block access is analogous to slicing:
            m.block<2,2>(0,1)          // 2x2 block starting at (0,1)
            m.topRows(2)               // first 2 rows
            m.leftCols(2)              // first 2 columns
            m(Eigen::seq(0,4,2), Eigen::all)  // every other row (Eigen 3.4+)
        NumPy slicing is more concise: arr[::2, :]
    """
    print("\n" + "=" * 70)
    print("4. Slicing")
    print("=" * 70)

    arr: NDArray[np.int_] = np.array([[1, 2, 3], [10, 11, 12], [7, 8, 9]])
    print(f"Original array:\n{arr}")

    print(f"\narr[:2, 1:]         -> {arr[:2, 1]}")       # first 2 rows, cols from 1
    print(f"arr[:2, 1:]         ->\n{arr[:2, 1:]}")
    print(f"arr[2, :]           -> {arr[2, :]}")          # row 2, all columns
    print(f"arr[2:, :]          ->\n{arr[2:, :]}")        # row 2 onward
    print(f"arr[:, :2]          ->\n{arr[:, :2]}")        # all rows, first 2 cols
    print(f"arr[::2, ::2]       ->\n{arr[::2, ::2]}")     # every other row & col
    print(f"arr[::-2, ::-2]     ->\n{arr[::-2, ::-2]}")   # reversed strided

    # Demonstrate shared memory via slices
    view = arr[0, :]
    view[0] = 999
    print(f"\nAfter modifying view[0]=999, original arr[0,0] = {arr[0, 0]}  (shared memory!)")
    arr[0, 0] = 1  # restore


# ---------------------------------------------------------------------------
# 5. Reshape
# ---------------------------------------------------------------------------

def demo_reshape() -> None:
    """Demonstrate reshape, flatten, ravel, and transpose.

    C++ Comparison: NumPy ndarray vs C++ Eigen::Matrix
    ---------------------------------------------------
        Eigen:
            m.reshaped(rows, cols)   // reshape (Eigen 3.4+)
            m.transpose()            // returns a lazy transpose view
            m.eval()                 // force evaluation (like .copy() in NumPy)
            m.array()                // element-wise ops (Eigen::Array)
        NumPy:
            arr.reshape(new_shape)
            arr.T  or  arr.transpose()
            arr.flatten()   -> contiguous copy
            arr.ravel()     -> contiguous view when possible
    """
    print("\n" + "=" * 70)
    print("5. Reshape")
    print("=" * 70)

    arr: NDArray[np.int_] = np.arange(1, 13)
    print(f"Original (shape {arr.shape}): {arr}")

    reshaped_3x4: NDArray[np.int_] = arr.reshape(3, 4)
    print(f"\nreshape(3, 4):\n{reshaped_3x4}")

    reshaped_4x3: NDArray[np.int_] = arr.reshape(4, 3)
    print(f"\nreshape(4, 3):\n{reshaped_4x3}")

    # Using -1 for automatic dimension inference
    reshaped_auto: NDArray[np.int_] = arr.reshape(2, -1)
    print(f"\nreshape(2, -1) -> inferred as (2, 6):\n{reshaped_auto}")

    reshaped_3d: NDArray[np.int_] = arr.reshape(2, 2, 3)
    print(f"\nreshape(2, 2, 3) -> 3D:\n{reshaped_3d}")

    # flatten vs ravel
    flat: NDArray[np.int_] = reshaped_3x4.flatten()
    print(f"\nflatten() (copy):   {flat}")
    raveled: NDArray[np.int_] = reshaped_3x4.ravel()
    print(f"ravel() (view):     {raveled}")

    # Transpose
    transposed: NDArray[np.int_] = reshaped_3x4.T
    print(f"\nTranspose (.T) of reshape(3,4):\n{transposed}")

    # expand_dims / squeeze
    arr_1d: NDArray[np.int_] = np.array([1, 2, 3])
    expanded: NDArray[np.int_] = np.expand_dims(arr_1d, axis=0)
    print(f"\nexpand_dims(arr_1d, axis=0): {expanded}  shape={expanded.shape}")
    squeezed: NDArray[np.int_] = np.squeeze(expanded)
    print(f"squeeze(expanded):           {squeezed}  shape={squeezed.shape}")


# ---------------------------------------------------------------------------
# 6. Enterprise Example: Sensor Data Processing
# ---------------------------------------------------------------------------

def enterprise_sensor_data() -> None:
    """Process multi-sensor time-series data using vectorized NumPy operations.

    Scenario:
        A factory floor has 4 temperature sensors sampled every second for
        1 hour (3600 samples). We need to:
          - Generate synthetic data with drift and noise
          - Compute per-sensor statistics (mean, std, min, max)
          - Detect anomalies (> 2 sigma from mean)
          - Reshape into 5-minute windows for batch analysis

    C++ Comparison: NumPy vectorization vs C++ loops
    -------------------------------------------------
    Anomaly detection in C++ (manual loop):
        for (int s = 0; s < num_sensors; ++s) {
            for (int t = 0; t < num_samples; ++t) {
                double z = (data[s][t] - mean[s]) / std_dev[s];
                if (std::abs(z) > 2.0) anomaly_mask[s][t] = true;
            }
        }

    NumPy vectorized (zero explicit loops):
        z_scores = (data - means[:, None]) / stds[:, None]
        anomaly_mask = np.abs(z_scores) > 2.0
    """
    print("\n" + "=" * 70)
    print("6. Enterprise: Sensor Data Processing")
    print("=" * 70)

    np.random.seed(42)
    num_sensors: int = 4
    num_samples: int = 3600  # 1 hour at 1 Hz

    # Synthetic sensor data: baseline + slow drift + Gaussian noise
    base_temps: NDArray[np.float64] = np.array([22.0, 23.5, 21.0, 24.0])
    drift: NDArray[np.float64] = np.linspace(0, 3.0, num_samples)
    noise: NDArray[np.float64] = np.random.normal(0, 0.5, (num_sensors, num_samples))
    sensor_data: NDArray[np.float64] = base_temps[:, None] + drift[None, :] + noise

    print(f"Sensor data shape: {sensor_data.shape}  (sensors x samples)")

    # Per-sensor statistics (axis=1 collapses time dimension)
    means: NDArray[np.float64] = sensor_data.mean(axis=1)
    stds: NDArray[np.float64] = sensor_data.std(axis=1)
    mins: NDArray[np.float64] = sensor_data.min(axis=1)
    maxs: NDArray[np.float64] = sensor_data.max(axis=1)

    print("\nPer-sensor statistics:")
    for i in range(num_sensors):
        print(
            f"  Sensor {i}: mean={means[i]:.2f}, std={stds[i]:.2f}, "
            f"min={mins[i]:.2f}, max={maxs[i]:.2f}"
        )

    # Anomaly detection: |z-score| > 2.0
    z_scores: NDArray[np.float64] = (sensor_data - means[:, None]) / stds[:, None]
    anomaly_mask: NDArray[np.bool_] = np.abs(z_scores) > 2.0
    anomaly_count: NDArray[np.int_] = anomaly_mask.sum(axis=1)
    print(f"\nAnomalies per sensor (>2 sigma): {anomaly_count}")

    # Reshape into 5-minute windows (300 samples each) for batch stats
    windows_per_sensor: int = num_samples // 300
    # sensor_data shape: (4, 3600) -> take sensor 0, reshape to (12, 300)
    sensor0_windows: NDArray[np.float64] = sensor_data[0, : windows_per_sensor * 300].reshape(
        windows_per_sensor, 300
    )
    window_means: NDArray[np.float64] = sensor0_windows.mean(axis=1)
    print(f"\nSensor 0 - mean temp per 5-min window:")
    for w, wm in enumerate(window_means):
        print(f"  Window {w:2d} ({w*5:3d}-{(w+1)*5:3d} min): {wm:.2f} C")


# ---------------------------------------------------------------------------
# 7. Enterprise Example: Image Pixel Manipulation
# ---------------------------------------------------------------------------

def enterprise_image_processing() -> None:
    """Demonstrate image manipulation using pure NumPy array operations.

    Scenario:
        A security camera system processes 640x480 RGB frames. Using NumPy
        slicing and vectorized ops we perform:
          - Brightness adjustment
          - Channel isolation (extract R, G, B planes)
          - Grayscale conversion (weighted sum)
          - Cropping (region of interest)
          - Horizontal / vertical flip
          - Down-sampling (decimation)

    C++ Comparison: NumPy ndarray vs C++ Eigen::Matrix
    ---------------------------------------------------
    Eigen is designed for linear algebra, not multi-dimensional image data.
    Typical C++ image pipelines use OpenCV cv::Mat or raw pixel loops:
        for (int y = 0; y < height; ++y)
            for (int x = 0; x < width; ++x)
                gray[y][x] = 0.299*R + 0.587*G + 0.114*B;
    NumPy eliminates both loops:
        gray = (img[:,:,0]*0.299 + img[:,:,1]*0.587 + img[:,:,2]*0.114)
    """
    print("\n" + "=" * 70)
    print("7. Enterprise: Image Pixel Manipulation")
    print("=" * 70)

    np.random.seed(7)
    height, width = 480, 640
    # Simulate an RGB image as a uint8 array (H x W x 3)
    image: NDArray[np.uint8] = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    print(f"Image shape: {image.shape}, dtype: {image.dtype}")

    # --- Brightness adjustment (vectorized) ---
    brightness_offset: int = 30
    brighter: NDArray[np.int16] = image.astype(np.int16) + brightness_offset
    brighter_clipped: NDArray[np.uint8] = np.clip(brighter, 0, 255).astype(np.uint8)
    print(f"Brightness +{brightness_offset}: min={brighter_clipped.min()}, max={brighter_clipped.max()}")

    # --- Channel isolation ---
    red_channel: NDArray[np.uint8] = image[:, :, 0]
    green_channel: NDArray[np.uint8] = image[:, :, 1]
    blue_channel: NDArray[np.uint8] = image[:, :, 2]
    print(f"R channel mean: {red_channel.mean():.1f}")
    print(f"G channel mean: {green_channel.mean():.1f}")
    print(f"B channel mean: {blue_channel.mean():.1f}")

    # --- Grayscale conversion (weighted luminance) ---
    # Standard weights: R=0.299, G=0.587, B=0.114
    grayscale: NDArray[np.float64] = (
        image[:, :, 0].astype(np.float64) * 0.299
        + image[:, :, 1].astype(np.float64) * 0.587
        + image[:, :, 2].astype(np.float64) * 0.114
    )
    print(f"Grayscale shape: {grayscale.shape}, mean: {grayscale.mean():.1f}")

    # --- Crop: region of interest (center 200x200) ---
    cy, cx = height // 2, width // 2
    crop_size = 100
    roi: NDArray[np.uint8] = image[
        cy - crop_size : cy + crop_size, cx - crop_size : cx + crop_size, :
    ]
    print(f"ROI crop shape: {roi.shape}")

    # --- Flip operations ---
    flipped_v: NDArray[np.uint8] = image[::-1, :, :]     # vertical flip
    flipped_h: NDArray[np.uint8] = image[:, ::-1, :]     # horizontal flip
    print(f"Vertical flip shape:   {flipped_v.shape}")
    print(f"Horizontal flip shape: {flipped_h.shape}")

    # --- Down-sampling (decimation by factor 4) ---
    downsampled: NDArray[np.uint8] = image[::4, ::4, :]
    print(f"Downsampled (4x) shape: {downsampled.shape}")


# ---------------------------------------------------------------------------
# 8. Enterprise Example: Financial Time Series
# ---------------------------------------------------------------------------

def enterprise_financial_timeseries() -> None:
    """Analyze financial time-series data with NumPy vectorized operations.

    Scenario:
        A quantitative trading desk analyzes 3 years of daily OHLCV data for
        5 stocks. NumPy operations used:
          - Generate synthetic price data (geometric Brownian motion)
          - Compute daily returns (vectorized pct_change)
          - Rolling statistics via stride_tricks or manual windows
          - Correlation matrix across stocks
          - Portfolio value using reshaped weight arrays

    C++ Comparison: NumPy vectorization vs C++ loops
    -------------------------------------------------
    Correlation matrix in C++ (double loop):
        for (int i = 0; i < n; ++i)
            for (int j = 0; j < n; ++j)
                corr[i][j] = covariance(ret[i], ret[j]) / (sd[i] * sd[j]);
    NumPy:
        corr = np.corrcoef(returns)  # single function call, BLAS-optimized
    """
    print("\n" + "=" * 70)
    print("8. Enterprise: Financial Time Series")
    print("=" * 70)

    np.random.seed(0)
    trading_days: int = 756  # ~3 years
    num_stocks: int = 5
    stock_names: list[str] = ["AAPL", "GOOG", "MSFT", "AMZN", "TSLA"]

    # Simulate daily close prices using geometric Brownian motion
    # S(t+1) = S(t) * exp((mu - sigma^2/2)*dt + sigma*sqrt(dt)*Z)
    annual_mu: NDArray[np.float64] = np.array([0.12, 0.10, 0.08, 0.15, 0.20])
    annual_sigma: NDArray[np.float64] = np.array([0.25, 0.22, 0.20, 0.28, 0.45])
    dt: float = 1.0 / 252.0
    initial_prices: NDArray[np.float64] = np.array([150.0, 2800.0, 300.0, 3300.0, 700.0])

    # Generate random daily shocks: (stocks x days)
    shocks: NDArray[np.float64] = np.random.normal(0, 1, (num_stocks, trading_days))

    # Drift component and diffusion component
    drift: NDArray[np.float64] = (annual_mu - 0.5 * annual_sigma**2) * dt
    diffusion: NDArray[np.float64] = annual_sigma * np.sqrt(dt)

    # Log-returns (vectorized)
    log_returns: NDArray[np.float64] = drift[:, None] + diffusion[:, None] * shocks

    # Cumulative product to get price paths
    cum_returns: NDArray[np.float64] = np.exp(np.cumsum(log_returns, axis=1))
    prices: NDArray[np.float64] = initial_prices[:, None] * cum_returns

    print(f"Price matrix shape: {prices.shape}  (stocks x days)")

    # Daily simple returns
    daily_returns: NDArray[np.float64] = np.diff(prices, axis=1) / prices[:, :-1]

    # Per-stock annualized return and volatility
    print("\nStock | Ann. Return | Ann. Volatility | Final Price")
    print("-" * 58)
    for i, name in enumerate(stock_names):
        ann_ret: float = daily_returns[i].mean() * 252
        ann_vol: float = daily_returns[i].std() * np.sqrt(252)
        final_price: float = prices[i, -1]
        print(f"  {name:5s} | {ann_ret:>11.2%} | {ann_vol:>15.2%} | {final_price:>11.2f}")

    # Correlation matrix of daily returns
    corr_matrix: NDArray[np.float64] = np.corrcoef(daily_returns)
    print(f"\nCorrelation matrix shape: {corr_matrix.shape}")
    print("Pairwise correlations:")
    for i in range(num_stocks):
        for j in range(i + 1, num_stocks):
            print(f"  {stock_names[i]}-{stock_names[j]}: {corr_matrix[i, j]:.3f}")

    # Portfolio analysis: equal-weight portfolio
    weights: NDArray[np.float64] = np.full(num_stocks, 1.0 / num_stocks)
    portfolio_daily_returns: NDArray[np.float64] = weights @ daily_returns
    cumulative_portfolio: NDArray[np.float64] = np.cumprod(1 + portfolio_daily_returns)

    # Maximum drawdown
    running_max: NDArray[np.float64] = np.maximum.accumulate(cumulative_portfolio)
    drawdowns: NDArray[np.float64] = (cumulative_portfolio - running_max) / running_max
    max_drawdown: float = drawdowns.min()

    print(f"\nEqual-weight portfolio:")
    print(f"  Total return:      {cumulative_portfolio[-1] - 1:.2%}")
    print(f"  Annualized return: {portfolio_daily_returns.mean() * 252:.2%}")
    print(f"  Annualized vol:    {portfolio_daily_returns.std() * np.sqrt(252):.2%}")
    print(f"  Max drawdown:      {max_drawdown:.2%}")

    # Rolling 20-day volatility (manual vectorized window)
    window: int = 20
    # Use stride tricks for efficient rolling computation
    shape: tuple[int, int] = (daily_returns.shape[1] - window + 1, window)
    strides: tuple[int, int] = (daily_returns.strides[1], daily_returns.strides[1])
    rolling_windows: NDArray[np.float64] = np.lib.stride_tricks.as_strided(
        daily_returns[0], shape=shape, strides=strides
    )
    rolling_vol: NDArray[np.float64] = rolling_windows.std(axis=1) * np.sqrt(252)
    print(f"\nStock 0 ({stock_names[0]}) rolling {window}-day annualized vol:")
    print(f"  First window: {rolling_vol[0]:.2%}")
    print(f"  Last window:  {rolling_vol[-1]:.2%}")
    print(f"  Mean:         {rolling_vol.mean():.2%}")


# ---------------------------------------------------------------------------
# 9. Utility: Quick ndarray vs list performance comparison
# ---------------------------------------------------------------------------

def performance_demo() -> None:
    """Compare NumPy vectorized operations vs Python loop performance.

    C++ Comparison: NumPy vectorization vs C++ loops
    -------------------------------------------------
    This is analogous to comparing:
        - Naive C++ element-wise loop (like Python for-loop, slow)
        - Optimized BLAS call or SIMD-vectorized C++ loop (like NumPy, fast)
    NumPy achieves C-like speed because its core loops are written in C and
    compiled with platform-specific optimizations (SSE, AVX, etc.).
    """
    print("\n" + "=" * 70)
    print("9. Performance: NumPy Vectorization vs Python Loops")
    print("=" * 70)

    import time

    n: int = 1_000_000
    a_list: list[float] = list(range(n))
    a_array: NDArray[np.int_] = np.arange(n)

    # Python loop: element-wise square and sum
    t0: float = time.perf_counter()
    sum_loop: float = sum(x * x for x in a_list)
    t_loop: float = time.perf_counter() - t0

    # NumPy vectorized: element-wise square and sum
    t0 = time.perf_counter()
    sum_numpy: int = np.sum(a_array * a_array)  # type: ignore[assignment]
    t_numpy: float = time.perf_counter() - t0

    print(f"Sum of squares for {n:,} elements:")
    print(f"  Python loop:  {t_loop:.4f}s  (result={sum_loop})")
    print(f"  NumPy vector: {t_numpy:.6f}s  (result={sum_numpy})")
    print(f"  Speedup:      {t_loop / t_numpy:.0f}x faster with NumPy")


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all demonstrations."""
    print("NumPy Fundamentals - Day 68")
    print(f"NumPy version: {np.__version__}\n")

    demo_array_creation()
    demo_array_attributes()
    demo_indexing()
    demo_slicing()
    demo_reshape()

    # Enterprise examples
    enterprise_sensor_data()
    enterprise_image_processing()
    enterprise_financial_timeseries()

    # Performance comparison
    performance_demo()

    print("\n" + "=" * 70)
    print("All demonstrations complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
