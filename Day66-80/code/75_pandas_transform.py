"""
Day 75 - Deep Dive into pandas (Part 4): Data Transformation, GroupBy, and Pivot Tables
========================================================================================

Topics Covered:
    - Element-wise transforms: map(), applymap() / map() on DataFrames, apply()
    - GroupBy mechanics: split-apply-combine
    - Aggregation: agg() with multiple functions, named aggregation
    - Pivot tables and cross tabs
    - Enterprise examples: sales aggregation, cohort analysis, data reshaping

Requirements:
    pip install pandas numpy openpyxl
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any, Callable


# ---------------------------------------------------------------------------
# 1. Helper: sample data generators
# ---------------------------------------------------------------------------

def make_sales_data(n: int = 500, seed: int = 42) -> pd.DataFrame:
    """Generate a realistic sales transaction DataFrame.

    Columns: order_id, order_date, region, channel, brand, unit_price,
             quantity, customer_id
    """
    rng = np.random.default_rng(seed)

    regions = ["Shanghai", "Beijing", "Guangdong", "Zhejiang", "Jiangsu"]
    channels = ["Tmall", "JD", "Pinduoduo", "Douyin", "Offline"]
    brands = ["Alpha", "Beta", "Gamma", "Delta"]

    dates = pd.date_range("2024-01-01", periods=180, freq="D")
    chosen_dates = rng.choice(dates, size=n)

    df = pd.DataFrame({
        "order_id": [f"ORD-{i:06d}" for i in range(1, n + 1)],
        "order_date": chosen_dates,
        "region": rng.choice(regions, size=n),
        "channel": rng.choice(channels, size=n),
        "brand": rng.choice(brands, size=n),
        "unit_price": rng.integers(50, 500, size=n).astype(float),
        "quantity": rng.integers(1, 100, size=n),
        "customer_id": rng.integers(1000, 1100, size=n),
    })
    df["revenue"] = df["unit_price"] * df["quantity"]
    return df


def make_student_scores(seed: int = 0) -> pd.DataFrame:
    """Generate a small student scores DataFrame (Chinese names)."""
    rng = np.random.default_rng(seed)
    names = ["Guan Yu", "Zhang Fei", "Zhao Yun", "Ma Chao", "Huang Zhong"]
    courses = ["Chinese", "Math", "English"]
    scores = rng.integers(50, 101, size=(5, 3))
    return pd.DataFrame(scores, columns=courses, index=names)


# ---------------------------------------------------------------------------
# 2. map() -- element-wise transform on a Series
# ---------------------------------------------------------------------------

def demo_map() -> None:
    """Demonstrate Series.map() with a dictionary and a function."""
    print("\n" + "=" * 70)
    print("DEMO: Series.map()")
    print("=" * 70)

    df = make_sales_data(20)

    # Map region names to short codes using a dict
    region_map: dict[str, str] = {
        "Shanghai": "SH", "Beijing": "BJ", "Guangdong": "GD",
        "Zhejiang": "ZJ", "Jiangsu": "JS",
    }
    df["region_code"] = df["region"].map(region_map)
    print("\nRegion -> Code mapping (first 5 rows):")
    print(df[["region", "region_code"]].head())

    # Map with a function: classify unit price tiers
    def price_tier(price: float) -> str:
        if price < 150:
            return "Low"
        elif price < 300:
            return "Mid"
        return "High"

    df["price_tier"] = df["unit_price"].map(price_tier)
    print("\nPrice tier mapping (first 10 rows):")
    print(df[["unit_price", "price_tier"]].head(10))


# ---------------------------------------------------------------------------
# 3. DataFrame.map() (replaces deprecated applymap in pandas >= 2.1)
# ---------------------------------------------------------------------------

def demo_applymap() -> None:
    """Demonstrate element-wise transform on an entire DataFrame."""
    print("\n" + "=" * 70)
    print("DEMO: DataFrame.map() / applymap()")
    print("=" * 70)

    scores = make_student_scores()
    print("\nOriginal scores:")
    print(scores)

    # Apply a function element-wise: convert to letter grade
    def to_letter(score: int) -> str:
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        return "F"

    # pandas >= 2.1 uses DataFrame.map(); older versions use applymap()
    if hasattr(pd.DataFrame, "map"):
        graded = scores.map(to_letter)
    else:
        graded = scores.applymap(to_letter)
    print("\nLetter grades:")
    print(graded)

    # Format numbers with a lambda
    formatted = scores.map(lambda x: f"{x:>3d}%")  # type: ignore[union-attr]
    print("\nFormatted scores:")
    print(formatted)


# ---------------------------------------------------------------------------
# 4. apply() -- row / column wise transforms
# ---------------------------------------------------------------------------

def demo_apply() -> None:
    """Demonstrate DataFrame.apply() along axes."""
    print("\n" + "=" * 70)
    print("DEMO: DataFrame.apply()")
    print("=" * 70)

    scores = make_student_scores()
    print("\nOriginal scores:")
    print(scores)

    # Column-wise (axis=0): normalize each column to 0-1 range
    col_min = scores.min()
    col_max = scores.max()
    normalized = scores.apply(lambda col: (col - col_min[col.name]) / (col_max[col.name] - col_min[col.name]))
    print("\nColumn-wise normalization (0-1):")
    print(normalized.round(2))

    # Row-wise (axis=1): compute student average and rank
    scores["Average"] = scores.apply(lambda row: row.mean(), axis=1)
    scores["Rank"] = scores["Average"].rank(ascending=False).astype(int)
    print("\nWith average and rank:")
    print(scores)

    # Row-wise with extra logic: pass/fail based on all subjects >= 60
    raw = make_student_scores()
    raw["All_Pass"] = raw.apply(lambda row: all(row >= 60), axis=1)
    print("\nPass/fail status:")
    print(raw)


# ---------------------------------------------------------------------------
# 5. GroupBy: split-apply-combine
# ---------------------------------------------------------------------------

def demo_groupby_basics() -> None:
    """Basic groupby operations on sales data."""
    print("\n" + "=" * 70)
    print("DEMO: GroupBy Basics")
    print("=" * 70)

    df = make_sales_data(300)
    print(f"\nSales data shape: {df.shape}")

    # --- Single group, single aggregation ---
    region_revenue = df.groupby("region")["revenue"].sum()
    print("\nRevenue by region:")
    print(region_revenue.sort_values(ascending=False))

    # --- Single group, multiple aggregations via agg() ---
    region_stats = df.groupby("region")["revenue"].agg(
        total="sum", avg="mean", max_single="max", min_single="min"
    )
    print("\nRegion revenue statistics (named aggregation):")
    print(region_stats)

    # --- Multiple groups ---
    region_channel = (
        df.groupby(["region", "channel"])["revenue"]
        .sum()
        .reset_index()
    )
    print("\nRevenue by region x channel (first 10):")
    print(region_channel.head(10))

    # --- Grouping by date component ---
    monthly = (
        df.groupby(df["order_date"].dt.month)["revenue"]
        .sum()
        .rename("monthly_revenue")
    )
    print("\nMonthly revenue:")
    print(monthly)


def demo_groupby_advanced() -> None:
    """Advanced groupby: multiple aggregation functions on multiple columns."""
    print("\n" + "=" * 70)
    print("DEMO: Advanced GroupBy Aggregation")
    print("=" * 70)

    df = make_sales_data(500)

    # Different agg functions per column using a dict
    result = df.groupby("region").agg({
        "revenue": ["sum", "mean"],
        "quantity": ["sum", "max", "min"],
        "order_id": "count",
    })
    print("\nMulti-column aggregation (raw MultiIndex columns):")
    print(result)

    # Flatten MultiIndex columns
    result.columns = [
        "total_revenue", "avg_revenue",
        "total_qty", "max_qty", "min_qty",
        "order_count",
    ]
    print("\nFlattened column names:")
    print(result)

    # Custom aggregation with a lambda
    cv = df.groupby("region")["revenue"].agg(
        coefficient_of_variation=lambda x: x.std() / x.mean() * 100
    )
    print("\nRevenue coefficient of variation by region (%):")
    print(cv.round(2))


# ---------------------------------------------------------------------------
# 6. Pivot Tables
# ---------------------------------------------------------------------------

def demo_pivot_table() -> None:
    """Demonstrate pd.pivot_table with various configurations."""
    print("\n" + "=" * 70)
    print("DEMO: Pivot Tables")
    print("=" * 70)

    df = make_sales_data(500)
    df["month"] = df["order_date"].dt.month

    # --- Basic pivot table: region x month -> sum of revenue ---
    pivot1 = pd.pivot_table(
        df,
        index="region",
        columns="month",
        values="revenue",
        aggfunc="sum",
        fill_value=0,
    )
    print("\nPivot table: revenue by region x month (first 6 months):")
    print(pivot1.iloc[:, :6])

    # --- Multiple agg functions ---
    pivot2 = pd.pivot_table(
        df,
        index="region",
        values=["revenue", "quantity"],
        aggfunc={"revenue": "sum", "quantity": "mean"},
    )
    print("\nPivot table: total revenue + avg quantity by region:")
    print(pivot2.round(1))

    # --- Margins (totals row and column) ---
    pivot3 = pd.pivot_table(
        df,
        index="region",
        columns="month",
        values="revenue",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="Total",
    )
    print("\nPivot table with margins (first 4 months + Total):")
    print(pivot3.iloc[:, :5])


def demo_crosstab() -> None:
    """Demonstrate pd.crosstab for frequency and aggregation."""
    print("\n" + "=" * 70)
    print("DEMO: Cross Tabulation")
    print("=" * 70)

    df = make_sales_data(500)
    df["month"] = df["order_date"].dt.month

    # Frequency table: how many orders per region x channel
    ct_freq = pd.crosstab(df["region"], df["channel"])
    print("\nOrder frequency: region x channel:")
    print(ct_freq)

    # Crosstab with aggregation: sum revenue
    ct_rev = pd.crosstab(
        index=df["region"],
        columns=df["channel"],
        values=df["revenue"],
        aggfunc="sum",
    ).fillna(0).astype(int)
    print("\nRevenue crosstab: region x channel:")
    print(ct_rev)

    # Normalized crosstab (proportions)
    ct_norm = pd.crosstab(
        df["region"], df["channel"], normalize="index"
    )
    print("\nNormalized crosstab (row proportions):")
    print(ct_norm.round(3))


# ---------------------------------------------------------------------------
# 7. Enterprise Example: Sales Aggregation Dashboard
# ---------------------------------------------------------------------------

def sales_aggregation_demo() -> None:
    """Simulate building a sales aggregation report."""
    print("\n" + "=" * 70)
    print("ENTERPRISE EXAMPLE: Sales Aggregation Report")
    print("=" * 70)

    df = make_sales_data(1000)
    df["month"] = df["order_date"].dt.to_period("M")

    # KPI 1: Monthly revenue trend
    monthly_trend = (
        df.groupby("month")["revenue"]
        .agg(["sum", "count", "mean"])
        .rename(columns={"sum": "total_revenue", "count": "orders", "mean": "avg_order_value"})
    )
    print("\nMonthly KPI Summary:")
    print(monthly_trend)

    # KPI 2: Region performance with multiple metrics
    region_perf = df.groupby("region").agg(
        revenue=("revenue", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
        avg_order=("revenue", "mean"),
        qty_total=("quantity", "sum"),
    ).sort_values("revenue", ascending=False)
    region_perf["revenue_per_customer"] = (
        region_perf["revenue"] / region_perf["customers"]
    ).round(2)
    print("\nRegion Performance:")
    print(region_perf)

    # KPI 3: Top 5 brand-region combinations
    brand_region = (
        df.groupby(["brand", "region"])["revenue"]
        .sum()
        .reset_index()
        .nlargest(5, "revenue")
    )
    print("\nTop 5 Brand-Region Combinations by Revenue:")
    print(brand_region.to_string(index=False))


# ---------------------------------------------------------------------------
# 8. Enterprise Example: Cohort Analysis
# ---------------------------------------------------------------------------

def cohort_analysis_demo() -> None:
    """Perform a cohort analysis on customer acquisition month vs. retention."""
    print("\n" + "=" * 70)
    print("ENTERPRISE EXAMPLE: Cohort Analysis")
    print("=" * 70)

    df = make_sales_data(2000, seed=99)

    # Assign each customer to their first-purchase cohort month
    df["order_month"] = df["order_date"].dt.to_period("M")
    cohort_map = (
        df.groupby("customer_id")["order_month"]
        .min()
        .rename("cohort")
    )
    df = df.merge(cohort_map, on="customer_id")

    # Compute period_number = months since cohort start
    df["period_number"] = (
        (df["order_month"].astype("int64") - df["cohort"].astype("int64"))
    )

    # Build cohort table: count unique customers
    cohort_table = (
        df.groupby(["cohort", "period_number"])["customer_id"]
        .nunique()
        .reset_index()
        .pivot(index="cohort", columns="period_number", values="customer_id")
        .fillna(0)
        .astype(int)
    )

    # Convert to retention rates
    cohort_sizes = cohort_table.iloc[:, 0]
    retention = cohort_table.divide(cohort_sizes, axis=0).round(3)

    print("\nCohort Retention Table (unique customers, first 6 periods):")
    print(cohort_table.iloc[:, :6])
    print("\nRetention Rates (first 6 periods):")
    print(retention.iloc[:, :6])


# ---------------------------------------------------------------------------
# 9. Enterprise Example: Data Reshaping (Melt, Stack, Unstack)
# ---------------------------------------------------------------------------

def data_reshaping_demo() -> None:
    """Demonstrate melt, stack, unstack, and wide-to-long / long-to-wide."""
    print("\n" + "=" * 70)
    print("ENTERPRISE EXAMPLE: Data Reshaping")
    print("=" * 70)

    scores = make_student_scores()
    scores.index.name = "student"
    print("\nOriginal (wide format):")
    print(scores)

    # --- melt: wide -> long ---
    melted = scores.reset_index().melt(
        id_vars="student",
        value_vars=["Chinese", "Math", "English"],
        var_name="subject",
        value_name="score",
    )
    print("\nMelted (long format):")
    print(melted.head(10))

    # --- pivot: long -> wide ---
    wide_again = melted.pivot(index="student", columns="subject", values="score")
    print("\nPivoted back to wide:")
    print(wide_again)

    # --- stack / unstack ---
    stacked = scores.stack()
    stacked.name = "score"
    print("\nStacked (MultiIndex Series, first 10):")
    print(stacked.head(10))

    unstacked = stacked.unstack(level=-1)
    print("\nUnstacked back to DataFrame:")
    print(unstacked)

    # --- Real-world reshape: region x month revenue matrix ---
    df = make_sales_data(500)
    df["month"] = df["order_date"].dt.strftime("%Y-%m")
    region_month = (
        df.groupby(["region", "month"])["revenue"]
        .sum()
        .unstack(fill_value=0)
    )
    print("\nRegion x Month revenue matrix (first 4 months):")
    print(region_month.iloc[:, :4])


# ---------------------------------------------------------------------------
# 10. Descriptive Statistics and Sorting
# ---------------------------------------------------------------------------

def descriptive_stats_demo() -> None:
    """Demonstrate describe, sort_values, nlargest, nsmallest."""
    print("\n" + "=" * 70)
    print("DEMO: Descriptive Statistics and Sorting")
    print("=" * 70)

    scores = make_student_scores()
    print("\nStudent scores:")
    print(scores)

    # Descriptive statistics per subject
    print("\nDescriptive statistics per subject:")
    print(scores.describe().round(2))

    # Mean by student (row-wise)
    print("\nMean score per student:")
    print(scores.mean(axis=1).round(2))

    # Variance by subject
    print("\nScore variance by subject:")
    print(scores.var().round(2))

    # Sort by Math descending
    sorted_df = scores.sort_values(by="Math", ascending=False)
    print("\nSorted by Math (descending):")
    print(sorted_df)

    # Top 3 by Chinese
    print("\nTop 3 by Chinese:")
    print(scores.nlargest(3, "Chinese"))

    # Bottom 2 by English
    print("\nBottom 2 by English:")
    print(scores.nsmallest(2, "English"))


# ---------------------------------------------------------------------------
# 11. Combining Techniques: Full Pipeline
# ---------------------------------------------------------------------------

def full_pipeline_demo() -> None:
    """End-to-end pipeline: generate data -> transform -> aggregate -> present."""
    print("\n" + "=" * 70)
    print("FULL PIPELINE: Data -> Transform -> Aggregate -> Present")
    print("=" * 70)

    df = make_sales_data(800, seed=7)

    # Step 1: Feature engineering with map / apply
    df["price_tier"] = df["unit_price"].map(
        lambda p: "Budget" if p < 150 else ("Standard" if p < 300 else "Premium")
    )
    df["month"] = df["order_date"].dt.month
    df["quarter"] = df["order_date"].dt.quarter

    # Step 2: GroupBy with multiple aggregations
    summary = df.groupby(["region", "quarter"]).agg(
        total_revenue=("revenue", "sum"),
        order_count=("order_id", "count"),
        avg_order=("revenue", "mean"),
        unique_customers=("customer_id", "nunique"),
    ).reset_index()
    summary["revenue_per_order"] = (summary["total_revenue"] / summary["order_count"]).round(2)

    print("\nRegion x Quarter summary:")
    print(summary.head(12))

    # Step 3: Pivot table for cross-tabulation view
    pivot = pd.pivot_table(
        summary,
        index="region",
        columns="quarter",
        values="total_revenue",
        aggfunc="sum",
        fill_value=0,
    )
    pivot.columns = [f"Q{q}" for q in pivot.columns]
    print("\nRegion quarterly revenue pivot:")
    print(pivot)

    # Step 4: Apply row-wise for growth rate (Q2 vs Q1)
    if "Q1" in pivot.columns and "Q2" in pivot.columns:
        pivot["QoQ_Growth_%"] = (
            (pivot["Q2"] - pivot["Q1"]) / pivot["Q1"] * 100
        ).round(2)
        print("\nWith Q1->Q2 growth rate:")
        print(pivot)

    # Step 5: Rank regions
    pivot["Revenue_Rank"] = pivot.iloc[:, :4].sum(axis=1).rank(ascending=False).astype(int)
    print("\nFinal table with revenue rank:")
    print(pivot)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all demonstrations."""
    print("=" * 70)
    print("Day 75: pandas Transform, GroupBy, Aggregation & Pivot Tables")
    print("=" * 70)
    print(f"pandas version: {pd.__version__}")
    print(f"numpy version:  {np.__version__}")

    # Descriptive statistics
    descriptive_stats_demo()

    # Element-wise transforms
    demo_map()
    demo_applymap()
    demo_apply()

    # GroupBy
    demo_groupby_basics()
    demo_groupby_advanced()

    # Pivot tables and crosstabs
    demo_pivot_table()
    demo_crosstab()

    # Enterprise examples
    sales_aggregation_demo()
    cohort_analysis_demo()
    data_reshaping_demo()

    # Full pipeline
    full_pipeline_demo()

    print("\n" + "=" * 70)
    print("All demonstrations completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
