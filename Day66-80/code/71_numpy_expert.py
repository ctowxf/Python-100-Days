"""
NumPy Expert-Level Operations — Day 71
=======================================
Covers:
  1. Advanced indexing (fancy, boolean, combined)
  2. Structured arrays (heterogeneous data)
  3. Performance optimization (vectorization, memory layout, broadcasting)
  4. Enterprise examples: large dataset processing, memory-efficient operations

Prerequisites: Day 66-70 (NumPy basics through linear algebra)
"""

import gc
import os
import sys
import time
import tracemalloc
from typing import Any, Optional, Sequence

import numpy as np
from numpy.typing import NDArray


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    """Print a formatted section header."""
    width = 70
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}\n")


def timer(func):
    """Decorator that prints wall-clock elapsed time of a callable."""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  [timer] {func.__name__} finished in {elapsed:.6f}s")
        return result
    return wrapper


# ===================================================================
# 1. Advanced Indexing
# ===================================================================

def demo_fancy_indexing() -> None:
    """Fancy (integer-array) indexing: select arbitrary elements by index arrays."""
    section("1-A  Fancy Indexing")

    rng = np.random.default_rng(42)
    arr: NDArray[np.float64] = rng.standard_normal((6, 5))
    print("Original array (6x5):")
    print(arr)

    # Select specific rows and columns by integer arrays
    row_idx = np.array([0, 2, 4])
    col_idx = np.array([1, 3, 4])
    selected = arr[row_idx, col_idx]          # shape (3,)
    print(f"\nElements at (0,1), (2,3), (4,4): {selected}")

    # Fancy index a full sub-matrix (outer product of indices)
    rows = np.array([1, 3, 5])
    cols = np.array([0, 2, 4])
    sub = arr[np.ix_(rows, cols)]             # shape (3, 3)
    print(f"\nSub-matrix via np.ix_ (rows [1,3,5], cols [0,2,4]):\n{sub}")

    # Use fancy indexing for assignment
    arr[np.array([0, 1, 2]), np.array([0, 1, 2])] = -999.0
    print(f"\nAfter setting diagonal of first 3 rows to -999:\n{arr}")


def demo_boolean_indexing() -> None:
    """Boolean masks for conditional selection and modification."""
    section("1-B  Boolean Indexing")

    rng = np.random.default_rng(0)
    temps: NDArray[np.float64] = rng.normal(loc=25, scale=8, size=(4, 7))
    print("Weekly temperatures (4 weeks x 7 days):\n", np.round(temps, 1))

    # Select all readings above 30 degrees
    hot_mask = temps > 30.0
    hot_values = temps[hot_mask]
    print(f"\nReadings > 30 C: {np.round(hot_values, 1)}")
    print(f"Count: {hot_values.size}")

    # Combine masks: readings between 20 and 30
    comfortable = temps[(temps >= 20) & (temps <= 30)]
    print(f"Comfortable readings (20-30): {comfortable.size} out of {temps.size}")

    # Conditional modification: cap values at 35
    capped = np.where(temps > 35, 35.0, temps)
    print(f"\nCapped at 35 (max before: {temps.max():.1f}, after: {capped.max():.1f})")


def demo_combined_indexing() -> None:
    """Mix fancy and boolean indexing in a single expression."""
    section("1-C  Combined Advanced Indexing")

    rng = np.random.default_rng(7)
    data: NDArray[np.int64] = rng.integers(10, 100, size=(5, 6))
    print("Integer array:\n", data)

    # Select specific rows where column-0 > 50, then pick columns [1, 3]
    mask = data[:, 0] > 50
    result = data[mask][:, [1, 3]]
    print(f"\nRows where col-0 > 50, keeping cols [1,3]:\n{result}")

    # np.where returns indices — useful for locating qualifying elements
    locs = np.where(data > 80)
    print(f"\nCoordinates of elements > 80: {list(zip(locs[0], locs[1]))}")


def demo_indexing_edge_cases() -> None:
    """Edge-case handling: out-of-bounds, empty selections, multi-dim fancy."""
    section("1-D  Indexing Edge Cases & Tips")

    arr = np.arange(12).reshape(3, 4)
    print("Array:\n", arr)

    # Negative indices work as expected
    print(f"\nLast element: {arr[-1, -1]}")
    print(f"Last row, reversed: {arr[-1, ::-1]}")

    # Empty boolean selection
    mask_all_false = arr > 999
    empty = arr[mask_all_false]
    print(f"\nEmpty selection shape: {empty.shape}, size: {empty.size}")

    # Multi-dimensional fancy index — index arrays broadcast together
    row_idx = np.array([[0, 1], [2, 0]])
    col_idx = np.array([[2, 3], [0, 1]])
    result = arr[row_idx, col_idx]
    print(f"\n2D fancy index result:\n{result}")


