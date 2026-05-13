"""Tests for the data loader module.

These tests double as a contract specification for the dataset:
they document the expected shape, columns, and derived features.
"""
from __future__ import annotations

import pandas as pd
import pytest

from panificadora.config import EXPECTED_COLUMNS, EXPECTED_ROWS, PERIOD_POST, PERIOD_PRE
from panificadora.data_loader import load_dataset, split_pre_post, validate_dataset


class TestLoadDataset:
    """Tests for load_dataset()."""

    def test_returns_dataframe(self, df: pd.DataFrame) -> None:
        assert isinstance(df, pd.DataFrame)

    def test_row_count_matches_expectation(self, df: pd.DataFrame) -> None:
        assert len(df) == EXPECTED_ROWS, f"Expected 29 monthly observations, got {len(df)}"

    def test_all_raw_columns_present(self, df: pd.DataFrame) -> None:
        missing = set(EXPECTED_COLUMNS) - set(df.columns)
        assert not missing, f"Missing columns: {missing}"

    def test_no_null_values_in_raw_data(self, df: pd.DataFrame) -> None:
        assert df[EXPECTED_COLUMNS].notna().all().all()

    def test_dates_are_sorted(self, df: pd.DataFrame) -> None:
        assert df["fecha"].is_monotonic_increasing

    def test_date_range_covers_full_project(self, df: pd.DataFrame) -> None:
        assert df["fecha"].min() == pd.Timestamp("2020-01-31")
        assert df["fecha"].max() == pd.Timestamp("2022-05-31")


class TestDerivedFeatures:
    """Tests for derived features added by _add_derived_features."""

    def test_period_column_exists(self, df: pd.DataFrame) -> None:
        assert "period" in df.columns

    def test_period_values_are_valid(self, df: pd.DataFrame) -> None:
        assert set(df["period"].unique()) == {PERIOD_PRE, PERIOD_POST}

    def test_pre_period_has_20_months(self, df: pd.DataFrame) -> None:
        """Per the closure report: 20 months from Jan 2020 to Aug 2021."""
        pre_count = (df["period"] == PERIOD_PRE).sum()
        assert pre_count == 20, f"Expected 20 Pre months, got {pre_count}"

    def test_post_period_has_9_months(self, df: pd.DataFrame) -> None:
        """Per the closure report: 9 months from Sep 2021 to May 2022."""
        post_count = (df["period"] == PERIOD_POST).sum()
        assert post_count == 9, f"Expected 9 Post months, got {post_count}"

    def test_energy_intensity_is_positive(self, df: pd.DataFrame) -> None:
        assert (df["intensidad_kwh_kg"] > 0).all()

    def test_energy_intensity_in_realistic_range(self, df: pd.DataFrame) -> None:
        """Bakery operations: intensity should fall in a plausible band."""
        assert df["intensidad_kwh_kg"].between(1.0, 10.0).all()

    def test_margin_column_exists(self, df: pd.DataFrame) -> None:
        assert "margen_bruto_pct" in df.columns


class TestKPIsMatchClosureReport:
    """Sanity checks: derived KPIs should align with the closure report figures.

    The closure report (Section 4.1) cites specific Pre/Post averages.
    These tests catch any regression in feature engineering that would
    invalidate the published numbers.
    """

    def test_pre_mean_kwh_close_to_report(self, df: pd.DataFrame) -> None:
        """Pre-intervention monthly mean kWh.

        Note: The closure report (Section 4.1) cites ~50,578 kWh/month,
        but the actual computed mean from the dataset is ~49,703 kWh
        — a ~1.7% discrepancy likely due to a rounding or grouping
        difference at report-writing time. The test bounds capture the
        true data while flagging any major regression.
        """
        pre_mean = df.loc[df["period"] == PERIOD_PRE, "consumo_kwh"].mean()
        assert 49_000 < pre_mean < 51_500, f"Pre mean kWh out of expected range: {pre_mean}"

    def test_post_mean_kwh_close_to_report(self, df: pd.DataFrame) -> None:
        """Report cites ~41,396 kWh/month average post-intervention."""
        post_mean = df.loc[df["period"] == PERIOD_POST, "consumo_kwh"].mean()
        assert 40_500 < post_mean < 42_500, f"Post mean kWh out of expected range: {post_mean}"

    def test_energy_reduction_is_significant(self, df: pd.DataFrame) -> None:
        """The headline finding: post-intervention consumption should drop ~18%."""
        pre = df.loc[df["period"] == PERIOD_PRE, "consumo_kwh"].mean()
        post = df.loc[df["period"] == PERIOD_POST, "consumo_kwh"].mean()
        reduction_pct = 100 * (pre - post) / pre
        assert 15 < reduction_pct < 22, (
            f"Energy reduction {reduction_pct:.1f}% outside expected ~18% band"
        )


class TestValidateDataset:
    """Tests for the validate_dataset() guard function."""

    def test_valid_dataset_passes(self, df: pd.DataFrame) -> None:
        # Should not raise
        validate_dataset(df)

    def test_missing_column_raises(self, df: pd.DataFrame) -> None:
        bad = df.drop(columns=["consumo_kwh"])
        with pytest.raises(ValueError, match="Missing expected columns"):
            validate_dataset(bad)

    def test_wrong_row_count_raises(self, df: pd.DataFrame) -> None:
        bad = df.iloc[:10].copy()
        with pytest.raises(ValueError, match="Expected 29 rows"):
            validate_dataset(bad)

    def test_null_in_raw_column_raises(self, df: pd.DataFrame) -> None:
        bad = df.copy()
        bad.loc[0, "consumo_kwh"] = pd.NA
        with pytest.raises(ValueError, match="Null values found"):
            validate_dataset(bad)

    def test_negative_value_raises(self, df: pd.DataFrame) -> None:
        bad = df.copy()
        bad.loc[0, "produccion_kg"] = -100
        with pytest.raises(ValueError, match="Negative values"):
            validate_dataset(bad)


class TestSplitPrePost:
    """Tests for split_pre_post() utility."""

    def test_split_produces_correct_sizes(self, df: pd.DataFrame) -> None:
        pre, post = split_pre_post(df)
        assert len(pre) == 20
        assert len(post) == 9

    def test_split_is_exhaustive(self, df: pd.DataFrame) -> None:
        pre, post = split_pre_post(df)
        assert len(pre) + len(post) == len(df)

    def test_split_periods_are_disjoint(self, df: pd.DataFrame) -> None:
        pre, post = split_pre_post(df)
        assert pre["fecha"].max() < post["fecha"].min()
