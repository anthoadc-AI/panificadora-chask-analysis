"""Streamlit Dashboard — Panificadora Chask Modernization Analysis.

Launch with: `streamlit run dashboard/app.py`
              or `make dashboard`

The dashboard mirrors the four analytical notebooks but adds full
interactivity through sidebar controls. All computations reuse the
exact same functions from `src/panificadora`, so any change to the
analytical engine is reflected here automatically.
"""
from __future__ import annotations

import pandas as pd
import plotly.io as pio
import streamlit as st

from panificadora import load_dataset
from panificadora.anomaly import (
    feature_importance_energy,
    isolation_forest_anomalies,
    zscore_anomalies,
)
from panificadora.config import (
    ENERGY_COST_USD_PER_KWH,
    INTERVENTION_CUTOFF,
    ISOLATION_FOREST_CONTAMINATION,
    ISOLATION_FOREST_N_ESTIMATORS,
    PERIOD_POST,
    PERIOD_PRE,
    PROJECT_INVESTMENT_USD,
    RANDOM_STATE,
    ZSCORE_THRESHOLD,
)
from panificadora.eda import correlation_matrix, describe_by_period
from panificadora.roi import compute_roi
from panificadora.stats import compare_all_variables
from panificadora.viz import (
    KPIS_FOR_BOXPLOT,
    plot_boxplots_interactive,
    plot_correlation_interactive,
    plot_feature_importance_interactive,
    plot_intensity_interactive,
    plot_roi_interactive,
    plot_sales_margin_interactive,
    plot_stat_tests_interactive,
    plot_timeseries_interactive,
    plot_trends_interactive,
)

# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="Panificadora Chask Dashboard",
    page_icon="🥖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "Energy and operational efficiency analysis of the Panificadora Chask "
            "modernization project (2020–2022).\n\n"
            "Built by Anthony Davila · INGEDAV S.R.L."
        ),
    },
)

pio.templates.default = "plotly_white"


# ============================================================
# Cached data layer
# ============================================================

@st.cache_data
def get_data() -> pd.DataFrame:
    """Load the dataset once per session."""
    return load_dataset()


@st.cache_data
def get_descriptive_stats(_df: pd.DataFrame) -> pd.DataFrame:
    return describe_by_period(_df)


@st.cache_data
def get_correlation(_df: pd.DataFrame) -> pd.DataFrame:
    return correlation_matrix(_df)


@st.cache_data
def get_stat_tests(_df: pd.DataFrame) -> pd.DataFrame:
    return compare_all_variables(_df, KPIS_FOR_BOXPLOT)


@st.cache_data
def get_feature_importance(_df: pd.DataFrame) -> tuple[pd.Series, float]:
    return feature_importance_energy(_df)


# ============================================================
# Sidebar — global controls
# ============================================================

