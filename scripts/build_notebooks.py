"""One-shot script to build the four analysis notebooks.

Run from the repo root: `python scripts/build_notebooks.py`
This script is NOT meant to be run by users — it bootstraps the notebooks
once. The generated .ipynb files in notebooks/ are the canonical artifacts.
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

NOTEBOOKS_DIR = Path(__file__).resolve().parents[1] / "notebooks"


def make_notebook(cells: list[nbf.NotebookNode], filename: str) -> Path:
    """Assemble cells into a notebook and write it to disk."""
    nb = nbf.v4.new_notebook()
    nb.cells = cells
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.10",
        },
    }
    out_path = NOTEBOOKS_DIR / filename
    NOTEBOOKS_DIR.mkdir(exist_ok=True)
    nbf.write(nb, out_path)
    return out_path


def md(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_markdown_cell(text)


def code(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_code_cell(text)


# ============================================================
# Notebook 1 — Exploratory Data Analysis
# ============================================================

NB1_CELLS = [
    md("""# 📊 Notebook 1 — Exploratory Data Analysis

**Project:** Panificadora Chask Plant Modernization
**Phase analyzed:** Pre vs Post intervention (cutoff: Aug 2021)

This notebook reproduces Section 4 of the closure report. It loads the 29-month
operations dataset, computes descriptive statistics by period, and renders the
five EDA figures (Figures 1, 2, 3, 4 and 10) as interactive Plotly charts.

> **Reproducibility note:** All computations are deterministic. The numbers
> shown here match what `make test` validates in CI."""),
    code("""# Setup
%load_ext autoreload
%autoreload 2

import pandas as pd
import plotly.io as pio

# Render interactive Plotly inside the notebook
pio.renderers.default = 'notebook'

from panificadora import load_dataset
from panificadora.eda import correlation_matrix, describe_by_period, summarize_change
from panificadora import viz

df = load_dataset()
print(f"Loaded {len(df)} monthly observations")
df.head()"""),
    md("""## 1.1 Descriptive statistics by period

The table below contrasts Pre and Post means with their percentage change.
Negative `pct_change` for `consumo_kwh` is the headline result; positive
change in `margen_bruto_pct` is the financial counterpart."""),
    code("""stats_df = describe_by_period(df)
stats_df.style.format({
    'mean_pre': '{:,.2f}',
    'mean_post': '{:,.2f}',
    'std_pre': '{:,.2f}',
    'std_post': '{:,.2f}',
    'abs_change': '{:+,.2f}',
    'pct_change': '{:+.2f}%',
})"""),
    code("""# One-line summary of the most relevant KPIs
for var in ['consumo_kwh', 'intensidad_kwh_kg', 'margen_bruto_pct', 'fallas_maquina']:
    print(summarize_change(stats_df, var))"""),
    md("""## 1.2 Figure 1 — Time series of energy and production

Both series share the same X-axis (monthly cutoff dates). The Pre and Post
regions are shaded; the vertical dashed line marks August 2021, when the
new machinery became fully operational."""),
    code("viz.plot_timeseries_interactive(df).show()"),
    md("""## 1.3 Figure 2 — KPI distributions Pre vs Post

Each box plot summarizes the distribution of one KPI per period. The white
diamond marks the mean; the box covers the IQR. Notice how `consumo_kwh`
and `intensidad_kwh_kg` shift downward, while `margen_bruto_pct` shifts up."""),
    code("viz.plot_boxplots_interactive(df).show()"),
    md("""## 1.4 Figure 3 — Correlation matrix

Pearson correlation captures linear relationships between numeric variables.
The strongest correlations to look for are between `consumo_kwh`,
`fallas_maquina`, and `produccion_kg` — they validate the field diagnosis
that failing machinery drove the energy excess."""),
    code("""corr = correlation_matrix(df)
viz.plot_correlation_interactive(corr).show()"""),
    md("""## 1.5 Figure 4 — Energy intensity over time

