"""Visualization layer: static (matplotlib) and interactive (Plotly) plots.

For each of the 10 figures referenced in the closure report this module
exposes two functions:

    plot_<name>_static(...)    -> matplotlib.figure.Figure  (saved to disk)
    plot_<name>_interactive(...) -> plotly.graph_objects.Figure

Both versions consume the *same* inputs (DataFrames and result objects
produced by eda, anomaly, stats, roi). Notebooks display the interactive
versions; the static versions feed reports/figures/ for the README,
documentation site, and the PDF report.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from plotly.subplots import make_subplots

from panificadora.anomaly import combined_anomaly_report, feature_importance_energy
from panificadora.config import (
    COLOR_NEUTRAL,
    COLOR_POST,
    COLOR_PRE,
    FIGURE_DPI,
    FIGURES_DIR,
    INTERVENTION_CUTOFF,
    PERIOD_POST,
    PERIOD_PRE,
)
from panificadora.eda import rolling_intensity
from panificadora.roi import ROIResult, payback_curve
from panificadora.stats import (
    RegressionFit,
    compare_all_variables,
    fit_linear_trend,
    project_trend,
)

# ============================================================
# Style configuration
# ============================================================

PLOTLY_TEMPLATE = "plotly_white"


def configure_style() -> None:
    """Apply project-wide matplotlib + seaborn style settings."""
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(
        {
            "figure.dpi": 100,
            "savefig.dpi": FIGURE_DPI,
            "savefig.bbox": "tight",
            "font.family": "DejaVu Sans",
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
        }
    )


def save_figure(fig: plt.Figure, name: str, subdir: Path | None = None) -> Path:
    """Save a matplotlib figure to reports/figures/ and return its path.

    Args:
        fig: Matplotlib Figure.
        name: Filename (with or without .png extension).
        subdir: Optional subdirectory inside FIGURES_DIR.

    Returns:
        Final saved path.
    """
    target_dir = FIGURES_DIR if subdir is None else FIGURES_DIR / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    if not name.endswith(".png"):
        name = f"{name}.png"
    out_path = target_dir / name

    fig.savefig(out_path, dpi=FIGURE_DPI, bbox_inches="tight")
    return out_path


def _period_palette() -> dict[str, str]:
    """Consistent color palette for Pre/Post comparisons."""
    return {PERIOD_PRE: COLOR_PRE, PERIOD_POST: COLOR_POST}


def _add_cutoff_line_mpl(ax: plt.Axes, label: str = "Intervention") -> None:
    """Draw the intervention cutoff as a vertical dashed line on a matplotlib axis."""
    ax.axvline(
        INTERVENTION_CUTOFF,
        color="black",
        linestyle="--",
        linewidth=1.2,
        alpha=0.6,
        label=label,
    )


def _add_period_shading_mpl(ax: plt.Axes, df: pd.DataFrame) -> None:
    """Shade Pre (red) and Post (green) regions on a time-series axis."""
    pre = df[df["period"] == PERIOD_PRE]
    post = df[df["period"] == PERIOD_POST]
    if len(pre) and len(post):
        ax.axvspan(pre["fecha"].min(), INTERVENTION_CUTOFF, color=COLOR_PRE, alpha=0.07)
        ax.axvspan(INTERVENTION_CUTOFF, post["fecha"].max(), color=COLOR_POST, alpha=0.07)


# ============================================================
# Figure 1 — Time series of energy consumption and production
# ============================================================


def plot_timeseries_static(df: pd.DataFrame) -> plt.Figure:
    """Figure 1 (static): kWh and kg over time with Pre/Post shading."""
    configure_style()
    fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True)

    axes[0].plot(df["fecha"], df["consumo_kwh"], marker="o", color=COLOR_NEUTRAL, lw=2)
    axes[0].set_ylabel("Energy (kWh)")
    axes[0].set_title("Figure 1 — Monthly Energy Consumption & Production")
    _add_period_shading_mpl(axes[0], df)
    _add_cutoff_line_mpl(axes[0])
    axes[0].legend(loc="upper right")

    axes[1].plot(df["fecha"], df["produccion_kg"], marker="s", color="#8E44AD", lw=2)
    axes[1].set_ylabel("Production (kg)")
    axes[1].set_xlabel("Month")
    _add_period_shading_mpl(axes[1], df)
    _add_cutoff_line_mpl(axes[1])

    fig.tight_layout()
    return fig


def plot_timeseries_interactive(df: pd.DataFrame) -> go.Figure:
    """Figure 1 (interactive): kWh and kg over time."""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Energy Consumption (kWh)", "Production (kg)"),
        vertical_spacing=0.12,
    )

    fig.add_trace(
        go.Scatter(
            x=df["fecha"],
            y=df["consumo_kwh"],
            mode="lines+markers",
            name="kWh",
            line=dict(color=COLOR_NEUTRAL, width=2),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["fecha"],
            y=df["produccion_kg"],
            mode="lines+markers",
            name="kg",
            line=dict(color="#8E44AD", width=2),
        ),
        row=2,
        col=1,
    )

    for r in (1, 2):
        fig.add_vline(
            x=INTERVENTION_CUTOFF,
            line_dash="dash",
            line_color="black",
            opacity=0.6,
            row=r,
            col=1,
        )

    fig.update_layout(
        height=550,
        template=PLOTLY_TEMPLATE,
        title="Figure 1 — Monthly Energy Consumption & Production",
        showlegend=False,
    )
    return fig


# ============================================================
# Figure 2 — Boxplots Pre vs Post
# ============================================================

KPIS_FOR_BOXPLOT: list[str] = [
    "consumo_kwh",
    "produccion_kg",
    "fallas_maquina",
    "tiempo_inactividad_horas",
    "intensidad_kwh_kg",
    "margen_bruto_pct",
]


def plot_boxplots_static(df: pd.DataFrame) -> plt.Figure:
    """Figure 2 (static): Pre vs Post boxplots for each KPI."""
    configure_style()
    n = len(KPIS_FOR_BOXPLOT)
    cols = 3
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(13, 7))
    axes = axes.flatten()

    palette = _period_palette()

    for i, kpi in enumerate(KPIS_FOR_BOXPLOT):
        sns.boxplot(
            data=df,
            x="period",
            y=kpi,
            hue="period",
            order=[PERIOD_PRE, PERIOD_POST],
            palette=palette,
            legend=False,
            ax=axes[i],
            showmeans=True,
            meanprops={"marker": "D", "markerfacecolor": "white", "markeredgecolor": "black"},
        )
        axes[i].set_title(kpi.replace("_", " ").title())
        axes[i].set_xlabel("")

    for j in range(n, len(axes)):
        axes[j].axis("off")

    fig.suptitle("Figure 2 — Distribution of KPIs: Pre vs Post Intervention", fontsize=14, y=1.02)
    fig.tight_layout()
    return fig


def plot_boxplots_interactive(df: pd.DataFrame) -> go.Figure:
    """Figure 2 (interactive): Pre vs Post boxplots."""
    melted = df.melt(
        id_vars=["period"],
        value_vars=KPIS_FOR_BOXPLOT,
        var_name="KPI",
        value_name="value",
    )
    fig = px.box(
        melted,
        x="period",
        y="value",
        color="period",
        facet_col="KPI",
        facet_col_wrap=3,
        category_orders={"period": [PERIOD_PRE, PERIOD_POST]},
        color_discrete_map=_period_palette(),
        template=PLOTLY_TEMPLATE,
        title="Figure 2 — Distribution of KPIs: Pre vs Post Intervention",
    )
    fig.update_yaxes(matches=None)
    fig.for_each_annotation(
        lambda a: a.update(text=a.text.split("=")[-1].replace("_", " ").title())
    )
    fig.update_layout(height=600, showlegend=False)
    return fig


# ============================================================
# Figure 3 — Correlation matrix
# ============================================================


def plot_correlation_static(corr: pd.DataFrame) -> plt.Figure:
    """Figure 3 (static): Pearson correlation heatmap."""
    configure_style()
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        cbar_kws={"label": "Pearson r"},
        ax=ax,
    )
    ax.set_title("Figure 3 — Correlation Matrix of Operational Variables")
    fig.tight_layout()
    return fig


def plot_correlation_interactive(corr: pd.DataFrame) -> go.Figure:
    """Figure 3 (interactive): Pearson correlation heatmap."""
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdYlGn",
        zmin=-1,
        zmax=1,
        aspect="auto",
        template=PLOTLY_TEMPLATE,
        title="Figure 3 — Correlation Matrix of Operational Variables",
    )
    fig.update_layout(height=600)
    return fig


# ============================================================
# Figure 4 — Energy intensity (kWh/kg) over time
# ============================================================


def plot_intensity_static(df: pd.DataFrame) -> plt.Figure:
    """Figure 4 (static): Energy intensity with 3-month moving average."""
    configure_style()
    fig, ax = plt.subplots(figsize=(11, 5))

    ax.plot(
        df["fecha"],
        df["intensidad_kwh_kg"],
        marker="o",
        color=COLOR_NEUTRAL,
        alpha=0.6,
        lw=1.5,
        label="Monthly kWh/kg",
    )
    ax.plot(
        df["fecha"],
        rolling_intensity(df, window=3),
        color="#E67E22",
        lw=2.5,
        label="3-month moving average",
    )

    _add_period_shading_mpl(ax, df)
    _add_cutoff_line_mpl(ax)

    ax.set_ylabel("Energy intensity (kWh/kg)")
    ax.set_xlabel("Month")
    ax.set_title("Figure 4 — Energy Intensity Over Time")
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


def plot_intensity_interactive(df: pd.DataFrame) -> go.Figure:
    """Figure 4 (interactive): Energy intensity over time."""
    smoothed = rolling_intensity(df, window=3)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["fecha"],
            y=df["intensidad_kwh_kg"],
            mode="lines+markers",
            name="Monthly kWh/kg",
            line=dict(color=COLOR_NEUTRAL, width=1.5),
            opacity=0.7,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["fecha"],
            y=smoothed,
            mode="lines",
            name="3-month MA",
            line=dict(color="#E67E22", width=3),
        )
    )
    fig.add_vline(x=INTERVENTION_CUTOFF, line_dash="dash", line_color="black", opacity=0.6)
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Figure 4 — Energy Intensity Over Time",
        yaxis_title="kWh/kg",
        height=450,
    )
    return fig


# ============================================================
# Figure 5 — Statistical tests: p-values & effect sizes
# ============================================================


def plot_stat_tests_static(results_df: pd.DataFrame) -> plt.Figure:
    """Figure 5 (static): p-values and Cohen's d per variable."""
    configure_style()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Left panel: p-values
    sorted_p = results_df.sort_values("p_value")
    colors = ["#27AE60" if v else "#C0392B" for v in sorted_p["significant"]]
    axes[0].barh(sorted_p.index, sorted_p["p_value"], color=colors)
    axes[0].axvline(0.05, color="black", linestyle="--", linewidth=1)
    axes[0].set_xlabel("p-value")
    axes[0].set_title("p-values (green = significant at α=0.05)")
    axes[0].invert_yaxis()

    # Right panel: Cohen's d
    sorted_d = results_df.reindex(sorted_p.index)
    d_colors = []
    for e in sorted_d["effect"]:
        d_colors.append(
            {"large": "#27AE60", "medium": "#F1C40F", "small": "#3498DB", "negligible": "#95A5A6"}[
                e
            ]
        )
    axes[1].barh(sorted_d.index, sorted_d["cohens_d"].abs(), color=d_colors)
    axes[1].set_xlabel("|Cohen's d|")
    axes[1].set_title("Effect size magnitude")
    axes[1].invert_yaxis()

    fig.suptitle("Figure 5 — Statistical Test Results", fontsize=14, y=1.02)
    fig.tight_layout()
    return fig


