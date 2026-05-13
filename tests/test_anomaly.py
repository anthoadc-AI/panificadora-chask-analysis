"""Tests for the anomaly detection module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from panificadora.anomaly import (
    combined_anomaly_report,
    feature_importance_energy,
    isolation_forest_anomalies,
    zscore_anomalies,
)


class TestZScoreAnomalies:
    def test_returns_boolean_series(self, df: pd.DataFrame) -> None:
        result = zscore_anomalies(df["consumo_kwh"])
        assert result.dtype == bool

    def test_same_length_as_input(self, df: pd.DataFrame) -> None:
        result = zscore_anomalies(df["consumo_kwh"])
        assert len(result) == len(df)

    def test_constant_series_returns_no_anomalies(self) -> None:
        constant = pd.Series([5.0] * 10)
        result = zscore_anomalies(constant)
        assert not result.any()

    def test_obvious_outlier_detected(self) -> None:
        values = pd.Series([10.0] * 20 + [1000.0])
        result = zscore_anomalies(values)
        assert result.iloc[-1] == True  # noqa: E712 — pandas boolean comparison

    def test_threshold_controls_strictness(self) -> None:
        values = pd.Series(np.concatenate([np.random.normal(0, 1, 50), [3.0]]))
        # Higher threshold should detect strictly fewer anomalies
        strict = zscore_anomalies(values, threshold=2.5).sum()
        loose = zscore_anomalies(values, threshold=1.5).sum()
        assert strict <= loose


class TestIsolationForestAnomalies:
    def test_returns_boolean_series(self, df: pd.DataFrame) -> None:
        result = isolation_forest_anomalies(df)
        assert result.dtype == bool

    def test_same_length_as_input(self, df: pd.DataFrame) -> None:
        result = isolation_forest_anomalies(df)
        assert len(result) == len(df)

    def test_contamination_controls_anomaly_count(self, df: pd.DataFrame) -> None:
        n_low = isolation_forest_anomalies(df, contamination=0.05).sum()
        n_high = isolation_forest_anomalies(df, contamination=0.20).sum()
        assert n_low <= n_high

    def test_deterministic_with_seed(self, df: pd.DataFrame) -> None:
        r1 = isolation_forest_anomalies(df, random_state=42)
        r2 = isolation_forest_anomalies(df, random_state=42)
        pd.testing.assert_series_equal(r1, r2)


class TestFeatureImportance:
    def test_returns_series_and_r2(self, df: pd.DataFrame) -> None:
        importances, r2 = feature_importance_energy(df)
        assert isinstance(importances, pd.Series)
        assert isinstance(r2, float)

    def test_importances_sum_to_one(self, df: pd.DataFrame) -> None:
        importances, _ = feature_importance_energy(df)
        assert importances.sum() == pytest.approx(1.0)

    def test_importances_non_negative(self, df: pd.DataFrame) -> None:
        importances, _ = feature_importance_energy(df)
        assert (importances >= 0).all()

    def test_r2_in_valid_range(self, df: pd.DataFrame) -> None:
        # On training set R² should be reasonably high (0-1, sometimes >1 for tree models? No, capped at 1)
        _, r2 = feature_importance_energy(df)
        assert 0.0 <= r2 <= 1.0

    def test_target_excluded_from_features(self, df: pd.DataFrame) -> None:
        importances, _ = feature_importance_energy(df, target="consumo_kwh")
        assert "consumo_kwh" not in importances.index


class TestCombinedReport:
    def test_returns_dataframe(self, df: pd.DataFrame) -> None:
        report = combined_anomaly_report(df)
        assert isinstance(report, pd.DataFrame)

    def test_has_required_columns(self, df: pd.DataFrame) -> None:
        report = combined_anomaly_report(df)
        expected = {"consumo_kwh", "anomaly_zscore", "anomaly_isolation_forest", "any_anomaly"}
        assert expected.issubset(set(report.columns))

    def test_any_anomaly_is_union(self, df: pd.DataFrame) -> None:
        report = combined_anomaly_report(df)
        expected_union = report["anomaly_zscore"] | report["anomaly_isolation_forest"]
        pd.testing.assert_series_equal(report["any_anomaly"], expected_union, check_names=False)
