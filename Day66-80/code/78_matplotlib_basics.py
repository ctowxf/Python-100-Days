"""
Day 78 - Data Visualization with Matplotlib
============================================
Comprehensive demonstrations of matplotlib for data visualization:
  - Line plots (trend analysis)
  - Bar charts (grouped, stacked, horizontal)
  - Scatter plots (correlation analysis)
  - Histograms (distribution and cumulative)
  - Subplots (multi-panel layouts)
  - Pie charts (composition)
  - Box plots (outlier detection)
  - Enterprise examples (sales trends, KPI dashboard, report figures)

C++ Comparison Note:
  In C/C++, producing charts typically requires external libraries such as
  gnuplot (via pipe or C API), Qt Charts (QChartView), or matplotlib-cpp.
  Matplotlib provides a Pythonic, declarative API that replaces hundreds of
  lines of C++ boilerplate with a few concise calls. For batch/server-side
  rendering, matplotlib's Agg backend generates PNG/SVG without a display,
  similar to gnuplot's "set terminal png" but with full programmatic control.

Requirements:
    pip install matplotlib numpy
"""

from __future__ import annotations

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Sequence

# ---------------------------------------------------------------------------
# Global configuration: Chinese font support and minus-sign rendering
# ---------------------------------------------------------------------------
# Matplotlib vs C++ gnuplot/Qt:
#   In gnuplot you would write:  set xlabel "身高" font "SimHei,12"
#   In Qt Charts you would call: axisX->setTitleFont(QFont("SimHei", 12))
#   In matplotlib a single rcParams tweak applies globally.
def configure_matplotlib(font_name: str = "SimHei") -> None:
    """Configure matplotlib for Chinese text rendering and style defaults.

    Args:
        font_name: Name of a CJK-capable font installed on the system.
    """
    if font_name not in matplotlib.font_manager.get_font_names():
        # Fallback: try common alternatives
        for fallback in ["Microsoft YaHei", "WenQuanYi Micro Hei", "Noto Sans CJK SC"]:
            if fallback in matplotlib.font_manager.get_font_names():
                font_name = fallback
                break
    plt.rcParams["font.sans-serif"].insert(0, font_name)
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 120
    plt.rcParams["savefig.dpi"] = 150
    plt.rcParams["figure.facecolor"] = "white"


# ===================================================================
# 1. LINE PLOTS - trend analysis over time
# ===================================================================