def render_sidebar() -> dict:
    """Render sidebar controls and return their current values."""
    st.sidebar.title("🥖 Chask Dashboard")
    st.sidebar.markdown(
        "Interactive analysis of the plant modernization project (2020–2022)."
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 ROI parameters")

    energy_tariff = st.sidebar.slider(
        "Energy tariff (USD/kWh)",
        min_value=0.030,
        max_value=0.200,
        value=ENERGY_COST_USD_PER_KWH,
        step=0.005,
        format="%.3f",
        help="Industrial electricity tariff in USD per kWh. Higher tariffs shorten payback.",
    )

    investment_usd = st.sidebar.number_input(
        "Project investment (USD)",
        min_value=10_000,
        max_value=500_000,
        value=int(PROJECT_INVESTMENT_USD),
        step=5_000,
        help="Total project cost: machinery, installation, EMS, training.",
    )

    downtime_cost = st.sidebar.slider(
        "Downtime cost (USD/hour)",
        min_value=5.0,
        max_value=50.0,
        value=12.0,
        step=1.0,
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Anomaly detection")

    z_threshold = st.sidebar.slider(
        "Z-score threshold |Z|",
        min_value=1.0,
        max_value=4.0,
        value=ZSCORE_THRESHOLD,
        step=0.1,
        help="Higher = stricter (fewer anomalies). Default 2.0 ≈ 5% of normal distribution.",
    )

    contamination = st.sidebar.slider(
        "Isolation Forest contamination",
        min_value=0.01,
        max_value=0.30,
        value=ISOLATION_FOREST_CONTAMINATION,
        step=0.01,
        format="%.2f",
        help="Expected fraction of anomalies in the data. Default: 10%.",
    )

    n_estimators = st.sidebar.slider(
        "Isolation Forest n_estimators",
        min_value=50,
        max_value=500,
        value=ISOLATION_FOREST_N_ESTIMATORS,
        step=50,
        help="More trees = more stable detection but slower.",
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Period filter")
    period_filter = st.sidebar.radio(
        "Show data for",
        options=["Both", PERIOD_PRE, PERIOD_POST],
        index=0,
        horizontal=True,
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "**Anthony Davila** · INGEDAV S.R.L.  \n"
        "MIT xPRO Data Engineering  \n"
        "[GitHub](https://github.com/anthoadc-AI) · "
        "[LinkedIn](https://linkedin.com/in/anthony-davila-034b921ba)"
    )

    return {
        "energy_tariff": energy_tariff,
        "investment_usd": float(investment_usd),
        "downtime_cost": downtime_cost,
        "z_threshold": z_threshold,
        "contamination": contamination,
        "n_estimators": n_estimators,
        "period_filter": period_filter,
    }


def apply_period_filter(df: pd.DataFrame, period_filter: str) -> pd.DataFrame:
    """Filter the dataframe by period selection."""
    if period_filter == "Both":
        return df
    return df[df["period"] == period_filter].copy()


# ============================================================
# KPI cards
# ============================================================

def kpi_metric_row(df: pd.DataFrame, stats: pd.DataFrame, params: dict) -> None:
    """Render the 4-metric top row that summarizes the headline findings."""
    col1, col2, col3, col4 = st.columns(4)

    energy_change = stats.loc["consumo_kwh", "pct_change"]
    intensity_change = stats.loc["intensidad_kwh_kg", "pct_change"]

    col1.metric(
        label="Energy consumption (kWh/month)",
        value=f"{stats.loc['consumo_kwh', 'mean_post']:,.0f}",
        delta=f"{energy_change:+.1f}% vs Pre",
        delta_color="inverse",  # Less is better
    )
    col2.metric(
        label="Energy intensity (kWh/kg)",
        value=f"{stats.loc['intensidad_kwh_kg', 'mean_post']:,.2f}",
        delta=f"{intensity_change:+.1f}% vs Pre",
        delta_color="inverse",
    )

    # ROI recomputed with sidebar params
    roi = compute_roi(
        df,
        investment_usd=params["investment_usd"],
        cost_per_kwh=params["energy_tariff"],
        downtime_cost_per_hour=params["downtime_cost"],
    )
    col3.metric(
        label="Annual benefit (USD)",
        value=f"${roi.total_annual_benefit_usd:,.0f}",
        delta=f"@ ${params['energy_tariff']:.3f}/kWh",
        delta_color="off",
    )
    payback_text = (
        f"{roi.payback_months:.0f} months" if roi.payback_months < 1000 else "—"
    )
    col4.metric(
        label="Payback period",
        value=payback_text,
        delta=f"on ${params['investment_usd']:,.0f}",
        delta_color="off",
    )


# ============================================================
# Tab renderers
# ============================================================

def render_overview_tab(df: pd.DataFrame, stats: pd.DataFrame, params: dict) -> None:
    """Top-level summary: headline KPIs + time-series figure."""
    st.subheader("Headline Results")
    kpi_metric_row(df, stats, params)

    st.markdown(
        f"""
**Intervention cutoff:** {INTERVENTION_CUTOFF.strftime('%B %Y')} —
new machinery fully operational.
**Sample sizes:** 20 months Pre · 9 months Post · 29 total observations.
"""
    )

    st.markdown("---")
    st.subheader("Monthly Energy Consumption and Production")
    st.plotly_chart(plot_timeseries_interactive(df), use_container_width=True)

    st.markdown("---")
    st.subheader("Sales and Gross Margin")
    st.plotly_chart(plot_sales_margin_interactive(df), use_container_width=True)


def render_eda_tab(df_full: pd.DataFrame, df_filtered: pd.DataFrame) -> None:
    """Exploratory analysis: distributions, correlations, intensity over time."""
    st.subheader("Descriptive Statistics by Period")
    stats = describe_by_period(df_full)
    st.dataframe(
        stats.style.format(
            {
                "mean_pre": "{:,.2f}",
                "mean_post": "{:,.2f}",
                "std_pre": "{:,.2f}",
                "std_post": "{:,.2f}",
                "abs_change": "{:+,.2f}",
                "pct_change": "{:+.2f}%",
            }
        ),
        use_container_width=True,
    )

    st.markdown("---")
    st.subheader("Pre vs Post Distributions")
    st.plotly_chart(plot_boxplots_interactive(df_full), use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader("Correlation Matrix")
        corr = get_correlation(df_filtered)
        st.plotly_chart(plot_correlation_interactive(corr), use_container_width=True)
    with col2:
        st.subheader("Energy Intensity over Time")
        st.plotly_chart(plot_intensity_interactive(df_full), use_container_width=True)


def render_anomaly_tab(df: pd.DataFrame, params: dict) -> None:
    """Anomaly detection with interactive Z-score and IF tuning."""
    st.subheader("Anomaly Detection")
    st.caption(
        "Adjust the thresholds in the sidebar to see how each method "
        "responds. Z-score is univariate; Isolation Forest is multivariate."
    )

    # Recompute anomalies with current sidebar params
    z_flags = zscore_anomalies(df["consumo_kwh"], threshold=params["z_threshold"])
    if_flags = isolation_forest_anomalies(
        df,
        contamination=params["contamination"],
        n_estimators=params["n_estimators"],
        random_state=RANDOM_STATE,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Z-score anomalies", f"{z_flags.sum()} / {len(df)}")
    col2.metric("Isolation Forest", f"{if_flags.sum()} / {len(df)}")
    col3.metric("Either method", f"{(z_flags | if_flags).sum()} / {len(df)}")

    # Build a custom time-series with current anomalies (re-using viz patterns)
    import plotly.graph_objects as go

    from panificadora.config import COLOR_NEUTRAL

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["fecha"],
            y=df["consumo_kwh"],
            mode="lines+markers",
            name="kWh",
            line=dict(color=COLOR_NEUTRAL, width=2),
            opacity=0.7,
        )
    )
    z_anom = df[z_flags]
    if_anom = df[if_flags]
    fig.add_trace(
        go.Scatter(
            x=z_anom["fecha"],
            y=z_anom["consumo_kwh"],
            mode="markers",
            name=f"Z-score (|Z|>{params['z_threshold']})",
            marker=dict(symbol="triangle-up", size=16, color="#E67E22"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=if_anom["fecha"],
            y=if_anom["consumo_kwh"],
            mode="markers",
            name=f"IF ({params['contamination']:.0%})",
            marker=dict(symbol="x", size=16, color="#C0392B"),
        )
    )
    fig.add_vline(
        x=INTERVENTION_CUTOFF, line_dash="dash", line_color="black", opacity=0.6
    )
    fig.update_layout(
        template="plotly_white",
        title="Anomaly Detection on Monthly Energy Consumption",
        yaxis_title="kWh",
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Detailed table
    st.markdown("---")
    st.subheader("Anomaly Detail")
    detail = df[["fecha", "consumo_kwh", "fallas_maquina", "tiempo_inactividad_horas", "period"]].copy()
    detail["z_score"] = z_flags.values
    detail["isolation_forest"] = if_flags.values
    detail["any"] = detail["z_score"] | detail["isolation_forest"]
    only_anomalies = st.checkbox("Show only anomalies", value=True)
    table = detail[detail["any"]] if only_anomalies else detail
    st.dataframe(table, use_container_width=True)

    st.markdown("---")
    st.subheader("Feature Importance — what drives energy consumption?")
    importances, r2 = get_feature_importance(df)
    st.plotly_chart(
        plot_feature_importance_interactive(importances, r2),
        use_container_width=True,
    )


def render_stats_tab(df: pd.DataFrame) -> None:
    """Statistical inference: hypothesis tests, effect sizes, regression trends."""
    st.subheader("Hypothesis Tests · Pre vs Post")
    st.caption(
        "Each variable is tested with Shapiro-Wilk for normality first, then "
        "Student's t (parametric) or Mann-Whitney U (non-parametric). "
        "Cohen's d quantifies practical effect size independent of sample size."
    )

    results = get_stat_tests(df)
    st.dataframe(
        results.style.format(
            {
                "mean_pre": "{:,.2f}",
                "mean_post": "{:,.2f}",
                "p_value": "{:.4g}",
                "cohens_d": "{:+.2f}",
            }
        ).background_gradient(subset=["p_value"], cmap="RdYlGn_r", vmin=0, vmax=0.1),
        use_container_width=True,
    )

    st.markdown("---")
    st.subheader("p-values and Effect Sizes")
    st.plotly_chart(plot_stat_tests_interactive(results), use_container_width=True)

    st.markdown("---")
    st.subheader("Pre/Post Regression Trends with 12-Month Projection")
    st.plotly_chart(plot_trends_interactive(df), use_container_width=True)


def render_roi_tab(df: pd.DataFrame, params: dict) -> None:
    """ROI calculator with tariff sensitivity sweep."""
    st.subheader("Return on Investment")
    st.caption(
        "All computations use the sidebar parameters. The sensitivity table "
        "below sweeps the energy tariff to show how payback responds."
    )

    roi = compute_roi(
        df,
        investment_usd=params["investment_usd"],
        cost_per_kwh=params["energy_tariff"],
        downtime_cost_per_hour=params["downtime_cost"],
    )

    col1, col2 = st.columns([3, 2])
    with col1:
        st.plotly_chart(plot_roi_interactive(roi), use_container_width=True)
    with col2:
        st.metric("Energy savings / year", f"${roi.energy_savings_annual_usd:,.0f}")
        st.metric("Downtime savings / year", f"${roi.downtime_savings_annual_usd:,.0f}")
        st.metric("Total annual benefit", f"${roi.total_annual_benefit_usd:,.0f}")
        payback_text = (
            f"{roi.payback_months:.0f} months ({roi.payback_months / 12:.1f} years)"
            if roi.payback_months < 1000
            else "Not achievable with current parameters"
        )
        st.metric("Payback", payback_text)

    st.markdown("---")
    st.subheader("Tariff Sensitivity Sweep")
    st.caption(
        "Holding investment and downtime cost fixed, how does the payback "
        "change as the energy tariff varies?"
    )
    sensitivity_rows = []
    for tariff in [0.05, 0.065, 0.08, 0.10, 0.12, 0.15]:
        r = compute_roi(
            df,
            investment_usd=params["investment_usd"],
            cost_per_kwh=tariff,
            downtime_cost_per_hour=params["downtime_cost"],
        )
        sensitivity_rows.append(
            {
                "tariff_usd_per_kwh": tariff,
                "annual_benefit_usd": r.total_annual_benefit_usd,
                "payback_months": r.payback_months,
                "payback_years": r.payback_months / 12,
            }
        )
    sens_df = pd.DataFrame(sensitivity_rows)
    st.dataframe(
        sens_df.style.format(
            {
                "tariff_usd_per_kwh": "${:.3f}",
                "annual_benefit_usd": "${:,.0f}",
                "payback_months": "{:.0f}",
                "payback_years": "{:.1f}",
            }
        ),
        use_container_width=True,
    )

    st.info(
        "💡 **Conservative scope:** this ROI captures only the directly quantifiable "
        "benefits from the dataset (energy + downtime). The +50% production capacity "
        "gain, quality improvements, and recovered lost sales are not included, so "
        "the real payback is meaningfully shorter than what's shown above."
    )


def render_data_tab(df: pd.DataFrame) -> None:
    """Raw data viewer with download."""
    st.subheader("Raw Dataset")
    st.caption("29 monthly observations from Jan 2020 to May 2022.")

    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download dataset as CSV",
        data=csv,
        file_name="dataset_panificadora.csv",
        mime="text/csv",
    )


# ============================================================
# Main entrypoint
# ============================================================

def main() -> None:
    params = render_sidebar()

    df_full = get_data()
    df_view = apply_period_filter(df_full, params["period_filter"])
    stats = get_descriptive_stats(df_full)

    st.title("🥖 Panificadora Chask — Modernization Dashboard")
    st.markdown(
        "Interactive analysis of the energy and operational impact of the "
        "plant modernization project executed by **INGEDAV S.R.L.** "
        "(Punata, Cochabamba, Bolivia · 2020–2022)."
    )

    tab_overview, tab_eda, tab_anomaly, tab_stats, tab_roi, tab_data = st.tabs(
        ["📈 Overview", "🔬 EDA", "🔍 Anomalies", "📐 Statistics", "💰 ROI", "📋 Data"]
    )

    with tab_overview:
        render_overview_tab(df_full, stats, params)
    with tab_eda:
        render_eda_tab(df_full, df_view)
    with tab_anomaly:
        render_anomaly_tab(df_full, params)
    with tab_stats:
        render_stats_tab(df_full)
    with tab_roi:
        render_roi_tab(df_full, params)
    with tab_data:
        render_data_tab(df_full)


if __name__ == "__main__":
    main()
