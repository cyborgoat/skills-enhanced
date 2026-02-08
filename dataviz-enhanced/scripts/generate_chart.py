#!/usr/bin/env python3
"""Core visualization engine — transforms structured data into publication-quality charts.

Chart types: line, bar, hbar, scatter, histogram, heatmap, box, pie, donut,
             area, bubble, timeseries, small_multiples

Usage:
    python generate_chart.py <data> <output> --type TYPE --x COL --y COL [options]

Examples:
    python generate_chart.py data.csv chart.png --type bar --x category --y sales
    python generate_chart.py data.csv chart.svg --type scatter --x age --y income --color region
    python generate_chart.py data.csv chart.pdf --type line --x date --y price --trend linear
    python generate_chart.py data.csv chart.png --type bar --x month --y revenue --highlights h.json
    python generate_chart.py data.csv chart.png --type bar --x country --y cost --top 15 --title "Top 15"
    python generate_chart.py data.csv chart.png --type hbar --x region --y cost --agg mean --groupby region
"""

import argparse
import json
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR.parent / "default-viz-config.json"

# ---------------------------------------------------------------------------
# Data reduction helpers
# ---------------------------------------------------------------------------

MAX_LABEL_LEN = 20  # Truncate tick labels beyond this length
LARGE_CATEGORY_THRESHOLD = 25  # Auto-warn / adjust when categories exceed this


def reduce_data(df: pd.DataFrame, y_col: str | list[str], **kwargs) -> pd.DataFrame:
    """Apply data reduction pipeline: groupby+agg, sort, top/bottom, max-categories.

    Order of operations:
      1. groupby + agg (if both provided)
      2. sort
      3. top / bottom N
      4. max_categories (group remainder into "Other")
    """
    y_primary = y_col[0] if isinstance(y_col, list) else y_col
    x_col = kwargs.get("x_col")
    groupby = kwargs.get("groupby")
    agg_func = kwargs.get("agg")
    top_n = kwargs.get("top")
    bottom_n = kwargs.get("bottom")
    sort_by = kwargs.get("sort_by")
    sort_order = kwargs.get("sort_order", "desc")
    max_categories = kwargs.get("max_categories")

    # 1. Aggregation
    if groupby and agg_func and groupby in df.columns:
        agg_map = {"mean": "mean", "sum": "sum", "median": "median",
                    "count": "count", "min": "min", "max": "max"}
        func = agg_map.get(agg_func, "mean")
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        agg_cols = [c for c in numeric_cols if c != groupby]
        if not agg_cols:
            agg_cols = [y_primary] if y_primary in df.columns else []
        df = df.groupby(groupby, as_index=False)[agg_cols].agg(func)
        # The groupby column becomes the x-axis if x_col matches
        if x_col and x_col not in df.columns and groupby in df.columns:
            df = df.rename(columns={groupby: x_col})

    # 2. Sort
    sort_col = sort_by or y_primary
    if sort_col and sort_col in df.columns:
        ascending = sort_order == "asc"
        df = df.sort_values(sort_col, ascending=ascending).reset_index(drop=True)

    # 3. Top / Bottom N
    if top_n and top_n > 0:
        if sort_col in df.columns:
            df = df.nlargest(top_n, sort_col).reset_index(drop=True)
            # Re-sort for display
            df = df.sort_values(sort_col, ascending=False).reset_index(drop=True)
    elif bottom_n and bottom_n > 0:
        if sort_col in df.columns:
            df = df.nsmallest(bottom_n, sort_col).reset_index(drop=True)
            df = df.sort_values(sort_col, ascending=True).reset_index(drop=True)

    # 4. Max categories — group remaining into "Other"
    if max_categories and max_categories > 0 and x_col and x_col in df.columns:
        if len(df) > max_categories:
            top_df = df.head(max_categories)
            rest = df.iloc[max_categories:]
            other_row = {x_col: "Other"}
            for c in df.columns:
                if c == x_col:
                    continue
                if pd.api.types.is_numeric_dtype(df[c]):
                    other_row[c] = rest[c].sum()
                else:
                    other_row[c] = "Other"
            df = pd.concat([top_df, pd.DataFrame([other_row])], ignore_index=True)

    return df


def auto_figsize(n_categories: int, chart_type: str, base: list[float]) -> tuple[float, float]:
    """Compute figure size that adapts to the number of categories."""
    w, h = base
    if chart_type in ("bar", "line", "area", "timeseries"):
        if n_categories > 15:
            w = max(w, n_categories * 0.45)
        if n_categories > 30:
            w = max(w, n_categories * 0.35)
    elif chart_type == "hbar":
        if n_categories > 12:
            h = max(h, n_categories * 0.4)
    elif chart_type in ("small_multiples",):
        pass  # handled by its own logic
    # Cap at reasonable limits
    return (min(w, 30), min(h, 24))