This is the most informative KPI for *efficiency*: kWh per kg produced.
Unlike absolute consumption, it isolates the productive efficiency of the
plant from production volume swings. The 3-month moving average smooths
monthly noise to reveal the underlying trend."""),
    code("viz.plot_intensity_interactive(df).show()"),
    md("""## 1.6 Figure 10 — Sales and gross margin

Monthly sales (bars) overlaid with gross margin percentage (line). The
margin lift after August 2021 reflects the reduction in operating costs
combined with the recovery of previously unmet demand."""),
    code("viz.plot_sales_margin_interactive(df).show()"),
    md("""## Key takeaways

1. **Energy reduction is unmistakable** in the time series — a clear drop after Aug 2021.
2. **Energy intensity drops ~14%**, confirming the plant produces more with less energy.
3. **Correlations validate the diagnosis**: failures ↔ consumption is positive and substantial.
4. **Margin improves** post-intervention despite slightly higher Post downtime
   (commissioning effect), thanks to lower operating costs.

→ **Next:** Notebook 2 examines anomalies and feature importance with ML methods."""),
]


# ============================================================
# Notebook 2 — Anomaly Detection
# ============================================================

NB2_CELLS = [
    md("""# 🔍 Notebook 2 — Anomaly Detection & Feature Importance

This notebook reproduces Section 5 of the closure report. We combine
two complementary methods to flag months with atypical operations:

- **Z-score** (univariate): flags points more than 2 σ from the mean of a single variable.
- **Isolation Forest** (multivariate, unsupervised ML): flags unusual combinations across several variables.

We then fit a Random Forest regressor to quantify each variable's
contribution to monthly energy consumption (Figure 9 in the report)."""),
    code("""%load_ext autoreload
%autoreload 2

import pandas as pd
import plotly.io as pio
pio.renderers.default = 'notebook'

from panificadora import load_dataset
from panificadora.anomaly import (
    combined_anomaly_report,
    feature_importance_energy,
    isolation_forest_anomalies,
    zscore_anomalies,
)
from panificadora import viz

df = load_dataset()
print(f"Loaded {len(df)} months of data")"""),
    md("""## 2.1 Univariate detection: Z-score

For each month, Z = (kWh - μ) / σ. We flag |Z| > 2.0."""),
    code("""z_flags = zscore_anomalies(df['consumo_kwh'], threshold=2.0)
z_anom = df.loc[z_flags, ['fecha', 'consumo_kwh', 'fallas_maquina', 'period']]
print(f"Z-score anomalies detected: {z_flags.sum()} / {len(df)}")
z_anom"""),
    md("""## 2.2 Multivariate detection: Isolation Forest

Isolation Forest is an unsupervised algorithm that isolates anomalies via
random partitioning of the feature space. We use 200 trees with a 10%
contamination rate, and 5 operational features."""),
    code("""if_flags = isolation_forest_anomalies(df)
if_anom = df.loc[if_flags, ['fecha', 'consumo_kwh', 'fallas_maquina', 'tiempo_inactividad_horas', 'period']]
print(f"Isolation Forest anomalies detected: {if_flags.sum()} / {len(df)}")
if_anom"""),
    md("""## 2.3 Combined report

The merged table shows which months are flagged by which method.
Months flagged by both methods are the strongest anomaly candidates."""),
    code("""report = combined_anomaly_report(df)
report[report['any_anomaly']].style.format({'consumo_kwh': '{:,.0f}'})"""),
    md("""## 2.4 Figure 6 — Anomalies on the time series

Triangle markers (orange) indicate Z-score anomalies; X markers (red)
indicate Isolation Forest anomalies. The fact that most anomalies cluster
in the Pre period validates the field diagnosis."""),
    code("viz.plot_anomalies_interactive(df).show()"),
    md("""## 2.5 Feature importance for energy consumption

