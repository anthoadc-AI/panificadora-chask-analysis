# Key Findings

This page consolidates the headline quantitative results of the analysis,
and documents the two discrepancies between the closure report and the
dataset that were surfaced by reproducing every calculation from raw data.

## Headline KPIs

| KPI | Pre-Intervention | Post-Intervention | Change |
| --- | ---: | ---: | ---: |
| Energy consumption (kWh/month) | 49,703 | 42,023 | **−15.5 %** |
| Energy intensity (kWh/kg) | 3.69 | 3.14 | **−14.9 %** |
| Machine failures (per month) | 7.05 | 8.78 | +24.5 % |
| Downtime (hours/month) | 26.6 | 31.6 | +18.9 % |
| Sales (USD/month) | 21,471 | 22,382 | +4.2 % |
| Gross margin (mean of monthly %) | 23.3 % | 21.3 % | **−2.0 pp** |
| Steady-state consumption (report) | 55,000 kWh | 40,000 kWh | −27 % |

## Statistical robustness

| Variable | Test | p-value | Cohen's d | Magnitude |
| --- | --- | ---: | ---: | --- |
| `consumo_kwh` | t-test | 2.7×10⁻⁹ | **−2.66** | **Large** |
| `intensidad_kwh_kg` | t-test | <0.001 | **−1.31** | **Large** |
| `fallas_maquina` | Mann-Whitney | 0.21 | +0.50 | Medium |
| `tiempo_inactividad_horas` | t-test | 0.25 | +0.44 | Small |
| `margen_bruto_pct` | Mann-Whitney | 0.82 | −0.10 | Negligible |
| `produccion_kg` | t-test | 0.91 | −0.04 | Negligible |

→ The **energy reduction is the firmest finding** of the entire analysis.

## Discrepancies between report and dataset

!!! warning "Discrepancy #1 — Energy reduction"
    **Closure report claim:** Pre = 50,578 kWh/month → Post = 41,396 kWh/month → **−18.2 %**.

    **Dataset-recomputed values:** Pre = 49,703 kWh/month → Post = 42,023 kWh/month → **−15.5 %**.

    **Gap:** The Pre mean differs by ~1.7 %, the Post mean by ~1.5 %.

    **Likely cause:** Rounding, alternative aggregation method, or a slightly
    different dataset version at report-writing time.

    **Material impact:** The headline conclusion (a statistically significant
    energy reduction with a *large* Cohen's *d*) is robust either way.

!!! danger "Discrepancy #2 — Gross margin"
    **Closure report claim:** Margin rose from **23.7 % to 31.9 %** — a
    **+8.2 percentage-point** improvement.

    **Dataset-recomputed values (mean of monthly margins):** Pre = 23.3 % →
    Post = 21.3 % — a **−2.0 percentage-point** decline.

    **Gap:** Direction reversed. This is the more material discrepancy.

    **Possible explanations:** The report may have computed the margin
    differently — e.g. (Σ sales − Σ costs) / Σ sales rather than the mean
    of monthly margins — or used a longer post-intervention window not
    represented in the dataset.

    **Material impact:** The margin improvement should **not** be reported
    as a project outcome without further data and explanation. The
    energy-side findings remain solid.

## Why surface these discrepancies?

It would be easier — and arguably more flattering — to silently align
the analysis with the report's published numbers. Surfacing the gaps
instead serves three purposes:

1. **Reproducibility integrity** — code that disagrees with the published
   numbers must be auditable, not hidden.
2. **Stakeholder trust** — a quantitative consultant who flags their own
   discrepancies is more credible than one who never finds any.
3. **Methodological teaching** — this is exactly the kind of moment that
   distinguishes a portfolio project from a marketing document.

## Conservative ROI

| Component | Annual value |
| --- | ---: |
| Energy savings (at $0.065/kWh) | $5,990 |
| Downtime savings (slight negative) | −$721 |
| **Total annual benefit (conservative)** | **$5,269** |
| Investment | $85,000 |
| **Conservative payback** | **~16 years** |

The conservative payback excludes:

- **+50 % production capacity** — recovered demand the old plant could not serve.
- **Quality consistency gains** — fewer rejects and rework cycles.
- **Strategic positioning** — competitive advantage in the regional market.

Including these would shorten the payback meaningfully; the dataset alone
does not provide the demand-side and pricing data needed to quantify them.

## What the project unambiguously delivered

Setting aside the discrepancies above, the project's clear, robust wins are:

- ✅ **Substantial, statistically significant energy reduction** (~15-18 %).
- ✅ **Improved energy intensity** — more product per kWh.
- ✅ **EMS infrastructure for ongoing optimization**.
- ✅ **+50 % production capacity** (per the closure report; not refutable from the dataset).
- ✅ **Modern, replicable methodology** for future plant audits.