def demo_line_plot_basic() -> None:
    """Draw a sine curve with star markers (mirrors document example)."""
    x: np.ndarray = np.linspace(-2 * np.pi, 2 * np.pi, 120)
    y: np.ndarray = np.sin(x)

    plt.figure(figsize=(8, 4))
    plt.plot(x, y, linewidth=2, marker="*", color="red", markersize=4)
    plt.title("Basic Line Plot: sin(x)")
    plt.xlabel("x")
    plt.ylabel("sin(x)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("line_basic.png")
    plt.show()


def demo_line_plot_dual() -> None:
    """Plot sine and cosine on the same axes with annotations."""
    x: np.ndarray = np.linspace(-2 * np.pi, 2 * np.pi, 120)
    y1: np.ndarray = np.sin(x)
    y2: np.ndarray = np.cos(x)

    plt.figure(figsize=(8, 4))
    plt.plot(x, y1, linewidth=2, marker="*", color="red", label="sin(x)")
    plt.plot(x, y2, linewidth=2, marker="^", color="blue", label="cos(x)")

    plt.annotate(
        "sin(x)",
        xytext=(0.5, -0.75),
        xy=(0, -0.25),
        fontsize=12,
        arrowprops={"arrowstyle": "->", "color": "darkgreen",
                     "connectionstyle": "angle3, angleA=90, angleB=0"},
    )
    plt.annotate(
        "cos(x)",
        xytext=(-3, 0.75),
        xy=(-1.25, 0.5),
        fontsize=12,
        arrowprops={"arrowstyle": "->", "color": "darkgreen",
                     "connectionstyle": "arc3, rad=0.35"},
    )

    plt.title("Sine and Cosine Curves")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("line_dual.png")
    plt.show()


# ===================================================================
# 2. BAR CHARTS - comparing categorical data
# ===================================================================

def demo_bar_grouped() -> None:
    """Grouped bar chart comparing two sales teams across quarters."""
    x: np.ndarray = np.arange(4)
    y1: np.ndarray = np.array([35, 48, 22, 40])
    y2: np.ndarray = np.array([28, 55, 33, 47])

    plt.figure(figsize=(7, 4))
    plt.bar(x - 0.15, y1, width=0.3, label="Team A", color="steelblue")
    plt.bar(x + 0.15, y2, width=0.3, label="Team B", color="coral")
    plt.xticks(x, labels=["Q1", "Q2", "Q3", "Q4"])
    plt.ylabel("Sales (10k units)")
    plt.title("Quarterly Sales: Team A vs Team B")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig("bar_grouped.png")
    plt.show()


def demo_bar_stacked() -> None:
    """Stacked bar chart showing cumulative quarterly performance."""
    labels: list[str] = ["Q1", "Q2", "Q3", "Q4"]
    y1: np.ndarray = np.array([35, 48, 22, 40])
    y2: np.ndarray = np.array([28, 55, 33, 47])

    plt.figure(figsize=(7, 4))
    plt.bar(labels, y1, width=0.4, label="Team A", color="steelblue")
    plt.bar(labels, y2, width=0.4, bottom=y1, label="Team B", color="coral")
    plt.ylabel("Sales (10k units)")
    plt.title("Stacked Quarterly Sales")
    plt.legend(loc="lower right")
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig("bar_stacked.png")
    plt.show()


def demo_bar_horizontal() -> None:
    """Horizontal bar chart (useful for long category labels)."""
    categories: list[str] = ["Electronics", "Clothing", "Groceries", "Furniture", "Books"]
    values: np.ndarray = np.array([420, 310, 280, 190, 150])

    plt.figure(figsize=(7, 4))
    colors: list[str] = ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974"]
    plt.barh(categories, values, color=colors)
    plt.xlabel("Revenue (10k)")
    plt.title("Revenue by Product Category")
    plt.grid(axis="x", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig("bar_horizontal.png")
    plt.show()


# ===================================================================
# 3. SCATTER PLOTS - correlation analysis
# ===================================================================

def demo_scatter_basic() -> None:
    """Scatter plot: income vs online shopping expenditure."""
    income: np.ndarray = np.array([5550, 7500, 10500, 15000, 20000, 25000, 30000, 40000])
    spending: np.ndarray = np.array([800, 1800, 1250, 2000, 1800, 2100, 2500, 3500])

    plt.figure(figsize=(7, 4))
    plt.scatter(income, spending, s=80, c="darkcyan", edgecolors="black", alpha=0.8)
    plt.xlabel("Monthly Income (CNY)")
    plt.ylabel("Online Shopping Spending (CNY)")
    plt.title("Income vs Online Shopping Expenditure")

    # Add trend line
    z: np.ndarray = np.polyfit(income, spending, 1)
    p: np.poly1d = np.poly1d(z)
    x_line: np.ndarray = np.linspace(income.min(), income.max(), 100)
    plt.plot(x_line, p(x_line), "r--", alpha=0.7, label=f"Trend: y={z[0]:.2f}x+{z[1]:.0f}")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig("scatter_basic.png")
    plt.show()


def demo_scatter_bubble() -> None:
    """Bubble chart: three-variable relationship (x, y, size)."""
    rng: np.random.Generator = np.random.default_rng(42)
    n: int = 30
    x: np.ndarray = rng.uniform(10, 100, n)
    y: np.ndarray = 0.5 * x + rng.normal(0, 10, n)
    sizes: np.ndarray = rng.uniform(50, 500, n)
    colors: np.ndarray = rng.uniform(0, 1, n)

    plt.figure(figsize=(8, 5))
    plt.scatter(x, y, s=sizes, c=colors, cmap="viridis", alpha=0.6, edgecolors="grey")
    plt.colorbar(label="Category Index")
    plt.xlabel("Marketing Spend (10k)")
    plt.ylabel("Revenue (10k)")
    plt.title("Bubble Chart: Spend vs Revenue (bubble = market share)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig("scatter_bubble.png")
    plt.show()


# ===================================================================
# 4. HISTOGRAMS - data distribution
# ===================================================================

def demo_histogram() -> None:
    """Histogram of student heights with configurable bins."""
    heights: np.ndarray = np.array([
        170, 163, 174, 164, 159, 168, 165, 171, 171, 167,
        165, 161, 175, 170, 174, 170, 174, 170, 173, 173,
        167, 169, 173, 153, 165, 169, 158, 166, 164, 173,
        162, 171, 173, 171, 165, 152, 163, 170, 171, 163,
        165, 166, 155, 155, 171, 161, 167, 172, 164, 155,
        168, 171, 173, 169, 165, 162, 168, 177, 174, 178,
        161, 180, 155, 155, 166, 175, 159, 169, 165, 174,
        175, 160, 152, 168, 164, 175, 168, 183, 166, 166,
        182, 174, 167, 168, 176, 170, 169, 173, 177, 168,
        172, 159, 173, 185, 161, 170, 170, 184, 171, 172,
    ])

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Standard histogram (count)
    axes[0].hist(heights, bins=np.arange(145, 196, 5), color="darkcyan", edgecolor="white")
    axes[0].set_xlabel("Height (cm)")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Height Distribution (Count)")

    # Cumulative density histogram
    axes[1].hist(
        heights,
        bins=np.arange(145, 196, 5),
        color="darkcyan",
        edgecolor="white",
        density=True,
        cumulative=True,
    )
    axes[1].set_xlabel("Height (cm)")
    axes[1].set_ylabel("Cumulative Probability")
    axes[1].set_title("Height CDF")

    fig.suptitle("Student Height Analysis (n=100)", fontsize=13)
    fig.tight_layout()
    fig.savefig("histogram.png")
    plt.show()


# ===================================================================
# 5. SUBPLOTS - multi-panel layouts
# ===================================================================

def demo_subplots() -> None:
    """Create a 2x2 subplot layout mixing different chart types."""
    rng: np.random.Generator = np.random.default_rng(0)
    x: np.ndarray = np.linspace(-2 * np.pi, 2 * np.pi, 80)

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))

    # Top-left: Line plot
    axes[0, 0].plot(x, np.sin(x), "r-", linewidth=1.5, label="sin")
    axes[0, 0].plot(x, np.cos(x), "b--", linewidth=1.5, label="cos")
    axes[0, 0].set_title("Line Plot")
    axes[0, 0].legend(fontsize=9)
    axes[0, 0].grid(True, linestyle="--", alpha=0.4)

    # Top-right: Bar chart
    cats: list[str] = ["A", "B", "C", "D", "E"]
    vals: np.ndarray = rng.integers(20, 80, 5)
    axes[0, 1].bar(cats, vals, color=["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974"])
    axes[0, 1].set_title("Bar Chart")
    axes[0, 1].grid(axis="y", linestyle="--", alpha=0.4)

    # Bottom-left: Scatter
    xs: np.ndarray = rng.normal(50, 15, 60)
    ys: np.ndarray = 0.8 * xs + rng.normal(0, 10, 60)
    axes[1, 0].scatter(xs, ys, s=40, c="teal", alpha=0.7, edgecolors="white")
    axes[1, 0].set_title("Scatter Plot")
    axes[1, 0].grid(True, linestyle="--", alpha=0.4)

    # Bottom-right: Histogram
    data: np.ndarray = rng.normal(170, 8, 200)
    axes[1, 1].hist(data, bins=15, color="salmon", edgecolor="white", alpha=0.85)
    axes[1, 1].set_title("Histogram")
    axes[1, 1].grid(axis="y", linestyle="--", alpha=0.4)

    fig.suptitle("Mixed Chart Types in Subplots", fontsize=14)
    fig.tight_layout()
    fig.savefig("subplots_mixed.png")
    plt.show()


def demo_subplots_nested() -> None:
    """Demonstrate nested axes (inset plot) using add_axes."""
    x: np.ndarray = np.linspace(-2 * np.pi, 2 * np.pi, 120)

    fig: Figure = plt.figure(figsize=(10, 4))
    ax_main: Axes = fig.add_axes((0.08, 0.12, 0.55, 0.78))
    ax_main.plot(x, np.sin(x), linewidth=2, marker="*", color="red", markersize=4)
    ax_main.set_title("Main Plot with Inset Views")
    ax_main.set_xlabel("x")
    ax_main.set_ylabel("sin(x)")
    ax_main.grid(True, linestyle="--", alpha=0.4)

    # Inset 1 (top-right): zoom on cosine
    ax_inset1: Axes = fig.add_axes((0.68, 0.52, 0.28, 0.36))
    ax_inset1.plot(x, np.cos(x), marker="^", color="blue", markersize=2)
    ax_inset1.set_title("cos(x)", fontsize=9)
    ax_inset1.tick_params(labelsize=7)

    # Inset 2 (bottom-right): zoom on tangent (clipped)
    ax_inset2: Axes = fig.add_axes((0.68, 0.10, 0.28, 0.36))
    tan_y: np.ndarray = np.clip(np.tan(x), -5, 5)
    ax_inset2.plot(x, tan_y, marker=".", color="green", markersize=2)
    ax_inset2.set_title("tan(x) [clipped]", fontsize=9)
    ax_inset2.tick_params(labelsize=7)

    fig.savefig("subplots_nested.png")
    plt.show()


# ===================================================================
# 6. PIE CHART - composition / proportion
# ===================================================================

def demo_pie_chart() -> None:
    """Donut-style pie chart showing fruit sales proportions."""
    data: np.ndarray = np.array([320, 210, 180, 270, 150, 200, 350])
    labels: list[str] = ["Apple", "Banana", "Peach", "Lychee", "Pomegranate", "Mangosteen", "Durian"]
    colors: np.ndarray = np.array([
        [0.85, 0.33, 0.10],
        [0.99, 0.75, 0.44],
        [0.11, 0.62, 0.47],
        [0.46, 0.32, 0.65],
        [0.80, 0.52, 0.25],
        [0.55, 0.75, 0.24],
        [0.90, 0.63, 0.10],
    ])

    plt.figure(figsize=(6, 6))
    plt.pie(
        data,
        autopct="%.1f%%",
        radius=1,
        pctdistance=0.8,
        colors=colors,
        textprops={"fontsize": 9, "color": "black"},
        wedgeprops={"linewidth": 1, "width": 0.35},
        labels=labels,
    )
    plt.title("Fruit Sales Proportion")
    plt.tight_layout()
    plt.savefig("pie_donut.png")
    plt.show()


# ===================================================================
# 7. BOX PLOTS - outlier detection and distribution summary
# ===================================================================

def demo_boxplot() -> None:
    """Box plot with mean marker and notch, including outliers."""
    rng: np.random.Generator = np.random.default_rng(7)
    data: np.ndarray = rng.integers(0, 100, 47)
    data = np.append(data, [160, 200, -50])  # outliers

    plt.figure(figsize=(6, 4))
    bp = plt.boxplot(data, whis=1.5, showmeans=True, notch=True,
                     meanprops={"marker": "D", "markerfacecolor": "red", "markersize": 6})
    plt.ylim([-100, 250])
    plt.xticks([1], labels=["Sample Data"])
    plt.ylabel("Value")
    plt.title("Box Plot: Distribution with Outliers")
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig("boxplot.png")
    plt.show()


def demo_boxplot_groups() -> None:
    """Multiple box plots side by side for group comparison."""
    rng: np.random.Generator = np.random.default_rng(10)
    departments: dict[str, np.ndarray] = {
        "Engineering": rng.normal(75, 12, 50),
        "Marketing": rng.normal(65, 15, 50),
        "Sales": rng.normal(70, 10, 50),
        "HR": rng.normal(60, 8, 50),
    }

    plt.figure(figsize=(8, 5))
    plt.boxplot(departments.values(), labels=departments.keys(), showmeans=True,
                meanprops={"marker": "s", "markerfacecolor": "gold", "markersize": 5})
    plt.ylabel("Performance Score")
    plt.title("Department Performance Comparison")
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig("boxplot_groups.png")
    plt.show()


# ===================================================================
# ENTERPRISE EXAMPLE 1: Sales Trend Chart
# ===================================================================

def enterprise_sales_trend() -> None:
    """
    Simulate a monthly sales trend chart with year-over-year comparison.

    Enterprise use-case:
      A retail company tracks monthly revenue across two consecutive years
      to identify seasonal patterns and growth trends.
    """
    rng: np.random.Generator = np.random.default_rng(2024)
    months: list[str] = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    # Simulated revenue (10k CNY)
    base_pattern: np.ndarray = np.array([80, 65, 90, 85, 110, 120, 95, 88, 105, 130, 150, 180])
    revenue_2023: np.ndarray = base_pattern + rng.normal(0, 5, 12)
    revenue_2024: np.ndarray = base_pattern * 1.15 + rng.normal(0, 5, 12)

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(months, revenue_2023, "o-", color="#4C72B0", linewidth=2, markersize=6, label="2023")
    ax.plot(months, revenue_2024, "s-", color="#C44E52", linewidth=2, markersize=6, label="2024")

    # Fill the gap between years
    ax.fill_between(months, revenue_2023, revenue_2024, alpha=0.15, color="#C44E52")

    # Annotate peak month
    peak_idx: int = int(np.argmax(revenue_2024))
    ax.annotate(
        f"Peak: {revenue_2024[peak_idx]:.0f}k",
        xy=(peak_idx, revenue_2024[peak_idx]),
        xytext=(peak_idx - 2, revenue_2024[peak_idx] + 15),
        fontsize=10,
        arrowprops={"arrowstyle": "->", "color": "black"},
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "lightyellow"},
    )

    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Revenue (10k CNY)", fontsize=11)
    ax.set_title("Monthly Sales Trend: 2023 vs 2024", fontsize=13, fontweight="bold")
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    fig.tight_layout()
    fig.savefig("enterprise_sales_trend.png", bbox_inches="tight")
    plt.show()


