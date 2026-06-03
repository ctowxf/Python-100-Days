"""
Day 79 - Advanced Matplotlib: High-Level Statistical Charts
===========================================================

This module demonstrates advanced matplotlib techniques including:
- Bubble charts, area charts, radar charts, rose charts
- 3D surface plots
- Plot customization, annotations, and styles
- Animation support
- Enterprise-grade publication-quality figures
- Interactive dashboard layout

Usage:
    python 79_matplotlib_advanced.py

Requirements:
    pip install matplotlib numpy
"""

from __future__ import annotations

import warnings
from typing import Optional, Sequence

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch
from matplotlib import patheffects

# ---------------------------------------------------------------------------
# Global style configuration
# ---------------------------------------------------------------------------

def configure_global_style() -> None:
    """Set up a clean, publication-ready global style."""
    plt.rcParams.update({
        "figure.figsize": (10, 6),
        "figure.dpi": 120,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "font.family": "sans-serif",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.facecolor": "#f9f9f9",
        "figure.facecolor": "#ffffff",
    })


# ---------------------------------------------------------------------------
# 1. Bubble Chart
# ---------------------------------------------------------------------------

def demo_bubble_chart() -> None:
    """Visualize three-variable relationships with a bubble chart."""
    income = np.array([5550, 7500, 10500, 15000, 20000, 25000, 30000, 40000])
    outcome = np.array([800, 1800, 1250, 2000, 1800, 2100, 2500, 3500])
    nums = np.array([5, 3, 10, 5, 12, 20, 8, 10])

    fig, ax = plt.subplots(figsize=(9, 6))
    scatter = ax.scatter(
        income, outcome,
        s=nums * 30,
        c=nums,
        cmap="Reds",
        alpha=0.75,
        edgecolors="#333333",
        linewidths=0.8,
    )
    cbar = fig.colorbar(scatter, ax=ax, label="Purchase Count")
    ax.set_xlabel("Monthly Income (CNY)")
    ax.set_ylabel("Online Spending (CNY)")
    ax.set_title("Bubble Chart: Income vs. Online Spending")

    # Annotate each bubble with its count
    for inc, out, n in zip(income, outcome, nums):
        ax.annotate(str(n), (inc, out), ha="center", va="center", fontsize=8,
                    fontweight="bold", color="white",
                    path_effects=[patheffects.withStroke(linewidth=2, foreground="#333")])

    fig.tight_layout()
    fig.savefig("bubble_chart.png", dpi=150, bbox_inches="tight")
    plt.show()


# ---------------------------------------------------------------------------
# 2. Stacked Area Chart
# ---------------------------------------------------------------------------

def demo_area_chart() -> None:
    """Stacked area chart showing weekly time allocation."""
    days = np.arange(7)
    sleeping = [7, 8, 6, 6, 7, 8, 10]
    eating   = [2, 3, 2, 1, 2, 3, 2]
    working  = [7, 8, 7, 8, 6, 2, 3]
    playing  = [8, 5, 9, 9, 9, 11, 9]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.stackplot(
        days, sleeping, eating, working, playing,
        labels=["Sleep", "Eat", "Work", "Play"],
        colors=["#4c72b0", "#dd8452", "#55a868", "#c44e52"],
        alpha=0.85,
    )
    ax.set_xticks(days)
    ax.set_xticklabels([f"Day {d+1}" for d in days])
    ax.set_ylabel("Hours")
    ax.set_title("Weekly Time Allocation (Stacked Area)")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 32)

    fig.tight_layout()
    fig.savefig("stacked_area_chart.png", dpi=150, bbox_inches="tight")
    plt.show()


# ---------------------------------------------------------------------------
# 3. Radar Chart
# ---------------------------------------------------------------------------