def smart_tick_labels(ax: plt.Axes, labels, axis: str = "x",
                      max_label_len: int = MAX_LABEL_LEN) -> None:
    """Apply smart rotation, truncation, and spacing to tick labels."""
    if labels is None or len(labels) == 0:
        return

    n = len(labels)
    str_labels = [str(l) for l in labels]

    # Truncate long labels
    truncated = []
    for lab in str_labels:
        if len(lab) > max_label_len:
            truncated.append(lab[:max_label_len - 1] + "\u2026")
        else:
            truncated.append(lab)

    # Decide rotation
    max_len = max((len(l) for l in truncated), default=0)

    if axis == "x":
        if n > 30:
            rotation, ha = 90, "center"
        elif n > 15 or max_len > 10:
            rotation, ha = 45, "right"
        elif n > 8:
            rotation, ha = 30, "right"
        else:
            rotation, ha = 0, "center"

        ax.set_xticklabels(truncated, rotation=rotation, ha=ha)

        # If still too many, thin out ticks
        if n > 60:
            every = max(1, n // 30)
            for i, tick in enumerate(ax.xaxis.get_major_ticks()):
                if i % every != 0:
                    tick.set_visible(False)
    else:
        # Y-axis (hbar)
        ax.set_yticklabels(truncated)


def smart_legend(ax: plt.Axes, max_items: int = 15) -> None:
    """Render a legend that doesn't overflow; move outside if many items."""
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return
    n = len(handles)
    if n <= 6:
        ax.legend(frameon=False, fontsize=9)
    elif n <= max_items:
        ax.legend(frameon=False, fontsize=8, loc="upper left",
                  bbox_to_anchor=(1.02, 1), borderaxespad=0)
    else:
        # Too many — show first max_items and note the rest
        ax.legend(handles[:max_items], labels[:max_items],
                  frameon=False, fontsize=8, loc="upper left",
                  bbox_to_anchor=(1.02, 1), borderaxespad=0,
                  title=f"Showing {max_items} of {n}")


def group_small_slices(df: pd.DataFrame, x_col: str, y_col: str,
                       max_slices: int = 10) -> pd.DataFrame:
    """For pie/donut: group small slices into 'Other' to keep charts readable."""
    if len(df) <= max_slices:
        return df
    df_sorted = df.sort_values(y_col, ascending=False).reset_index(drop=True)
    top = df_sorted.head(max_slices - 1)
    rest = df_sorted.iloc[max_slices - 1:]
    other = pd.DataFrame([{x_col: "Other", y_col: rest[y_col].sum()}])
    return pd.concat([top, other], ignore_index=True)


def load_config(config_path: Path | None = None) -> dict:
    """Load visualization config from JSON file."""
    path = config_path or CONFIG_PATH
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_palette(config: dict, name: str | None = None) -> list[str]:
    """Get a color palette by name, defaulting to colorblind."""
    palettes = config.get("palettes", {})
    key = name or "colorblind"
    if key in palettes:
        return palettes[key]["colors"]
    return palettes.get("colorblind", {}).get("colors", sns.color_palette("colorblind").as_hex())


def apply_tufte_style(ax: plt.Axes, config: dict) -> None:
    """Apply Tufte-inspired minimal styling to an axes."""
    chart_cfg = config.get("chart", {})
    spine_cfg = chart_cfg.get("spines", {})
    grid_cfg = chart_cfg.get("grid", {})
    font_cfg = chart_cfg.get("fonts", {})

    # Spines
    for spine_name in ["top", "right", "left", "bottom"]:
        visible = spine_cfg.get(spine_name, spine_name in ("left", "bottom"))
        ax.spines[spine_name].set_visible(visible)
        if visible:
            ax.spines[spine_name].set_linewidth(spine_cfg.get("linewidth", 0.8))
            ax.spines[spine_name].set_color(spine_cfg.get("color", "#333333"))

    # Grid
    if grid_cfg.get("show", True):
        ax.grid(
            True,
            axis=grid_cfg.get("axis", "y"),
            linestyle=grid_cfg.get("style", "dashed"),
            alpha=grid_cfg.get("alpha", 0.3),
            color=grid_cfg.get("color", "#cccccc"),
            linewidth=grid_cfg.get("linewidth", 0.5),
        )
        ax.set_axisbelow(True)

    # Tick label styling
    tick_font = font_cfg.get("tick_label", {})
    ax.tick_params(
        labelsize=tick_font.get("size", 9),
        colors=tick_font.get("color", "#4d4d4d"),
    )


def set_title_and_labels(ax: plt.Axes, config: dict, title: str | None,
                         subtitle: str | None, xlabel: str | None, ylabel: str | None) -> None:
    """Set title, subtitle, and axis labels with Tufte fonts."""
    font_cfg = config.get("chart", {}).get("fonts", {})

    if title:
        title_font = font_cfg.get("title", {})
        ax.set_title(
            title,
            fontfamily=title_font.get("family", "Georgia"),
            fontsize=title_font.get("size", 16),
            fontweight=title_font.get("weight", "bold"),
            color=title_font.get("color", "#1a1a1a"),
            pad=20 if subtitle else 10,
            loc="left",
        )

    if subtitle:
        sub_font = font_cfg.get("subtitle", {})
        ax.text(
            0.0, 1.02, subtitle,
            transform=ax.transAxes,
            fontfamily=sub_font.get("family", "Georgia"),
            fontsize=sub_font.get("size", 12),
            color=sub_font.get("color", "#4d4d4d"),
            ha="left", va="bottom",
        )

    if xlabel:
        label_font = font_cfg.get("axis_label", {})
        ax.set_xlabel(
            xlabel,
            fontfamily=label_font.get("family", "Arial"),
            fontsize=label_font.get("size", 11),
            color=label_font.get("color", "#333333"),
        )
    if ylabel:
        label_font = font_cfg.get("axis_label", {})
        ax.set_ylabel(
            ylabel,
            fontfamily=label_font.get("family", "Arial"),
            fontsize=label_font.get("size", 11),
            color=label_font.get("color", "#333333"),
        )


def add_trend_line(ax: plt.Axes, x_vals: np.ndarray, y_vals: np.ndarray,
                   config: dict, method: str = "linear", degree: int = 2) -> None:
    """Add a trend line with optional R^2 annotation."""
    stat_cfg = config.get("statistics", {})
    trend_cfg = stat_cfg.get("trend_line", {})
    annot_cfg = stat_cfg.get("annotation", {})

    mask = np.isfinite(x_vals) & np.isfinite(y_vals)
    x_clean, y_clean = x_vals[mask], y_vals[mask]
    if len(x_clean) < 3:
        return

    x_sorted = np.sort(x_clean)
    x_line = np.linspace(x_sorted.min(), x_sorted.max(), 200)

    if method == "linear":
        slope, intercept, r_value, p_value, _ = stats.linregress(x_clean, y_clean)
        y_line = slope * x_line + intercept
        label = f"R\u00b2={r_value**2:.3f}, p={p_value:.2e}"
    else:
        coeffs = np.polyfit(x_clean, y_clean, degree)
        poly = np.poly1d(coeffs)
        y_line = poly(x_line)
        y_pred = poly(x_clean)
        ss_res = np.sum((y_clean - y_pred) ** 2)
        ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0
        label = f"R\u00b2={r2:.3f} (poly deg={degree})"

    ax.plot(
        x_line, y_line,
        color=trend_cfg.get("color", "#999999"),
        linestyle=trend_cfg.get("linestyle", "--"),
        linewidth=trend_cfg.get("linewidth", 1.0),
        alpha=trend_cfg.get("alpha", 0.7),
        zorder=5,
    )

    # Confidence band
    band_cfg = stat_cfg.get("confidence_band", {})
    if method == "linear" and band_cfg.get("alpha", 0.15) > 0:
        n = len(x_clean)
        se = np.sqrt(np.sum((y_clean - (slope * x_clean + intercept)) ** 2) / (n - 2))
        t_val = stats.t.ppf(0.975, n - 2)
        x_mean = np.mean(x_clean)
        x_var = np.sum((x_clean - x_mean) ** 2)
        margin = t_val * se * np.sqrt(1 / n + (x_line - x_mean) ** 2 / x_var)
        band_color = band_cfg.get("color") or trend_cfg.get("color", "#999999")
        ax.fill_between(
            x_line, y_line - margin, y_line + margin,
            alpha=band_cfg.get("alpha", 0.15),
            color=band_color,
            zorder=4,
        )

    ax.annotate(
        label,
        xy=(0.98, 0.02), xycoords="axes fraction",
        ha="right", va="bottom",
        fontsize=annot_cfg.get("fontsize", 9),
        color=annot_cfg.get("color", "#666666"),
    )


def apply_highlights(ax: plt.Axes, df: pd.DataFrame, highlights: list[dict],
                     config: dict, x_col: str, y_col: str) -> None:
    """Render highlight overlays on the chart."""
    hl_cfg = config.get("highlights", {})

    for hl in highlights:
        idx = hl.get("index")
        style = hl.get("suggested_style", "annotation_arrow")
        label = hl.get("label", "")
        styles = [style] if style != "combo" else hl_cfg.get("combo", {}).get("styles", ["color_shift", "annotation_arrow"])

        if idx is None or idx >= len(df):
            continue

        x_val = df[x_col].iloc[idx]
        y_val = df[y_col].iloc[idx]

        # Convert categorical x to position index for bar-like charts
        try:
            x_pos = float(x_val)
        except (ValueError, TypeError):
            x_pos = idx

        for s in styles:
            style_cfg = hl_cfg.get(s, {})

            if s == "halo_ring":
                ax.scatter(
                    [x_pos], [y_val],
                    s=style_cfg.get("size_multiplier", 3.0) * 100,
                    facecolors="none",
                    edgecolors=style_cfg.get("color", "#D55E00"),
                    linewidths=style_cfg.get("linewidth", 2.0),
                    alpha=style_cfg.get("alpha", 0.4),
                    zorder=10,
                )

            elif s == "color_shift":
                ax.scatter(
                    [x_pos], [y_val],
                    s=80,
                    color=style_cfg.get("color", "#D55E00"),
                    alpha=style_cfg.get("alpha", 1.0),
                    zorder=10,
                )

            elif s == "size_boost":
                ax.scatter(
                    [x_pos], [y_val],
                    s=style_cfg.get("size_multiplier", 2.5) * 60,
                    color=style_cfg.get("color", "#D55E00"),
                    alpha=0.8,
                    zorder=10,
                )

            elif s == "glow":
                ax.scatter(
                    [x_pos], [y_val],
                    s=style_cfg.get("size_multiplier", 5.0) * 100,
                    color=style_cfg.get("color", "#F0E442"),
                    alpha=style_cfg.get("alpha", 0.3),
                    zorder=3,
                )

            elif s == "annotation_arrow":
                offset = style_cfg.get("offset", [30, 30])
                ax.annotate(
                    label or f"{y_val}",
                    xy=(x_pos, y_val),
                    xytext=(offset[0], offset[1]),
                    textcoords="offset points",
                    fontsize=style_cfg.get("fontsize", 9),
                    color=style_cfg.get("color", "#333333"),
                    arrowprops=dict(
                        arrowstyle=style_cfg.get("arrowstyle", "->"),
                        color=style_cfg.get("color", "#333333"),
                        connectionstyle=style_cfg.get("connectionstyle", "arc3,rad=0.2"),
                    ),
                    zorder=15,
                )

            elif s == "band_shade":
                width = style_cfg.get("width", 0.5)
                ax.axvspan(
                    x_pos - width / 2, x_pos + width / 2,
                    color=style_cfg.get("color", "#D55E00"),
                    alpha=style_cfg.get("alpha", 0.1),
                    zorder=1,
                )

            elif s == "marker_change":
                ax.scatter(
                    [x_pos], [y_val],
                    s=style_cfg.get("size_multiplier", 1.8) * 60,
                    marker=style_cfg.get("marker", "D"),
                    color=hl_cfg.get("color_shift", {}).get("color", "#D55E00"),
                    zorder=10,
                )


# ---------------------------------------------------------------------------
# Chart type renderers
# ---------------------------------------------------------------------------

def chart_line(ax: plt.Axes, df: pd.DataFrame, x: str, y: str | list[str],
               config: dict, palette: list[str], **kwargs) -> None:
    """Render a line chart."""
    ct = config.get("chart_types", {}).get("line", {})
    y_cols = y if isinstance(y, list) else [y]

    # Suppress markers for large datasets to avoid clutter
    n_points = len(df)
    marker = ct.get("marker", "o") if n_points <= 50 else None
    markersize = ct.get("markersize", 4)

    for i, col in enumerate(y_cols):
        color = palette[i % len(palette)]
        ax.plot(
            df[x], df[col],
            color=color,
            linewidth=ct.get("linewidth", 2.0),
            marker=marker,
            markersize=markersize,
            alpha=ct.get("alpha", 1.0),
            label=col,
        )
    if len(y_cols) > 1:
        smart_legend(ax)

    # Smart x-tick labels for categorical x-axis
    if not pd.api.types.is_numeric_dtype(df[x]):
        positions = np.arange(len(df))
        ax.set_xticks(positions)
        smart_tick_labels(ax, df[x].values, axis="x")


def chart_bar(ax: plt.Axes, df: pd.DataFrame, x: str, y: str | list[str],
              config: dict, palette: list[str], **kwargs) -> None:
    """Render a vertical bar chart."""
    ct = config.get("chart_types", {}).get("bar", {})
    y_cols = y if isinstance(y, list) else [y]
    n = len(y_cols)
    width = ct.get("width", 0.7) / n
    positions = np.arange(len(df))

    for i, col in enumerate(y_cols):
        offset = (i - n / 2 + 0.5) * width
        ax.bar(
            positions + offset,
            df[col],
            width=width,
            color=palette[i % len(palette)],
            edgecolor=ct.get("edgecolor", "#ffffff"),
            linewidth=ct.get("edgewidth", 0.5),
            alpha=ct.get("alpha", 0.9),
            label=col,
        )

    ax.set_xticks(positions)
    smart_tick_labels(ax, df[x].values, axis="x")
    if n > 1:
        smart_legend(ax)


def chart_hbar(ax: plt.Axes, df: pd.DataFrame, x: str, y: str,
               config: dict, palette: list[str], **kwargs) -> None:
    """Render a horizontal bar chart."""
    ct = config.get("chart_types", {}).get("hbar", {})
    positions = np.arange(len(df))
    ax.barh(
        positions,
        df[y],
        height=ct.get("height", 0.7),
        color=[palette[i % len(palette)] for i in range(len(df))],
        edgecolor=ct.get("edgecolor", "#ffffff"),
        linewidth=ct.get("edgewidth", 0.5),
        alpha=ct.get("alpha", 0.9),
    )
    ax.set_yticks(positions)
    smart_tick_labels(ax, df[x].values, axis="y")
    ax.invert_yaxis()


def chart_scatter(ax: plt.Axes, df: pd.DataFrame, x: str, y: str,
                  config: dict, palette: list[str], **kwargs) -> None:
    """Render a scatter plot with optional color grouping."""
    ct = config.get("chart_types", {}).get("scatter", {})
    color_col = kwargs.get("color")

    # Reduce alpha for very large datasets to avoid overplotting
    n_points = len(df)
    alpha = ct.get("alpha", 0.7)
    size = ct.get("size", 40)
    if n_points > 500:
        alpha = min(alpha, 0.4)
        size = max(15, size * 0.6)
    elif n_points > 200:
        alpha = min(alpha, 0.5)
        size = max(20, size * 0.8)

    if color_col and color_col in df.columns:
        groups = df[color_col].unique()
        for i, group in enumerate(groups):
            mask = df[color_col] == group
            ax.scatter(
                df.loc[mask, x], df.loc[mask, y],
                s=size,
                color=palette[i % len(palette)],
                alpha=alpha,
                edgecolors=ct.get("edgecolor", "#ffffff"),
                linewidths=ct.get("edgewidth", 0.5),
                label=str(group),
            )
        smart_legend(ax)
    else:
        ax.scatter(
            df[x], df[y],
            s=size,
            color=palette[0],
            alpha=alpha,
            edgecolors=ct.get("edgecolor", "#ffffff"),
            linewidths=ct.get("edgewidth", 0.5),
        )


def chart_histogram(ax: plt.Axes, df: pd.DataFrame, x: str, y: str | None,
                    config: dict, palette: list[str], **kwargs) -> None:
    """Render a histogram."""
    ct = config.get("chart_types", {}).get("histogram", {})
    col = y or x
    ax.hist(
        df[col].dropna(),
        bins=kwargs.get("bins") or ct.get("bins", 30),
        color=palette[0],
        edgecolor=ct.get("edgecolor", "#ffffff"),
        linewidth=ct.get("edgewidth", 0.5),
        alpha=ct.get("alpha", 0.8),
    )


def chart_heatmap(ax: plt.Axes, df: pd.DataFrame, x: str | None, y: str | None,
                  config: dict, palette: list[str], **kwargs) -> None:
    """Render a heatmap from numeric columns."""
    ct = config.get("chart_types", {}).get("heatmap", {})
    numeric = df.select_dtypes(include=[np.number])
    if x and y:
        pivot = df.pivot_table(index=y, columns=x, aggfunc="mean")
        if pivot.columns.nlevels > 1:
            pivot.columns = pivot.columns.droplevel(0)
        data = pivot
    else:
        data = numeric.corr() if numeric.shape[1] > 1 else numeric

    sns.heatmap(
        data, ax=ax,
        cmap=ct.get("cmap", "YlOrRd"),
        annot=ct.get("annot", True),
        fmt=ct.get("fmt", ".1f"),
        linewidths=ct.get("linewidths", 0.5),
        linecolor=ct.get("linecolor", "#ffffff"),
        cbar_kws={"shrink": 0.8},
    )


def chart_box(ax: plt.Axes, df: pd.DataFrame, x: str | None, y: str,
              config: dict, palette: list[str], **kwargs) -> None:
    """Render a box plot."""
    ct = config.get("chart_types", {}).get("box", {})
    if x and x in df.columns:
        groups = df[x].unique()
        data = [df.loc[df[x] == g, y].dropna().values for g in groups]
        bp = ax.boxplot(
            data,
            widths=ct.get("width", 0.6),
            patch_artist=True,
            flierprops=dict(markersize=ct.get("fliersize", 4)),
        )
        for i, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(palette[i % len(palette)])
            patch.set_alpha(0.8)
        smart_tick_labels(ax, groups, axis="x")
    else:
        cols = [y] if isinstance(y, str) else y
        data = [df[c].dropna().values for c in cols]
        bp = ax.boxplot(
            data,
            widths=ct.get("width", 0.6),
            patch_artist=True,
            flierprops=dict(markersize=ct.get("fliersize", 4)),
        )
        for i, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(palette[i % len(palette)])
            patch.set_alpha(0.8)
        ax.set_xticklabels(cols)


def chart_pie(ax: plt.Axes, df: pd.DataFrame, x: str, y: str,
              config: dict, palette: list[str], **kwargs) -> None:
    """Render a pie chart — auto-groups small slices into 'Other'."""
    ct = config.get("chart_types", {}).get("pie", {})
    max_slices = kwargs.get("max_categories") or 10
    df = group_small_slices(df, x, y, max_slices=max_slices)
    colors = [palette[i % len(palette)] for i in range(len(df))]
    ax.pie(
        df[y],
        labels=df[x],
        colors=colors,
        startangle=ct.get("startangle", 90),
        autopct=ct.get("autopct", "%1.1f%%"),
        pctdistance=ct.get("pctdistance", 0.75),
        shadow=ct.get("shadow", False),
        textprops={"fontsize": 9},
    )
    ax.set_aspect("equal")


def chart_donut(ax: plt.Axes, df: pd.DataFrame, x: str, y: str,
                config: dict, palette: list[str], **kwargs) -> None:
    """Render a donut chart — auto-groups small slices into 'Other'."""
    ct = config.get("chart_types", {}).get("donut", {})
    max_slices = kwargs.get("max_categories") or 10
    df = group_small_slices(df, x, y, max_slices=max_slices)
    colors = [palette[i % len(palette)] for i in range(len(df))]
    wedge_width = ct.get("wedgeprops_width", 0.4)
    wedges, texts, autotexts = ax.pie(
        df[y],
        labels=df[x],
        colors=colors,
        startangle=ct.get("startangle", 90),
        autopct=ct.get("autopct", "%1.1f%%"),
        pctdistance=ct.get("pctdistance", 0.82),
        shadow=ct.get("shadow", False),
        wedgeprops=dict(width=wedge_width),
        textprops={"fontsize": 9},
    )
    ax.set_aspect("equal")


def chart_area(ax: plt.Axes, df: pd.DataFrame, x: str, y: str | list[str],
               config: dict, palette: list[str], **kwargs) -> None:
    """Render an area chart (stacked or single)."""
    ct = config.get("chart_types", {}).get("area", {})
    y_cols = y if isinstance(y, list) else [y]

    if kwargs.get("stacked") and len(y_cols) > 1:
        ax.stackplot(
            df[x],
            *[df[c] for c in y_cols],
            labels=y_cols,
            colors=palette[:len(y_cols)],
            alpha=ct.get("alpha", 0.4),
        )
    else:
        for i, col in enumerate(y_cols):
            ax.fill_between(
                df[x], df[col],
                alpha=ct.get("alpha", 0.4),
                color=palette[i % len(palette)],
                label=col,
            )
            ax.plot(
                df[x], df[col],
                color=palette[i % len(palette)],
                linewidth=ct.get("linewidth", 1.5),
            )
    if len(y_cols) > 1:
        smart_legend(ax)


def chart_bubble(ax: plt.Axes, df: pd.DataFrame, x: str, y: str,
                 config: dict, palette: list[str], **kwargs) -> None:
    """Render a bubble chart — requires a size column."""
    ct = config.get("chart_types", {}).get("bubble", {})
    size_col = kwargs.get("size")
    color_col = kwargs.get("color")

    if size_col and size_col in df.columns:
        s_range = ct.get("size_range", [20, 500])
        s_vals = df[size_col].astype(float)
        s_min, s_max = s_vals.min(), s_vals.max()
        if s_max > s_min:
            sizes = s_range[0] + (s_vals - s_min) / (s_max - s_min) * (s_range[1] - s_range[0])
        else:
            sizes = (s_range[0] + s_range[1]) / 2
    else:
        sizes = 80

    if color_col and color_col in df.columns:
        groups = df[color_col].unique()
        for i, group in enumerate(groups):
            mask = df[color_col] == group
            ax.scatter(
                df.loc[mask, x], df.loc[mask, y],
                s=sizes[mask] if hasattr(sizes, '__iter__') else sizes,
                color=palette[i % len(palette)],
                alpha=ct.get("alpha", 0.6),
                edgecolors=ct.get("edgecolor", "#ffffff"),
                linewidths=ct.get("edgewidth", 0.5),
                label=str(group),
            )
        smart_legend(ax)
    else:
        ax.scatter(
            df[x], df[y],
            s=sizes,
            color=palette[0],
            alpha=ct.get("alpha", 0.6),
            edgecolors=ct.get("edgecolor", "#ffffff"),
            linewidths=ct.get("edgewidth", 0.5),
        )


def chart_timeseries(ax: plt.Axes, df: pd.DataFrame, x: str, y: str | list[str],
                     config: dict, palette: list[str], **kwargs) -> None:
    """Render a time-series line chart with date formatting."""
    ct = config.get("chart_types", {}).get("timeseries", {})
    y_cols = y if isinstance(y, list) else [y]

    # Parse dates
    dates = pd.to_datetime(df[x], errors="coerce")

    for i, col in enumerate(y_cols):
        ax.plot(
            dates, df[col],
            color=palette[i % len(palette)],
            linewidth=ct.get("linewidth", 2.0),
            marker=ct.get("marker"),
            alpha=ct.get("alpha", 1.0),
            label=col,
        )

    # Auto-format dates
    ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.AutoDateLocator()))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")

    if len(y_cols) > 1:
        smart_legend(ax)