# ===================================================================
# 2. Structured Arrays
# ===================================================================

def demo_structured_arrays() -> None:
    """Create and manipulate structured (heterogeneous) arrays."""
    section("2-A  Structured Arrays — Creation & Access")

    # Define a compound dtype for employee records
    emp_dtype = np.dtype([
        ("name", "U20"),          # Unicode string, max 20 chars
        ("department", "U12"),
        ("salary", np.float64),
        ("years_exp", np.int32),
        ("is_active", np.bool_),
    ])

    employees = np.array([
        ("Alice",   "Engineering", 125000.0, 8,  True),
        ("Bob",     "Marketing",    98000.0, 5,  True),
        ("Charlie", "Engineering", 140000.0, 12, True),
        ("Diana",   "Finance",     110000.0, 7,  False),
        ("Eve",     "Engineering", 130000.0, 10, True),
    ], dtype=emp_dtype)

    print("All employees:\n", employees)
    print(f"\nDtype: {employees.dtype}")

    # Access individual fields (returns an ndarray)
    print(f"\nSalaries: {employees['salary']}")
    print(f"Departments: {employees['department']}")

    # Boolean selection on structured array
    engineers = employees[employees["department"] == "Engineering"]
    print(f"\nEngineers:\n{engineers}")

    # Sort by salary descending
    sorted_idx = np.argsort(-employees["salary"])
    top_earners = employees[sorted_idx]
    print(f"\nSorted by salary (descending):\n{top_earners}")


def demo_structured_ops() -> None:
    """Perform aggregate operations on structured arrays."""
    section("2-B  Structured Arrays — Aggregation & Modification")

    sensor_dtype = np.dtype([
        ("sensor_id", "U8"),
        ("timestamp", "datetime64[s]"),
        ("temperature", np.float32),
        ("humidity", np.float32),
        ("status", "U4"),
    ])

    sensors = np.array([
        ("S-001", "2025-01-15T08:00:00", 22.5, 45.0, "OK"),
        ("S-002", "2025-01-15T08:00:00", 23.1, 50.2, "OK"),
        ("S-001", "2025-01-15T09:00:00", 24.0, 42.8, "OK"),
        ("S-003", "2025-01-15T08:00:00", 19.8, 60.1, "WARN"),
        ("S-002", "2025-01-15T09:00:00", 25.5, 48.0, "OK"),
        ("S-003", "2025-01-15T09:00:00", 18.2, 62.5, "FAIL"),
    ], dtype=sensor_dtype)

    print("Sensor readings:\n", sensors)

    # Aggregate: mean temperature
    mean_temp = sensors["temperature"].mean()
    print(f"\nMean temperature: {mean_temp:.2f}")

    # Filter unhealthy sensors
    bad = sensors[(sensors["status"] == "WARN") | (sensors["status"] == "FAIL")]
    print(f"Problematic readings:\n{bad}")

    # Modify in-place: convert humidity to ratio
    sensors["humidity"] /= 100.0
    print(f"\nHumidity after conversion to ratio:\n{sensors['humidity']}")

    # Nested structured dtype (compound fields)
    point_dtype = np.dtype([("x", np.float64), ("y", np.float64)])
    line_dtype = np.dtype([("start", point_dtype), ("end", point_dtype)])
    lines = np.array([
        ((0.0, 0.0), (1.0, 1.0)),
        ((2.0, 3.0), (5.0, 7.0)),
    ], dtype=line_dtype)
    print(f"\nNested structured array (lines):\n{lines}")
    print(f"Line 0 start.x: {lines[0]['start']['x']}")


# ===================================================================
# 3. Performance Optimization
# ===================================================================

