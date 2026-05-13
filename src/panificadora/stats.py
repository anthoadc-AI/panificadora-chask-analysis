"""Statistical inference: normality tests, group comparisons, regression.

Implements the protocol described in Section 6 of the closure report:

    1. Shapiro-Wilk for normality of each group.
    2. Student's t (parametric) or Mann-Whitney U (non-parametric)
       depending on normality outcome.
    3. Cohen's d to quantify practical effect size.
    4. Linear regression for Pre/Post trend analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from scipy import stats

from panificadora.config import ALPHA, PERIOD_POST, PERIOD_PRE


@dataclass
class GroupTestResult:
    """Result of comparing a single variable across Pre/Post groups."""

    variable: str
    n_pre: int
    n_post: int
    mean_pre: float
    mean_post: float
    test_used: Literal["t-test", "mann-whitney"]
    statistic: float
    p_value: float
    significant: bool  # at alpha
    cohens_d: float
    effect_magnitude: Literal["negligible", "small", "medium", "large"]
    pre_normal: bool
    post_normal: bool


def shapiro_wilk(values: np.ndarray | pd.Series, alpha: float = ALPHA) -> tuple[float, bool]:
    """Run the Shapiro-Wilk normality test.

    H0: data is drawn from a normal distribution.

    Args:
        values: 1D numeric data.
        alpha: Significance level.

    Returns:
        Tuple (p_value, is_normal). is_normal is True if p > alpha.
    """
    arr = np.asarray(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) < 3:
        return float("nan"), False
    _, p = stats.shapiro(arr)
    return float(p), bool(p > alpha)


def cohens_d(group_a: np.ndarray | pd.Series, group_b: np.ndarray | pd.Series) -> float:
    """Compute Cohen's d effect size between two groups.

    Uses the pooled standard deviation (unbiased, n-1 denominator).
    Sign convention: positive d means group_b > group_a.

    Args:
        group_a: Reference group (e.g. Pre).
        group_b: Comparison group (e.g. Post).

    Returns:
        Cohen's d as a float. NaN if pooled std is zero.
    """
    a = np.asarray(group_a, dtype=float)
    b = np.asarray(group_b, dtype=float)
    a = a[~np.isnan(a)]
    b = b[~np.isnan(b)]

    n_a, n_b = len(a), len(b)
    if n_a < 2 or n_b < 2:
        return float("nan")

    var_a = a.var(ddof=1)
    var_b = b.var(ddof=1)
    pooled_std = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))

    if pooled_std == 0:
        return float("nan")

    return float((b.mean() - a.mean()) / pooled_std)


def classify_effect(d: float) -> Literal["negligible", "small", "medium", "large"]:
    """Classify Cohen's d magnitude per standard interpretive ranges.

    | |d|          | Magnitude   |
    | < 0.2        | negligible  |
    | 0.2 to 0.5   | small       |
    | 0.5 to 0.8   | medium      |
    | > 0.8        | large       |
    """
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    if abs_d < 0.5:
        return "small"
    if abs_d < 0.8:
        return "medium"
    return "large"


def compare_groups(
    df: pd.DataFrame,
    variable: str,
    group_col: str = "period",
    group_a: str = PERIOD_PRE,
    group_b: str = PERIOD_POST,
    alpha: float = ALPHA,
) -> GroupTestResult:
    """Run the full statistical comparison protocol for one variable.

    Steps:
        1. Test normality of each group (Shapiro-Wilk).
        2. Pick t-test if both groups are normal, else Mann-Whitney U.
        3. Compute Cohen's d.

    Args:
        df: DataFrame containing variable and group_col.
        variable: Column name to compare across groups.
        group_col: Column distinguishing the two groups.
        group_a: Value in group_col defining the first (reference) group.
        group_b: Value in group_col defining the second (comparison) group.
        alpha: Significance level for both normality and inference.

    Returns:
        GroupTestResult with all statistics needed to report the outcome.
    """
    a = df.loc[df[group_col] == group_a, variable].dropna()
    b = df.loc[df[group_col] == group_b, variable].dropna()

    _, pre_normal = shapiro_wilk(a, alpha=alpha)
    _, post_normal = shapiro_wilk(b, alpha=alpha)

    if pre_normal and post_normal:
        stat, p = stats.ttest_ind(a, b, equal_var=False)
        test_used: Literal["t-test", "mann-whitney"] = "t-test"
    else:
        stat, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        test_used = "mann-whitney"

    d = cohens_d(a, b)

    return GroupTestResult(
        variable=variable,
        n_pre=len(a),
        n_post=len(b),
        mean_pre=float(a.mean()),
        mean_post=float(b.mean()),
        test_used=test_used,
        statistic=float(stat),
        p_value=float(p),
        significant=bool(p < alpha),
        cohens_d=d,
        effect_magnitude=classify_effect(d),
        pre_normal=pre_normal,
        post_normal=post_normal,
    )


def compare_all_variables(df: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    """Run compare_groups across multiple variables and tabulate results.

    Args:
        df: DataFrame with 'period' column.
        variables: List of column names to test.

    Returns:
        DataFrame indexed by variable with all key statistics as columns.
    """
    results = [compare_groups(df, v) for v in variables if v in df.columns]
    rows = [
        {
            "variable": r.variable,
            "n_pre": r.n_pre,
            "n_post": r.n_post,
            "mean_pre": r.mean_pre,
            "mean_post": r.mean_post,
            "test": r.test_used,
            "p_value": r.p_value,
            "significant": r.significant,
            "cohens_d": r.cohens_d,
            "effect": r.effect_magnitude,
        }
        for r in results
    ]
    return pd.DataFrame(rows).set_index("variable")


@dataclass
class RegressionFit:
    """Output of a simple linear regression fit on a time series."""

    n: int
    slope: float
    intercept: float
    r_squared: float
    p_value: float
    std_err: float


def fit_linear_trend(x: np.ndarray | pd.Series, y: np.ndarray | pd.Series) -> RegressionFit:
    """Fit y = slope * x + intercept using OLS.

    Used in Section 6.5 of the report to compare Pre vs Post energy trends.

    Args:
        x: Independent variable (e.g. month index).
        y: Dependent variable (e.g. consumo_kwh).

    Returns:
        RegressionFit with slope, intercept, R² and inferential stats.
    """
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)

    result = stats.linregress(x_arr, y_arr)
    return RegressionFit(
        n=len(x_arr),
        slope=float(result.slope),
        intercept=float(result.intercept),
        r_squared=float(result.rvalue**2),
        p_value=float(result.pvalue),
        std_err=float(result.stderr),
    )


def project_trend(fit: RegressionFit, x_future: np.ndarray | pd.Series) -> np.ndarray:
    """Project a fitted regression line onto future x-values."""
    x_arr = np.asarray(x_future, dtype=float)
    return fit.slope * x_arr + fit.intercept
