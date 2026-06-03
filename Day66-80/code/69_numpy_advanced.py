"""
NumPy Advanced Operations - Day 69
===================================
Topics: Broadcasting, Universal Functions (ufuncs), Matrix Operations, Linear Algebra.

C++ Comparison (NumPy broadcasting vs C++ Eigen broadcasting):
---------------------------------------------------------------
NumPy broadcasting allows arithmetic on arrays of different shapes without
explicit loops or memory copies. Rules:
  1. If arrays differ in ndim, prepend 1s to the smaller shape.
  2. Dimensions of size 1 are stretched to match the other.
  3. Incompatible shapes raise ValueError.

In C++ Eigen, broadcasting is done via .rowwise() and .colwise() replicators:
  Eigen::MatrixXd A(3, 3);
  Eigen::VectorXd v(3);
  // Replicate v across columns: A.colwise() + v
  // Replicate a row vector across rows: A.rowwise() + rv.transpose()

Key differences:
  - NumPy: implicit, shape-rules-driven, zero-copy when possible.
  - Eigen: explicit .colwise()/.rowwise() semantics; compile-time known sizes
    (Eigen::Matrix<double,3,3>) enable stronger optimizations.
  - NumPy broadcasts any rank; Eigen broadcasting is limited to 1-D expansions.
  - Eigen expressions are lazy and fused; NumPy ufuncs also fuse loops but
    intermediate arrays may still be materialized.

Dependencies: numpy, scipy (optional for PCA), matplotlib (optional for visualization)
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# Type aliases for readability
FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


# =============================================================================
# 1. Broadcasting
# =============================================================================

def broadcasting_demo() -> None:
    """Demonstrate NumPy broadcasting rules with practical examples."""
    print("=" * 60)
    print("1. BROADCASTING")
    print("=" * 60)

    # Rule 1: scalar broadcasts to any shape
    arr = np.arange(12).reshape(3, 4)
    print(f"\nOriginal (3x4):\n{arr}")
    print(f"Add 100 (scalar broadcast):\n{arr + 100}")

    # Rule 2: 1-D array broadcasts across rows
    col_means = np.array([10.0, 20.0, 30.0, 40.0])
    centered = arr - col_means  # (3,4) - (4,) -> (3,4)
    print(f"\nColumn means: {col_means}")
    print(f"Centered (subtract col mean per column):\n{centered}")

    # Rule 3: higher-dimensional broadcasting
    # Shape (2,3,4) + (4,) -> (2,3,4)
    cube = np.ones((2, 3, 4))
    vec = np.array([1, 2, 3, 4])
    result = cube * vec
    print(f"\nCube (2,3,4) * vec (4,): shape = {result.shape}")

    # Incompatible shapes
    try:
        a = np.ones((3, 4))
        b = np.ones((3, 3))
        _ = a + b
    except ValueError as e:
        print(f"\nIncompatible shapes caught: {e}")

    # --- C++ Eigen equivalent (pseudocode) ---
    # Eigen::MatrixXd A = Eigen::MatrixXd::Ones(3, 4);
    # Eigen::RowVectorXd rv(4);
    # rv << 10, 20, 30, 40;
    # Eigen::MatrixXd centered = A.rowwise() - rv;  // explicit row-wise subtract
    #
    # In Eigen, you must explicitly state the broadcasting axis; NumPy infers it.


# =============================================================================
# 2. Universal Functions (ufuncs)
# =============================================================================

def ufunc_demo() -> None:
    """Demonstrate universal functions: element-wise ops, reduce, accumulate, outer."""
    print("\n" + "=" * 60)
    print("2. UNIVERSAL FUNCTIONS (ufuncs)")
    print("=" * 60)

    arr = np.array([1, 4, 9, 16, 25])

    # Element-wise math ufuncs
    print(f"\narr:          {arr}")
    print(f"sqrt:         {np.sqrt(arr)}")
    print(f"log2:         {np.log2(arr)}")
    print(f"exp:          {np.exp(np.array([0.0, 1.0, 2.0]))}")
    print(f"abs of [-3,2]: {np.abs(np.array([-3, 2]))}")

    # Comparison ufuncs return boolean arrays
    a = np.array([1, 5, 3, 7, 2])
    b = np.array([2, 4, 3, 8, 1])
    print(f"\na:            {a}")
    print(f"b:            {b}")
    print(f"a > b:        {np.greater(a, b)}")
    print(f"max(a,b):     {np.maximum(a, b)}")
    print(f"min(a,b):     {np.minimum(a, b)}")

    # reduce: collapse along an axis
    print(f"\nadd.reduce:   {np.add.reduce(a)}         # sum")
    print(f"multiply.reduce: {np.multiply.reduce(a)}  # product")

    # accumulate: running computation
    print(f"add.accumulate:     {np.add.accumulate(a)}")
    print(f"multiply.accumulate: {np.multiply.accumulate(a)}")

    # outer: Cartesian product of two 1-D arrays
    x = np.array([1, 2, 3])
    y = np.array([10, 20])
    print(f"\nouter product:\n{np.multiply.outer(x, y)}")

    # Custom ufunc (advanced): vectorize a Python function
    @np.vectorize
    def clamp(val: float, lo: float = 0.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, val))

    data = np.array([-0.5, 0.3, 0.7, 1.5])
    print(f"\nClamped to [0,1]: {clamp(data)}")

    # --- C++ comparison ---
    # In Eigen, element-wise ops are .array() methods:
    #   (A.array() * B.array()).matrix()   # element-wise multiply, then back to matrix
    # NumPy ufuncs operate element-wise by default; Eigen distinguishes
    # matrix vs array semantics explicitly.


# =============================================================================
# 3. Descriptive Statistics (from Day 69 doc)
# =============================================================================

def descriptive_statistics_demo() -> None:
    """Descriptive statistics: mean, median, variance, std, axis-wise ops."""
    print("\n" + "=" * 60)
    print("3. DESCRIPTIVE STATISTICS")
    print("=" * 60)

    np.random.seed(42)
    arr1d: IntArray = np.random.randint(1, 100, 10)
    print(f"\n1-D array: {arr1d}")

    # Central tendency
    print(f"Sum:        {arr1d.sum()}")
    print(f"Mean:       {arr1d.mean():.2f}")
    print(f"Median:     {np.median(arr1d):.2f}")
    print(f"Quantile .5: {np.quantile(arr1d, 0.5):.2f}")

    # Dispersion
    print(f"Max:        {arr1d.max()}")
    print(f"Min:        {arr1d.min()}")
    print(f"Range (ptp): {np.ptp(arr1d)}")
    q1, q3 = np.quantile(arr1d, [0.25, 0.75])
    print(f"IQR:        {q3 - q1:.2f}")
    print(f"Variance:   {arr1d.var():.2f}")
    print(f"Std Dev:    {arr1d.std():.2f}")
    print(f"CV (std/mean): {arr1d.std() / arr1d.mean():.4f}")

    # 2-D array with axis operations
    arr2d: IntArray = np.random.randint(60, 101, (5, 3))
    print(f"\n2-D array (5x3):\n{arr2d}")
    print(f"Overall mean:   {arr2d.mean():.2f}")
    print(f"Mean per col (axis=0): {arr2d.mean(axis=0)}")
    print(f"Mean per row (axis=1): {np.round(arr2d.mean(axis=1), 2)}")
    print(f"Max per col:    {arr2d.max(axis=0)}")
    print(f"Max per row:    {arr2d.max(axis=1)}")


# =============================================================================
# 4. Matrix Operations
# =============================================================================

def matrix_operations_demo() -> None:
    """Matrix multiplication, transpose, reshape, and related operations."""
    print("\n" + "=" * 60)
    print("4. MATRIX OPERATIONS")
    print("=" * 60)

    A = np.array([[1, 2, 3],
                  [4, 5, 6]])
    B = np.array([[7, 8],
                  [9, 10],
                  [11, 12]])

    # Matrix multiplication: (2x3) @ (3x2) = (2x2)
    C = A @ B  # equivalent to np.matmul(A, B) or A.dot(B)
    print(f"\nA (2x3):\n{A}")
    print(f"B (3x2):\n{B}")
    print(f"A @ B (2x2):\n{C}")

    # Element-wise vs matrix multiplication
    D = np.array([[1, 2],
                  [3, 4]])
    E = np.array([[5, 6],
                  [7, 8]])
    print(f"\nD:\n{D}")
    print(f"E:\n{E}")
    print(f"D * E (element-wise):\n{D * E}")
    print(f"D @ E (matrix multiply):\n{D @ E}")

    # Transpose
    print(f"\nA^T:\n{A.T}")
    print(f"A.swapaxes(0,1):\n{A.swapaxes(0, 1)}")

    # Reshape and flatten
    flat = A.flatten()
    reshaped = flat.reshape(3, 2)
    print(f"\nA flattened: {flat}")
    print(f"Reshaped to (3,2):\n{reshaped}")

    # np.dot vs np.matmul vs @
    # For 2-D arrays they are equivalent
    print(f"\nnp.dot(A,B) == A @ B: {np.array_equal(np.dot(A, B), A @ B)}")

    # Einstein summation (einsum) - powerful generalized contraction
    # Trace of a square matrix
    sq = np.array([[1, 2], [3, 4]])
    print(f"\nTrace via einsum: {np.einsum('ii->', sq)}  (expected: 5)")

    # Batch matrix multiplication
    batch_A = np.random.randn(2, 3, 3)
    batch_B = np.random.randn(2, 3, 3)
    batch_C = np.matmul(batch_A, batch_B)  # batched @
    print(f"Batch matmul shape: {batch_C.shape}  (2,3,3)")


# =============================================================================
# 5. Linear Algebra (numpy.linalg)
# =============================================================================

def linear_algebra_demo() -> None:
    """Solve linear systems, eigenvalues, SVD, determinants, inverses."""
    print("\n" + "=" * 60)
    print("5. LINEAR ALGEBRA")
    print("=" * 60)

    # Solve Ax = b
    A = np.array([[3.0, 1.0],
                  [1.0, 2.0]])
    b = np.array([9.0, 8.0])
    x = np.linalg.solve(A, b)
    print(f"\nSolve Ax = b:")
    print(f"  A = {A.tolist()}")
    print(f"  b = {b.tolist()}")
    print(f"  x = {x}")
    print(f"  Verify A @ x = {A @ x}")

    # Determinant
    det = np.linalg.det(A)
    print(f"\ndet(A) = {det:.4f}")

    # Inverse
    A_inv = np.linalg.inv(A)
    print(f"\nA_inv:\n{A_inv}")
    print(f"A @ A_inv (should be I):\n{np.round(A @ A_inv, 10)}")

    # Eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eig(A)
    print(f"\nEigenvalues:  {eigenvalues}")
    print(f"Eigenvectors (columns):\n{eigenvectors}")

    # Singular Value Decomposition (SVD)
    M = np.array([[1.0, 2.0, 3.0],
                  [4.0, 5.0, 6.0]])
    U, S, Vt = np.linalg.svd(M, full_matrices=False)
    print(f"\nSVD of M (2x3):")
    print(f"  U shape: {U.shape}, S: {S}, Vt shape: {Vt.shape}")
    # Reconstruct
    M_reconstructed = U @ np.diag(S) @ Vt
    print(f"  Reconstructed (should equal M):\n{np.round(M_reconstructed, 10)}")

    # Norms
    v = np.array([3.0, 4.0])
    print(f"\n||v||_2 = {np.linalg.norm(v):.4f}")       # L2 norm
    print(f"||v||_1 = {np.linalg.norm(v, ord=1):.4f}")  # L1 norm

    # Condition number (stability of linear system)
    cond = np.linalg.cond(A)
    print(f"\nCondition number of A: {cond:.4f}")


# =============================================================================
# 6. Enterprise Example: Recommendation System (User-Item Matrix)
# =============================================================================

def recommendation_system_demo() -> None:
    """
    Simulate a recommendation system using matrix factorization.

    In production systems (e.g., collaborative filtering at scale), the
    user-item rating matrix R is decomposed via SVD or NMF:
        R ≈ U @ Sigma @ Vt
    Missing entries are predicted from the low-rank approximation.
    """
    print("\n" + "=" * 60)
    print("6. ENTERPRISE: Recommendation System (Matrix Factorization)")
    print("=" * 60)

    np.random.seed(0)

    # User-Item rating matrix (0 = unrated)
    # Rows: users (Alice, Bob, Carol, Dave, Eve)
    # Cols: items (Movie1..Movie6)
    R = np.array([
        [5, 3, 0, 1, 0, 0],
        [4, 0, 0, 1, 0, 0],
        [0, 1, 2, 5, 4, 0],
        [0, 0, 4, 4, 5, 3],
        [1, 0, 2, 0, 3, 5],
    ], dtype=np.float64)

    users = ["Alice", "Bob", "Carol", "Dave", "Eve"]
    items = ["Movie1", "Movie2", "Movie3", "Movie4", "Movie5", "Movie6"]

    print(f"\nOriginal user-item matrix (rows=users, cols=items):")
    print(f"  Items: {items}")
    for i, row in enumerate(R):
        print(f"  {users[i]:>6s}: {row.astype(int).tolist()}")

    # Fill zeros with column means for SVD
    col_means = np.true_divide(R.sum(axis=0), (R != 0).sum(axis=0))
    R_filled = R.copy()
    for j in range(R.shape[1]):
        mask = R[:, j] == 0
        R_filled[mask, j] = col_means[j]

    # Mean-center per user
    user_means = R_filled.mean(axis=1, keepdims=True)
    R_centered = R_filled - user_means

    # Low-rank SVD (k=2 factors)
    k = 2
    U, S, Vt = np.linalg.svd(R_centered, full_matrices=False)
    U_k, S_k, Vt_k = U[:, :k], S[:k], Vt[:k, :]

    # Reconstruct predicted ratings
    R_pred = (U_k @ np.diag(S_k) @ Vt_k) + user_means

    print(f"\nPredicted ratings (SVD, k={k}):")
    for i, name in enumerate(users):
        preds = np.round(R_pred[i], 2).tolist()
        print(f"  {name:>6s}: {[f'{p:.1f}' for p in preds]}")

    # Recommend top-2 unrated items for Alice
    alice_ratings = R_pred[0]
    unrated_mask = R[0] == 0
    scores = alice_ratings.copy()
    scores[~unrated_mask] = -np.inf  # exclude already-rated
    top_indices = np.argsort(scores)[::-1][:2]
    print(f"\nTop-2 recommendations for Alice:")
    for idx in top_indices:
        print(f"  {items[idx]} (predicted score: {alice_ratings[idx]:.2f})")


# =============================================================================
# 7. Enterprise Example: Image Transformation
# =============================================================================

def image_transformation_demo() -> None:
    """
    Demonstrate image transformations using matrix operations.

    Images are represented as 2-D (grayscale) or 3-D (color) arrays.
    Geometric transformations (rotation, scaling, affine) are matrix multiplications.
    """
    print("\n" + "=" * 60)
    print("7. ENTERPRISE: Image Transformation (Matrix Operations)")
    print("=" * 60)

    # Simulate a small 4x4 grayscale image
    image: FloatArray = np.array([
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 1.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
    ])

    print(f"\nOriginal image (4x4 grayscale):\n{image}")

    # Transpose (mirror along diagonal)
    flipped = image.T
    print(f"\nTransposed:\n{flipped}")

    # Flip horizontal (left-right) and vertical (up-down)
    print(f"Flip LR:\n{np.fliplr(image)}")
    print(f"Flip UD:\n{np.flipud(image)}")

    # Rotation by 90 degrees using np.rot90
    rot90 = np.rot90(image)
    rot180 = np.rot90(image, k=2)
    print(f"\nRotated 90 CCW:\n{rot90}")
    print(f"Rotated 180:\n{rot180}")

    # Brightness adjustment (broadcasting scalar)
    brightened = np.clip(image + 0.3, 0, 1)
    print(f"\nBrightened (add 0.3, clipped to [0,1]):\n{brightened}")

    # Contrast scaling (broadcasting scalar)
    high_contrast = np.clip(image * 2.0, 0, 1)
    print(f"\nHigh contrast (multiply by 2):\n{high_contrast}")

    # Color image: shape (H, W, 3)
    color_image: FloatArray = np.stack([image, image * 0.5, image * 0.8], axis=-1)
    print(f"\nColor image shape: {color_image.shape}  (H, W, channels)")

    # Apply a color channel swap using advanced indexing
    swapped = color_image[:, :, [2, 0, 1]]  # BGR -> RGB-ish
    print(f"Channel-swapped shape: {swapped.shape}")

    # Affine transformation matrix (2x3 for 2-D points)
    # Scale by 2x in x, 1.5x in y, then translate by (1, 1)
    affine = np.array([
        [2.0, 0.0, 1.0],
        [0.0, 1.5, 1.0],
    ])
    # Apply to a point
    point = np.array([1.0, 1.0, 1.0])  # homogeneous coordinates
    transformed = affine @ point
    print(f"\nAffine transform of point (1,1): {transformed}")

    # In enterprise CV pipelines, these operations are vectorized over all
    # pixels simultaneously using broadcasting, avoiding per-pixel Python loops.


# =============================================================================
# 8. Enterprise Example: PCA (Principal Component Analysis)
# =============================================================================

def pca_demo() -> None:
    """
    Implement PCA from scratch using NumPy linear algebra.

    PCA finds orthogonal directions of maximum variance in data by
    computing the eigendecomposition of the covariance matrix:
        C = (1/n) * X^T @ X  (after centering)
    The top-k eigenvectors form the projection matrix.
    """
    print("\n" + "=" * 60)
    print("8. ENTERPRISE: PCA (Principal Component Analysis)")
    print("=" * 60)

    np.random.seed(42)

    # Generate correlated 3-D data (e.g., features: height, weight, BMI)
    n_samples = 200
    mean = np.array([170.0, 70.0, 24.0])
    # Correlation structure
    cov = np.array([
        [100.0,  60.0,  15.0],
        [ 60.0,  80.0,  20.0],
        [ 15.0,  20.0,   4.0],
    ])
    X: FloatArray = np.random.multivariate_normal(mean, cov, n_samples)

    print(f"\nData shape: {X.shape}  (samples x features)")
    print(f"Feature means: {np.round(X.mean(axis=0), 2)}")

    # Step 1: Center the data
    X_centered = X - X.mean(axis=0)

    # Step 2: Compute covariance matrix
    cov_matrix = (X_centered.T @ X_centered) / (n_samples - 1)
    print(f"\nCovariance matrix:\n{np.round(cov_matrix, 2)}")

    # Step 3: Eigendecomposition
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    # eigh returns in ascending order; reverse for descending
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    print(f"\nEigenvalues: {np.round(eigenvalues, 4)}")
    print(f"Explained variance ratio: {np.round(eigenvalues / eigenvalues.sum(), 4)}")

    # Step 4: Project onto top-2 components
    k = 2
    W = eigenvectors[:, :k]  # (3, 2) projection matrix
    X_pca = X_centered @ W   # (200, 2)

    print(f"\nProjected data shape: {X_pca.shape}  (samples x components)")
    print(f"Sample projections (first 5):\n{np.round(X_pca[:5], 2)}")

    # Reconstruction (approximate)
    X_reconstructed = X_pca @ W.T + X.mean(axis=0)
    reconstruction_error = np.mean((X - X_reconstructed) ** 2)
    print(f"\nMean reconstruction error (k={k}): {reconstruction_error:.4f}")

    # Verify with numpy's built-in (using SVD approach)
    # np.linalg.svd on centered data gives equivalent results
    U_full, S_full, Vt_full = np.linalg.svd(X_centered, full_matrices=False)
    svd_eigenvalues = (S_full ** 2) / (n_samples - 1)
    print(f"SVD-based eigenvalues: {np.round(svd_eigenvalues, 4)}")
    print(f"Match eigendecomp: {np.allclose(np.sort(eigenvalues)[::-1], svd_eigenvalues, atol=1e-8)}")

    # --- C++ Eigen comparison ---
    # In Eigen, PCA would be:
    #   Eigen::MatrixXd centered = X.rowwise() - X.colwise().mean();
    #   Eigen::MatrixXd cov = (centered.adjoint() * centered) / (n - 1);
    #   Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> solver(cov);
    #   // solver.eigenvalues() in ascending order
    #   // solver.eigenvectors() columns are eigenvectors
    # Eigen's SelfAdjointEigenSolver is optimized for symmetric matrices,
    # similar to np.linalg.eigh. For large-scale PCA, randomized SVD
    # (e.g., scipy.sparse.linalg.svds) or sklearn.decomposition.PCA is used.


# =============================================================================
# 9. Advanced: Sparse Matrices and Performance
# =============================================================================

def sparse_and_performance_demo() -> None:
    """Demonstrate sparse matrix operations and vectorization benefits."""
    print("\n" + "=" * 60)
    print("9. Sparse Matrices & Performance")
    print("=" * 60)

    # Sparse matrices are critical for recommendation systems (most entries unrated)
    from scipy.sparse import csr_matrix

    # Create a sparse user-item matrix (1000 users x 500 items, ~5% density)
    np.random.seed(0)
    n_users, n_items = 1000, 500
    density = 0.05
    n_nonzero = int(n_users * n_items * density)

    rows = np.random.randint(0, n_users, n_nonzero)
    cols = np.random.randint(0, n_items, n_nonzero)
    vals = np.random.randint(1, 6, n_nonzero).astype(np.float64)

    sparse_R = csr_matrix((vals, (rows, cols)), shape=(n_users, n_items))
    dense_R = sparse_R.toarray()

    print(f"\nMatrix shape: ({n_users}, {n_items})")
    print(f"Non-zero entries: {sparse_R.nnz}")
    print(f"Density: {sparse_R.nnz / (n_users * n_items) * 100:.1f}%")
    print(f"Sparse memory: {sparse_R.data.nbytes + sparse_R.indices.nbytes + sparse_R.indptr.nbytes} bytes")
    print(f"Dense memory:  {dense_R.nbytes} bytes")
    print(f"Memory ratio (dense/sparse): {dense_R.nbytes / (sparse_R.data.nbytes + sparse_R.indices.nbytes + sparse_R.indptr.nbytes):.1f}x")

    # Sparse matrix-vector multiplication (common in iterative solvers)
    user_vector = np.random.randn(n_items)
    result = sparse_R @ user_vector  # efficient sparse dot product
    print(f"\nSparse @ dense vector result shape: {result.shape}")

    # Vectorization vs loop performance comparison
    import time

    size = 1_000_000
    a_np = np.random.randn(size)
    b_np = np.random.randn(size)

    # NumPy vectorized
    start = time.perf_counter()
    _ = a_np * b_np + a_np ** 2
    numpy_time = time.perf_counter() - start

    # Python loop (simulated on small subset)
    small = 10_000
    a_list = a_np[:small].tolist()
    b_list = b_np[:small].tolist()

    start = time.perf_counter()
    _ = [a * b + a ** 2 for a, b in zip(a_list, b_list)]
    loop_time_small = time.perf_counter() - start

    print(f"\nVectorization performance (n={size}):")
    print(f"  NumPy vectorized: {numpy_time * 1000:.2f} ms")
    print(f"  Python loop (n={small}): {loop_time_small * 1000:.2f} ms")
    print(f"  (Loop on full size would be ~{loop_time_small * (size/small) * 1000:.0f} ms "
          f"vs {numpy_time * 1000:.2f} ms NumPy)")


# =============================================================================
# 10. Array Methods Summary (from Day 69 doc)
# =============================================================================

def array_methods_demo() -> None:
    """Demonstrate common array methods covered in the Day 69 documentation."""
    print("\n" + "=" * 60)
    print("10. COMMON ARRAY METHODS (Day 69 Documentation)")
    print("=" * 60)

    arr = np.array([[1, 2, 3],
                    [4, 5, 6],
                    [7, 8, 9]])
    print(f"\nOriginal:\n{arr}")

    # astype: type conversion
    arr_float = arr.astype(np.float64)
    print(f"\nastype(float64): dtype={arr_float.dtype}")

    # reshape
    reshaped = arr.reshape(1, 9)
    print(f"reshape(1,9): {reshaped}")

    # flatten vs ravel
    print(f"flatten(): {arr.flatten()}  (returns copy)")
    print(f"ravel():   {arr.ravel()}    (returns view when possible)")

    # nonzero
    mask_arr = np.array([[0, 1, 0], [3, 0, 0], [0, 0, 7]])
    nonzero_idx = mask_arr.nonzero()
    print(f"\nnonzero of:\n{mask_arr}")
    print(f"  row indices: {nonzero_idx[0]}")
    print(f"  col indices: {nonzero_idx[1]}")

    # all / any
    bool_arr = np.array([True, True, False])
    print(f"\nall({bool_arr}): {bool_arr.all()}")
    print(f"any({bool_arr}): {bool_arr.any()}")

    # round
    precise = np.array([3.14159, 2.71828, 1.61803])
    print(f"\nOriginal: {precise}")
    print(f"round(2): {precise.round(2)}")

    # fill
    filled = np.empty(5)
    filled.fill(42.0)
    print(f"fill(42): {filled}")

    # tolist
    print(f"tolist(): {arr.tolist()}, type={type(arr.tolist())}")

    # swapaxes / transpose
    arr3d = np.arange(24).reshape(2, 3, 4)
    print(f"\n3-D array shape: {arr3d.shape}")
    print(f"transpose shape: {arr3d.transpose().shape}")       # reverses axes
    print(f"transpose(1,0,2): {arr3d.transpose(1, 0, 2).shape}")  # swap first two


# =============================================================================
# Main Entry Point
# =============================================================================

def main() -> None:
    """Run all demonstrations."""
    print("NumPy Advanced Operations - Comprehensive Examples")
    print("=" * 60)
    print(f"NumPy version: {np.__version__}")
    print()

    broadcasting_demo()
    ufunc_demo()
    descriptive_statistics_demo()
    matrix_operations_demo()
    linear_algebra_demo()
    recommendation_system_demo()
    image_transformation_demo()
    pca_demo()
    sparse_and_performance_demo()
    array_methods_demo()

    print("\n" + "=" * 60)
    print("All demonstrations completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
