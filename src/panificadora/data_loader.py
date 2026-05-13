"""Dataset loading, validation, and feature engineering.

This module is the single source of truth for the analytical dataset.
It loads the raw CSV, validates schema integrity, and computes derived
columns used across the rest of the codebase.

Derived columns:
    - period: 'Pre' or 'Post' intervention label based on INTERVENTION_CUTOFF.
    - intensidad_kwh_kg: Energy intensity (kWh per kg produced).
    - margen_bruto_pct: Gross margin percentage from sales and costs.
    - mes / anio: Calendar month and year extracted from fecha.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from panificadora.config import (
    DATASET_PATH,
    EXPECTED_COLUMNS,
    EXPECTED_ROWS,
    INTERVENTION_CUTOFF,
    PERIOD_POST,
    PERIOD_PRE,
)


def load_dataset(path: Path | None = None, validate: bool = True) -> pd.DataFrame:
    """Load the Panificadora Chask monthly operations dataset.

    Reads the raw CSV, parses dates, sorts chronologically, and computes
    derived columns. Optionally validates schema integrity.

    Args:
        path: Path to the CSV file. Defaults to the canonical location
            under data/raw/.
        validate: If True, run full schema and integrity validation
            and raise ValueError on any inconsistency.

    Returns:
        DataFrame with original columns plus derived features:
        period, intensidad_kwh_kg, margen_bruto_pct, mes, anio.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        ValueError: If validation is enabled and the dataset fails any check.
    """
    csv_path = path if path is not None else DATASET_PATH

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {csv_path}. "
            "Make sure data/raw/dataset_panificadora.csv is present."
        )

    df = pd.read_csv(csv_path, parse_dates=["fecha"])
    df = df.sort_values("fecha").reset_index(drop=True)

    df = _add_derived_features(df)

    if validate:
        validate_dataset(df)

    return df


def _add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add columns derived from the raw data.

    Computed features:
        - period: Pre/Post intervention label
        - intensidad_kwh_kg: kWh consumed per kg produced (efficiency KPI)
        - margen_bruto_pct: 100 * (ventas - costos) / ventas
        - mes, anio: calendar components from fecha
    """
    df = df.copy()

    df["period"] = df["fecha"].apply(
        lambda d: PERIOD_PRE if d <= INTERVENTION_CUTOFF else PERIOD_POST
    )

    # Energy intensity: the KPI that matters most for efficiency analysis.
    # Guarded against zero production (shouldn't occur but defensive).
    df["intensidad_kwh_kg"] = df["consumo_kwh"] / df["produccion_kg"].replace(0, pd.NA)

    df["margen_bruto_pct"] = (
        100.0 * (df["ventas_usd"] - df["costos_usd"]) / df["ventas_usd"].replace(0, pd.NA)
    )

    df["mes"] = df["fecha"].dt.month
    df["anio"] = df["fecha"].dt.year

    return df


def validate_dataset(df: pd.DataFrame) -> None:
    """Validate dataset schema and integrity.

    Checks:
        1. All expected columns are present.
        2. Row count matches the expected 29 observations.
        3. No null values in raw columns.
        4. Date range is monotonic and covers Jan 2020 – May 2022.
        5. Numeric columns have non-negative values.
        6. Both Pre and Post periods are populated.

    Args:
        df: DataFrame returned by load_dataset.

    Raises:
        ValueError: With a descriptive message on the first failed check.
    """
    # Check 1: column presence
    missing = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {sorted(missing)}")

    # Check 2: row count
    if len(df) != EXPECTED_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_ROWS} rows, got {len(df)}. "
            "Dataset may be incomplete or contaminated."
        )

    # Check 3: nulls in raw columns
    raw_nulls = df[EXPECTED_COLUMNS].isna().sum()
    if raw_nulls.any():
        offenders = raw_nulls[raw_nulls > 0].to_dict()
        raise ValueError(f"Null values found in raw columns: {offenders}")

    # Check 4: chronological date range
    if not df["fecha"].is_monotonic_increasing:
        raise ValueError("Dates are not sorted chronologically.")

    expected_start = pd.Timestamp("2020-01-31")
    expected_end = pd.Timestamp("2022-05-31")
    if df["fecha"].min() != expected_start or df["fecha"].max() != expected_end:
        raise ValueError(
            f"Date range mismatch: got [{df['fecha'].min()}, {df['fecha'].max()}], "
            f"expected [{expected_start}, {expected_end}]"
        )

    # Check 5: non-negative numerics
    numeric_cols = [c for c in EXPECTED_COLUMNS if c != "fecha"]
    negatives = (df[numeric_cols] < 0).any()
    if negatives.any():
        offenders = negatives[negatives].index.tolist()
        raise ValueError(f"Negative values found in columns: {offenders}")

    # Check 6: both periods present
    if "period" in df.columns:
        period_counts = df["period"].value_counts()
        if PERIOD_PRE not in period_counts or PERIOD_POST not in period_counts:
            raise ValueError(
                f"Both Pre and Post periods must be present. Got: {period_counts.to_dict()}"
            )


def split_pre_post(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the dataset into Pre and Post intervention subsets.

    Args:
        df: DataFrame returned by load_dataset (must have 'period' column).

    Returns:
        Tuple (pre_df, post_df) with the two subsets.
    """
    if "period" not in df.columns:
        raise ValueError("DataFrame must contain a 'period' column. Did you call load_dataset?")

    pre_df = df[df["period"] == PERIOD_PRE].copy()
    post_df = df[df["period"] == PERIOD_POST].copy()

    return pre_df, post_df