# ===================================================================
# ENTERPRISE EXAMPLE 2: KPI Dashboard
# ===================================================================

def enterprise_kpi_dashboard() -> None:
    """
    Multi-panel KPI dashboard for executive reporting.

    Enterprise use-case:
      A management dashboard combining revenue trends, product mix,
      regional comparison, and distribution analysis in a single view.

    C++ comparison:
      Building this in Qt Charts would require ~300-500 lines of C++ to
      create QChart objects, configure axes, series, legends, and layout.
      Matplotlib achieves the same with ~60 lines of declarative Python.
    """
    rng: np.random.Generator = np.random.default_rng(2024)
    fig = plt.figure(figsize=(14, 9))
    fig.suptitle("Executive KPI Dashboard - Q4 2024", fontsize=16, fontweight="bold", y=0.98)

    # --- Panel 1: Revenue trend (top-left) ---
    ax1: Axes = fig.add_subplot(2, 3, 1)
    months: list[str] = ["Oct", "Nov", "Dec"]
    revenue: np.ndarray = np.array([1300, 1500, 1800])
    cost: np.ndarray = np.array([850, 950, 1100])
    ax1.plot(months, revenue, "o-", color="#2ca02c", linewidth=2, label="Revenue")
    ax1.plot(months, cost, "s--", color="#d62728", linewidth=2, label="Cost")
    ax1.fill_between(months, cost, revenue, alpha=0.2, color="#2ca02c")
    ax1.set_title("Revenue vs Cost", fontsize=10)
    ax1.set_ylabel("Amount (10k CNY)")
    ax1.legend(fontsize=8)
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    # --- Panel 2: Product mix pie (top-center) ---
    ax2: Axes = fig.add_subplot(2, 3, 2)
    products: list[str] = ["Electronics", "Clothing", "Food", "Home", "Other"]
    shares: np.ndarray = np.array([35, 25, 20, 12, 8])
    pie_colors: list[str] = ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974"]
    ax2.pie(shares, labels=products, autopct="%1.0f%%", colors=pie_colors,
            textprops={"fontsize": 8}, wedgeprops={"linewidth": 0.8})
    ax2.set_title("Product Mix", fontsize=10)

    # --- Panel 3: Regional bar chart (top-right) ---
    ax3: Axes = fig.add_subplot(2, 3, 3)
    regions: list[str] = ["North", "East", "South", "West", "Central"]
    regional_rev: np.ndarray = rng.integers(200, 600, 5)
    bar_colors: list[str] = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    ax3.barh(regions, regional_rev, color=bar_colors)
    ax3.set_xlabel("Revenue (10k CNY)")
    ax3.set_title("Revenue by Region", fontsize=10)
    ax3.grid(axis="x", linestyle="--", alpha=0.4)

    # --- Panel 4: Customer age distribution (bottom-left) ---
    ax4: Axes = fig.add_subplot(2, 3, 4)
    ages: np.ndarray = rng.normal(35, 10, 500).clip(18, 70)
    ax4.hist(ages, bins=15, color="steelblue", edgecolor="white", alpha=0.85)
    ax4.axvline(np.mean(ages), color="red", linestyle="--", linewidth=1.5, label=f"Mean={np.mean(ages):.1f}")
    ax4.set_xlabel("Age")
    ax4.set_ylabel("Count")
    ax4.set_title("Customer Age Distribution", fontsize=10)
    ax4.legend(fontsize=8)

    # --- Panel 5: Quarterly box plots (bottom-center) ---
    ax5: Axes = fig.add_subplot(2, 3, 5)
    quarterly_data: list[np.ndarray] = [
        rng.normal(50, 10, 80) for _ in range(4)
    ]
    ax5.boxplot(quarterly_data, labels=["Q1", "Q2", "Q3", "Q4"], showmeans=True,
                meanprops={"marker": "D", "markerfacecolor": "gold", "markersize": 4})
    ax5.set_ylabel("Order Size (units)")
    ax5.set_title("Order Size Distribution by Quarter", fontsize=10)
    ax5.grid(axis="y", linestyle="--", alpha=0.4)

    # --- Panel 6: Satisfaction scatter (bottom-right) ---
    ax6: Axes = fig.add_subplot(2, 3, 6)
    n_cust: int = 100
    orders_count: np.ndarray = rng.integers(1, 50, n_cust)
    satisfaction: np.ndarray = 3.5 + 0.03 * orders_count + rng.normal(0, 0.4, n_cust)
    satisfaction = satisfaction.clip(1, 5)
    ax6.scatter(orders_count, satisfaction, s=25, c="teal", alpha=0.6, edgecolors="white")
    ax6.set_xlabel("Orders Count")
    ax6.set_ylabel("Satisfaction (1-5)")
    ax6.set_title("Orders vs Satisfaction", fontsize=10)
    ax6.grid(True, linestyle="--", alpha=0.4)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig("enterprise_kpi_dashboard.png", bbox_inches="tight")
    plt.show()


