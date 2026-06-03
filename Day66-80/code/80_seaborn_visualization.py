"""
Day 80 - Seaborn Statistical Visualization
===========================================
Comprehensive guide to Seaborn for statistical data visualization.

Covers:
    - Seaborn basics and theme configuration
    - Distribution plots (histplot, kdeplot, ecdfplot)
    - Relational plots (scatterplot, lineplot, jointplot)
    - Categorical plots (boxplot, violinplot, swarmplot, barplot, countplot)
    - Regression plots (lmplot, regplot)
    - Heatmaps and correlation matrices
    - Pair plots for multivariate exploration
    - FacetGrid for small multiples

Enterprise Examples:
    - Correlation analysis for financial metrics
    - A/B test result visualization
    - Customer segmentation analysis

Requirements:
    pip install seaborn pandas numpy matplotlib scipy
"""

from __future__ import annotations

import warnings
from typing import Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from numpy.typing import NDArray

# Suppress FutureWarnings from seaborn/pandas for cleaner output
warnings.filterwarnings("ignore", category=FutureWarning)


# ---------------------------------------------------------------------------
# 1. Theme & Style Configuration
# ---------------------------------------------------------------------------

def configure_seaborn_theme(
    style: str = "whitegrid",
    palette: str = "deep",
    font_scale: float = 1.1,
    context: str = "notebook",
    use_chinese: bool = False,
) -> None:
    """Configure Seaborn theme and optional Chinese font support.

    Args:
        style: One of 'darkgrid', 'whitegrid', 'dark', 'white', 'ticks'.
        palette: Any valid Seaborn palette name (e.g. 'deep', 'muted', 'Dark2').
        font_scale: Scaling factor for font elements.
        context: One of 'paper', 'notebook', 'talk', 'poster'.
        use_chinese: If True, insert SimHei into matplotlib font list.
    """
    sns.set_theme(style=style, palette=palette, font_scale=font_scale, context=context)

    if use_chinese:
        # Must be called AFTER set_theme to avoid being overwritten
        if "SimHei" not in plt.rcParams["font.sans-serif"]:
            plt.rcParams["font.sans-serif"].insert(0, "SimHei")
        plt.rcParams["axes.unicode_minus"] = False

    print(f"[Theme] style={style}, palette={palette}, context={context}, font_scale={font_scale}")


# ---------------------------------------------------------------------------
# 2. Distribution Plots
# ---------------------------------------------------------------------------

