"""Tests for the ROI module."""

from __future__ import annotations

import pandas as pd
import pytest

from panificadora.roi import (
    compute_roi,
    downtime_savings,
    energy_savings,
    payback_curve,
)


class TestEnergySavings:
    def test_returns_two_floats(self, df: pd.DataFrame) -> None:
        monthly_kwh, annual_usd = energy_savings(df)
        assert isinstance(monthly_kwh, float)
        assert isinstance(annual_usd, float)

    def test_monthly_savings_positive(self, df: pd.DataFrame) -> None:
        """Headline finding: consumption decreased post-intervention."""
        monthly_kwh, _ = energy_savings(df)
        assert monthly_kwh > 0

    def test_annual_equals_monthly_times_12_times_rate(self, df: pd.DataFrame) -> None:
        rate = 0.10
        monthly_kwh, annual_usd = energy_savings(df, cost_per_kwh=rate)
        assert annual_usd == pytest.approx(monthly_kwh * rate * 12.0)


class TestDowntimeSavings:
    def test_returns_two_floats(self, df: pd.DataFrame) -> None:
        h, usd = downtime_savings(df)
        assert isinstance(h, float)
        assert isinstance(usd, float)

    def test_annual_consistent_with_hourly_rate(self, df: pd.DataFrame) -> None:
        rate = 15.0
        h, usd = downtime_savings(df, cost_per_hour=rate)
        assert usd == pytest.approx(h * rate * 12.0)


class TestComputeROI:
    def test_returns_complete_result(self, df: pd.DataFrame) -> None:
        roi = compute_roi(df)
        assert hasattr(roi, "total_annual_benefit_usd")
        assert hasattr(roi, "payback_months")
        assert hasattr(roi, "roi_year_1_pct")

    def test_total_benefit_is_sum_of_parts(self, df: pd.DataFrame) -> None:
        roi = compute_roi(df)
        expected_total = roi.energy_savings_annual_usd + roi.downtime_savings_annual_usd
        assert roi.total_annual_benefit_usd == pytest.approx(expected_total)

    def test_positive_total_implies_finite_payback(self, df: pd.DataFrame) -> None:
        roi = compute_roi(df)
        if roi.total_annual_benefit_usd > 0:
            assert roi.payback_months > 0
            assert roi.payback_months != float("inf")


class TestPaybackCurve:
    def test_correct_length(self) -> None:
        curve = payback_curve(monthly_benefit_usd=1000, investment_usd=12_000, horizon_months=24)
        assert len(curve) == 25  # 0..24 inclusive

    def test_starts_at_negative_investment(self) -> None:
        curve = payback_curve(monthly_benefit_usd=1000, investment_usd=12_000)
        assert curve.iloc[0]["net_position_usd"] == -12_000

    def test_breakeven_month_identified(self) -> None:
        """Investment 12k, benefit 1k/month → breakeven at month 12."""
        curve = payback_curve(monthly_benefit_usd=1000, investment_usd=12_000, horizon_months=24)
        first_paid = curve[curve["has_paid_back"]].iloc[0]
        assert first_paid["month"] == 12

    def test_monotonically_increasing(self) -> None:
        curve = payback_curve(monthly_benefit_usd=500, investment_usd=10_000)
        assert curve["net_position_usd"].is_monotonic_increasing