A Random Forest regressor predicts monthly `consumo_kwh` from the other
operational variables. Its built-in feature importances tell us which
variables explain the most variance — and therefore where to prioritize
attention in future optimization efforts."""),
    code("""importances, r2 = feature_importance_energy(df)
print(f"Random Forest R² on training set: {r2:.3f}")
print()
importances.to_frame('importance').style.format({'importance': '{:.3f}'}).bar(color='#3498DB')"""),
    md("""## 2.6 Figure 9 — Variable importance bar chart"""),
    code("viz.plot_feature_importance_interactive(importances, r2).show()"),
    md("""## Key takeaways

1. **Both methods agree**: the most anomalous months sit in the Pre-intervention period,
   coinciding with high failure rates.
2. **Isolation Forest catches multivariate anomalies** that Z-score misses — a key benefit of combining methods.
3. **`fallas_maquina` and `produccion_kg` are the dominant predictors** of energy consumption.
   This is consistent with the field diagnosis: failing machinery was a primary energy waster.

→ **Next:** Notebook 3 formalizes whether the Pre→Post changes are statistically significant."""),
]


# ============================================================
# Notebook 3 — Statistical Tests
# ============================================================

NB3_CELLS = [
    md("""# 📐 Notebook 3 — Statistical Inference

This notebook reproduces Section 6 of the closure report. It runs the
formal protocol:

1. **Shapiro–Wilk** test for normality on each group.
2. **Student's *t*** (parametric) or **Mann–Whitney U** (non-parametric)
   depending on the normality outcome.
3. **Cohen's *d*** to quantify the *practical* magnitude of the difference.
4. **Linear regression** on Pre and Post sub-series for trend analysis,
   plus a 12-month projection of the Post trend.

Significance threshold: **α = 0.05**, two-sided."""),
    code("""%load_ext autoreload
%autoreload 2

import pandas as pd
import plotly.io as pio
pio.renderers.default = 'notebook'

from panificadora import load_dataset
from panificadora.config import PERIOD_PRE, PERIOD_POST
from panificadora.stats import (
    compare_all_variables,
    compare_groups,
    fit_linear_trend,
    shapiro_wilk,
)
from panificadora.viz import KPIS_FOR_BOXPLOT
from panificadora import viz

df = load_dataset()"""),
    md("""## 3.1 Normality check (Shapiro–Wilk)

We test each variable in each group. p > 0.05 → cannot reject normality."""),
    code("""rows = []
for var in KPIS_FOR_BOXPLOT:
    for period in [PERIOD_PRE, PERIOD_POST]:
        series = df.loc[df['period'] == period, var]
        p, is_normal = shapiro_wilk(series)
        rows.append({'variable': var, 'period': period, 'p_value': p, 'normal_at_alpha_0.05': is_normal})

normality_df = pd.DataFrame(rows).pivot(index='variable', columns='period', values='p_value')
normality_df.columns = ['p_Post', 'p_Pre']
normality_df.style.format('{:.4f}').background_gradient(cmap='RdYlGn', vmin=0, vmax=0.1)"""),
    md("""## 3.2 Pre vs Post group comparison

For each KPI we automatically pick the appropriate test based on normality
and report the p-value, Cohen's *d* and effect classification."""),
    code("""results = compare_all_variables(df, KPIS_FOR_BOXPLOT)
results.style.format({
    'mean_pre': '{:,.2f}',
    'mean_post': '{:,.2f}',
    'p_value': '{:.4g}',
    'cohens_d': '{:+.2f}',
}).background_gradient(subset=['p_value'], cmap='RdYlGn_r', vmin=0, vmax=0.1)"""),
    md("""## 3.3 Figure 5 — p-values and effect sizes

The dashed line in the left panel marks α = 0.05. Bars to the left of it
are statistically significant. The right panel shows Cohen's *d*, color-coded:

| Color    | Effect size  |
| -------- | ------------ |
| 🟢 Green | Large (d>0.8) |
| 🟡 Yellow| Medium       |
| 🔵 Blue  | Small        |
| ⚪ Gray  | Negligible   |"""),
    code("viz.plot_stat_tests_interactive(results).show()"),
    md("""## 3.4 Linear regression: Pre vs Post trends

Fitting `consumo_kwh ~ month_index` separately on each period reveals
whether the improvement is a discrete jump or a sustained trend."""),
    code("""import numpy as np
df_sorted = df.sort_values('fecha').reset_index(drop=True)
df_sorted['month_idx'] = np.arange(len(df_sorted))

pre_sub = df_sorted[df_sorted['period'] == PERIOD_PRE]
post_sub = df_sorted[df_sorted['period'] == PERIOD_POST]

fit_pre = fit_linear_trend(pre_sub['month_idx'], pre_sub['consumo_kwh'])
fit_post = fit_linear_trend(post_sub['month_idx'], post_sub['consumo_kwh'])

trend_df = pd.DataFrame({
    'Period': ['Pre', 'Post'],
    'Slope (kWh/month)': [fit_pre.slope, fit_post.slope],
    'Intercept': [fit_pre.intercept, fit_post.intercept],
    'R²': [fit_pre.r_squared, fit_post.r_squared],
    'p-value': [fit_pre.p_value, fit_post.p_value],
    'n': [fit_pre.n, fit_post.n],
})
trend_df.style.format({
    'Slope (kWh/month)': '{:+.1f}',
    'Intercept': '{:,.0f}',
    'R²': '{:.3f}',
    'p-value': '{:.4g}',
})"""),
    md("""## 3.5 Figure 7 — Trends with 12-month projection"""),
    code("viz.plot_trends_interactive(df).show()"),
    md("""## Key takeaways

1. **The energy reduction is robustly significant**: p ≪ 0.05 with a *large*
   Cohen's *d*. This is the firmest finding of the entire analysis.
2. **Intensity is also significant** with a large effect — efficiency improved, not just consumption.
3. **Production and margin changes are not statistically significant** at this sample size.
   This is expected: production is bounded by demand, and margin needs longer to stabilize.
4. **Both Pre and Post trends slope downward**, but the Post slope is more pronounced —
   the intervention not only reduced consumption but accelerated the rate of improvement.

→ **Next:** Notebook 4 quantifies the financial return."""),
]