def plot_distribution_analysis(data: pd.DataFrame, column: str) -> plt.Figure:
    """Plot histogram with KDE, standalone KDE, and ECDF for a single variable.

    Args:
        data: DataFrame containing the data.
        column: Column name to visualize.

    Returns:
        matplotlib Figure with three subplots.
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle(f"Distribution Analysis: {column}", fontsize=16, fontweight="bold")

    # Histogram + KDE
    sns.histplot(data=data, x=column, kde=True, color="steelblue", ax=axes[0])
    axes[0].set_title("Histogram + KDE")

    # KDE only (filled)
    sns.kdeplot(data=data, x=column, fill=True, color="coral", ax=axes[1])
    axes[1].set_title("Kernel Density Estimate")

    # ECDF (Empirical Cumulative Distribution Function)
    sns.ecdfplot(data=data, x=column, color="seagreen", ax=axes[2])
    axes[2].set_title("Empirical CDF")

    plt.tight_layout()
    return fig


def plot_bivariate_distribution(
    data: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
) -> plt.Figure:
    """Plot joint distribution with marginal histograms/scatter/regression.

    Args:
        data: DataFrame.
        x: Column for x-axis.
        y: Column for y-axis.
        hue: Optional categorical column for color grouping.

    Returns:
        JointGrid figure.
    """
    g = sns.jointplot(
        data=data, x=x, y=y, hue=hue,
        kind="scatter", height=8, ratio=4,
        marginal_kws=dict(fill=True),
    )
    g.figure.suptitle(f"Joint Distribution: {x} vs {y}", y=1.02, fontsize=14)
    return g.figure


# ---------------------------------------------------------------------------
# 3. Pair Plots (Multivariate Exploration)
# ---------------------------------------------------------------------------

def plot_pairwise_relationships(
    data: pd.DataFrame,
    hue: Optional[str] = None,
    vars_list: Optional[Sequence[str]] = None,
    palette: str = "Dark2",
    diag_kind: str = "kde",
) -> plt.Figure:
    """Create a pair plot to explore pairwise relationships among numeric columns.

    Args:
        data: DataFrame.
        hue: Categorical column for color encoding.
        vars_list: Subset of columns to include (default: all numeric).
        palette: Color palette name.
        diag_kind: 'hist' or 'kde' for diagonal plots.

    Returns:
        PairGrid figure.
    """
    g = sns.pairplot(
        data=data,
        hue=hue,
        vars=vars_list,
        palette=palette,
        diag_kind=diag_kind,
        plot_kws={"alpha": 0.6, "s": 40, "edgecolor": "white", "linewidth": 0.5},
        diag_kws={"fill": True, "alpha": 0.5},
    )
    g.figure.suptitle("Pairwise Relationships", y=1.02, fontsize=14)
    return g.figure


# ---------------------------------------------------------------------------
# 4. Heatmaps
# ---------------------------------------------------------------------------

def plot_correlation_heatmap(
    data: pd.DataFrame,
    columns: Optional[Sequence[str]] = None,
    method: str = "pearson",
    annot: bool = True,
    fmt: str = ".2f",
    cmap: str = "RdBu_r",
    figsize: tuple[int, int] = (10, 8),
) -> plt.Figure:
    """Plot a correlation heatmap for selected (or all) numeric columns.

    Args:
        data: DataFrame.
        columns: Subset of numeric columns (default: all numeric).
        method: Correlation method - 'pearson', 'spearman', or 'kendall'.
        annot: Whether to annotate cells with values.
        fmt: Format string for annotations.
        cmap: Colormap name.
        figsize: Figure size.

    Returns:
        matplotlib Figure.
    """
    if columns is not None:
        numeric_data = data[columns].select_dtypes(include="number")
    else:
        numeric_data = data.select_dtypes(include="number")

    corr = numeric_data.corr(method=method)

    fig, ax = plt.subplots(figsize=figsize)
    mask = np.triu(np.ones_like(corr, dtype=bool))  # mask upper triangle

    sns.heatmap(
        corr,
        mask=mask,
        annot=annot,
        fmt=fmt,
        cmap=cmap,
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8, "label": "Correlation Coefficient"},
        ax=ax,
    )
    ax.set_title(f"Correlation Heatmap ({method.title()})", fontsize=14, fontweight="bold")
    plt.tight_layout()
    return fig


def plot_pivot_heatmap(
    data: pd.DataFrame,
    index: str,
    columns: str,
    values: str,
    aggfunc: str = "mean",
    cmap: str = "YlOrRd",
    figsize: tuple[int, int] = (10, 6),
) -> plt.Figure:
    """Plot a heatmap from a pivoted DataFrame (e.g. average metric by two categories).

    Args:
        data: DataFrame.
        index: Column for rows.
        columns: Column for columns.
        values: Column whose values fill the cells.
        aggfunc: Aggregation function name ('mean', 'sum', 'count', etc.).
        cmap: Colormap.
        figsize: Figure size.

    Returns:
        matplotlib Figure.
    """
    pivot = pd.pivot_table(data, values=values, index=index, columns=columns, aggfunc=aggfunc)

    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".1f",
        cmap=cmap,
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title(f"{aggfunc.title()} of {values} by {index} and {columns}", fontsize=13)
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 5. Categorical Plots
# ---------------------------------------------------------------------------

def plot_categorical_comparison(
    data: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
) -> plt.Figure:
    """Generate a 2x2 grid of categorical plots: box, violin, swarm, and bar.

    Args:
        data: DataFrame.
        x: Categorical column for x-axis.
        y: Numeric column for y-axis.
        hue: Optional second categorical column.

    Returns:
        matplotlib Figure.
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f"Categorical Comparison: {y} by {x}", fontsize=16, fontweight="bold")

    # Box plot - shows quartiles and outliers
    sns.boxplot(data=data, x=x, y=y, hue=hue, ax=axes[0, 0], palette="Set2")
    axes[0, 0].set_title("Box Plot")

    # Violin plot - shows full distribution shape
    sns.violinplot(data=data, x=x, y=y, hue=hue, ax=axes[0, 1], palette="Set2", inner="quartile")
    axes[0, 1].set_title("Violin Plot")

    # Swarm plot - shows individual data points
    sns.swarmplot(data=data, x=x, y=y, hue=hue, ax=axes[1, 0], palette="Set2", size=4, alpha=0.7)
    axes[1, 0].set_title("Swarm Plot")

    # Bar plot - shows mean with confidence interval
    sns.barplot(data=data, x=x, y=y, hue=hue, ax=axes[1, 1], palette="Set2", errorbar="sd")
    axes[1, 1].set_title("Bar Plot (Mean +/- SD)")

    plt.tight_layout()
    return fig


