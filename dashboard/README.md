# 🥖 Streamlit Dashboard

Interactive dashboard for the Panificadora Chask modernization analysis.

## Launch

From the repo root:

```bash
# Make sure dependencies are installed
make install-dev

# Launch the dashboard
make dashboard

# Or directly:
streamlit run dashboard/app.py
```

The app opens at http://localhost:8501.

## Features

The sidebar exposes every parameter that drives the analysis:

| Group | Control | Effect |
| --- | --- | --- |
| 💰 ROI | Energy tariff (USD/kWh) | Recomputes annual benefits and payback |
| 💰 ROI | Project investment (USD) | Re-scales payback period |
| 💰 ROI | Downtime cost (USD/hour) | Adjusts the downtime savings component |
| 🔍 Anomaly | Z-score threshold | Stricter (higher) → fewer univariate anomalies |
| 🔍 Anomaly | Isolation Forest contamination | Expected fraction of anomalies in the data |
| 🔍 Anomaly | Isolation Forest n_estimators | More trees → more stable detection |
| 📅 Filter | Period (Pre / Post / Both) | Filters correlation and intensity views |

## Tabs

| Tab | Content |
| --- | --- |
| 📈 Overview | Headline KPI cards · monthly time series · sales & margin |
| 🔬 EDA | Pre/Post descriptive stats · distributions · correlation matrix · intensity over time |
| 🔍 Anomalies | Live Z-score + Isolation Forest detection with parameter tuning · feature importance |
| 📐 Statistics | Hypothesis tests (Shapiro-Wilk → t/Mann-Whitney) · Cohen's d · regression trends |
| 💰 ROI | Live ROI calculator · payback curve · tariff sensitivity sweep |
| 📋 Data | Raw dataset viewer with CSV download |

## Architecture

The dashboard contains **no analytical logic of its own** — every chart and metric
is computed by the same functions in `src/panificadora/` that power the notebooks
and the test suite. Streamlit's `@st.cache_data` ensures heavy computations
(Isolation Forest, Random Forest) run only when their inputs change.