def chart_small_multiples(fig: plt.Figure, df: pd.DataFrame, x: str, y: str,
                          config: dict, palette: list[str], **kwargs) -> None:
    """Render small multiples — faceted by a grouping column."""
    ct = config.get("chart_types", {}).get("small_multiples", {})
    group_col = kwargs.get("group") or kwargs.get("color")
    if not group_col or group_col not in df.columns:
        print("Error: small_multiples requires --group COL", file=sys.stderr)
        sys.exit(1)

    groups = df[group_col].unique()
    max_cols = ct.get("max_cols", 4)
    n_groups = len(groups)
    n_cols = min(n_groups, max_cols)
    n_rows = (n_groups + n_cols - 1) // n_cols
    subplot_size = ct.get("subplot_size", [3, 2.5])

    fig.set_size_inches(subplot_size[0] * n_cols, subplot_size[1] * n_rows)
    fig.clear()

    axes = fig.subplots(n_rows, n_cols, sharex=ct.get("share_x", True),
                        sharey=ct.get("share_y", True), squeeze=False)

    for i, group in enumerate(groups):
        row, col = divmod(i, n_cols)
        ax = axes[row][col]
        subset = df[df[group_col] == group]
        ax.plot(subset[x], subset[y], color=palette[i % len(palette)], linewidth=1.5)
        ax.set_title(str(group), fontsize=10, fontfamily="Georgia")
        apply_tufte_style(ax, config)

    # Hide empty subplots
    for i in range(n_groups, n_rows * n_cols):
        row, col = divmod(i, n_cols)
        axes[row][col].set_visible(False)

    fig.tight_layout()


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