def demo_radar_chart() -> None:
    """Compare two athletes across multiple skill dimensions."""
    labels = np.array(["Speed", "Power", "Experience", "Defense", "Serve", "Skill"])
    player_a = np.array([93, 95, 98, 92, 96, 97])
    player_b = np.array([30, 40, 65, 80, 45, 60])

    angles = np.linspace(0, 2 * np.pi, labels.size, endpoint=False).tolist()
    # Close the polygon
    player_a = np.append(player_a, player_a[0]).tolist()
    player_b = np.append(player_b, player_b[0]).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, player_a, color="#c44e52", alpha=0.25)
    ax.plot(angles, player_a, color="#c44e52", linewidth=2, label="Player A")
    ax.fill(angles, player_b, color="#4c72b0", alpha=0.25)
    ax.plot(angles, player_b, color="#4c72b0", linewidth=2, label="Player B")

    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_ylim(0, 100)
    ax.set_title("Athlete Skill Comparison", y=1.08)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1))

    fig.tight_layout()
    fig.savefig("radar_chart.png", dpi=150, bbox_inches="tight")
    plt.show()


# ---------------------------------------------------------------------------
# 4. Rose (Nightingale) Chart
# ---------------------------------------------------------------------------

def demo_rose_chart() -> None:
    """Nightingale rose chart for cyclical categorical data."""
    np.random.seed(42)
    group1 = np.random.randint(20, 50, 4)
    group2 = np.random.randint(10, 60, 4)
    categories = [f"A-Q{i}" for i in range(1, 5)] + [f"B-Q{i}" for i in range(1, 5)]
    values = np.concatenate([group1, group2])

    theta = np.linspace(0, 2 * np.pi, len(categories), endpoint=False)
    width = 2 * np.pi / len(categories)
    colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    bars = ax.bar(theta, values, width=width, color=colors, edgecolor="white",
                  linewidth=0.8, bottom=0, alpha=0.9)

    ax.set_thetagrids(np.degrees(theta), categories, fontsize=10)
    ax.set_title("Quarterly Comparison (Rose Chart)", y=1.08)

    # Add value labels on each petal
    for bar, val in zip(bars, values):
        angle = bar.get_x() + bar.get_width() / 2
        ax.text(angle, bar.get_height() + 2, str(val),
                ha="center", va="bottom", fontsize=9, fontweight="bold")

    fig.tight_layout()
    fig.savefig("rose_chart.png", dpi=150, bbox_inches="tight")
    plt.show()


# ---------------------------------------------------------------------------
# 5. 3D Surface Plot
# ---------------------------------------------------------------------------

def demo_3d_surface() -> None:
    """Render a 3D surface with colour mapping."""
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    x = np.arange(-2, 2, 0.08)
    y = np.arange(-2, 2, 0.08)
    x, y = np.meshgrid(x, y)
    z = (1 - y**5 + x**5) * np.exp(-x**2 - y**2)

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(x, y, z, cmap="viridis", edgecolor="none", alpha=0.9)
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label="Z value")

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("3D Surface Plot")
    ax.view_init(elev=30, azim=135)

    fig.tight_layout()
    fig.savefig("3d_surface_chart.png", dpi=150, bbox_inches="tight")
    plt.show()


# ---------------------------------------------------------------------------
# 6. Advanced Annotations & Customization
# ---------------------------------------------------------------------------