# ===================================================================
# ENTERPRISE EXAMPLE 3: Report Figures
# ===================================================================

def enterprise_report_figures() -> None:
    """
    Publication-quality figures suitable for inclusion in business reports.

    Enterprise use-case:
      Generate a set of polished charts for a quarterly business review
      document (PDF/PowerPoint). Charts use consistent styling, clear
      labels, and professional color palettes.

    C++ comparison:
      gnuplot script for similar output would require:
        set terminal pdfcairo enhanced font "Helvetica,10"
        set output "report.pdf"
        set style data histogram
        set style fill solid 0.8
        ... (50+ lines for each chart)
      Matplotlib handles all of this programmatically with full control.
    """
    rng: np.random.Generator = np.random.default_rng(99)

    # Consistent style for all report figures
    report_style: dict = {
        "figure.facecolor": "white",
        "axes.facecolor": "#f8f9fa",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "font.size": 10,
    }

    with plt.rc_context(report_style):
        # Figure 1: Yearly revenue with trend projection
        fig1, ax1 = plt.subplots(figsize=(8, 4.5))
        years: np.ndarray = np.arange(2019, 2025)
        actual_rev: np.ndarray = np.array([4200, 3800, 4600, 5100, 5800, 6500])
        projected_rev: np.ndarray = np.array([np.nan, np.nan, np.nan, np.nan, np.nan, 6500])
        # Simple linear projection for 2025-2026
        fit_coeffs: np.ndarray = np.polyfit(years, actual_rev, 1)
        proj_years: np.ndarray = np.array([2025, 2026])
        proj_values: np.ndarray = np.polyval(fit_coeffs, proj_years)

        ax1.bar(years, actual_rev, color="#4C72B0", label="Actual", zorder=3)
        ax1.bar(proj_years, proj_values, color="#4C72B0", alpha=0.4, hatch="//", label="Projected", zorder=3)
        ax1.set_xticks(np.concatenate([years, proj_years]))
        ax1.set_ylabel("Annual Revenue (10k CNY)")
        ax1.set_title("Annual Revenue Trend & 2-Year Projection", fontsize=12, fontweight="bold")
        ax1.legend()
        fig1.tight_layout()
        fig1.savefig("report_revenue_projection.png", bbox_inches="tight")

        # Figure 2: Pareto chart (bar + cumulative line)
        fig2, ax2 = plt.subplots(figsize=(8, 4.5))
        defect_types: list[str] = ["Cracks", "Scratches", "Dents", "Color", "Dimension", "Other"]
        defect_counts: np.ndarray = np.array([45, 30, 20, 15, 8, 5])
        sorted_idx: np.ndarray = np.argsort(defect_counts)[::-1]
        defect_counts_sorted: np.ndarray = defect_counts[sorted_idx]
        defect_types_sorted: list[str] = [defect_types[i] for i in sorted_idx]
        cumulative_pct: np.ndarray = np.cumsum(defect_counts_sorted) / defect_counts_sorted.sum() * 100

        ax2.bar(defect_types_sorted, defect_counts_sorted, color="#C44E52", zorder=3)
        ax2.set_ylabel("Defect Count")
        ax2.set_title("Pareto Analysis: Top Defect Categories", fontsize=12, fontweight="bold")
        ax2_twin: Axes = ax2.twinx()
        ax2_twin.plot(defect_types_sorted, cumulative_pct, "o-", color="#1f77b4", linewidth=2)
        ax2_twin.set_ylabel("Cumulative %")
        ax2_twin.axhline(80, color="grey", linestyle=":", alpha=0.6)
        ax2_twin.text(len(defect_types_sorted) - 1, 82, "80% threshold", fontsize=8, color="grey")
        fig2.tight_layout()
        fig2.savefig("report_pareto.png", bbox_inches="tight")

        # Figure 3: Heatmap-style correlation display
        fig3, ax3 = plt.subplots(figsize=(6, 5))
        metrics: list[str] = ["Revenue", "Profit", "Customers", "Orders", "AOV"]
        corr_matrix: np.ndarray = np.array([
            [1.00, 0.85, 0.72, 0.91, 0.55],
            [0.85, 1.00, 0.60, 0.78, 0.68],
            [0.72, 0.60, 1.00, 0.82, 0.30],
            [0.91, 0.78, 0.82, 1.00, 0.45],
            [0.55, 0.68, 0.30, 0.45, 1.00],
        ])
        im = ax3.imshow(corr_matrix, cmap="RdYlGn", vmin=0, vmax=1)
        ax3.set_xticks(range(len(metrics)))
        ax3.set_yticks(range(len(metrics)))
        ax3.set_xticklabels(metrics, fontsize=9, rotation=45, ha="right")
        ax3.set_yticklabels(metrics, fontsize=9)
        # Annotate cells
        for i in range(len(metrics)):
            for j in range(len(metrics)):
                ax3.text(j, i, f"{corr_matrix[i, j]:.2f}", ha="center", va="center",
                         fontsize=9, color="black" if corr_matrix[i, j] > 0.5 else "white")
        fig3.colorbar(im, ax=ax3, shrink=0.8)
        ax3.set_title("KPI Correlation Matrix", fontsize=12, fontweight="bold")
        fig3.tight_layout()
        fig3.savefig("report_correlation_heatmap.png", bbox_inches="tight")

        plt.show()