def demo_vectorization_vs_loop() -> None:
    """Benchmark pure Python loop vs NumPy vectorized operation."""
    section("3-A  Vectorization vs Python Loop")

    n = 500_000
    rng = np.random.default_rng(99)
    a_list = rng.standard_normal(n).tolist()
    b_list = rng.standard_normal(n).tolist()
    a_np = np.array(a_list)
    b_np = np.array(b_list)

    # Python loop: element-wise Euclidean distance sum
    @timer
    def python_loop() -> float:
        total = 0.0
        for i in range(n):
            diff = a_list[i] - b_list[i]
            total += diff * diff
        return total ** 0.5

    # NumPy vectorized
    @timer
    def numpy_vectorized() -> float:
        return float(np.sqrt(np.sum((a_np - b_np) ** 2)))

    dist_py = python_loop()
    dist_np = numpy_vectorized()
    print(f"  Python loop result:   {dist_py:.6f}")
    print(f"  NumPy vectorized:     {dist_np:.6f}")
    print(f"  Difference:           {abs(dist_py - dist_np):.2e}")


def demo_broadcasting_optimization() -> None:
    """Leverage broadcasting to avoid explicit loops and temporaries."""
    section("3-B  Broadcasting for Memory & Speed")

    rng = np.random.default_rng(1)
    # 1000 samples, 50 features
    X: NDArray[np.float64] = rng.standard_normal((1000, 50))
    # Mean-center without explicit loop or tile
    col_means = X.mean(axis=0)            # shape (50,)
    centered = X - col_means              # broadcast: (1000,50) - (50,)
    print(f"Shape after centering: {centered.shape}")
    print(f"Column means (should be ~0): {centered.mean(axis=0)[:5]}")

    # Normalize each row to unit length using broadcasting
    row_norms = np.linalg.norm(centered, axis=1, keepdims=True)  # (1000, 1)
    normalized = centered / row_norms     # broadcast
    norms_after = np.linalg.norm(normalized, axis=1)
    print(f"Row norms after normalization (first 5): {norms_after[:5]}")


def demo_memory_layout() -> None:
    """Demonstrate C-order vs F-order and its performance impact."""
    section("3-C  Memory Layout: C-order vs F-order")

    rows, cols = 10_000, 500
    rng = np.random.default_rng(5)

    c_arr = np.ascontiguousarray(rng.standard_normal((rows, cols)))
    f_arr = np.asfortranarray(c_arr)

    print(f"C-order contiguous: {c_arr.flags['C_CONTIGUOUS']}, "
          f"stride: {c_arr.strides}")
    print(f"F-order contiguous: {f_arr.flags['F_CONTIGUOUS']}, "
          f"stride: {f_arr.strides}")

    # Column-wise sum is faster on F-order (columns are contiguous)
    @timer
    def sum_cols_c() -> NDArray:
        return c_arr.sum(axis=0)

    @timer
    def sum_cols_f() -> NDArray:
        return f_arr.sum(axis=0)

    r1 = sum_cols_c()
    r2 = sum_cols_f()
    print(f"  Results match: {np.allclose(r1, r2)}")

    # Row-wise sum is faster on C-order (rows are contiguous)
    @timer
    def sum_rows_c() -> NDArray:
        return c_arr.sum(axis=1)

    @timer
    def sum_rows_f() -> NDArray:
        return f_arr.sum(axis=1)

    sum_rows_c()
    sum_rows_f()


def demo_inplace_operations() -> None:
    """Use in-place operations to reduce memory allocations."""
    section("3-D  In-Place Operations to Save Memory")

    tracemalloc.start()
    rng = np.random.default_rng(10)
    arr = rng.standard_normal((2000, 2000)).astype(np.float32)

    snap1 = tracemalloc.take_snapshot()

    # NOT in-place — creates a new array each time
    for _ in range(5):
        arr = arr * 2.0 + 1.0      # new allocation every iteration

    snap2 = tracemalloc.take_snapshot()
    stats = snap2.compare_to(snap1, "lineno")
    top = stats[0] if stats else None
    print(f"Out-of-place 5 iters — top alloc: {top}")

    # Reset
    arr = rng.standard_normal((2000, 2000)).astype(np.float32)
    tracemalloc.clear_traces()
    snap3 = tracemalloc.take_snapshot()

    # In-place — modifies the existing buffer
    for _ in range(5):
        arr *= 2.0
        arr += 1.0

    snap4 = tracemalloc.take_snapshot()
    stats2 = snap4.compare_to(snap3, "lineno")
    top2 = stats2[0] if stats2 else None
    print(f"In-place 5 iters — top alloc: {top2}")
    tracemalloc.stop()