def plot_stat_tests_interactive(results_df: pd.DataFrame) -> go.Figure:
    """Figure 5 (interactive): p-values and effect sizes."""
    sorted_df = results_df.sort_values("p_value")

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("p-values", "|Cohen's d|"),
        horizontal_spacing=0.15,
    )

    p_colors = ["#27AE60" if v else "#C0392B" for v in sorted_df["significant"]]
    fig.add_trace(
        go.Bar(
            x=sorted_df["p_value"],
            y=sorted_df.index,
            orientation="h",
            marker_color=p_colors,
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    fig.add_vline(x=0.05, line_dash="dash", line_color="black", row=1, col=1)

    effect_color_map = {
        "large": "#27AE60",
        "medium": "#F1C40F",
        "small": "#3498DB",
        "negligible": "#95A5A6",
    }
    d_colors = [effect_color_map[e] for e in sorted_df["effect"]]
    fig.add_trace(
        go.Bar(
            x=sorted_df["cohens_d"].abs(),
            y=sorted_df.index,
            orientation="h",
            marker_color=d_colors,
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=500,
        title="Figure 5 — Statistical Test Results",
    )
    return fig


# ============================================================
# Figure 6 — Anomaly detection on energy consumption
# ============================================================


def plot_anomalies_static(df: pd.DataFrame) -> plt.Figure:
    """Figure 6 (static): kWh time series with Z-score and IF anomalies."""
    configure_style()
    report = combined_anomaly_report(df)

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(report.index, report["consumo_kwh"], color=COLOR_NEUTRAL, lw=2, alpha=0.7)

    z_anom = report[report["anomaly_zscore"]]
    if_anom = report[report["anomaly_isolation_forest"]]

    ax.scatter(
        z_anom.index,
        z_anom["consumo_kwh"],
        marker="^",
        s=140,
        color="#E67E22",
        label="Z-score anomaly",
        zorder=5,
    )
    ax.scatter(
        if_anom.index,
        if_anom["consumo_kwh"],
        marker="x",
        s=140,
        color="#C0392B",
        label="Isolation Forest",
        zorder=5,
        linewidths=2.5,
    )

    _add_cutoff_line_mpl(ax)
    ax.set_ylabel("Energy consumption (kWh)")
    ax.set_xlabel("Month")
    ax.set_title("Figure 6 — Anomaly Detection on Energy Consumption")
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


def plot_anomalies_interactive(df: pd.DataFrame) -> go.Figure:
    """Figure 6 (interactive): Anomaly detection time series."""
    report = combined_anomaly_report(df)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=report.index,
            y=report["consumo_kwh"],
            mode="lines+markers",
            name="kWh",
            line=dict(color=COLOR_NEUTRAL, width=2),
            opacity=0.7,
        )
    )

    z_anom = report[report["anomaly_zscore"]]
    if_anom = report[report["anomaly_isolation_forest"]]

    fig.add_trace(
        go.Scatter(
            x=z_anom.index,
            y=z_anom["consumo_kwh"],
            mode="markers",
            name="Z-score",
            marker=dict(symbol="triangle-up", size=14, color="#E67E22"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=if_anom.index,
            y=if_anom["consumo_kwh"],
            mode="markers",
            name="Isolation Forest",
            marker=dict(symbol="x", size=14, color="#C0392B"),
        )
    )

    fig.add_vline(x=INTERVENTION_CUTOFF, line_dash="dash", line_color="black", opacity=0.6)
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Figure 6 — Anomaly Detection on Energy Consumption",
        yaxis_title="kWh",
        height=480,
    )
    return fig


# ============================================================
# Figure 7 — Regression trends with projection
# ============================================================


def _build_trend_fits(df: pd.DataFrame) -> tuple[RegressionFit, RegressionFit, np.ndarray]:
    """Helper: fit Pre and Post linear trends and return month indices."""
    df_sorted = df.sort_values("fecha").reset_index(drop=True)
    df_sorted["month_idx"] = np.arange(len(df_sorted))

    pre = df_sorted[df_sorted["period"] == PERIOD_PRE]
    post = df_sorted[df_sorted["period"] == PERIOD_POST]

    fit_pre = fit_linear_trend(pre["month_idx"], pre["consumo_kwh"])
    fit_post = fit_linear_trend(post["month_idx"], post["consumo_kwh"])

    return fit_pre, fit_post, df_sorted["month_idx"].to_numpy()


def plot_trends_static(df: pd.DataFrame, projection_months: int = 12) -> plt.Figure:
    """Figure 7 (static): Linear trends Pre/Post with 12-month projection."""
    configure_style()
    fit_pre, fit_post, _ = _build_trend_fits(df)
    df_sorted = df.sort_values("fecha").reset_index(drop=True)
    df_sorted["month_idx"] = np.arange(len(df_sorted))

    pre_df = df_sorted[df_sorted["period"] == PERIOD_PRE]
    post_df = df_sorted[df_sorted["period"] == PERIOD_POST]

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.scatter(
        pre_df["fecha"], pre_df["consumo_kwh"], color=COLOR_PRE, s=50, label="Pre data", alpha=0.7
    )
    ax.scatter(
        post_df["fecha"],
        post_df["consumo_kwh"],
        color=COLOR_POST,
        s=50,
        label="Post data",
        alpha=0.7,
    )

    pre_x = pre_df["month_idx"].to_numpy()
    ax.plot(pre_df["fecha"], project_trend(fit_pre, pre_x), color=COLOR_PRE, lw=2.5)

    post_x = post_df["month_idx"].to_numpy()
    ax.plot(post_df["fecha"], project_trend(fit_post, post_x), color=COLOR_POST, lw=2.5)

    # Projection
    last_idx = df_sorted["month_idx"].max()
    proj_x = np.arange(last_idx + 1, last_idx + 1 + projection_months)
    proj_dates = pd.date_range(
        start=df_sorted["fecha"].max() + pd.offsets.MonthEnd(1),
        periods=projection_months,
        freq="ME",
    )
    proj_y = project_trend(fit_post, proj_x)
    ax.plot(
        proj_dates,
        proj_y,
        color=COLOR_POST,
        lw=2,
        linestyle="--",
        label=f"Projection +{projection_months}m",
    )
    ax.fill_between(proj_dates, proj_y * 0.95, proj_y * 1.05, color=COLOR_POST, alpha=0.15)

    _add_cutoff_line_mpl(ax)
    ax.set_ylabel("Energy consumption (kWh)")
    ax.set_xlabel("Month")
    ax.set_title("Figure 7 — Pre/Post Trends with 12-Month Projection")
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


def plot_trends_interactive(df: pd.DataFrame, projection_months: int = 12) -> go.Figure:
    """Figure 7 (interactive): Linear trends Pre/Post with projection."""
    fit_pre, fit_post, _ = _build_trend_fits(df)
    df_sorted = df.sort_values("fecha").reset_index(drop=True)
    df_sorted["month_idx"] = np.arange(len(df_sorted))

    pre_df = df_sorted[df_sorted["period"] == PERIOD_PRE]
    post_df = df_sorted[df_sorted["period"] == PERIOD_POST]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=pre_df["fecha"],
            y=pre_df["consumo_kwh"],
            mode="markers",
            name="Pre",
            marker=dict(color=COLOR_PRE, size=8),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=pre_df["fecha"],
            y=project_trend(fit_pre, pre_df["month_idx"].to_numpy()),
            mode="lines",
            name="Pre trend",
            line=dict(color=COLOR_PRE, width=3),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=post_df["fecha"],
            y=post_df["consumo_kwh"],
            mode="markers",
            name="Post",
            marker=dict(color=COLOR_POST, size=8),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=post_df["fecha"],
            y=project_trend(fit_post, post_df["month_idx"].to_numpy()),
            mode="lines",
            name="Post trend",
            line=dict(color=COLOR_POST, width=3),
        )
    )

    last_idx = int(df_sorted["month_idx"].max())
    proj_x = np.arange(last_idx + 1, last_idx + 1 + projection_months)
    proj_dates = pd.date_range(
        start=df_sorted["fecha"].max() + pd.offsets.MonthEnd(1),
        periods=projection_months,
        freq="ME",
    )
    proj_y = project_trend(fit_post, proj_x)
    fig.add_trace(
        go.Scatter(
            x=proj_dates,
            y=proj_y,
            mode="lines",
            name="Projection",
            line=dict(color=COLOR_POST, width=2, dash="dash"),
        )
    )

    fig.add_vline(x=INTERVENTION_CUTOFF, line_dash="dash", line_color="black", opacity=0.6)
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Figure 7 — Pre/Post Trends with 12-Month Projection",
        yaxis_title="kWh",
        height=500,
    )
    return fig