def plot_count_categories(
    data: pd.DataFrame,
    x: str,
    hue: Optional[str] = None,
) -> plt.Figure:
    """Plot count of observations per category.

    Args:
        data: DataFrame.
        x: Categorical column.
        hue: Optional grouping column.

    Returns:
        matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.countplot(data=data, x=x, hue=hue, palette="pastel", ax=ax, edgecolor="black")
    ax.set_title(f"Count of Observations by {x}", fontsize=14, fontweight="bold")
    ax.set_xlabel(x)
    ax.set_ylabel("Count")
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 6. Regression Plots
# ---------------------------------------------------------------------------

def plot_linear_regression(
    data: pd.DataFrame,
    x: str,
    y: str,
    hue: Optional[str] = None,
) -> plt.Figure:
    """Plot linear regression with optional grouping via hue.

    Args:
        data: DataFrame.
        x: Independent variable.
        y: Dependent variable.
        hue: Optional categorical grouping.

    Returns:
        FacetGrid figure.
    """
    g = sns.lmplot(
        data=data, x=x, y=y, hue=hue,
        height=6, aspect=1.3,
        scatter_kws={"alpha": 0.6, "s": 40},
        line_kws={"linewidth": 2},
    )
    g.figure.suptitle(f"Linear Regression: {y} ~ {x}", y=1.02, fontsize=14)
    return g.figure


# ---------------------------------------------------------------------------
# 7. Enterprise Example: Correlation Analysis for Financial Metrics
# ---------------------------------------------------------------------------

def generate_financial_data(n_samples: int = 500, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic financial metrics dataset.

    Columns:
        revenue, cost, profit, marketing_spend, customer_count,
        avg_order_value, churn_rate, nps_score

    Args:
        n_samples: Number of data points.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with correlated financial metrics.
    """
    rng = np.random.default_rng(seed)

    marketing_spend = rng.normal(50, 15, n_samples).clip(5, 120)
    customer_count = (marketing_spend * rng.normal(10, 2, n_samples) + rng.normal(200, 50, n_samples)).clip(50, 2000)
    avg_order_value = rng.normal(75, 20, n_samples).clip(15, 200)
    revenue = customer_count * avg_order_value / 100 + rng.normal(0, 10, n_samples)
    cost = revenue * rng.uniform(0.4, 0.7, n_samples)
    profit = revenue - cost
    churn_rate = (rng.normal(0.05, 0.02, n_samples) - marketing_spend * 0.0002).clip(0.01, 0.15)
    nps_score = (rng.normal(40, 15, n_samples) + marketing_spend * 0.1 - churn_rate * 200).clip(-100, 100)

    df = pd.DataFrame({
        "revenue": np.round(revenue, 2),
        "cost": np.round(cost, 2),
        "profit": np.round(profit, 2),
        "marketing_spend": np.round(marketing_spend, 2),
        "customer_count": np.round(customer_count, 0).astype(int),
        "avg_order_value": np.round(avg_order_value, 2),
        "churn_rate": np.round(churn_rate, 4),
        "nps_score": np.round(nps_score, 1),
    })
    return df


