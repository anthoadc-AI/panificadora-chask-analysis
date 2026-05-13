"""Tests for the statistical inference module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from panificadora.stats import (
    classify_effect,
    cohens_d,
    compare_all_variables,
    compare_groups,
    fit_linear_trend,
    project_trend,
    shapiro_wilk,
)


class TestShapiroWilk:
    def test_normal_data_passes(self) -> None:
        rng = np.random.default_rng(seed=42)
        data = rng.normal(0, 1, 100)
        p, is_normal = shapiro_wilk(data)
        assert is_normal
        assert 0 <= p <= 1

    def test_uniform_data_rejected(self) -> None:
        rng = np.random.default_rng(seed=42)
        data = rng.uniform(0, 1, 100)
        _, is_normal = shapiro_wilk(data)
        assert not is_normal

    def test_handles_nans(self) -> None:
        data = np.array([1.0, 2.0, np.nan, 3.0, 4.0, 5.0])
        p, _ = shapiro_wilk(data)
        # Should return a valid p without crashing
        assert 0 <= p <= 1 or np.isnan(p)


class TestCohensD:
    def test_zero_when_identical(self) -> None:
        a = np.array([1.0, 2.0, 3.0, 4.0])
        b = np.array([1.0, 2.0, 3.0, 4.0])
        d = cohens_d(a, b)
        assert d == pytest.approx(0.0)

    def test_positive_when_b_larger(self) -> None:
        a = np.array([1.0, 2.0, 3.0, 4.0])
        b = np.array([5.0, 6.0, 7.0, 8.0])
        d = cohens_d(a, b)
        assert d > 0

    def test_negative_when_b_smaller(self) -> None:
        a = np.array([5.0, 6.0, 7.0, 8.0])
        b = np.array([1.0, 2.0, 3.0, 4.0])
        d = cohens_d(a, b)
        assert d < 0


class TestClassifyEffect:
    @pytest.mark.parametrize(
        "d,expected",
        [
            (0.0, "negligible"),
            (0.1, "negligible"),
            (0.3, "small"),
            (0.6, "medium"),
            (1.0, "large"),
            (-1.5, "large"),
        ],
    )
    def test_classification_thresholds(self, d: float, expected: str) -> None:
        assert classify_effect(d) == expected


class TestCompareGroups:
    def test_returns_result_object(self, df: pd.DataFrame) -> None:
        result = compare_groups(df, "consumo_kwh")
        assert hasattr(result, "p_value")
        assert hasattr(result, "cohens_d")

    def test_consumo_kwh_significant(self, df: pd.DataFrame) -> None:
        """The headline finding: energy consumption is significantly different."""
        result = compare_groups(df, "consumo_kwh")
        assert result.significant
        assert result.p_value < 0.05
        assert result.effect_magnitude == "large"

    def test_means_match_describe(self, df: pd.DataFrame) -> None:
        """Sanity check: stats means should match direct pandas means."""
        result = compare_groups(df, "consumo_kwh")
        from panificadora.config import PERIOD_POST, PERIOD_PRE

        expected_pre = df.loc[df["period"] == PERIOD_PRE, "consumo_kwh"].mean()
        expected_post = df.loc[df["period"] == PERIOD_POST, "consumo_kwh"].mean()
        assert result.mean_pre == pytest.approx(expected_pre)
        assert result.mean_post == pytest.approx(expected_post)


class TestCompareAllVariables:
    def test_returns_dataframe(self, df: pd.DataFrame) -> None:
        result = compare_all_variables(df, ["consumo_kwh", "produccion_kg"])
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2


class TestRegression:
    def test_perfect_linear_fit(self) -> None:
        x = np.arange(10)
        y = 2.0 * x + 3.0  # slope=2, intercept=3
        fit = fit_linear_trend(x, y)
        assert fit.slope == pytest.approx(2.0)
        assert fit.intercept == pytest.approx(3.0)
        assert fit.r_squared == pytest.approx(1.0)

    def test_project_extrapolates_linearly(self) -> None:
        x = np.arange(10)
        y = 2.0 * x + 3.0
        fit = fit_linear_trend(x, y)
        future = project_trend(fit, np.array([20.0]))
        assert future[0] == pytest.approx(43.0)  # 2*20+3