# ============================================================
# Notebook 4 — ROI Analysis
# ============================================================

NB4_CELLS = [
    md("""# 💰 Notebook 4 — ROI and Payback Analysis

This notebook reproduces Section 7.4 of the closure report. It converts
the operational improvements (Notebooks 1–3) into dollars and computes
the project's payback timeline.

> **Conservative scope.** The ROI here uses *only* directly quantifiable
> savings from the dataset: energy and downtime. The +50 % production
> capacity gain, quality improvements, and recovered lost sales are
> documented but require additional demand-side data to monetize, so
> they're excluded from this calculation. The *real* payback is shorter
> than what we compute here."""),
    code("""%load_ext autoreload
%autoreload 2

import pandas as pd
import plotly.io as pio
pio.renderers.default = 'notebook'

from panificadora import load_dataset
from panificadora.config import ENERGY_COST_USD_PER_KWH, PROJECT_INVESTMENT_USD
from panificadora.roi import compute_roi, downtime_savings, energy_savings, payback_curve
from panificadora import viz

df = load_dataset()"""),
    md("""## 4.1 Economic assumptions

These live in `panificadora.config` and can be overridden for sensitivity analysis."""),
    code("""print(f"Energy tariff:              ${ENERGY_COST_USD_PER_KWH:.4f} per kWh")
print(f"Project investment:         ${PROJECT_INVESTMENT_USD:>10,.0f}")
print(f"Downtime cost (assumed):    $12.00 per hour")"""),
    md("""## 4.2 Component savings"""),
    code("""monthly_kwh_saved, annual_energy_usd = energy_savings(df)
monthly_hours_saved, annual_downtime_usd = downtime_savings(df)

savings_df = pd.DataFrame([
    {'component': 'Energy',   'monthly_units': monthly_kwh_saved,  'unit': 'kWh',   'annual_usd': annual_energy_usd},
    {'component': 'Downtime', 'monthly_units': monthly_hours_saved,'unit': 'hours', 'annual_usd': annual_downtime_usd},
])
savings_df.style.format({'monthly_units': '{:+,.1f}', 'annual_usd': '${:+,.0f}'})"""),
    md("""## 4.3 Aggregate ROI"""),
    code("""roi = compute_roi(df)

roi_summary = pd.DataFrame([
    {'Metric': 'Energy savings (USD/year)',     'Value': roi.energy_savings_annual_usd},
    {'Metric': 'Downtime savings (USD/year)',   'Value': roi.downtime_savings_annual_usd},
    {'Metric': 'TOTAL annual benefit (USD)',    'Value': roi.total_annual_benefit_usd},
    {'Metric': 'Investment (USD)',              'Value': roi.investment_usd},
    {'Metric': 'Payback (months)',              'Value': roi.payback_months},
    {'Metric': 'Year-1 ROI (%)',                'Value': roi.roi_year_1_pct},
])
roi_summary.style.format({'Value': '{:,.2f}'})"""),
    md("""## 4.4 Figure 8 — Annualized benefits and payback curve

The right panel shows the *net position* over time. Below zero = still
underwater on the investment; above zero = the project has paid for itself."""),
    code("viz.plot_roi_interactive(roi).show()"),
    md("""## 4.5 Sensitivity to energy tariff

The payback period is highly sensitive to the assumed cost per kWh.
A higher industrial tariff dramatically shortens the time to recoup
the investment. Sweep:"""),
    code("""sensitivity = []
for tariff in [0.05, 0.065, 0.08, 0.10, 0.12, 0.15]:
    r = compute_roi(df, cost_per_kwh=tariff)
    sensitivity.append({
        'tariff_usd_per_kwh': tariff,
        'annual_benefit_usd': r.total_annual_benefit_usd,
        'payback_months': r.payback_months,
        'payback_years': r.payback_months / 12,
    })
sens_df = pd.DataFrame(sensitivity)
sens_df.style.format({
    'tariff_usd_per_kwh': '${:.3f}',
    'annual_benefit_usd': '${:,.0f}',
    'payback_months': '{:.0f}',
    'payback_years': '{:.1f}',
})"""),
    md("""## Key takeaways

1. **Energy is the dominant lever** in the conservative ROI: it represents
   the majority of the quantified annual benefit.
2. **The payback period reported here is conservative.** Including the
   +50 % capacity gain, quality benefits, and recovered sales would
   meaningfully shorten the figure.
3. **Strategic value beyond cash flow** — the modernization positions
   the bakery to capture growth that the old plant could not serve, and
   leaves an EMS infrastructure for continuous data-driven improvement.
4. **The ROI is sensitive to tariffs**: at higher industrial rates, the
   payback shrinks substantially. Worth re-evaluating periodically as
   energy costs evolve.

→ **End of analysis.** All ten figures from the closure report have been
reproduced from the raw dataset using the modular code in `src/panificadora/`."""),
]


def main() -> None:
    paths = []
    paths.append(make_notebook(NB1_CELLS, "01_exploratory_data_analysis.ipynb"))
    paths.append(make_notebook(NB2_CELLS, "02_anomaly_detection.ipynb"))
    paths.append(make_notebook(NB3_CELLS, "03_statistical_tests.ipynb"))
    paths.append(make_notebook(NB4_CELLS, "04_roi_analysis.ipynb"))
    for p in paths:
        print(f"✓ {p}")


if __name__ == "__main__":
    main()