def run_correlation_analysis(data: pd.DataFrame) -> plt.Figure:
    """Full correlation analysis with heatmap, pair plot excerpt, and regression.

    Args:
        data: Financial metrics DataFrame.

    Returns:
        matplotlib Figure (correlation heatmap).
    """
    fig = plot_correlation_heatmap(
        data,
        cmap="coolwarm",
        figsize=(10, 8),
    )
    return fig


# ---------------------------------------------------------------------------
# 8. Enterprise Example: A/B Test Visualization
# ---------------------------------------------------------------------------

def generate_ab_test_data(
    n_control: int = 2000,
    n_treatment: int = 2000,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic A/B test data for an e-commerce conversion experiment.

    Columns:
        group: 'Control' or 'Treatment'
        session_duration: Minutes spent on site
        pages_viewed: Number of pages viewed
        converted: 1 if purchased, 0 otherwise
        revenue: Purchase amount (0 if not converted)

    Args:
        n_control: Sample size for control group.
        n_treatment: Sample size for treatment group.
        seed: Random seed.

    Returns:
        DataFrame with A/B test results.
    """
    rng = np.random.default_rng(seed)

    def _generate_group(n: int, conv_rate: float, rev_mean: float, rev_std: float) -> pd.DataFrame:
        duration = rng.gamma(shape=3, scale=4, size=n)
        pages = rng.poisson(lam=5, size=n) + 1
        converted = rng.binomial(1, conv_rate, n)
        revenue = np.where(converted, rng.normal(rev_mean, rev_std, n).clip(5, 500), 0.0)
        return pd.DataFrame({
            "session_duration": np.round(duration, 1),
            "pages_viewed": pages,
            "converted": converted,
            "revenue": np.round(revenue, 2),
        })

    control = _generate_group(n_control, conv_rate=0.08, rev_mean=45, rev_std=20)
    control["group"] = "Control"

    treatment = _generate_group(n_treatment, conv_rate=0.12, rev_mean=52, rev_std=22)
    treatment["group"] = "Treatment"

    return pd.concat([control, treatment], ignore_index=True)


def visualize_ab_test(data: pd.DataFrame) -> plt.Figure:
    """Create a multi-panel visualization of A/B test results.

    Panels:
        1. Conversion rate bar chart with 95% CI
        2. Revenue distribution for converters (violin + strip)
        3. Session duration by group (box plot)
        4. Pages viewed by group (box plot)

    Args:
        data: A/B test DataFrame.

    Returns:
        matplotlib Figure with 4 subplots.
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("A/B Test Results Dashboard", fontsize=18, fontweight="bold", y=1.01)

    colors = {"Control": "#4C72B0", "Treatment": "#DD8452"}

    # 1. Conversion Rate
    conv_rates = data.groupby("group")["converted"].agg(["mean", "count"])
    conv_rates["se"] = np.sqrt(conv_rates["mean"] * (1 - conv_rates["mean"]) / conv_rates["count"])
    conv_rates["ci95"] = 1.96 * conv_rates["se"]
    conv_rates = conv_rates.reset_index()

    bars = axes[0, 0].bar(
        conv_rates["group"], conv_rates["mean"],
        yerr=conv_rates["ci95"],
        color=[colors[g] for g in conv_rates["group"]],
        edgecolor="black", capsize=8, width=0.5,
    )
    for bar, rate in zip(bars, conv_rates["mean"]):
        axes[0, 0].text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
            f"{rate:.2%}", ha="center", fontsize=13, fontweight="bold",
        )
    axes[0, 0].set_title("Conversion Rate (95% CI)", fontsize=13)
    axes[0, 0].set_ylabel("Conversion Rate")
    axes[0, 0].set_ylim(0, conv_rates["mean"].max() * 1.4)

    # 2. Revenue Distribution (converters only)
    converters = data[data["converted"] == 1]
    sns.violinplot(
        data=converters, x="group", y="revenue",
        palette=colors, ax=axes[0, 1], inner="quartile", cut=0,
    )
    sns.stripplot(
        data=converters, x="group", y="revenue",
        color="black", alpha=0.15, size=3, ax=axes[0, 1],
    )
    axes[0, 1].set_title("Revenue Distribution (Converters)", fontsize=13)
    axes[0, 1].set_ylabel("Revenue ($)")

    # 3. Session Duration
    sns.boxplot(
        data=data, x="group", y="session_duration",
        palette=colors, ax=axes[1, 0], width=0.5,
    )
    axes[1, 0].set_title("Session Duration by Group", fontsize=13)
    axes[1, 0].set_ylabel("Minutes")

    # 4. Pages Viewed
    sns.boxplot(
        data=data, x="group", y="pages_viewed",
        palette=colors, ax=axes[1, 1], width=0.5,
    )
    axes[1, 1].set_title("Pages Viewed by Group", fontsize=13)
    axes[1, 1].set_ylabel("Pages")

    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 9. Enterprise Example: Customer Segmentation Plots