# ============================================================
# Figure 8 — ROI: annual benefits & payback curve
# ============================================================


def plot_roi_static(roi: ROIResult) -> plt.Figure:
    """Figure 8 (static): Annual benefits bar + cumulative payback curve."""
    configure_style()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    benefits = {
        "Energy": roi.energy_savings_annual_usd,
        "Downtime": roi.downtime_savings_annual_usd,
        "Total": roi.total_annual_benefit_usd,
    }
    colors = ["#3498DB", "#9B59B6", "#27AE60"]
    axes[0].bar(benefits.keys(), benefits.values(), color=colors)
    axes[0].set_ylabel("USD / year")
    axes[0].set_title("Annualized Benefits")
    for i, (k, v) in enumerate(benefits.items()):
        axes[0].text(i, v, f"${v:,.0f}", ha="center", va="bottom", fontweight="bold")

    monthly = roi.total_annual_benefit_usd / 12.0
    curve = payback_curve(monthly, roi.investment_usd, horizon_months=144)
    axes[1].plot(curve["month"], curve["net_position_usd"], color=COLOR_NEUTRAL, lw=2)
    axes[1].axhline(0, color="black", linestyle="--", linewidth=1)
    if np.isfinite(roi.payback_months) and roi.payback_months <= 144:
        axes[1].axvline(roi.payback_months, color=COLOR_POST, linestyle="--", linewidth=1.5)
        axes[1].text(
            roi.payback_months,
            curve["net_position_usd"].max() * 0.1,
            f"Payback\n{roi.payback_months:.0f}m",
            color=COLOR_POST,
            fontweight="bold",
        )
    axes[1].set_xlabel("Months from project end")
    axes[1].set_ylabel("Net position (USD)")
    axes[1].set_title("Cumulative Payback (energy + downtime only)")
    axes[1].fill_between(
        curve["month"],
        0,
        curve["net_position_usd"],
        where=curve["net_position_usd"] >= 0,
        color=COLOR_POST,
        alpha=0.15,
    )
    axes[1].fill_between(
        curve["month"],
        0,
        curve["net_position_usd"],
        where=curve["net_position_usd"] < 0,
        color=COLOR_PRE,
        alpha=0.15,
    )

    fig.suptitle("Figure 8 — ROI and Payback Analysis", fontsize=14, y=1.02)
    fig.tight_layout()
    return fig


