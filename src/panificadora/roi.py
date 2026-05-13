"""Return on Investment quantification.

Implements Section 7.4 of the closure report:
    - Annualized energy savings from kWh reduction.
    - Annualized savings from downtime reduction.
    - Cumulative payback curve against project investment.

All economic assumptions live in `config.py` for transparency and
easy override (e.g. for sensitivity analysis).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from panificadora.config import (
    ENERGY_COST_USD_PER_KWH,
    PERIOD_POST,
    PERIOD_PRE,
    PROJECT_INVESTMENT_USD,
)

# Reference labor cost per hour of downtime (USD).
# Conservative estimate: includes idle labor + lost margin.
DOWNTIME_COST_USD_PER_HOUR: float = 12.0


@dataclass
class ROIResult:
    """Aggregate financial outcome of the intervention."""

    energy_kwh_saved_monthly: float
    energy_savings_annual_usd: float
    downtime_hours_saved_monthly: float
    downtime_savings_annual_usd: float
    total_annual_benefit_usd: float
    investment_usd: float
    payback_months: float
    roi_year_1_pct: float


def energy_savings(
    df: pd.DataFrame,
    cost_per_kwh: float = ENERGY_COST_USD_PER_KWH,
) -> tuple[float, float]:
    """Quantify monthly kWh savings and the equivalent annual USD savings.

    Args:
        df: DataFrame from load_dataset with 'period' and 'consumo_kwh'.
        cost_per_kwh: Tariff in USD per kWh.

    Returns:
        Tuple (kwh_saved_per_month, usd_saved_per_year).
    """
    pre_mean = df.loc[df["period"] == PERIOD_PRE, "consumo_kwh"].mean()
    post_mean = df.loc[df["period"] == PERIOD_POST, "consumo_kwh"].mean()
    monthly_savings_kwh = float(pre_mean - post_mean)
    annual_savings_usd = monthly_savings_kwh * cost_per_kwh * 12.0
    return monthly_savings_kwh, annual_savings_usd


def downtime_savings(
    df: pd.DataFrame,
    cost_per_hour: float = DOWNTIME_COST_USD_PER_HOUR,
) -> tuple[float, float]:
    """Quantify monthly hours of downtime saved and equivalent annual USD.

    Note: The closure report observes a small *increase* in downtime in
    the immediate Post period due to commissioning and calibration of
    new equipment. This function returns the raw arithmetic difference;
    interpret accordingly.

    Args:
        df: DataFrame with 'period' and 'tiempo_inactividad_horas'.
        cost_per_hour: Cost imputed per hour of downtime (USD).

    Returns:
        Tuple (hours_saved_per_month, usd_saved_per_year).
    """
    pre_mean = df.loc[df["period"] == PERIOD_PRE, "tiempo_inactividad_horas"].mean()
    post_mean = df.loc[df["period"] == PERIOD_POST, "tiempo_inactividad_horas"].mean()
    monthly_hours_saved = float(pre_mean - post_mean)
    annual_savings_usd = monthly_hours_saved * cost_per_hour * 12.0
    return monthly_hours_saved, annual_savings_usd


def compute_roi(
    df: pd.DataFrame,
    investment_usd: float = PROJECT_INVESTMENT_USD,
    cost_per_kwh: float = ENERGY_COST_USD_PER_KWH,
    downtime_cost_per_hour: float = DOWNTIME_COST_USD_PER_HOUR,
) -> ROIResult:
    """Aggregate all financial benefits and compute payback metrics.

    Caveat (Section 7.4 of report): This calculation captures only the
    benefits directly quantifiable from the dataset (energy + downtime).
    It excludes the +50% production capacity gain, quality improvements,
    and recovered lost sales, so the actual payback is meaningfully
    shorter than the figure reported here.

    Args:
        df: DataFrame from load_dataset.
        investment_usd: Total project cost (default from config).
        cost_per_kwh: Energy tariff.
        downtime_cost_per_hour: Imputed downtime cost.

    Returns:
        ROIResult with all financial KPIs.
    """
    kwh_saved, energy_usd = energy_savings(df, cost_per_kwh)
    hours_saved, downtime_usd = downtime_savings(df, downtime_cost_per_hour)

    total_annual = energy_usd + downtime_usd

    if total_annual > 0:
        payback_months = (investment_usd / total_annual) * 12.0
    else:
        payback_months = float("inf")

    roi_y1_pct = 100.0 * (total_annual - investment_usd) / investment_usd

    return ROIResult(
        energy_kwh_saved_monthly=kwh_saved,
        energy_savings_annual_usd=energy_usd,
        downtime_hours_saved_monthly=hours_saved,
        downtime_savings_annual_usd=downtime_usd,
        total_annual_benefit_usd=total_annual,
        investment_usd=investment_usd,
        payback_months=payback_months,
        roi_year_1_pct=roi_y1_pct,
    )


def payback_curve(
    monthly_benefit_usd: float,
    investment_usd: float = PROJECT_INVESTMENT_USD,
    horizon_months: int = 144,
) -> pd.DataFrame:
    """Build the cumulative payback curve.

    Args:
        monthly_benefit_usd: Net benefit per month (annual / 12).
        investment_usd: Up-front project cost.
        horizon_months: Number of months to project (default 12 years).

    Returns:
        DataFrame with columns:
            - month (int, 0..horizon_months)
            - cumulative_benefit_usd
            - net_position_usd  (= cumulative_benefit - investment)
            - has_paid_back  (bool)
    """
    months = np.arange(horizon_months + 1)
    cumulative = months * monthly_benefit_usd
    net = cumulative - investment_usd
    return pd.DataFrame(
        {
            "month": months,
            "cumulative_benefit_usd": cumulative,
            "net_position_usd": net,
            "has_paid_back": net >= 0,
        }
    )