# ---------------------------------------------------------------------------

def generate_customer_segmentation_data(
    n_customers: int = 800,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic customer data with latent segments.

    Columns:
        annual_spend: Total annual spending ($)
        frequency: Number of purchases per year
        recency: Days since last purchase
        avg_order_value: Average order value ($)
        tenure_months: How long the customer has been with the company
        segment: Ground-truth label ('Champions', 'Loyal', 'At Risk', 'Lost')

    Args:
        n_customers: Number of customers.
        seed: Random seed.

    Returns:
        DataFrame with customer features and segment labels.
    """
    rng = np.random.default_rng(seed)

    segments = {
        "Champions": {"n": 150, "spend": (3000, 800), "freq": (25, 5), "rec": (10, 5), "aov": (120, 30), "ten": (36, 12)},
        "Loyal":     {"n": 250, "spend": (1500, 400), "freq": (15, 4), "rec": (30, 15), "aov": (90, 20),  "ten": (24, 10)},
        "At Risk":   {"n": 200, "spend": (600, 300),  "freq": (6, 3),  "rec": (90, 30), "aov": (65, 20),  "ten": (18, 8)},
        "Lost":      {"n": 200, "spend": (150, 100),  "freq": (2, 1),  "rec": (200, 60),"aov": (40, 15),  "ten": (8, 4)},
    }

    frames: list[pd.DataFrame] = []
    for seg_name, params in segments.items():
        df_seg = pd.DataFrame({
            "annual_spend": rng.normal(params["spend"][0], params["spend"][1], params["n"]).clip(10, 8000),
            "frequency": rng.normal(params["freq"][0], params["freq"][1], params["n"]).clip(1, 50).astype(int),
            "recency": rng.normal(params["rec"][0], params["rec"][1], params["n"]).clip(1, 365).astype(int),
            "avg_order_value": rng.normal(params["aov"][0], params["aov"][1], params["n"]).clip(5, 300),
            "tenure_months": rng.normal(params["ten"][0], params["ten"][1], params["n"]).clip(1, 72).astype(int),
            "segment": seg_name,
        })
        frames.append(df_seg)

    return pd.concat(frames, ignore_index=True).sample(frac=1, random_state=seed).reset_index(drop=True)


def visualize_customer_segments(data: pd.DataFrame) -> plt.Figure:
    """Multi-panel visualization of customer segments.

    Panels:
        1. Scatter: annual_spend vs frequency, colored by segment
        2. Box plot: recency distribution per segment
        3. Heatmap: mean metrics per segment
        4. Scatter: avg_order_value vs annual_spend

    Args:
        data: Customer segmentation DataFrame.

    Returns:
        matplotlib Figure.
    """
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle("Customer Segmentation Analysis", fontsize=18, fontweight="bold", y=1.01)

    palette = sns.color_palette("Set2", n_colors=data["segment"].nunique())
    segment_order = ["Champions", "Loyal", "At Risk", "Lost"]

    # 1. Scatter: Spend vs Frequency
    sns.scatterplot(
        data=data, x="annual_spend", y="frequency", hue="segment",
        hue_order=segment_order, palette=palette,
        alpha=0.7, s=50, edgecolor="white", linewidth=0.3, ax=axes[0, 0],
    )
    axes[0, 0].set_title("Annual Spend vs Purchase Frequency", fontsize=13)
    axes[0, 0].set_xlabel("Annual Spend ($)")
    axes[0, 0].set_ylabel("Purchases / Year")
    axes[0, 0].legend(title="Segment", fontsize=9)

    # 2. Box plot: Recency
    sns.boxplot(
        data=data, x="segment", y="recency",
        order=segment_order, palette=palette, ax=axes[0, 1], width=0.6,
    )
    axes[0, 1].set_title("Recency by Segment", fontsize=13)
    axes[0, 1].set_xlabel("Segment")
    axes[0, 1].set_ylabel("Days Since Last Purchase")

    # 3. Heatmap: Mean metrics per segment
    numeric_cols = ["annual_spend", "frequency", "recency", "avg_order_value", "tenure_months"]
    segment_means = data.groupby("segment")[numeric_cols].mean().reindex(segment_order)

    # Normalize each column to [0, 1] for visual comparison
    normalized = (segment_means - segment_means.min()) / (segment_means.max() - segment_means.min())
    sns.heatmap(
        normalized, annot=segment_means.round(1), fmt="",
        cmap="YlGnBu", linewidths=1, ax=axes[1, 0],
        cbar_kws={"label": "Normalized Scale (0-1)"},
    )
    axes[1, 0].set_title("Segment Metrics (values = raw means)", fontsize=13)
    axes[1, 0].set_ylabel("")

    # 4. Scatter: Avg Order Value vs Annual Spend
    sns.scatterplot(
        data=data, x="avg_order_value", y="annual_spend", hue="segment",
        hue_order=segment_order, palette=palette,
        alpha=0.6, s=40, edgecolor="white", linewidth=0.3, ax=axes[1, 1],
    )
    axes[1, 1].set_title("Avg Order Value vs Annual Spend", fontsize=13)
    axes[1, 1].set_xlabel("Avg Order Value ($)")
    axes[1, 1].set_ylabel("Annual Spend ($)")
    axes[1, 1].legend(title="Segment", fontsize=9)

    plt.tight_layout()
    return fig


def plot_segment_pairplot(data: pd.DataFrame) -> plt.Figure:
    """Pair plot of numeric features colored by customer segment.

    Args:
        data: Customer segmentation DataFrame.

    Returns:
        PairGrid figure.
    """
    segment_order = ["Champions", "Loyal", "At Risk", "Lost"]
    g = sns.pairplot(
        data=data,
        vars=["annual_spend", "frequency", "recency", "avg_order_value"],
        hue="segment",
        hue_order=segment_order,
        palette="Set2",
        diag_kind="kde",
        plot_kws={"alpha": 0.5, "s": 25, "edgecolor": "white", "linewidth": 0.3},
        diag_kws={"fill": True, "alpha": 0.4},
        height=2.5,
    )
    g.figure.suptitle("Customer Segments - Pair Plot", y=1.02, fontsize=16)
    return g.figure


# ---------------------------------------------------------------------------
# 10. Seaborn Built-in Dataset Demos
# ---------------------------------------------------------------------------

def demo_with_builtin_datasets() -> None:
    """Run a series of plots using Seaborn's built-in datasets for quick exploration."""
    print("=" * 60)
    print("Seaborn Built-in Dataset Demonstrations")
    print("=" * 60)

    # Load the tips dataset
    tips = sns.load_dataset("tips")
    print(f"\n[Tips Dataset] shape={tips.shape}")
    print(tips.describe())

    # 1. Distribution of total bill
    fig1 = plot_distribution_analysis(tips, "total_bill")
    fig1.suptitle("Tips Dataset: Total Bill Distribution", fontsize=14)

    # 2. Pair plot with gender hue
    fig2 = plot_pairwise_relationships(tips, hue="sex", palette="Dark2")

    # 3. Categorical comparison: total_bill by day
    fig3 = plot_categorical_comparison(tips, x="day", y="total_bill")
    fig3.suptitle("Tips Dataset: Total Bill by Day", fontsize=14)

    # 4. Regression: tip ~ total_bill
    fig4 = plot_linear_regression(tips, x="total_bill", y="tip", hue="sex")

    # 5. Heatmap: pivot of average total_bill by day and time
    fig5 = plot_pivot_heatmap(tips, index="day", columns="time", values="total_bill", aggfunc="mean")

    plt.show()
    print("\n[Demo] All built-in dataset plots displayed.")


# ---------------------------------------------------------------------------
# 11. Enterprise Example Runner
# ---------------------------------------------------------------------------

def run_enterprise_examples() -> None:
    """Run all enterprise examples: correlation, A/B test, segmentation."""
    print("=" * 60)
    print("Enterprise Visualization Examples")
    print("=" * 60)

    # --- Correlation Analysis ---
    print("\n[1/3] Financial Correlation Analysis")
    fin_data = generate_financial_data(n_samples=600)
    print(fin_data.describe().round(2))
    fig_corr = run_correlation_analysis(fin_data)

    # Additional: pair plot of key financial metrics
    fig_fin_pair = plot_pairwise_relationships(
        fin_data,
        vars_list=["revenue", "profit", "marketing_spend", "customer_count"],
        palette="coolwarm",
    )
    fig_fin_pair.suptitle("Financial Metrics Pair Plot", y=1.02, fontsize=14)

    # --- A/B Test Visualization ---
    print("\n[2/3] A/B Test Results")
    ab_data = generate_ab_test_data(n_control=2500, n_treatment=2500)
    print(ab_data.groupby("group")[["converted", "revenue", "session_duration"]].mean().round(3))
    fig_ab = visualize_ab_test(ab_data)

    # --- Customer Segmentation ---
    print("\n[3/3] Customer Segmentation")
    cust_data = generate_customer_segmentation_data(n_customers=1000)
    print(cust_data.groupby("segment")[["annual_spend", "frequency", "recency"]].mean().round(1))
    fig_seg = visualize_customer_segments(cust_data)
    fig_seg_pair = plot_segment_pairplot(cust_data)

    plt.show()
    print("\nEnterprise examples complete.")


# ---------------------------------------------------------------------------
# 12. Utility: Seaborn Palette Preview
# ---------------------------------------------------------------------------

def preview_palettes(
    palette_names: Optional[Sequence[str]] = None,
    n_colors: int = 10,
) -> plt.Figure:
    """Visualize a set of Seaborn color palettes.

    Args:
        palette_names: List of palette names to preview.
        n_colors: Number of discrete colors to show per palette.

    Returns:
        matplotlib Figure.
    """
    if palette_names is None:
        palette_names = [
            "deep", "muted", "pastel", "bright", "dark", "colorblind",
            "Set1", "Set2", "Set3", "Paired",
            "coolwarm", "RdBu_r", "viridis", "magma", "Dark2",
        ]

    fig, ax = plt.subplots(figsize=(14, len(palette_names) * 0.6))
    for i, name in enumerate(palette_names):
        try:
            colors = sns.color_palette(name, n_colors)
        except ValueError:
            colors = sns.color_palette(name, as_cmap=False) if name in sns.color_palette() else [(0.5, 0.5, 0.5)] * n_colors
        ax.barh(
            y=[i] * n_colors, width=[1] * n_colors, left=range(n_colors),
            color=colors, height=0.8, edgecolor="white", linewidth=0.5,
        )
        ax.text(-0.3, i, name, va="center", ha="right", fontsize=10, fontweight="bold")

    ax.set_xlim(-3, n_colors)
    ax.set_ylim(-0.5, len(palette_names) - 0.5)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Seaborn Color Palettes Preview", fontsize=14, fontweight="bold")
    sns.despine(left=True, bottom=True)
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    """Main entry point - runs all demonstrations and enterprise examples."""
    # Configure theme
    configure_seaborn_theme(style="whitegrid", palette="deep", context="notebook", font_scale=1.1)

    # Palette preview
    print("Previewing color palettes...")
    fig_palettes = preview_palettes()
    plt.show()

    # Built-in dataset demos
    demo_with_builtin_datasets()

    # Enterprise examples
    run_enterprise_examples()


if __name__ == "__main__":
    main()