def demo_dtype_optimization() -> None:
    """Choose appropriate dtypes to reduce memory and speed up compute."""
    section("3-E  Dtype Selection for Memory Efficiency")

    n = 2_000_000
    rng = np.random.default_rng(42)

    for dt in [np.float64, np.float32, np.float16]:
        arr = rng.standard_normal(n).astype(dt)
        mem_mb = arr.nbytes / (1024 ** 2)
        print(f"  {str(dt):40s}  {mem_mb:8.2f} MB  "
              f"sum={arr.sum():.4f}")

    # int8 for categorical data
    categories = rng.integers(0, 10, size=n).astype(np.int8)
    print(f"\n  int8 categorical array: {categories.nbytes / (1024**2):.2f} MB")


# ===================================================================
# 4. Enterprise Examples
# ===================================================================

@timer
def enterprise_log_analysis() -> None:
    """Simulate large-scale server log analysis with structured arrays."""
    section("4-A  Enterprise: Server Log Analysis (Structured Arrays)")

    log_dtype = np.dtype([
        ("timestamp", "datetime64[ms]"),
        ("server_id", "U8"),
        ("response_ms", np.float32),
        ("status_code", np.int16),
        ("bytes_sent", np.int32),
    ])

    rng = np.random.default_rng(2025)
    n_records = 500_000

    base_time = np.datetime64("2025-06-01T00:00:00", "ms")
    offsets = rng.integers(0, 86_400_000, size=n_records)  # within one day
    timestamps = base_time + offsets

    server_ids = rng.choice(
        np.array(["web-01", "web-02", "web-03", "api-01", "api-02"]),
        size=n_records,
    )
    response_ms = rng.exponential(scale=120.0, size=n_records).astype(np.float32)
    status_codes = rng.choice(
        np.array([200, 201, 301, 400, 404, 500], dtype=np.int16),
        size=n_records,
        p=[0.70, 0.05, 0.05, 0.08, 0.07, 0.05],
    )
    bytes_sent = rng.integers(100, 50_000, size=n_records, dtype=np.int32)

    logs = np.empty(n_records, dtype=log_dtype)
    logs["timestamp"] = timestamps
    logs["server_id"] = server_ids
    logs["response_ms"] = response_ms
    logs["status_code"] = status_codes
    logs["bytes_sent"] = bytes_sent

    print(f"Total log records: {n_records:,}")
    print(f"Memory usage: {logs.nbytes / (1024**2):.2f} MB")

    # 1) Error rate
    error_mask = logs["status_code"] >= 400
    error_rate = error_mask.sum() / n_records * 100
    print(f"\nError rate (4xx+5xx): {error_rate:.2f}%")

    # 2) P95 response time
    p95 = np.percentile(logs["response_ms"], 95)
    print(f"P95 response time: {p95:.1f} ms")

    # 3) Per-server stats
    unique_servers = np.unique(logs["server_id"])
    print(f"\nPer-server summary:")
    print(f"  {'Server':<10s} {'Requests':>10s} {'Avg ms':>10s} {'Error%':>10s}")
    print(f"  {'-'*40}")
    for sid in unique_servers:
        mask = logs["server_id"] == sid
        srv = logs[mask]
        srv_err = (srv["status_code"] >= 400).sum() / srv.size * 100
        print(f"  {sid:<10s} {srv.size:>10,} {srv['response_ms'].mean():>10.1f}"
              f" {srv_err:>9.2f}%")

    # 4) Total bytes transferred
    total_gb = logs["bytes_sent"].sum() / (1024 ** 3)
    print(f"\nTotal data transferred: {total_gb:.2f} GB")