def plot_roi_interactive(roi: ROIResult) -> go.Figure:
    """Figure 8 (interactive): Annual benefits + payback curve."""
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Annualized Benefits", "Cumulative Payback"),
        horizontal_spacing=0.15,
    )

    fig.add_trace(
        go.Bar(
            x=["Energy", "Downtime", "Total"],
            y=[
                roi.energy_savings_annual_usd,
                roi.downtime_savings_annual_usd,
                roi.total_annual_benefit_usd,
            ],
            marker_color=["#3498DB", "#9B59B6", "#27AE60"],
            text=[
                f"${roi.energy_savings_annual_usd:,.0f}",
                f"${roi.downtime_savings_annual_usd:,.0f}",
                f"${roi.total_annual_benefit_usd:,.0f}",
            ],
            textposition="outside",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    monthly = roi.total_annual_benefit_usd / 12.0
    curve = payback_curve(monthly, roi.investment_usd, horizon_months=144)
    fig.add_trace(
        go.Scatter(
            x=curve["month"],
            y=curve["net_position_usd"],
            mode="lines",
            line=dict(color=COLOR_NEUTRAL, width=2),
            fill="tozeroy",
            showlegend=False,
        ),
        row=1,
        col=2,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="black", row=1, col=2)

    fig.update_yaxes(title_text="USD / year", row=1, col=1)
    fig.update_xaxes(title_text="Months", row=1, col=2)
    fig.update_yaxes(title_text="Net position (USD)", row=1, col=2)

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=500,
        title="Figure 8 — ROI and Payback Analysis",
    )
    return fig


# ============================================================
# Figure 9 — Feature importance from Random Forest
# ============================================================


def plot_feature_importance_static(importances: pd.Series, r2: float) -> plt.Figure:
    """Figure 9 (static): Variable importance for energy consumption."""
    configure_style()
    fig, ax = plt.subplots(figsize=(9, 5))
    importances_sorted = importances.sort_values(ascending=True)
    ax.barh(importances_sorted.index, importances_sorted.values, color=COLOR_NEUTRAL)
    ax.set_xlabel("Importance")
    ax.set_title(f"Figure 9 — Feature Importance on Energy Consumption (R²={r2:.3f})")
    for i, (name, val) in enumerate(importances_sorted.items()):
        ax.text(val, i, f" {val:.3f}", va="center")
    fig.tight_layout()
    return fig


def plot_feature_importance_interactive(importances: pd.Series, r2: float) -> go.Figure:
    """Figure 9 (interactive): Variable importance bar chart."""
    importances_sorted = importances.sort_values(ascending=True)
    fig = go.Figure(
        go.Bar(
            x=importances_sorted.values,
            y=importances_sorted.index,
            orientation="h",
            marker_color=COLOR_NEUTRAL,
            text=[f"{v:.3f}" for v in importances_sorted.values],
            textposition="outside",
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=f"Figure 9 — Feature Importance on Energy Consumption (R²={r2:.3f})",
        xaxis_title="Importance",
        height=450,
    )
    return fig


# ============================================================
# Figure 10 — Sales and gross margin
# ============================================================


def plot_sales_margin_static(df: pd.DataFrame) -> plt.Figure:
    """Figure 10 (static): Monthly sales bars + gross margin line."""
    configure_style()
    fig, ax1 = plt.subplots(figsize=(11, 5))

    ax1.bar(
        df["fecha"], df["ventas_usd"], color=COLOR_NEUTRAL, alpha=0.7, width=25, label="Sales (USD)"
    )
    ax1.set_ylabel("Sales (USD)", color=COLOR_NEUTRAL)
    ax1.tick_params(axis="y", labelcolor=COLOR_NEUTRAL)
    ax1.set_xlabel("Month")

    ax2 = ax1.twinx()
    ax2.plot(
        df["fecha"],
        df["margen_bruto_pct"],
        marker="o",
        color="#F39C12",
        lw=2.5,
        label="Gross margin (%)",
    )
    ax2.set_ylabel("Gross margin (%)", color="#F39C12")
    ax2.tick_params(axis="y", labelcolor="#F39C12")
    ax2.spines["right"].set_visible(True)
    ax2.grid(False)

    _add_cutoff_line_mpl(ax1, label="Intervention")

    ax1.set_title("Figure 10 — Monthly Sales and Gross Margin")
    fig.tight_layout()
    return fig


def plot_sales_margin_interactive(df: pd.DataFrame) -> go.Figure:
    """Figure 10 (interactive): Sales bars + gross margin line."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=df["fecha"],
            y=df["ventas_usd"],
            name="Sales (USD)",
            marker_color=COLOR_NEUTRAL,
            opacity=0.7,
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["fecha"],
            y=df["margen_bruto_pct"],
            mode="lines+markers",
            name="Gross margin (%)",
            line=dict(color="#F39C12", width=3),
        ),
        secondary_y=True,
    )

    fig.add_vline(x=INTERVENTION_CUTOFF, line_dash="dash", line_color="black", opacity=0.6)
    fig.update_yaxes(title_text="Sales (USD)", secondary_y=False)
    fig.update_yaxes(title_text="Gross margin (%)", secondary_y=True)
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Figure 10 — Monthly Sales and Gross Margin",
        height=500,
    )
    return fig


# ============================================================
# Convenience: generate all 10 static figures in one call
# ============================================================

FIGURE_FILENAMES: dict[str, str] = {
    "timeseries": "figura_01_series_temporales",
    "boxplots": "figura_02_boxplots_pre_post",
    "correlation": "figura_03_matriz_correlacion",
    "intensity": "figura_04_intensidad_energetica",
    "stat_tests": "figura_05_tests_estadisticos",
    "anomalies": "figura_06_deteccion_anomalias",
    "trends": "figura_07_tendencias_regresion",
    "roi": "figura_08_roi_payback",
    "feature_importance": "figura_09_feature_importance",
    "sales_margin": "figura_10_ventas_margen",
}


def generate_all_static_figures(
    df: pd.DataFrame,
    roi: ROIResult,
    save: bool = True,
    close_after: bool = True,
) -> dict[str, Any]:
    """Generate all 10 static figures and optionally save to reports/figures/.

    Args:
        df: Full dataset from load_dataset.
        roi: ROIResult from compute_roi.
        save: If True, save each figure to reports/figures/.
        close_after: If True, close each figure after saving to free memory.

    Returns:
        Dict mapping figure key to its saved Path (or matplotlib Figure if not saving).
    """
    from panificadora.eda import correlation_matrix as _corr

    stats_df = compare_all_variables(df, KPIS_FOR_BOXPLOT)
    importances, r2 = feature_importance_energy(df)
    corr = _corr(df)

    figures = {
        "timeseries": plot_timeseries_static(df),
        "boxplots": plot_boxplots_static(df),
        "correlation": plot_correlation_static(corr),
        "intensity": plot_intensity_static(df),
        "stat_tests": plot_stat_tests_static(stats_df),
        "anomalies": plot_anomalies_static(df),
        "trends": plot_trends_static(df),
        "roi": plot_roi_static(roi),
        "feature_importance": plot_feature_importance_static(importances, r2),
        "sales_margin": plot_sales_margin_static(df),
    }

    output: dict[str, Any] = {}
    for key, fig in figures.items():
        if save:
            path = save_figure(fig, FIGURE_FILENAMES[key])
            output[key] = path
        else:
            output[key] = fig
        if close_after:
            plt.close(fig)

    return output
