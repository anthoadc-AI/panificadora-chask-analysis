<!-- omit in toc -->
# 🥖 Panificadora Chask — Plant Modernization Analysis

> Energy efficiency and operational impact analysis of an industrial bakery modernization project executed by **INGEDAV S.R.L.** in Punata, Cochabamba, Bolivia (2020–2022).

[![CI](https://github.com/anthoadc-AI/panificadora-chask-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/anthoadc-AI/panificadora-chask-analysis/actions/workflows/ci.yml)
[![Docs](https://github.com/anthoadc-AI/panificadora-chask-analysis/actions/workflows/docs.yml/badge.svg)](https://anthoadc-ai.github.io/panificadora-chask-analysis/)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**🌐 Language / Idioma:** [English](#english) · [Español](#español)
**📖 Documentation:** [anthoadc-ai.github.io/panificadora-chask-analysis](https://anthoadc-ai.github.io/panificadora-chask-analysis/)

---

## English

### Overview

The **Panificadora Chask** plant in Punata, Cochabamba (Bolivia) operated with obsolete, semi-manual machinery that capped its production capacity, drove excessive energy consumption (~55,000 kWh/month) and generated frequent equipment failures. Between December 2020 and June 2022, **INGEDAV S.R.L.** executed a four-phase modernization project covering diagnosis, CAD-based redesign, manufacture and installation of new high-efficiency equipment (industrial mixer, sheeter, beaters), an Energy Management System (EMS), and staff training.

This repository reproduces, from raw data, the **quantitative analysis** that backed the closure report. It is built as a portfolio-grade data engineering project: modular code in `src/`, reproducible notebooks, a Streamlit dashboard, a full pytest suite, and CI on every push.

### Key Findings

| KPI | Pre-Intervention | Post-Intervention | Change |
| --- | --- | --- | --- |
| Energy consumption (kWh/month, mean) | 49,703 | 42,023 | **−15.5%** |
| Energy intensity (kWh/kg) | 3.69 | 3.14 | **−14.9%** |
| Machine failures (per month) | 7.05 | 8.78 | +24.5% |
| Downtime (hours/month) | 26.6 | 31.6 | +18.9% |
| Gross margin (per-month mean) | 23.3% | 21.3% | **−2.0 pp** |
| Steady-state consumption (report-cited) | 55,000 kWh | 40,000 kWh | **−27%** |

> 📋 **Note on reproducibility.** Two figures in the closure report don't match
> the dataset when recomputed:
> - The **energy reduction** is cited as −18.2 % in the report; the actual dataset gives **−15.5 %** (the Pre mean differs by ~1.7 %, the Post mean by ~1.5 %).
> - The **gross margin** is reported as rising from 23.7 % to 31.9 % (**+8.2 pp**); the dataset, computed row-by-row, shows a slight **decline of −2.0 pp**.
>
> These gaps are likely due to rounding, alternative aggregation methods, or
> dataset versions used at report-writing time. This repository always uses
> the dataset-derived numbers and surfaces the discrepancies — a deliberate
> exercise in reproducible research. The headline result (statistically
> significant energy reduction with large Cohen's *d*) is robust either way;
> the secondary margin claim is not supported by the dataset as provided.

### Repository Structure

```
panificadora-chask-analysis/
├── data/
│   └── raw/dataset_panificadora.csv     # 29 monthly observations (Jan 2020 – May 2022)
├── notebooks/                           # Jupyter narratives (EDA, anomalies, tests, ROI)
├── src/panificadora/                    # Reusable analysis engine
│   ├── config.py                        # Paths, constants, KPI baselines
│   └── data_loader.py                   # Load + validate + feature engineering
├── reports/figures/                     # Generated figures (10 figures from the report)
├── dashboard/                           # Streamlit interactive dashboard
├── tests/                               # pytest test suite
├── docs/                                # MkDocs documentation site
└── .github/workflows/ci.yml             # Automated testing & linting
```

### Quick Start

```bash
# 1. Clone and enter the repo
git clone https://github.com/anthoadc-AI/panificadora-chask-analysis.git
cd panificadora-chask-analysis

# 2. Create a virtual environment (recommended)
python -m venv .venv && source .venv/bin/activate

# 3. Install in development mode
make install-dev

# 4. (Optional) Initialize Git with 4 phased commits + version tags
bash scripts/init_git_history.sh

# 5. Run the tests
make test

# 6. Launch the notebooks
make notebook

# 7. Or launch the dashboard
make dashboard
```

### Interactive Dashboard

The Streamlit dashboard (`make dashboard`) exposes the analysis with live controls:

- **ROI calculator** with sliders for energy tariff, investment, and downtime cost
- **Live anomaly tuning** for the Z-score threshold and Isolation Forest contamination / n_estimators
- **Period filter** to view Pre, Post, or both
- **Six tabs**: Overview · EDA · Anomalies · Statistics · ROI · Raw Data (with CSV download)

See [`dashboard/README.md`](dashboard/README.md) for the full feature list.

### Methodology

The analysis pipeline follows the same structure as the original closure report:

1. **Exploratory Data Analysis (EDA)** — Descriptive statistics by period, time-series visualizations, distribution comparisons, correlation matrix, energy-intensity tracking.
2. **Anomaly Detection** — Univariate via **Z-score** (|Z| > 2.0) and multivariate via **Isolation Forest** (200 trees, 10% contamination).
3. **Statistical Inference** — Shapiro–Wilk normality test → Student's *t* or Mann–Whitney U → **Cohen's *d*** effect size on every KPI.
4. **Trend Analysis** — Separate linear regressions for Pre and Post periods, with 12-month projection.
5. **ROI Quantification** — Energy savings, downtime reduction, payback curve against an estimated USD 85,000 investment.

### Tech Stack

| Layer | Tools |
| --- | --- |
| Core | pandas, numpy, scipy |
| ML | scikit-learn (Isolation Forest, Random Forest) |
| Statistics | scipy.stats, statsmodels |
| Visualization | matplotlib, seaborn, plotly |
| Dashboard | Streamlit |
| Testing | pytest, pytest-cov |
| Quality | ruff, mypy |
| CI/CD | GitHub Actions |
| Docs | MkDocs Material |

### Author

**Anthony Davila** — Mechanical Engineer · Project Director at INGEDAV S.R.L.
MIT xPRO Professional Certificate in Data Engineering

[LinkedIn](https://linkedin.com/in/anthony-davila-034b921ba) · [GitHub](https://github.com/anthoadc-AI)

---

## Español

### Descripción General

La **Panificadora Chask**, ubicada en Punata, Cochabamba (Bolivia), operaba con maquinaria obsoleta y semi-manual que limitaba su capacidad productiva, consumía ~55.000 kWh/mes y sufría fallas frecuentes. Entre diciembre de 2020 y junio de 2022, **INGEDAV S.R.L.** ejecutó un proyecto de modernización en cuatro fases que incluyó diagnóstico, rediseño CAD, fabricación e instalación de equipos de alta eficiencia (amasadora, laminadora, batidoras industriales), un Sistema de Gestión de Energía (EMS) y capacitación al personal.

Este repositorio reproduce, desde los datos crudos, el **análisis cuantitativo** que respaldó el informe de cierre del proyecto. Está construido como un proyecto de data engineering nivel portafolio: código modular en `src/`, notebooks reproducibles, dashboard Streamlit, suite completa de pytest, y CI automático en cada commit.

### Hallazgos Clave

| KPI | Pre-Intervención | Post-Intervención | Variación |
| --- | --- | --- | --- |
| Consumo energético (kWh/mes, media) | 49.703 | 42.023 | **−15,5%** |
| Intensidad energética (kWh/kg) | 3,69 | 3,14 | **−14,9%** |
| Fallas de máquina (por mes) | 7,05 | 8,78 | +24,5% |
| Tiempo inactivo (horas/mes) | 26,6 | 31,6 | +18,9% |
| Margen bruto (media mensual) | 23,3% | 21,3% | **−2,0 pp** |
| Consumo en estado estacionario (informe) | 55.000 kWh | 40.000 kWh | **−27%** |

> 📋 **Nota sobre reproducibilidad.** Dos cifras del informe de cierre no coinciden con el dataset al recalcularlas:
> - La **reducción energética** se reporta como −18,2 % en el informe; el dataset arroja **−15,5 %** (la media Pre difiere ~1,7 %, la Post ~1,5 %).
> - El **margen bruto** se reporta subiendo de 23,7 % a 31,9 % (**+8,2 pp**); el dataset, calculado fila por fila, muestra un leve **descenso de −2,0 pp**.
>
> Estas diferencias probablemente se deben a redondeos, métodos de agregación
> alternativos o versiones del dataset utilizadas al redactar el informe. Este
> repositorio siempre usa los números derivados del dataset y documenta las
> discrepancias — un ejercicio deliberado de investigación reproducible. El
> hallazgo principal (reducción energética estadísticamente significativa con
> *d* de Cohen grande) es robusto en cualquier caso; la afirmación secundaria
> sobre el margen no está respaldada por el dataset tal como fue entregado.

### Estructura del Repositorio

```
panificadora-chask-analysis/
├── data/
│   └── raw/dataset_panificadora.csv     # 29 observaciones mensuales (Ene 2020 – May 2022)
├── notebooks/                           # Narrativas Jupyter (EDA, anomalías, tests, ROI)
├── src/panificadora/                    # Motor de análisis reutilizable
│   ├── config.py                        # Rutas, constantes, baselines de KPIs
│   └── data_loader.py                   # Carga + validación + features derivadas
├── reports/figures/                     # Figuras generadas (las 10 del informe)
├── dashboard/                           # Dashboard interactivo Streamlit
├── tests/                               # Suite de tests pytest
├── docs/                                # Sitio de documentación MkDocs
└── .github/workflows/ci.yml             # Testing y linting automatizado
```

### Inicio Rápido

```bash
# 1. Clonar y entrar al repositorio
git clone https://github.com/anthoadc-AI/panificadora-chask-analysis.git
cd panificadora-chask-analysis

# 2. Crear un entorno virtual (recomendado)
python -m venv .venv && source .venv/bin/activate

# 3. Instalar en modo desarrollo
make install-dev

# 4. (Opcional) Inicializar Git con 4 commits por fase + tags semánticos
bash scripts/init_git_history.sh

# 5. Ejecutar los tests
make test

# 6. Abrir los notebooks
make notebook

# 7. O lanzar el dashboard
make dashboard
```

### Dashboard Interactivo

El dashboard Streamlit (`make dashboard`) expone el análisis con controles en vivo:

- **Calculadora de ROI** con sliders para tarifa eléctrica, inversión y costo de inactividad
- **Tuning de anomalías** en vivo: umbral Z-score y parámetros (contamination / n_estimators) de Isolation Forest
- **Filtro de periodo** para ver Pre, Post o ambos
- **Seis pestañas**: Resumen · EDA · Anomalías · Estadística · ROI · Datos crudos (con descarga CSV)

Ver [`dashboard/README.md`](dashboard/README.md) para la lista completa de funcionalidades.

### Metodología

El pipeline de análisis sigue la misma estructura del informe de cierre original:

1. **Análisis Exploratorio de Datos (EDA)** — Estadísticas descriptivas por periodo, visualizaciones de series temporales, comparación de distribuciones, matriz de correlación, evolución de la intensidad energética.
2. **Detección de Anomalías** — Univariada con **Z-score** (|Z| > 2,0) y multivariada con **Isolation Forest** (200 árboles, contaminación del 10%).
3. **Inferencia Estadística** — Test de normalidad **Shapiro–Wilk** → *t* de Student o Mann–Whitney U → tamaño de efecto **d de Cohen** en cada KPI.
4. **Análisis de Tendencias** — Regresiones lineales separadas para los periodos Pre y Post, con proyección a 12 meses.
5. **Cuantificación de ROI** — Ahorros energéticos, reducción de inactividad, curva de payback contra una inversión estimada de USD 85.000.

### Stack Tecnológico

| Capa | Herramientas |
| --- | --- |
| Núcleo | pandas, numpy, scipy |
| ML | scikit-learn (Isolation Forest, Random Forest) |
| Estadística | scipy.stats, statsmodels |
| Visualización | matplotlib, seaborn, plotly |
| Dashboard | Streamlit |
| Testing | pytest, pytest-cov |
| Calidad | ruff, mypy |
| CI/CD | GitHub Actions |
| Documentación | MkDocs Material |

### Autor

**Anthony Davila** — Ingeniero Mecánico · Director de Proyecto en INGEDAV S.R.L.
MIT xPRO Professional Certificate in Data Engineering

[LinkedIn](https://linkedin.com/in/anthony-davila-034b921ba) · [GitHub](https://github.com/anthoadc-AI)

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