# ===================================================================
# UTILITY: savefig-before-show reminder
# ===================================================================

def savefig_before_show_demo() -> None:
    """
    Demonstrate the critical rule: call savefig() BEFORE show().

    Matplotlib releases the figure object upon show(), so any savefig()
    call after show() produces a blank image. This is a common pitfall
    that does not exist in gnuplot (where 'set output' is declared upfront).
    """
    x: np.ndarray = np.linspace(0, 10, 100)
    plt.figure(figsize=(6, 3))
    plt.plot(x, np.sin(x), "b-", linewidth=2)
    plt.title("savefig() must come BEFORE show()")

    # CORRECT order:
    plt.savefig("correct_save.png", bbox_inches="tight")
    plt.show()
    # If we called plt.savefig() here, the file would be blank.


# ===================================================================
# MAIN ENTRY POINT
# ===================================================================

def main() -> None:
    """Run all demonstrations in sequence."""
    configure_matplotlib()

    print("=" * 60)
    print("  Matplotlib Basics - Day 78 Demonstrations")
    print("=" * 60)

    sections: list[tuple[str, callable]] = [
        ("1. Basic Line Plot", demo_line_plot_basic),
        ("2. Dual Line Plot with Annotations", demo_line_plot_dual),
        ("3. Grouped Bar Chart", demo_bar_grouped),
        ("4. Stacked Bar Chart", demo_bar_stacked),
        ("5. Horizontal Bar Chart", demo_bar_horizontal),
        ("6. Scatter Plot with Trend Line", demo_scatter_basic),
        ("7. Bubble Chart", demo_scatter_bubble),
        ("8. Histograms (Count & CDF)", demo_histogram),
        ("9. Mixed Subplots (2x2)", demo_subplots),
        ("10. Nested/Inset Axes", demo_subplots_nested),
        ("11. Donut Pie Chart", demo_pie_chart),
        ("12. Box Plot (Single)", demo_boxplot),
        ("13. Box Plot (Grouped)", demo_boxplot_groups),
        ("14. [Enterprise] Sales Trend", enterprise_sales_trend),
        ("15. [Enterprise] KPI Dashboard", enterprise_kpi_dashboard),
        ("16. [Enterprise] Report Figures", enterprise_report_figures),
        ("17. Savefig-Before-Show Rule", savefig_before_show_demo),
    ]

    for title, func in sections:
        print(f"\n--- {title} ---")
        try:
            func()
        except Exception as exc:
            print(f"  [ERROR] {exc}")

    print("\n" + "=" * 60)
    print("  All demonstrations complete. Charts saved as PNG files.")
    print("=" * 60)


if __name__ == "__main__":
    main()
