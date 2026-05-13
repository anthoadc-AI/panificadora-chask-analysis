"""Tests for the EDA module."""

from __future__ import annotations

import pandas as pd
import pytest

from panificadora.eda import (
    correlation_matrix,
    describe_by_period,
    rolling_intensity,
    summarize_change,
)


class TestDescribeByPeriod:
    def test_returns_dataframe(self, df: pd.DataFrame) -> None:
        result = describe_by_period(df)
        assert isinstance(result, pd.DataFrame)

    def test_contains_expected_columns(self, df: pd.DataFrame) -> None:
        result = describe_by_period(df)
        expected = {"mean_pre", "mean_post", "std_pre", "std_post", "abs_change", "pct_change"}
        assert expected.issubset(set(result.columns))

    def test_consumo_kwh_decreases(self, df: pd.DataFrame) -> None:
        result = describe_by_period(df)
        row = result.loc["consumo_kwh"]
        assert row["pct_change"] < 0, "Energy consumption should decrease post-intervention"

    def test_consumo_kwh_decrease_in_expected_range(self, df: pd.DataFrame) -> None:
        result = describe_by_period(df)
        pct = result.loc["consumo_kwh", "pct_change"]
        # Report cites -18.2%; actual ~-15.5% — accept anywhere from -12 to -22%
        assert -22 < pct < -12, f"Energy reduction {pct:.1f}% outside expected band"

    def test_subset_of_columns(self, df: pd.DataFrame) -> None:
        result = describe_by_period(df, columns=["consumo_kwh"])
        assert len(result) == 1
        assert result.index[0] == "consumo_kwh"


class TestCorrelationMatrix:
    def test_returns_square_dataframe(self, df: pd.DataFrame) -> None:
        corr = correlation_matrix(df)
        assert corr.shape[0] == corr.shape[1]

    def test_diagonal_is_one(self, df: pd.DataFrame) -> None:
        corr = correlation_matrix(df)
        for i in range(len(corr)):
            assert corr.iloc[i, i] == pytest.approx(1.0)

    def test_values_bounded(self, df: pd.DataFrame) -> None:
        corr = correlation_matrix(df)
        assert (corr.abs() <= 1.0).all().all()

    def test_symmetric(self, df: pd.DataFrame) -> None:
        corr = correlation_matrix(df)
        # Pearson correlation is symmetric: r(X,Y) == r(Y,X)
        for i in range(len(corr)):
            for j in range(len(corr)):
                assert corr.iloc[i, j] == pytest.approx(corr.iloc[j, i])


class TestRollingIntensity:
    def test_same_length_as_input(self, df: pd.DataFrame) -> None:
        smoothed = rolling_intensity(df, window=3)
        assert len(smoothed) == len(df)

    def test_no_extreme_outliers_after_smoothing(self, df: pd.DataFrame) -> None:
        smoothed = rolling_intensity(df, window=3)
        # Smoothed values should fall within the original range
        original = df["intensidad_kwh_kg"]
        assert smoothed.min() >= original.min() - 0.01
        assert smoothed.max() <= original.max() + 0.01


class TestSummarizeChange:
    def test_summary_format(self, df: pd.DataFrame) -> None:
        stats_df = describe_by_period(df)
        summary = summarize_change(stats_df, "consumo_kwh")
        assert "consumo_kwh" in summary
        assert "→" in summary
        assert "%" in summary