@timer
def enterprise_batch_processing() -> None:
    """Process large datasets in memory-efficient batches using np.memmap."""
    section("4-B  Enterprise: Batch Processing with Memory-Mapped Files")

    import tempfile

    tmpdir = tempfile.mkdtemp()
    filepath = os.path.join(tmpdir, "large_dataset.dat")
    n_samples = 1_000_000
    n_features = 100

    # Phase 1: write data in chunks (simulates streaming ingestion)
    print(f"Writing {n_samples:,} x {n_features} matrix to disk...")
    mm_write = np.memmap(filepath, dtype=np.float32, mode="w+",
                         shape=(n_samples, n_features))
    rng = np.random.default_rng(77)
    chunk_size = 100_000
    for start in range(0, n_samples, chunk_size):
        end = min(start + chunk_size, n_samples)
        mm_write[start:end] = rng.standard_normal((end - start, n_features))
    del mm_write  # flush to disk

    # Phase 2: read and process in batches
    mm_read = np.memmap(filepath, dtype=np.float32, mode="r",
                        shape=(n_samples, n_features))
    print(f"File size on disk: {os.path.getsize(filepath) / (1024**2):.1f} MB")

    running_mean = np.zeros(n_features, dtype=np.float64)
    running_count = 0
    for start in range(0, n_samples, chunk_size):
        end = min(start + chunk_size, n_samples)
        batch = mm_read[start:end]
        batch_size = end - start
        # Incremental mean update
        running_mean = (
            running_mean * running_count + batch.sum(axis=0)
        ) / (running_count + batch_size)
        running_count += batch_size

    print(f"Computed mean via batch processing (first 5 features): "
          f"{running_mean[:5]}")

    # Phase 3: use chunked operations for matrix-vector product
    vector = rng.standard_normal(n_features).astype(np.float32)
    result = np.empty(n_samples, dtype=np.float32)
    for start in range(0, n_samples, chunk_size):
        end = min(start + chunk_size, n_samples)
        result[start:end] = mm_read[start:end] @ vector

    print(f"Matrix-vector product result shape: {result.shape}")
    print(f"Result mean: {result.mean():.6f}")

    # Cleanup — on Windows the memmap handle must be fully released first
    del mm_read
    gc.collect()
    for attempt in range(5):
        try:
            os.remove(filepath)
            os.rmdir(tmpdir)
            break
        except PermissionError:
            time.sleep(0.1)


@timer
def enterprise_vector_similarity() -> None:
    """Large-scale cosine similarity using vectorized dot products.

    Mirrors the document's recommendation example but scaled up:
    compare 10,000 user preference vectors against 1,000 item vectors.
    """
    section("4-C  Enterprise: Batch Cosine Similarity (Recommendation)")

    rng = np.random.default_rng(314)
    n_users = 10_000
    n_items = 1_000
    dim = 128

    user_vecs = rng.standard_normal((n_users, dim)).astype(np.float32)
    item_vecs = rng.standard_normal((n_items, dim)).astype(np.float32)

    # Normalize to unit vectors (L2)
    user_norms = np.linalg.norm(user_vecs, axis=1, keepdims=True)
    item_norms = np.linalg.norm(item_vecs, axis=1, keepdims=True)
    user_unit = user_vecs / user_norms
    item_unit = item_vecs / item_norms

    # Full cosine similarity matrix: (n_users, n_items)
    # similarity[i, j] = dot(user_unit[i], item_unit[j])
    sim_matrix = user_unit @ item_unit.T
    print(f"Similarity matrix shape: {sim_matrix.shape}")
    print(f"Memory: {sim_matrix.nbytes / (1024**2):.1f} MB")

    # Top-5 recommendations per user
    top_k = 5
    top_indices = np.argpartition(-sim_matrix, top_k, axis=1)[:, :top_k]
    # Sort within top-k
    for i in range(min(3, n_users)):
        row = top_indices[i]
        row_sorted = row[np.argsort(-sim_matrix[i, row])]
        scores = sim_matrix[i, row_sorted]
        print(f"  User {i} top-{top_k} items: {row_sorted.tolist()} "
              f"scores: [{', '.join(f'{s:.3f}' for s in scores)}]")


@timer
def enterprise_time_series_resample() -> None:
    """Efficiently aggregate time-series sensor data using structured arrays."""
    section("4-D  Enterprise: Time-Series Aggregation")

    # Simulate 1M sensor readings over one month
    n = 1_000_000
    rng = np.random.default_rng(55)
    base = np.datetime64("2025-06-01T00:00:00", "s")
    offsets = rng.integers(0, 30 * 86400, size=n)
    timestamps = base + offsets
    temperatures = (20 + 10 * np.sin(offsets * 2 * np.pi / 86400)
                    + rng.normal(0, 2, n)).astype(np.float32)

    # Sort by timestamp for efficient grouping
    order = np.argsort(timestamps)
    timestamps = timestamps[order]
    temperatures = temperatures[order]

    # Convert timestamps to day index for grouping
    day_index = ((timestamps - base) / np.timedelta64(1, "D")).astype(np.int32)

    # Vectorized daily aggregation via bincount
    day_sum = np.bincount(day_index, weights=temperatures, minlength=30)
    day_count = np.bincount(day_index, minlength=30)
    daily_mean = np.where(day_count > 0, day_sum / day_count, 0.0)

    print(f"Daily mean temperatures (first 10 days):")
    for d in range(10):
        print(f"  Day {d:2d}: {daily_mean[d]:.2f} C  "
              f"({day_count[d]:,} readings)")

    # Find hottest and coldest days
    hottest = np.argmax(daily_mean)
    coldest = np.argmin(daily_mean)
    print(f"\nHottest day: {hottest} ({daily_mean[hottest]:.2f} C)")
    print(f"Coldest day: {coldest} ({daily_mean[coldest]:.2f} C)")


