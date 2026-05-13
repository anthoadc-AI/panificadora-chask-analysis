"""Project-wide configuration: paths, constants, and reference values.

All hard-coded values from the closure report (cut-off dates, KPI baselines,
energy cost assumptions) live here so they can be overridden centrally.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# ===== Paths =====
# Anchor: this file lives at src/panificadora/config.py, so go up 3 levels.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"

REPORTS_DIR: Path = PROJECT_ROOT / "reports"
FIGURES_DIR: Path = REPORTS_DIR / "figures"

DATASET_PATH: Path = RAW_DATA_DIR / "dataset_panificadora.csv"

# ===== Intervention timeline =====
# The new machinery became fully operational in August 2021.
# The cut-off marks the boundary between Pre and Post intervention periods.
INTERVENTION_CUTOFF: pd.Timestamp = pd.Timestamp("2021-08-31")

PROJECT_START: pd.Timestamp = pd.Timestamp("2020-12-21")
PROJECT_END: pd.Timestamp = pd.Timestamp("2022-06-04")

# ===== Expected dataset schema =====
EXPECTED_COLUMNS: list[str] = [
    "fecha",
    "produccion_kg",
    "consumo_kwh",
    "fallas_maquina",
    "mantenimiento",
    "ventas_usd",
    "costos_usd",
    "tiempo_inactividad_horas",
]

EXPECTED_ROWS: int = 29

# ===== Period labels =====
PERIOD_PRE: str = "Pre"
PERIOD_POST: str = "Post"

# ===== Economic assumptions for ROI =====
# Reference energy cost in USD per kWh for Bolivia industrial tariff (2022).
ENERGY_COST_USD_PER_KWH: float = 0.065

# Estimated total project investment in USD (from closure report Section 7.4).
PROJECT_INVESTMENT_USD: float = 85_000.0

# ===== Statistical analysis defaults =====
ALPHA: float = 0.05  # Significance level for hypothesis tests
ZSCORE_THRESHOLD: float = 2.0  # |Z| threshold for univariate anomaly detection
ISOLATION_FOREST_CONTAMINATION: float = 0.10
ISOLATION_FOREST_N_ESTIMATORS: int = 200
RANDOM_STATE: int = 42  # For reproducibility across all stochastic methods

# ===== Visualization defaults =====
FIGURE_DPI: int = 120
COLOR_PRE: str = "#E74C3C"  # Red for pre-intervention
COLOR_POST: str = "#27AE60"  # Green for post-intervention
COLOR_NEUTRAL: str = "#3498DB"