CHART_RENDERERS = {
    "line": chart_line,
    "bar": chart_bar,
    "hbar": chart_hbar,
    "scatter": chart_scatter,
    "histogram": chart_histogram,
    "heatmap": chart_heatmap,
    "box": chart_box,
    "pie": chart_pie,
    "donut": chart_donut,
    "area": chart_area,
    "bubble": chart_bubble,
    "timeseries": chart_timeseries,
}


def generate(data_path: Path, output_path: Path, chart_type: str,
             x_col: str, y_col: str | None, config: dict, **kwargs) -> None:
    """Generate a chart from data file to output image."""
    # Load data
    ext = data_path.suffix.lower()
    if ext == ".json":
        df = pd.read_json(data_path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(data_path, engine="openpyxl")
    else:
        df = pd.read_csv(data_path)

    original_rows = len(df)

    # Multi-column y support (comma-separated)
    y_cols = y_col
    if y_col and "," in y_col:
        y_cols = [c.strip() for c in y_col.split(",")]

    # Validate columns exist (before reduction, since groupby may rename)
    all_cols = [x_col] if x_col else []
    if isinstance(y_cols, list):
        all_cols.extend(y_cols)
    elif y_cols:
        all_cols.append(y_cols)
    for col_name in kwargs.get("extra_cols", []):
        if col_name:
            all_cols.append(col_name)

    # Only validate columns that aren't the groupby target (which may create x_col)
    groupby_col = kwargs.get("groupby")
    for c in all_cols:
        if c and c not in df.columns:
            # If using groupby that will produce this column, skip validation
            if groupby_col and groupby_col in df.columns:
                continue
            print(f"Error: Column '{c}' not found. Available: {list(df.columns)}", file=sys.stderr)
            sys.exit(1)

    # ----- Data reduction pipeline -----
    has_reduction = any(kwargs.get(k) for k in ("agg", "groupby", "top", "bottom", "max_categories"))
    if has_reduction:
        df = reduce_data(df, y_cols or y_col, x_col=x_col, **kwargs)
        if len(df) < original_rows:
            print(f"Data reduced: {original_rows} → {len(df)} rows", file=sys.stderr)

    # ----- Auto-adjust figure size -----
    chart_cfg = config.get("chart", {})
    base_figsize = kwargs.get("figsize") or chart_cfg.get("figsize", [10, 6])
    dpi = kwargs.get("dpi") or chart_cfg.get("dpi", 150)

    # Only auto-scale if user didn't explicitly set figsize
    if not kwargs.get("figsize"):
        n_cats = len(df)
        figsize = auto_figsize(n_cats, chart_type, base_figsize)
    else:
        figsize = tuple(base_figsize)

    if chart_type == "small_multiples":
        fig = plt.figure(figsize=figsize, dpi=dpi, facecolor=chart_cfg.get("background", "#ffffff"))
        chart_small_multiples(fig, df, x_col, y_cols or y_col, config, get_palette(config, kwargs.get("palette")), **kwargs)
    else:
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi, facecolor=chart_cfg.get("background", "#ffffff"))
        ax.set_facecolor(chart_cfg.get("background", "#ffffff"))

        palette = get_palette(config, kwargs.get("palette"))
        # Remove non-renderer kwargs to avoid unexpected keyword args
        exclude_keys = {"palette", "figsize", "dpi", "extra_cols", "title", "subtitle",
                        "xlabel", "ylabel", "trend", "degree", "highlights",
                        "top", "bottom", "agg", "groupby", "sort_by", "sort_order",
                        "max_categories", "x_col"}
        render_kwargs = {k: v for k, v in kwargs.items() if k not in exclude_keys}
        renderer = CHART_RENDERERS.get(chart_type)
        if not renderer:
            print(f"Error: Unknown chart type '{chart_type}'", file=sys.stderr)
            print(f"Available: {', '.join(sorted(CHART_RENDERERS.keys()))}", file=sys.stderr)
            sys.exit(1)

        renderer(ax, df, x_col, y_cols or y_col, config, palette, **render_kwargs)

        # Styling
        apply_tufte_style(ax, config)
        set_title_and_labels(
            ax, config,
            title=kwargs.get("title"),
            subtitle=kwargs.get("subtitle"),
            xlabel=kwargs.get("xlabel", x_col),
            ylabel=kwargs.get("ylabel", y_cols if isinstance(y_cols, str) else (y_cols[0] if y_cols else None)),
        )

        # Trend line
        if kwargs.get("trend"):
            try:
                x_num = pd.to_numeric(df[x_col], errors="coerce").values
                y_num = pd.to_numeric(df[y_cols] if isinstance(y_cols, str) else df[y_cols[0]], errors="coerce").values
                add_trend_line(ax, x_num, y_num, config,
                               method=kwargs["trend"],
                               degree=kwargs.get("degree", 2))
            except Exception as e:
                print(f"Warning: Could not add trend line: {e}", file=sys.stderr)

        # Highlights
        highlights_path = kwargs.get("highlights")
        if highlights_path:
            with open(highlights_path, "r", encoding="utf-8") as f:
                highlights = json.load(f)
            y_for_hl = y_cols if isinstance(y_cols, str) else y_cols[0]
            apply_highlights(ax, df, highlights, config, x_col, y_for_hl)

    plt.tight_layout()

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = output_path.suffix.lstrip(".").lower()
    if fmt == "svg":
        fig.savefig(output_path, format="svg", bbox_inches="tight", facecolor=fig.get_facecolor())
    elif fmt == "pdf":
        fig.savefig(output_path, format="pdf", bbox_inches="tight", facecolor=fig.get_facecolor())
    else:
        fig.savefig(output_path, format="png", bbox_inches="tight", dpi=dpi, facecolor=fig.get_facecolor())

    plt.close(fig)
    print(f"Chart saved to {output_path} ({chart_type}, {len(df)} data points)")


