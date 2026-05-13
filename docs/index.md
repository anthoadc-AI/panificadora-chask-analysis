---
hide:
  - navigation
---

# 🥖 Panificadora Chask — Modernization Analysis

!!! abstract "Project Snapshot"
    Energy efficiency and operational impact analysis of an industrial bakery
    modernization project executed by **INGEDAV S.R.L.** in Punata, Cochabamba,
    Bolivia between **December 2020 and June 2022**.

## What this site is

This is the technical documentation for a reproducible data analysis that
quantifies the impact of a four-phase plant modernization project. It is
companion to the GitHub repository, generated automatically from docstrings
and Markdown source via MkDocs Material.

The original closure report claimed a **−27 % steady-state energy reduction**
and a **+50 % production capacity gain**. This analysis re-derives those
figures from the raw monthly operations dataset, validates them with
formal statistical tests, and surfaces (in the spirit of reproducible
research) two small discrepancies between the report and the dataset.

## Headline findings

<div class="grid cards" markdown>

-   :material-flash:{ .lg .middle } **Energy reduction: −15.5 %**

    ---

    Pre = 49,703 kWh/month → Post = 42,023 kWh/month.
    Statistically significant (p ≈ 2.7 × 10⁻⁹, Cohen's *d* = −2.66).

-   :material-chart-line:{ .lg .middle } **Energy intensity: −14.9 %**

    ---

    kWh per kg of product fell from 3.69 to 3.14 — the plant produces
    more with less energy.

-   :material-cog:{ .lg .middle } **Anomalies cluster in Pre**

    ---

    Isolation Forest flags 3/29 months as anomalous; all sit in the
    Pre-intervention window and coincide with high failure counts.

-   :material-currency-usd:{ .lg .middle } **Conservative ROI**

    ---

    Energy + downtime savings alone repay ~USD 5,269/year. Production
    gains and recovered sales make the real payback meaningfully shorter.

</div>

## Navigation

- **[Getting Started](getting-started.md)** — install the package and reproduce the analysis locally.
- **[The Analysis](analysis/overview.md)** — chapter-by-chapter walkthrough mirroring the four notebooks.
- **[Dashboard](dashboard.md)** — interactive Streamlit application with live parameter tuning.
- **[API Reference](api/config.md)** — auto-generated documentation for every public function.
- **[Key Findings](findings.md)** — the consolidated KPIs and the report-vs-dataset discrepancies.

## Source code

[:fontawesome-brands-github: View on GitHub](https://github.com/anthoadc-AI/panificadora-chask-analysis){ .md-button .md-button--primary }
[:material-bookshelf: Closure Report (PDF)](https://github.com/anthoadc-AI/panificadora-chask-analysis){ .md-button }

---

*Built by **Anthony Davila** · Mechanical Engineer · MIT xPRO Data Engineering · INGEDAV S.R.L.*