def demo_annotations() -> None:
    """Showcase matplotlib annotation capabilities."""
    np.random.seed(0)
    x = np.linspace(0, 10, 100)
    y = np.sin(x)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, y, color="#4c72b0", linewidth=2)

    # Mark the peak
    peak_idx = np.argmax(y)
    ax.annotate(
        "Peak",
        xy=(x[peak_idx], y[peak_idx]),
        xytext=(x[peak_idx] + 1.5, y[peak_idx] + 0.3),
        fontsize=12,
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#c44e52", lw=2),
        bbox=dict(boxstyle="round,pad=0.3", fc="#ffeedd", ec="#c44e52", lw=1.5),
    )

    # Mark the trough
    trough_idx = np.argmin(y)
    ax.annotate(
        "Trough",
        xy=(x[trough_idx], y[trough_idx]),
        xytext=(x[trough_idx] + 1.5, y[trough_idx] - 0.4),
        fontsize=12,
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#55a868", lw=2),
        bbox=dict(boxstyle="round,pad=0.3", fc="#ddffdd", ec="#55a868", lw=1.5),
    )

    # Horizontal reference line
    ax.axhline(y=0, color="grey", linestyle="--", linewidth=0.8, alpha=0.6)
    # Shaded region
    ax.axvspan(3, 5, alpha=0.1, color="orange", label="Region of interest")

    ax.set_title("Sine Wave with Annotations")
    ax.set_xlabel("x")
    ax.set_ylabel("sin(x)")
    ax.legend()

    fig.tight_layout()
    fig.savefig("annotations_demo.png", dpi=150, bbox_inches="tight")
    plt.show()


# ---------------------------------------------------------------------------
# 7. Publication-Quality Figure (Enterprise Example)
# ---------------------------------------------------------------------------

def demo_publication_figure() -> None:
    """
    Produce a publication-quality multi-panel figure suitable for
    journal submission, demonstrating subplots, shared axes, and
    consistent styling.
    """
    np.random.seed(42)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle("Publication-Quality Multi-Panel Figure", fontsize=16, fontweight="bold", y=0.98)

    # Panel A - Line plot with confidence interval
    ax = axes[0, 0]
    t = np.linspace(0, 2 * np.pi, 200)
    mean = np.sin(t)
    std = 0.15
    ax.plot(t, mean, color="#c44e52", lw=2, label="Mean")
    ax.fill_between(t, mean - std, mean + std, color="#c44e52", alpha=0.2, label="95% CI")
    ax.set_title("(a) Signal with Confidence Interval")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.legend(loc="upper right", fontsize=9)

    # Panel B - Grouped bar chart
    ax = axes[0, 1]
    categories = ["Control", "Treatment A", "Treatment B", "Treatment C"]
    group1 = [4.2, 5.8, 6.1, 5.5]
    group2 = [3.8, 5.2, 7.3, 6.0]
    x_pos = np.arange(len(categories))
    w = 0.35
    ax.bar(x_pos - w/2, group1, w, label="Baseline", color="#4c72b0")
    ax.bar(x_pos + w/2, group2, w, label="Follow-up", color="#dd8452")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories, rotation=15, ha="right")
    ax.set_title("(b) Treatment Outcomes")
    ax.set_ylabel("Score")
    ax.legend(fontsize=9)

    # Panel C - Histogram with KDE overlay
    ax = axes[1, 0]
    data = np.random.normal(0, 1, 1000)
    ax.hist(data, bins=40, density=True, alpha=0.6, color="#55a868", edgecolor="white", label="Histogram")
    # Simple KDE via numpy
    from numpy import exp, sqrt, pi
    kde_x = np.linspace(-4, 4, 300)
    kde_y = (1 / sqrt(2 * pi)) * exp(-0.5 * kde_x**2)
    ax.plot(kde_x, kde_y, color="#c44e52", lw=2, label="KDE (Gaussian)")
    ax.set_title("(c) Distribution with KDE")
    ax.set_xlabel("Value")
    ax.set_ylabel("Density")
    ax.legend(fontsize=9)

    # Panel D - Scatter with regression line
    ax = axes[1, 1]
    x_sc = np.random.uniform(1, 10, 80)
    y_sc = 2.5 * x_sc + np.random.normal(0, 3, 80)
    ax.scatter(x_sc, y_sc, s=25, alpha=0.6, color="#8172b2", edgecolor="white", linewidths=0.3)
    # Linear fit
    coeffs = np.polyfit(x_sc, y_sc, 1)
    fit_x = np.linspace(1, 10, 100)
    fit_y = np.polyval(coeffs, fit_x)
    ax.plot(fit_x, fit_y, color="#c44e52", lw=2, linestyle="--",
            label=f"y = {coeffs[0]:.2f}x + {coeffs[1]:.2f}")
    r_sq = 1 - np.sum((y_sc - np.polyval(coeffs, x_sc))**2) / np.sum((y_sc - y_sc.mean())**2)
    ax.text(0.05, 0.92, f"$R^2 = {r_sq:.3f}$", transform=ax.transAxes, fontsize=11,
            verticalalignment="top", bbox=dict(boxstyle="round", fc="white", ec="grey"))
    ax.set_title("(d) Scatter with Regression")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend(fontsize=9, loc="lower right")

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig("publication_figure.png", dpi=300, bbox_inches="tight")
    plt.show()