def main():
    parser = argparse.ArgumentParser(
        description="Generate publication-quality charts from structured data."
    )
    parser.add_argument("data", type=Path, help="Input data file (CSV, JSON, Excel)")
    parser.add_argument("output", type=Path, help="Output image file (PNG, SVG, PDF)")
    parser.add_argument("--type", required=True, dest="chart_type",
                        choices=list(CHART_RENDERERS.keys()) + ["small_multiples"],
                        help="Chart type")
    parser.add_argument("--x", required=True, dest="x_col", help="X-axis column name")
    parser.add_argument("--y", dest="y_col", help="Y-axis column name (comma-separated for multi-series)")
    parser.add_argument("--title", help="Chart title")
    parser.add_argument("--subtitle", help="Chart subtitle")
    parser.add_argument("--xlabel", help="X-axis label (default: column name)")
    parser.add_argument("--ylabel", help="Y-axis label (default: column name)")
    parser.add_argument("--palette", choices=["colorblind", "sequential", "diverging", "categorical", "monochrome"],
                        help="Color palette name")
    parser.add_argument("--color", help="Column for color grouping (scatter, bubble)")
    parser.add_argument("--size", help="Column for size encoding (bubble)")
    parser.add_argument("--group", help="Column for faceting (small_multiples)")
    parser.add_argument("--trend", choices=["linear", "polynomial"], help="Add trend line")
    parser.add_argument("--degree", type=int, default=2, help="Polynomial degree for trend line")
    parser.add_argument("--highlights", type=Path, help="Path to highlights JSON file")
    parser.add_argument("--stacked", action="store_true", help="Use stacked area chart")
    parser.add_argument("--bins", type=int, help="Number of bins for histogram")
    parser.add_argument("--figsize", nargs=2, type=float, metavar=("W", "H"), help="Figure size in inches")
    parser.add_argument("--dpi", type=int, help="Output resolution")
    parser.add_argument("--config", type=Path, help="Path to custom config JSON")

    # Data reduction arguments
    data_group = parser.add_argument_group("data reduction",
                                           "Filter, aggregate, and limit data before plotting")
    data_group.add_argument("--top", type=int, metavar="N",
                            help="Show only the top N rows by y-value (descending)")
    data_group.add_argument("--bottom", type=int, metavar="N",
                            help="Show only the bottom N rows by y-value (ascending)")
    data_group.add_argument("--agg", choices=["mean", "sum", "median", "count", "min", "max"],
                            help="Aggregation function (use with --groupby)")
    data_group.add_argument("--groupby", metavar="COL",
                            help="Column to group by before aggregation")
    data_group.add_argument("--sort-by", dest="sort_by", metavar="COL",
                            help="Column to sort by (default: y-column)")
    data_group.add_argument("--sort-order", dest="sort_order", choices=["asc", "desc"],
                            default="desc", help="Sort direction (default: desc)")
    data_group.add_argument("--max-categories", dest="max_categories", type=int, metavar="N",
                            help="Max categories to show; remainder grouped as 'Other'")

    args = parser.parse_args()
    config = load_config(args.config)

    extra_cols = [args.color, args.size, args.group]

    generate(
        data_path=args.data,
        output_path=args.output,
        chart_type=args.chart_type,
        x_col=args.x_col,
        y_col=args.y_col,
        config=config,
        title=args.title,
        subtitle=args.subtitle,
        xlabel=args.xlabel,
        ylabel=args.ylabel,
        palette=args.palette,
        color=args.color,
        size=args.size,
        group=args.group,
        trend=args.trend,
        degree=args.degree,
        highlights=args.highlights,
        stacked=args.stacked,
        bins=args.bins,
        figsize=args.figsize,
        dpi=args.dpi,
        extra_cols=extra_cols,
        top=args.top,
        bottom=args.bottom,
        agg=args.agg,
        groupby=args.groupby,
        sort_by=args.sort_by,
        sort_order=args.sort_order,
        max_categories=args.max_categories,
    )


if __name__ == "__main__":
    main()
