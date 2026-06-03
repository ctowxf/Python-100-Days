"""
Day 70 - NumPy Applications Part 3: Statistical Functions, Random Number Generation, and File I/O
===============================================================================================

Topics covered:
  1. Array operations (scalar, element-wise, universal functions)
  2. Broadcasting mechanism
  3. Statistical functions
  4. Random number generation
  5. File I/O with NumPy
  6. C++ comparison: NumPy random vs C++ <random>
  7. Enterprise examples: Monte Carlo simulation, data generation, statistical analysis

C++ Comparison Note:
    NumPy's random module provides a high-level, vectorized interface for generating
    random numbers, while C++'s <random> header offers fine-grained control over
    engine types (mt19937, ranlux48, etc.) and distribution objects.

    In C++ <random>:
        std::mt19937 gen(seed);
        std::normal_distribution<> dist(mean, stddev);
        double value = dist(gen);  // one value at a time (scalar)

    In NumPy:
        rng = np.random.default_rng(seed)
        values = rng.normal(mean, stddev, size=10000)  # vectorized, all at once

    NumPy trades per-element engine control for massive parallelism and brevity.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Optional, Sequence
from pathlib import Path


# =============================================================================
# Part 1: Array Operations (from the document)
# =============================================================================

def demonstrate_scalar_operations() -> None:
    """Show array-to-scalar arithmetic and relational operations."""
    print("=" * 60)
    print("Part 1a: Array vs Scalar Operations")
    print("=" * 60)

    arr: np.ndarray = np.arange(1, 10)

    print(f"Original array:  {arr}")
    print(f"arr + 10:        {arr + 10}")
    print(f"arr * 10:        {arr * 10}")
    print(f"arr > 5:         {arr > 5}")
    print(f"arr % 2 == 0:    {arr % 2 == 0}")


def demonstrate_array_operations() -> None:
    """Show element-wise arithmetic and relational operations between arrays."""
    print("\n" + "=" * 60)
    print("Part 1b: Array vs Array Operations")
    print("=" * 60)

    arr1: np.ndarray = np.arange(1, 10)
    arr2: np.ndarray = np.array([1, 1, 1, 2, 2, 2, 3, 3, 3])

    print(f"arr1:            {arr1}")
    print(f"arr2:            {arr2}")
    print(f"arr1 + arr2:     {arr1 + arr2}")
    print(f"arr1 * arr2:     {arr1 * arr2}")
    print(f"arr1 ** arr2:    {arr1 ** arr2}")
    print(f"arr1 > arr2:     {arr1 > arr2}")
    print(f"arr1 % arr2 == 0:{arr1 % arr2 == 0}")


def demonstrate_universal_functions() -> None:
    """Show universal unary and binary functions."""
    print("\n" + "=" * 60)
    print("Part 1c: Universal Functions")
    print("=" * 60)

    arr: np.ndarray = np.arange(1, 10)

    # Unary functions
    print("--- Unary Functions ---")
    print(f"sqrt:  {np.sqrt(arr)}")
    print(f"log2:  {np.log2(arr)}")
    print(f"exp:   {np.exp(arr)}")
    print(f"sign:  {np.sign(np.array([-3, 0, 5]))}")
    print(f"ceil:  {np.ceil(np.array([1.2, 2.5, 3.8]))}")
    print(f"floor: {np.floor(np.array([1.2, 2.5, 3.8]))}")

    # Binary functions
    print("\n--- Binary Functions ---")
    a3: np.ndarray = np.array([[4, 5, 6], [7, 8, 9]])
    a4: np.ndarray = np.array([[1, 2, 3], [3, 2, 1]])
    print(f"maximum(a3, a4):\n{np.maximum(a3, a4)}")
    print(f"power(a3, a4):\n{np.power(a3, a4)}")


def demonstrate_broadcasting() -> None:
    """Show how NumPy broadcasting handles arrays of different shapes."""
    print("\n" + "=" * 60)
    print("Part 1d: Broadcasting Mechanism")
    print("=" * 60)

    a5: np.ndarray = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2], [3, 3, 3]])
    a6: np.ndarray = np.array([1, 2, 3])
    a7: np.ndarray = np.array([[1], [2], [3], [4]])

    print(f"a5 shape {a5.shape} + a6 shape {a6.shape}:")
    print(f"{a5 + a6}\n")

    print(f"a5 shape {a5.shape} + a7 shape {a7.shape}:")
    print(f"{a5 + a7}")


def demonstrate_array_utilities() -> None:
    """Show utility functions: unique, stack, concatenate, append, insert, where, etc."""
    print("\n" + "=" * 60)
    print("Part 1e: Array Utility Functions")
    print("=" * 60)

    arr: np.ndarray = np.arange(1, 10)

    # Unique
    data: np.ndarray = np.array([1, 2, 2, 3, 3, 3, 4])
    print(f"unique({data}): {np.unique(data)}")

    # Stack and concatenate
    a8: np.ndarray = np.array([[1, 1, 1], [2, 2, 2], [3, 3, 3]])
    a9: np.ndarray = np.array([[4, 4, 4], [5, 5, 5], [6, 6, 6]])
    print(f"\nhstack:\n{np.hstack((a8, a9))}")
    print(f"\nvstack:\n{np.vstack((a8, a9))}")

    # Append and insert
    print(f"\nappend(arr, [10, 100]): {np.append(arr, [10, 100])}")
    print(f"insert(arr, 1, [98, 99, 100]): {np.insert(arr, 1, [98, 99, 100])}")

    # Conditional extraction
    print(f"\nwhere(arr <= 5, arr * 10, arr ** 2): {np.where(arr <= 5, arr * 10, arr ** 2)}")
    print(f"extract(arr % 2 != 0, arr): {np.extract(arr % 2 != 0, arr)}")
    print(f"select([arr <= 3, arr >= 7], [arr * 10, arr ** 2]): "
          f"{np.select([arr <= 3, arr >= 7], [arr * 10, arr ** 2])}")

    # Repeat and tile
    print(f"\nrepeat(arr, 3): {np.repeat(arr, 3)}")
    print(f"tile(arr, 2):    {np.tile(arr, 2)}")

    # Resize
    print(f"\nresize(arr, (5, 3)):\n{np.resize(arr, (5, 3))}")


# =============================================================================
# Part 2: Statistical Functions
# =============================================================================

def demonstrate_statistical_functions() -> None:
    """Show NumPy statistical aggregation functions on arrays."""
    print("\n" + "=" * 60)
    print("Part 2: Statistical Functions")
    print("=" * 60)

    rng: np.random.Generator = np.random.default_rng(42)
    data: np.ndarray = rng.normal(loc=100, scale=15, size=1000)

    print(f"Dataset: 1000 samples from N(100, 15)")
    print(f"  Mean:             {np.mean(data):.4f}")
    print(f"  Median:           {np.median(data):.4f}")
    print(f"  Std Dev:          {np.std(data, ddof=1):.4f}")
    print(f"  Variance:         {np.var(data, ddof=1):.4f}")
    print(f"  Min:              {np.min(data):.4f}")
    print(f"  Max:              {np.max(data):.4f}")
    print(f"  25th percentile:  {np.percentile(data, 25):.4f}")
    print(f"  75th percentile:  {np.percentile(data, 75):.4f}")
    print(f"  IQR:              {np.percentile(data, 75) - np.percentile(data, 25):.4f}")

    # Multi-dimensional statistics
    print("\n--- Multi-dimensional Statistics ---")
    matrix: np.ndarray = rng.integers(1, 100, size=(4, 5))
    print(f"Matrix:\n{matrix}")
    print(f"  Row means (axis=1):    {np.mean(matrix, axis=1)}")
    print(f"  Col means (axis=0):    {np.mean(matrix, axis=0)}")
    print(f"  Col std (axis=0):      {np.std(matrix, axis=0, ddof=1)}")

    # Covariance and correlation
    print("\n--- Covariance and Correlation ---")
    x: np.ndarray = rng.normal(0, 1, size=200)
    y: np.ndarray = 2.0 * x + rng.normal(0, 0.5, size=200)
    print(f"  Covariance matrix:\n{np.cov(x, y)}")
    corr_matrix: np.ndarray = np.corrcoef(x, y)
    print(f"  Correlation coefficient: {corr_matrix[0, 1]:.4f}")

    # Histogram / binning
    print("\n--- Histogram / Binning ---")
    counts: np.ndarray
    bin_edges: np.ndarray
    counts, bin_edges = np.histogram(data, bins=5)
    print(f"  Bin edges:   {np.round(bin_edges, 2)}")
    print(f"  Bin counts:  {counts}")


# =============================================================================
# Part 3: Random Number Generation
# =============================================================================

def demonstrate_random_generation() -> None:
    """Show NumPy random number generation with the modern Generator API."""
    print("\n" + "=" * 60)
    print("Part 3: Random Number Generation")
    print("=" * 60)

    rng: np.random.Generator = np.random.default_rng(seed=2024)

    # Uniform distribution
    uniform_samples: np.ndarray = rng.uniform(low=0.0, high=1.0, size=10)
    print(f"Uniform [0,1) x10:     {np.round(uniform_samples, 4)}")

    # Normal / Gaussian distribution
    normal_samples: np.ndarray = rng.normal(loc=0, scale=1, size=10)
    print(f"Standard Normal x10:   {np.round(normal_samples, 4)}")

    # Integer random samples (like C++ std::uniform_int_distribution)
    int_samples: np.ndarray = rng.integers(low=1, high=100, size=10)
    print(f"Integers [1,100) x10:  {int_samples}")

    # Discrete distribution (weighted coin / die)
    choices: np.ndarray = rng.choice(
        a=["H", "T"],
        size=20,
        p=[0.6, 0.4],
    )
    print(f"Weighted coin x20:     {''.join(choices)}")

    # Shuffle (in-place) and permutation (returns copy)
    deck: np.ndarray = np.arange(1, 11)
    rng.shuffle(deck)
    print(f"Shuffled deck:         {deck}")
    print(f"Permuted (original):   {rng.permutation(np.arange(1, 11))}")

    # Multivariate normal
    mean: np.ndarray = np.array([0.0, 0.0])
    cov: np.ndarray = np.array([[1.0, 0.8], [0.8, 1.0]])
    mvn_samples: np.ndarray = rng.multivariate_normal(mean, cov, size=5)
    print(f"\nMultivariate Normal (corr=0.8) x5:\n{np.round(mvn_samples, 4)}")

    # Poisson distribution
    poisson_samples: np.ndarray = rng.poisson(lam=5.0, size=10)
    print(f"\nPoisson(lambda=5) x10: {poisson_samples}")

    # Exponential distribution
    exp_samples: np.ndarray = rng.exponential(scale=1.0, size=10)
    print(f"Exponential(scale=1) x10: {np.round(exp_samples, 4)}")


def cpp_random_comparison() -> None:
    """
    Compare NumPy random with C++ <random>.

    C++ approach (pseudo-code):
        #include <random>
        #include <vector>

        std::mt19937 gen(42);                          // Mersenne Twister engine
        std::normal_distribution<> norm_dist(0.0, 1.0);
        std::uniform_real_distribution<> unif_dist(0.0, 1.0);

        std::vector<double> normals(1000);
        for (auto& v : normals) v = norm_dist(gen);    // scalar loop

    NumPy approach:
        rng = np.random.default_rng(42)                // BitGenerator + Generator
        normals = rng.normal(0, 1, size=1000)          // vectorized, no loop

    Key differences:
        +----------------------------------------------------+----------------------------+
        | C++ <random>                                       | NumPy random               |
        +----------------------------------------------------+----------------------------+
        | Engine + Distribution separation (flexible)        | Generator wraps everything |
        | Per-element generation (loop required)             | Vectorized (array at once) |
        | Explicit seed on engine object                     | Seed passed to Generator   |
        | Deterministic thread-safe with local engines       | Global state in legacy API |
        | Supported engines: mt19937, ranlux48, minstd_rand | BitGenerator backends      |
        | Compile-time distribution types                    | Runtime function calls     |
        | Zero overhead abstractions (zero-cost)             | C-level optimized loops    |
        +----------------------------------------------------+----------------------------+

    NumPy's Generator (introduced in 1.17) uses PCG64 as default BitGenerator,
    which is faster and has better statistical properties than the legacy
    Mersenne Twister used in numpy.random.RandomState.
    """
    print("\n" + "=" * 60)
    print("Part 3b: NumPy random vs C++ <random>")
    print("=" * 60)
    print("See docstring of cpp_random_comparison() for full comparison table.\n")

    # Demonstrate the NumPy side concretely
    rng: np.random.Generator = np.random.default_rng(42)
    sample: np.ndarray = rng.normal(0, 1, size=100000)
    print(f"Generated 100,000 normal samples in one call:")
    print(f"  Mean = {np.mean(sample):.6f} (expect ~0)")
    print(f"  Std  = {np.std(sample, ddof=1):.6f} (expect ~1)")
    print(f"  Backing BitGenerator: {type(rng.bit_generator).__name__}")


# =============================================================================
# Part 4: File I/O
# =============================================================================

def demonstrate_file_io() -> None:
    """Show NumPy file I/O: .npy, .npz, .csv, and .txt formats."""
    print("\n" + "=" * 60)
    print("Part 4: File I/O with NumPy")
    print("=" * 60)

    rng: np.random.Generator = np.random.default_rng(99)
    data: np.ndarray = rng.integers(0, 100, size=(5, 4))
    print(f"Original data:\n{data}")

    # Use a temp directory for demo files
    out_dir: Path = Path(__file__).parent / "_numpy_io_demo"
    out_dir.mkdir(exist_ok=True)

    # --- .npy (single array, binary) ---
    npy_path: Path = out_dir / "array.npy"
    np.save(npy_path, data)
    loaded_npy: np.ndarray = np.load(npy_path)
    print(f"\nLoaded from .npy:\n{loaded_npy}")
    assert np.array_equal(data, loaded_npy), ".npy round-trip failed"

    # --- .npz (multiple arrays, compressed) ---
    npz_path: Path = out_dir / "arrays.npz"
    arr_a: np.ndarray = rng.normal(size=(3, 3))
    arr_b: np.ndarray = rng.integers(0, 10, size=(2, 5))
    np.savez(npz_path, matrix=arr_a, labels=arr_b)
    loaded_npz: np.lib.npyio.NpzFile = np.load(npz_path)
    print(f"\nLoaded 'matrix' from .npz:\n{np.round(loaded_npz['matrix'], 4)}")
    print(f"Loaded 'labels' from .npz:\n{loaded_npz['labels']}")

    # --- .csv (text, comma-separated) ---
    csv_path: Path = out_dir / "data.csv"
    header: str = "col_a,col_b,col_c,col_d"
    np.savetxt(csv_path, data, delimiter=",", header=header, comments="", fmt="%d")
    loaded_csv: np.ndarray = np.loadtxt(csv_path, delimiter=",", skiprows=1)
    print(f"\nLoaded from .csv:\n{loaded_csv.astype(int)}")

    # --- .txt (space-separated) ---
    txt_path: Path = out_dir / "data.txt"
    np.savetxt(txt_path, data, fmt="%d")
    loaded_txt: np.ndarray = np.loadtxt(txt_path)
    print(f"\nLoaded from .txt:\n{loaded_txt.astype(int)}")

    # Cleanup
    for f in out_dir.iterdir():
        f.unlink()
    out_dir.rmdir()
    print("\nTemporary I/O files cleaned up.")


# =============================================================================
# Part 5: Enterprise Examples
# =============================================================================

def enterprise_monte_carlo_simulation() -> None:
    """
    Monte Carlo simulation to estimate European call option price.

    Uses Geometric Brownian Motion:
        S_T = S_0 * exp((r - 0.5*sigma^2)*T + sigma*sqrt(T)*Z)
    where Z ~ N(0,1).

    This is a standard technique in quantitative finance for option pricing.
    """
    print("\n" + "=" * 60)
    print("Enterprise Example 1: Monte Carlo Option Pricing")
    print("=" * 60)

    # Parameters
    S0: float = 100.0       # Current stock price
    K: float = 105.0        # Strike price
    T: float = 1.0          # Time to maturity (years)
    r: float = 0.05         # Risk-free rate
    sigma: float = 0.20     # Volatility
    n_simulations: int = 500_000

    rng: np.random.Generator = np.random.default_rng(seed=42)

    # Generate terminal stock prices under GBM
    Z: np.ndarray = rng.standard_normal(n_simulations)
    ST: np.ndarray = S0 * np.exp((r - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)

    # Payoff of European call option
    payoff: np.ndarray = np.maximum(ST - K, 0.0)

    # Discounted expected payoff
    option_price: float = float(np.exp(-r * T) * np.mean(payoff))
    std_error: float = float(np.std(payoff) / np.sqrt(n_simulations))

    print(f"  Spot price (S0):        {S0}")
    print(f"  Strike (K):             {K}")
    print(f"  Volatility (sigma):     {sigma}")
    print(f"  Simulations:            {n_simulations:,}")
    print(f"  Estimated option price: {option_price:.4f}")
    print(f"  Standard error:         {std_error:.4f}")
    print(f"  95% confidence interval:[{option_price - 1.96*std_error:.4f}, "
          f"{option_price + 1.96*std_error:.4f}]")


def enterprise_data_generation() -> None:
    """
    Generate a synthetic enterprise sales dataset with realistic distributions.

    Simulates monthly sales data for multiple product lines across regions,
    useful for dashboard prototyping, testing ETL pipelines, and demos.
    """
    print("\n" + "=" * 60)
    print("Enterprise Example 2: Synthetic Sales Data Generation")
    print("=" * 60)

    rng: np.random.Generator = np.random.default_rng(seed=123)

    n_records: int = 1000
    regions: np.ndarray = rng.choice(
        ["North", "South", "East", "West"],
        size=n_records,
        p=[0.3, 0.25, 0.25, 0.2],
    )
    products: np.ndarray = rng.choice(
        ["Widget", "Gadget", "Doohickey"],
        size=n_records,
    )

    # Sales amounts: log-normal distribution (realistic for revenue data)
    base_sales: np.ndarray = rng.lognormal(mean=8.0, sigma=0.6, size=n_records)

    # Region multipliers
    region_mult: dict[str, float] = {"North": 1.1, "South": 0.9, "East": 1.0, "West": 1.05}
    mult_arr: np.ndarray = np.array([region_mult[r] for r in regions])
    sales: np.ndarray = np.round(base_sales * mult_arr, 2)

    # Units sold (correlated with sales)
    unit_price: dict[str, float] = {"Widget": 25.0, "Gadget": 50.0, "Doohickey": 15.0}
    prices: np.ndarray = np.array([unit_price[p] for p in products])
    units: np.ndarray = np.maximum(1, (sales / prices).astype(int))

    # Summary statistics
    print(f"  Generated {n_records} sales records")
    print(f"  Total revenue:    ${np.sum(sales):,.2f}")
    print(f"  Mean sale:        ${np.mean(sales):,.2f}")
    print(f"  Median sale:      ${np.median(sales):,.2f}")
    print(f"  Total units sold: {np.sum(units):,}")

    # Per-region breakdown
    print("\n  Revenue by region:")
    for region in ["North", "South", "East", "West"]:
        mask: np.ndarray = regions == region
        region_total: float = float(np.sum(sales[mask]))
        region_count: int = int(np.sum(mask))
        print(f"    {region:6s}: ${region_total:>12,.2f}  ({region_count} records)")


def enterprise_statistical_analysis() -> None:
    """
    Statistical quality control analysis using NumPy.

    Simulates a manufacturing process and applies SPC (Statistical Process Control)
    principles: control charts, process capability indices (Cp, Cpk).
    """
    print("\n" + "=" * 60)
    print("Enterprise Example 3: Statistical Process Control (SPC)")
    print("=" * 60)

    rng: np.random.Generator = np.random.default_rng(seed=77)

    # Process parameters
    target: float = 50.0       # Target dimension (mm)
    tolerance: float = 2.0     # +/- tolerance
    usl: float = target + tolerance  # Upper spec limit
    lsl: float = target - tolerance  # Lower spec limit
    process_sigma: float = 0.5

    # Generate 25 subgroups of 5 measurements each (standard SPC setup)
    n_subgroups: int = 25
    subgroup_size: int = 5
    measurements: np.ndarray = rng.normal(
        loc=target, scale=process_sigma, size=(n_subgroups, subgroup_size)
    )

    # Subgroup statistics
    subgroup_means: np.ndarray = np.mean(measurements, axis=1)
    subgroup_ranges: np.ndarray = np.ptp(measurements, axis=1)  # peak-to-peak = max - min

    # Control limits (X-bar chart)
    grand_mean: float = float(np.mean(subgroup_means))
    mean_range: float = float(np.mean(subgroup_ranges))

    # A2 constant for n=5 subgroup size
    A2: float = 0.577
    ucl_x: float = grand_mean + A2 * mean_range
    lcl_x: float = grand_mean - A2 * mean_range

    print(f"  Process target:        {target} mm")
    print(f"  Specification limits:  [{lsl}, {usl}] mm")
    print(f"  Grand mean (X-bar):    {grand_mean:.4f} mm")
    print(f"  Mean range (R-bar):    {mean_range:.4f} mm")
    print(f"  X-bar control limits:  [{lcl_x:.4f}, {ucl_x:.4f}]")

    # Check for out-of-control points
    out_of_control: int = int(np.sum(
        (subgroup_means > ucl_x) | (subgroup_means < lcl_x)
    ))
    print(f"  Out-of-control points: {out_of_control}")

    # Process capability indices
    sigma_hat: float = mean_range / 2.326  # d2 constant for n=5
    cp: float = (usl - lsl) / (6 * sigma_hat)
    cpk: float = min(
        (usl - grand_mean) / (3 * sigma_hat),
        (grand_mean - lsl) / (3 * sigma_hat),
    )
    print(f"\n  Estimated sigma:       {sigma_hat:.4f}")
    print(f"  Cp  (process capability):       {cp:.4f}")
    print(f"  Cpk (process capability index): {cpk:.4f}")

    if cpk >= 1.33:
        verdict: str = "CAPABLE (Cpk >= 1.33)"
    elif cpk >= 1.0:
        verdict = "MARGINAL (1.0 <= Cpk < 1.33)"
    else:
        verdict = "NOT CAPABLE (Cpk < 1.0)"
    print(f"  Verdict:               {verdict}")

    # Yield estimation
    defect_prob: float = float(
        1 - (np.sum((measurements >= lsl) & (measurements <= usl))
             / measurements.size)
    )
    print(f"  Estimated defect rate: {defect_prob:.6f} ({defect_prob * 1_000_000:.1f} PPM)")


# =============================================================================
# Main Entry Point
# =============================================================================

def main() -> None:
    """Run all demonstrations in sequence."""
    print("NumPy Applications Part 3 - Comprehensive Practice")
    print("=" * 60)

    # Part 1: Array operations from the document
    demonstrate_scalar_operations()
    demonstrate_array_operations()
    demonstrate_universal_functions()
    demonstrate_broadcasting()
    demonstrate_array_utilities()

    # Part 2: Statistical functions
    demonstrate_statistical_functions()

    # Part 3: Random number generation
    demonstrate_random_generation()
    cpp_random_comparison()

    # Part 4: File I/O
    demonstrate_file_io()

    # Part 5: Enterprise examples
    enterprise_monte_carlo_simulation()
    enterprise_data_generation()
    enterprise_statistical_analysis()

    print("\n" + "=" * 60)
    print("All demonstrations complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