# ---------------------------------------------------------------------------
# 8. Interactive Dashboard Layout (Enterprise Example)
# ---------------------------------------------------------------------------

def demo_dashboard_layout() -> None:
    """
    Build a dashboard-style layout using GridSpec, combining KPI cards,
    time-series, and a donut chart into a single canvas.
    """
    np.random.seed(7)
    fig = plt.figure(figsize=(14, 8))
    gs = GridSpec(2, 4, figure=fig, hspace=0.4, wspace=0.35)
    fig.suptitle("Executive Dashboard  |  Q1-Q4 Performance", fontsize=16, fontweight="bold")

    # --- KPI Cards (top row, first 3) ---
    kpi_data = [
        ("Revenue", "$4.2M", "+12%", "#4c72b0"),
        ("Users", "128K", "+8%", "#55a868"),
        ("Churn", "3.1%", "-0.5%", "#c44e52"),
    ]
    for i, (title, value, delta, color) in enumerate(kpi_data):
        ax = fig.add_subplot(gs[0, i])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        # Card background
        card = FancyBboxPatch((0.05, 0.05), 0.9, 0.9, boxstyle="round,pad=0.05",
                              facecolor=color, alpha=0.12, edgecolor=color, linewidth=2)
        ax.add_patch(card)
        ax.text(0.5, 0.68, value, ha="center", va="center", fontsize=26, fontweight="bold", color=color)
        ax.text(0.5, 0.42, title, ha="center", va="center", fontsize=13, color="#333")
        delta_color = "#55a868" if delta.startswith("+") or delta.startswith("-0") else "#c44e52"
        ax.text(0.5, 0.2, delta + " YoY", ha="center", va="center", fontsize=11,
                color=delta_color, fontweight="bold")

    # --- Donut chart (top-right) ---
    ax_donut = fig.add_subplot(gs[0, 3])
    segments = [35, 28, 20, 17]
    segment_labels = ["Product", "Services", "Licensing", "Other"]
    segment_colors = ["#4c72b0", "#dd8452", "#55a868", "#8172b2"]
    wedges, texts, autotexts = ax_donut.pie(
        segments, labels=segment_labels, colors=segment_colors,
        autopct="%1.0f%%", startangle=90, pctdistance=0.78,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
    )
    for txt in autotexts:
        txt.set_fontsize(9)
        txt.set_fontweight("bold")
    ax_donut.set_title("Revenue Split", fontsize=12)

    # --- Time-series chart (bottom, spans full width) ---
    ax_ts = fig.add_subplot(gs[1, :])
    months = np.arange(1, 13)
    rev = np.cumsum(np.random.uniform(0.2, 0.5, 12)) + 2
    users = np.cumsum(np.random.uniform(5, 15, 12)) + 80

    ln1 = ax_ts.plot(months, rev, color="#4c72b0", lw=2.5, marker="o", markersize=6, label="Revenue ($M)")
    ax_ts.fill_between(months, rev * 0.9, rev * 1.1, color="#4c72b0", alpha=0.1)
    ax_ts.set_xlabel("Month")
    ax_ts.set_ylabel("Revenue ($M)", color="#4c72b0")
    ax_ts.tick_params(axis="y", labelcolor="#4c72b0")

    ax_ts2 = ax_ts.twinx()
    ln2 = ax_ts2.plot(months, users, color="#55a868", lw=2.5, marker="s", markersize=6, linestyle="--", label="Users (K)")
    ax_ts2.set_ylabel("Users (K)", color="#55a868")
    ax_ts2.tick_params(axis="y", labelcolor="#55a868")

    # Combined legend
    lines = ln1 + ln2
    labels = [l.get_label() for l in lines]
    ax_ts.legend(lines, labels, loc="upper left", fontsize=10, framealpha=0.9)
    ax_ts.set_xticks(months)
    ax_ts.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax_ts.set_title("Monthly Trends", fontsize=12, pad=10)

    fig.savefig("dashboard_layout.png", dpi=200, bbox_inches="tight")
    plt.show()


