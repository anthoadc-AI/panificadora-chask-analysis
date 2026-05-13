"""Anomaly detection and feature importance.

Implements the two complementary anomaly detection methods described
in Section 5.2 of the closure report:

    - Z-score (univariate, |Z| > threshold)
    - Isolation Forest (multivariate, unsupervised ML)

Plus a Random Forest regressor for feature importance on energy
consumption, reproducing Figure 9 of the report.
"""

from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor

from panificadora.config import (
    ISOLATION_FOREST_CONTAMINATION,
    ISOLATION_FOREST_N_ESTIMATORS,
    RANDOM_STATE,
    ZSCORE_THRESHOLD,
)

# Variables used for multivariate anomaly detection (Section 5.2.2 of report)
ANOMALY_FEATURES: list[str] = [
    "consumo_kwh",
    "produccion_kg",
    "fallas_maquina",
    "tiempo_inactividad_horas",
    "intensidad_kwh_kg",
]


def zscore_anomalies(series: pd.Series, threshold: float = ZSCORE_THRESHOLD) -> pd.Series:
    """Flag univariate anomalies using the Z-score method.

    A point is anomalous when its standardized deviation from the mean
    exceeds the threshold in absolute value.

    Formula:
        Z = (x - mu) / sigma

    Args:
        series: Numeric series to analyze.
        threshold: |Z| cutoff above which a point is flagged.

    Returns:
        Boolean Series of the same length as input. True = anomaly.
    """
    mu = series.mean()
    sigma = series.std()
    if sigma == 0:
        return pd.Series(False, index=series.index)
    z = (series - mu) / sigma
    return z.abs() > threshold


def isolation_forest_anomalies(
    df: pd.DataFrame,
    features: list[str] | None = None,
    contamination: float = ISOLATION_FOREST_CONTAMINATION,
    n_estimators: int = ISOLATION_FOREST_N_ESTIMATORS,
    random_state: int = RANDOM_STATE,
) -> pd.Series:
    """Flag multivariate anomalies using Isolation Forest.

    Isolation Forest isolates anomalies by recursively partitioning the
    feature space; anomalies typically require fewer partitions to be
    isolated than normal points.

    Args:
        df: DataFrame containing the feature columns.
        features: Columns to use as features. Defaults to ANOMALY_FEATURES.
        contamination: Expected fraction of anomalies (default 10%).
        n_estimators: Number of trees in the forest (default 200).
        random_state: Seed for reproducibility.

    Returns:
        Boolean Series aligned with df. True = anomaly.
    """
    feat = features if features is not None else ANOMALY_FEATURES
    available = [c for c in feat if c in df.columns]
    X = df[available].to_numpy()

    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
    )
    # sklearn convention: -1 = anomaly, 1 = inlier
    predictions = model.fit_predict(X)
    return pd.Series(predictions == -1, index=df.index)


def feature_importance_energy(
    df: pd.DataFrame,
    target: str = "consumo_kwh",
    n_estimators: int = ISOLATION_FOREST_N_ESTIMATORS,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.Series, float]:
    """Estimate variable importance on energy consumption.

    Fits a Random Forest regressor with `target` as the dependent
    variable and returns feature importances along with R² on the
    training set (the dataset is too small for a meaningful test split).

    Reproduces Figure 9 of the closure report.

    Args:
        df: DataFrame with all features and the target column.
        target: Column to predict (default: 'consumo_kwh').
        n_estimators: Number of trees (default 200).
        random_state: Seed for reproducibility.

    Returns:
        Tuple of:
            - Series of importances, indexed by feature name, sorted desc.
            - R² score on the full dataset.
    """
    feature_cols = [
        "produccion_kg",
        "fallas_maquina",
        "mantenimiento",
        "tiempo_inactividad_horas",
        "ventas_usd",
        "costos_usd",
    ]
    available = [c for c in feature_cols if c in df.columns and c != target]
    X = df[available]
    y = df[target]

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
    )
    model.fit(X, y)

    importances = pd.Series(model.feature_importances_, index=available).sort_values(
        ascending=False
    )

    r2 = float(model.score(X, y))

    return importances, r2


def combined_anomaly_report(df: pd.DataFrame) -> pd.DataFrame:
    """Build a per-month anomaly report combining both methods.

    Args:
        df: DataFrame from load_dataset.

    Returns:
        DataFrame indexed by fecha with columns:
            - consumo_kwh
            - anomaly_zscore (bool)
            - anomaly_isolation_forest (bool)
            - any_anomaly (bool)
    """
    z_flags = zscore_anomalies(df["consumo_kwh"])
    if_flags = isolation_forest_anomalies(df)

    report = pd.DataFrame(
        {
            "fecha": df["fecha"].values,
            "consumo_kwh": df["consumo_kwh"].values,
            "anomaly_zscore": z_flags.values,
            "anomaly_isolation_forest": if_flags.values,
        }
    )
    report["any_anomaly"] = report["anomaly_zscore"] | report["anomaly_isolation_forest"]
    return report.set_index("fecha")
