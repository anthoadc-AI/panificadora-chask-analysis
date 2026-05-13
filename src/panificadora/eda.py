"""Exploratory Data Analysis: descriptive statistics and correlations.

This module provides the pure computation layer for EDA. Plotting lives
in `viz.py` so that the same numerical results can be visualized with
either matplotlib (static) or Plotly (interactive).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from panificadora.config import PERIOD_POST, PERIOD_PRE

# Variables analyzed throughout the report
KPI_COLUMNS: list[str] = [
    "consumo_kwh",
    "produccion_kg",
    "fallas_maquina",
    "tiempo_inactividad_horas",
    "ventas_usd",
    "costos_usd",
    "intensidad_kwh_kg",
    "margen_bruto_pct",
]


def describe_by_period(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Compute Pre/Post descriptive statistics for each KPI.

    Reproduces Section 4.1 of the closure report (Pre vs Post means,
    standard deviations and percentage change).

    Args:
        df: DataFrame from load_dataset (must contain 'period' column).
        columns: Subset of columns to describe. Defaults to KPI_COLUMNS.

    Returns:
        DataFrame indexed by variable with columns:
        mean_pre, mean_post, std_pre, std_post, pct_change, abs_change.
    """
    cols = columns if columns is not None else KPI_COLUMNS

    pre = df[df["period"] == PERIOD_PRE]
    post = df[df["period"] == PERIOD_POST]

    rows = []
    for col in cols:
        if col not in df.columns:
            continue
        mean_pre = pre[col].mean()
        mean_post = post[col].mean()
        std_pre = pre[col].std()
        std_post = post[col].std()
        pct = 100.0 * (mean_post - mean_pre) / mean_pre if mean_pre != 0 else np.nan

        rows.append(
            {
                "variable": col,
                "mean_pre": mean_pre,
                "mean_post": mean_post,
                "std_pre": std_pre,
                "std_post": std_post,
                "abs_change": mean_post - mean_pre,
                "pct_change": pct,
            }
        )

    return pd.DataFrame(rows).set_index("variable")


def correlation_matrix(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Compute Pearson correlation matrix for selected variables.

    Args:
        df: DataFrame from load_dataset.
        columns: Subset of columns to correlate. Defaults to KPI_COLUMNS.

    Returns:
        Square DataFrame of pairwise Pearson correlation coefficients.
    """
    cols = columns if columns is not None else KPI_COLUMNS
    available = [c for c in cols if c in df.columns]
    return df[available].corr(method="pearson")


def rolling_intensity(df: pd.DataFrame, window: int = 3) -> pd.Series:
    """Compute centered moving average of energy intensity (kWh/kg).

    Used for Figure 4 of the closure report to smooth month-to-month
    variability and reveal the underlying trend.

    Args:
        df: DataFrame with 'intensidad_kwh_kg' column, sorted by fecha.
        window: Number of months for the moving window (default: 3).

    Returns:
        Series of the rolling mean, indexed like the input DataFrame.
    """
    return df["intensidad_kwh_kg"].rolling(window=window, center=True, min_periods=1).mean()


def summarize_change(stats_df: pd.DataFrame, variable: str) -> str:
    """Format a single-line summary of a variable's Pre/Post change.

    Useful for quick CLI output and for embedding in notebook markdown.

    Args:
        stats_df: DataFrame returned by describe_by_period.
        variable: Row label (e.g. 'consumo_kwh').

    Returns:
        Human-readable string like:
        'consumo_kwh: 49,703 → 41,396 (-16.7%)'
    """
    row = stats_df.loc[variable]
    return (
        f"{variable}: {row['mean_pre']:,.0f} → {row['mean_post']:,.0f} "
        f"({row['pct_change']:+.1f}%)"
    )