# ---------------------------------------------------------------------------
# 9. Animation Example
# ---------------------------------------------------------------------------

def demo_animation() -> None:
    """
    Animate a growing sine wave. Requires a matplotlib backend that
    supports animation (e.g. TkAgg, Qt5Agg).
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.linspace(0, 4 * np.pi, 300)
    line, = ax.plot([], [], color="#4c72b0", lw=2)
    ax.set_xlim(0, 4 * np.pi)
    ax.set_ylim(-1.3, 1.3)
    ax.set_title("Animated Sine Wave")
    ax.set_xlabel("x")
    ax.set_ylabel("sin(x)")

    def init() -> list:
        line.set_data([], [])
        return [line]

    def animate(frame: int) -> list:
        end = int(frame * 4)
        line.set_data(x[:end], np.sin(x[:end]))
        return [line]

    anim = animation.FuncAnimation(
        fig, animate, init_func=init, frames=80, interval=40, blit=True,
    )

    # Save as GIF if Pillow is available, otherwise just show
    try:
        anim.save("animated_sine.gif", writer="pillow", fps=25)
        print("Animation saved to animated_sine.gif")
    except Exception:
        print("Pillow not installed; displaying animation in window instead.")

    plt.show()


# ---------------------------------------------------------------------------
# 10. Style Gallery
# ---------------------------------------------------------------------------

def demo_style_gallery() -> None:
    """Compare several built-in matplotlib styles side by side."""
    styles = ["default", "ggplot", "seaborn-v0_8-darkgrid", "bmh", "fivethirtyeight"]
    x = np.linspace(0, 10, 100)

    fig, axes = plt.subplots(1, len(styles), figsize=(18, 3.5), sharey=True)
    for ax, style_name in zip(axes, styles):
        with plt.style.context(style_name):
            ax.plot(x, np.sin(x), label="sin")
            ax.plot(x, np.cos(x), label="cos")
            ax.set_title(style_name, fontsize=10, fontweight="bold")
            ax.tick_params(labelsize=8)

    axes[0].legend(fontsize=8)
    fig.suptitle("Built-in Style Comparison", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig("style_gallery.png", dpi=150, bbox_inches="tight")
    plt.show()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all demonstrations sequentially."""
    configure_global_style()

    demos: list[tuple[str, object]] = [
        ("Bubble Chart",             demo_bubble_chart),
        ("Stacked Area Chart",       demo_area_chart),
        ("Radar Chart",              demo_radar_chart),
        ("Rose Chart",               demo_rose_chart),
        ("3D Surface Plot",          demo_3d_surface),
        ("Annotations & Customization", demo_annotations),
        ("Publication Figure",       demo_publication_figure),
        ("Dashboard Layout",         demo_dashboard_layout),
        ("Animation",                demo_animation),
        ("Style Gallery",            demo_style_gallery),
    ]

    for name, func in demos:
        print(f"\n{'='*60}")
        print(f"  Running: {name}")
        print(f"{'='*60}")
        try:
            func()  # type: ignore[operator]
        except Exception as exc:
            warnings.warn(f"[{name}] failed: {exc}", stacklevel=2)


if __name__ == "__main__":
    main()
