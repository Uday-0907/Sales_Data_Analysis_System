"""
Matplotlib Visualization Module for Sales Data Analysis System.
Produces high-quality, professional, light-themed charts (bar, horizontal bar, donut, line, histogram)
fully compliant with academic Level-1 requirements. Modern executive aesthetic.
"""

from typing import Optional, List
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import numpy as np


# Palette for Light Theme charts
CHART_BG = "#FFFFFF"
AXIS_BG = "#FFFFFF"
GRID_COLOR = "#F1F5F9"
SPINE_COLOR = "#E2E8F0"
TEXT_COLOR = "#0F172A"
LABEL_COLOR = "#334155"
MUTED_TEXT = "#64748B"
PRIMARY_BLUE = "#2563EB"
SECONDARY_SKY = "#0EA5E9"
ACCENT_EMERALD = "#10B981"
ACCENT_AMBER = "#F59E0B"
ACCENT_VIOLET = "#8B5CF6"
ACCENT_ROSE = "#F43F5E"

PALETTE = [
    "#2563EB",  # Vibrant Blue
    "#0EA5E9",  # Sky Blue
    "#10B981",  # Emerald Green
    "#F59E0B",  # Warm Amber
    "#8B5CF6",  # Violet
    "#EC4899",  # Pink
    "#14B8A6",  # Teal
    "#6366F1"   # Indigo
]


def apply_theme(fig: plt.Figure, ax: plt.Axes) -> None:
    """Applies cohesive, clean light theme styling to figure and axes."""
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor(AXIS_BG)
    ax.grid(True, color=GRID_COLOR, linestyle="--", linewidth=0.8, alpha=0.9)
    ax.set_axisbelow(True)

    # Clean borders: remove top and right spines, subtle bottom and left
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SPINE_COLOR)
    ax.spines["bottom"].set_color(SPINE_COLOR)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)

    ax.tick_params(colors=MUTED_TEXT, labelsize=9)
    ax.xaxis.label.set_color(LABEL_COLOR)
    ax.yaxis.label.set_color(LABEL_COLOR)
    ax.title.set_color(TEXT_COLOR)


def create_bar_chart(
    df: pd.DataFrame,
    cat_col: str,
    val_col: str,
    title: str,
    x_label: str = "",
    y_label: str = "",
    horizontal: bool = False,
    color: str = PRIMARY_BLUE
) -> Optional[plt.Figure]:
    """
    Creates a clean, formatted light-themed Matplotlib bar chart.
    """
    if df is None or df.empty or cat_col not in df.columns or val_col not in df.columns:
        return None

    plot_df = df.dropna(subset=[cat_col, val_col]).copy()
    if plot_df.empty:
        return None

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
    apply_theme(fig, ax)

    categories = plot_df[cat_col].astype(str).tolist()
    values = pd.to_numeric(plot_df[val_col], errors="coerce").fillna(0).tolist()

    colors = [PALETTE[i % len(PALETTE)] for i in range(len(categories))]

    if horizontal:
        y_pos = np.arange(len(categories))
        ax.barh(y_pos, values, color=colors, edgecolor="#FFFFFF", height=0.6, linewidth=1.0)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories, fontsize=9, color=LABEL_COLOR)
        ax.invert_yaxis()
        ax.set_xlabel(y_label or val_col, fontsize=9.5, fontweight="medium", color=LABEL_COLOR)
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))
    else:
        x_pos = np.arange(len(categories))
        ax.bar(x_pos, values, color=colors, edgecolor="#FFFFFF", width=0.55, linewidth=1.0)
        ax.set_xticks(x_pos)
        
        # Rotate labels if long or numerous
        rotation = 35 if len(categories) > 4 or any(len(c) > 8 for c in categories) else 0
        ax.set_xticklabels(categories, rotation=rotation, ha="right" if rotation else "center", fontsize=9, color=LABEL_COLOR)
        ax.set_ylabel(y_label or val_col, fontsize=9.5, fontweight="medium", color=LABEL_COLOR)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, p: f"{y:,.0f}"))

    ax.set_title(title, fontsize=11.5, fontweight="bold", pad=12, color=TEXT_COLOR)
    fig.tight_layout()
    return fig