# ===================================================================
# 5. Supplementary: Linear Algebra & Polynomial (from the document)
# ===================================================================

def demo_document_examples() -> None:
    """Reproduce key examples from the NumPy Day 71 document."""
    section("5  Document Examples: Linear Algebra & Polynomials")

    # --- Vector dot product (cosine similarity) ---
    u = np.array([5, 1, 3])
    m1 = np.array([4, 5, 1])
    m2 = np.array([5, 1, 5])
    cos1 = np.dot(u, m1) / (np.linalg.norm(u) * np.linalg.norm(m1))
    cos2 = np.dot(u, m2) / (np.linalg.norm(u) * np.linalg.norm(m2))
    print(f"Movie recommendation — cosine(u, m1) = {cos1:.4f}")
    print(f"Movie recommendation — cosine(u, m2) = {cos2:.4f}")
    print(f"  => Recommend m2 (comedy-action) to user u")

    # --- Cross product ---
    print(f"\nCross product u x m1 = {np.cross(u, m1)}")
    print(f"Cross product m1 x u = {np.cross(m1, u)}")

    # --- Matrix inverse and determinant ---
    A = np.array([[1., 2.], [3., 4.]])
    A_inv = np.linalg.inv(A)
    print(f"\nA inverse:\n{A_inv}")
    print(f"A @ A_inv (should be I):\n{np.around(A @ A_inv)}")

    m5 = np.array([[1, 3, 5], [2, 4, 6], [4, 7, 9]])
    print(f"\ndet(m5) = {np.linalg.det(m5)}")
    print(f"rank(m5) = {np.linalg.matrix_rank(m5)}")

    # --- Solve linear system ---
    A_sys = np.array([[1, 2, 1], [3, 7, 2], [2, 2, 1]])
    b_sys = np.array([8, 23, 9]).reshape(-1, 1)
    x_sol = np.linalg.solve(A_sys, b_sys)
    print(f"\nSolution to Ax=b: {x_sol.flatten()}")

    # --- Polynomial fit ---
    from numpy.polynomial import Polynomial

    x_income = np.array([
        25000, 15850, 15500, 20500, 22000, 20010, 26050, 12500, 18500, 27300,
        15000, 8300, 23320, 5250, 5800, 9100, 4800, 16000, 28500, 32000,
        31300, 10800, 6750, 6020, 13300, 30020, 3200, 17300, 8835, 3500,
    ], dtype=np.float64)
    y_spending = np.array([
        2599, 1400, 1120, 2560, 1900, 1200, 2320, 800, 1650, 2200,
        980, 580, 1885, 600, 400, 800, 420, 1380, 1980, 3999,
        3800, 725, 520, 420, 1200, 4020, 350, 1500, 560, 500,
    ], dtype=np.float64)

    corr = np.corrcoef(x_income, y_spending)[0, 1]
    print(f"\nIncome vs Spending correlation: {corr:.4f}")

    coefs = Polynomial.fit(x_income, y_spending, deg=1).convert().coef
    print(f"Linear regression: y = {coefs[1]:.6f} * x + {coefs[0]:.2f}")


# ===================================================================
# Main entry point
# ===================================================================

def main() -> None:
    """Run all demonstrations."""
    print(f"NumPy version: {np.__version__}")
    print(f"Python version: {sys.version}")

    # Part 1 — Advanced Indexing
    demo_fancy_indexing()
    demo_boolean_indexing()
    demo_combined_indexing()
    demo_indexing_edge_cases()

    # Part 2 — Structured Arrays
    demo_structured_arrays()
    demo_structured_ops()

    # Part 3 — Performance Optimization
    demo_vectorization_vs_loop()
    demo_broadcasting_optimization()
    demo_memory_layout()
    demo_inplace_operations()
    demo_dtype_optimization()

    # Part 4 — Enterprise Examples
    enterprise_log_analysis()
    enterprise_batch_processing()
    enterprise_vector_similarity()
    enterprise_time_series_resample()

    # Part 5 — Document Examples
    demo_document_examples()

    section("ALL DEMONSTRATIONS COMPLETE")


if __name__ == "__main__":
    main()