def create_pie_chart(
    df: pd.DataFrame,
    cat_col: str,
    val_col: str,
    title: str,
    max_slices: int = 7
) -> Optional[plt.Figure]:
    """
    Creates a clean donut chart for small category counts (<= max_slices).
    Gracefully falls back to a horizontal bar chart if categories > max_slices.
    """
    if df is None or df.empty or cat_col not in df.columns or val_col not in df.columns:
        return None

    plot_df = df.dropna(subset=[cat_col, val_col]).copy()
    plot_df[val_col] = pd.to_numeric(plot_df[val_col], errors="coerce").fillna(0)
    plot_df = plot_df[plot_df[val_col] > 0]

    if plot_df.empty:
        return None

    # Fallback if too many categories
    if len(plot_df) > max_slices:
        return create_bar_chart(
            plot_df,
            cat_col,
            val_col,
            title=f"{title} (Top Categories)",
            horizontal=True
        )

    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=100)
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor(CHART_BG)

    categories = plot_df[cat_col].astype(str).tolist()
    values = plot_df[val_col].tolist()
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(categories))]

    wedges, texts, autotexts = ax.pie(
        values,
        labels=categories,
        colors=colors,
        autopct="%1.1f%%",
        startangle=140,
        pctdistance=0.75,
        wedgeprops=dict(width=0.45, edgecolor="#FFFFFF", linewidth=2.5),
        textprops=dict(color=LABEL_COLOR, fontsize=9, fontweight="medium")
    )

    for autotext in autotexts:
        autotext.set_color("#FFFFFF")
        autotext.set_fontsize(8.5)
        autotext.set_weight("bold")

    ax.set_title(title, fontsize=11.5, fontweight="bold", color=TEXT_COLOR, pad=12)
    fig.tight_layout()
    return fig


def create_line_chart(
    df: pd.DataFrame,
    date_col: str,
    val_col: str,
    title: str,
    x_label: str = "Period",
    y_label: str = "Sales Amount",
    color: str = PRIMARY_BLUE
) -> Optional[plt.Figure]:
    """
    Creates a clean chronological line chart for time-series trends with subtle area tint.
    """
    if df is None or df.empty or date_col not in df.columns or val_col not in df.columns:
        return None

    plot_df = df.dropna(subset=[date_col, val_col]).copy()
    if plot_df.empty:
        return None

    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=100)
    apply_theme(fig, ax)

    x_vals = plot_df[date_col].astype(str).tolist()
    y_vals = pd.to_numeric(plot_df[val_col], errors="coerce").fillna(0).tolist()

    x_pos = np.arange(len(x_vals))
    ax.plot(x_pos, y_vals, marker="o", markersize=5.5, color=color, linewidth=2.4,
            markeredgecolor="#FFFFFF", markeredgewidth=1.2, label=val_col)
    ax.fill_between(x_pos, y_vals, color=color, alpha=0.08)

    ax.set_xticks(x_pos)
    
    # Subsample x-axis ticks if too dense
    if len(x_vals) > 15:
        step = max(1, len(x_vals) // 10)
        selected_ticks = x_pos[::step]
        selected_labels = [x_vals[i] for i in selected_ticks]
        ax.set_xticks(selected_ticks)
        ax.set_xticklabels(selected_labels, rotation=35, ha="right", fontsize=9, color=LABEL_COLOR)
    else:
        ax.set_xticklabels(x_vals, rotation=35, ha="right", fontsize=9, color=LABEL_COLOR)

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, p: f"{y:,.0f}"))
    ax.set_xlabel(x_label, fontsize=9.5, fontweight="medium", color=LABEL_COLOR)
    ax.set_ylabel(y_label, fontsize=9.5, fontweight="medium", color=LABEL_COLOR)
    ax.set_title(title, fontsize=11.5, fontweight="bold", pad=12, color=TEXT_COLOR)
    fig.tight_layout()
    return fig


def create_histogram(
    series: pd.Series,
    title: str,
    x_label: str = "Value",
    bins: int = 20,
    color: str = SECONDARY_SKY
) -> Optional[plt.Figure]:
    """
    Creates a clean histogram showing the distribution of a numeric column.
    """
    clean_series = pd.to_numeric(series, errors="coerce").dropna()
    if clean_series.empty:
        return None

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)
    apply_theme(fig, ax)

    ax.hist(
        clean_series,
        bins=bins,
        color=color,
        edgecolor="#FFFFFF",
        linewidth=1.0,
        alpha=0.88
    )

    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, p: f"{y:,.0f}"))
    ax.set_xlabel(x_label, fontsize=9.5, fontweight="medium", color=LABEL_COLOR)
    ax.set_ylabel("Frequency (Record Count)", fontsize=9.5, fontweight="medium", color=LABEL_COLOR)
    ax.set_title(title, fontsize=11.5, fontweight="bold", pad=12, color=TEXT_COLOR)
    fig.tight_layout()
    return fig
