"""Smoke tests for the visualization module.

These tests don't validate aesthetics — they validate that every plotting
function executes end-to-end and returns the expected object type.
This catches API breaks (e.g. when matplotlib or Plotly change signatures).
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # Headless backend before any pyplot import

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go

from panificadora.eda import correlation_matrix
from panificadora.roi import compute_roi
from panificadora.stats import compare_all_variables
from panificadora.anomaly import feature_importance_energy
from panificadora.viz import (
    FIGURE_FILENAMES,
    KPIS_FOR_BOXPLOT,
    generate_all_static_figures,
    plot_anomalies_interactive,
    plot_anomalies_static,
    plot_boxplots_interactive,
    plot_boxplots_static,
    plot_correlation_interactive,
    plot_correlation_static,
    plot_feature_importance_interactive,
    plot_feature_importance_static,
    plot_intensity_interactive,
    plot_intensity_static,
    plot_roi_interactive,
    plot_roi_static,
    plot_sales_margin_interactive,
    plot_sales_margin_static,
    plot_stat_tests_interactive,
    plot_stat_tests_static,
    plot_timeseries_interactive,
    plot_timeseries_static,
    plot_trends_interactive,
    plot_trends_static,
)


class TestStaticPlots:
    """Each static plot should return a matplotlib Figure."""

    def test_timeseries(self, df: pd.DataFrame) -> None:
        fig = plot_timeseries_static(df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_boxplots(self, df: pd.DataFrame) -> None:
        fig = plot_boxplots_static(df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_correlation(self, df: pd.DataFrame) -> None:
        corr = correlation_matrix(df)
        fig = plot_correlation_static(corr)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_intensity(self, df: pd.DataFrame) -> None:
        fig = plot_intensity_static(df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_stat_tests(self, df: pd.DataFrame) -> None:
        results = compare_all_variables(df, KPIS_FOR_BOXPLOT)
        fig = plot_stat_tests_static(results)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_anomalies(self, df: pd.DataFrame) -> None:
        fig = plot_anomalies_static(df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_trends(self, df: pd.DataFrame) -> None:
        fig = plot_trends_static(df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_roi(self, df: pd.DataFrame) -> None:
        roi = compute_roi(df)
        fig = plot_roi_static(roi)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_feature_importance(self, df: pd.DataFrame) -> None:
        imp, r2 = feature_importance_energy(df)
        fig = plot_feature_importance_static(imp, r2)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_sales_margin(self, df: pd.DataFrame) -> None:
        fig = plot_sales_margin_static(df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestInteractivePlots:
    """Each interactive plot should return a Plotly Figure."""

    def test_timeseries(self, df: pd.DataFrame) -> None:
        assert isinstance(plot_timeseries_interactive(df), go.Figure)

    def test_boxplots(self, df: pd.DataFrame) -> None:
        assert isinstance(plot_boxplots_interactive(df), go.Figure)

    def test_correlation(self, df: pd.DataFrame) -> None:
        corr = correlation_matrix(df)
        assert isinstance(plot_correlation_interactive(corr), go.Figure)

    def test_intensity(self, df: pd.DataFrame) -> None:
        assert isinstance(plot_intensity_interactive(df), go.Figure)

    def test_stat_tests(self, df: pd.DataFrame) -> None:
        results = compare_all_variables(df, KPIS_FOR_BOXPLOT)
        assert isinstance(plot_stat_tests_interactive(results), go.Figure)

    def test_anomalies(self, df: pd.DataFrame) -> None:
        assert isinstance(plot_anomalies_interactive(df), go.Figure)

    def test_trends(self, df: pd.DataFrame) -> None:
        assert isinstance(plot_trends_interactive(df), go.Figure)

    def test_roi(self, df: pd.DataFrame) -> None:
        roi = compute_roi(df)
        assert isinstance(plot_roi_interactive(roi), go.Figure)

    def test_feature_importance(self, df: pd.DataFrame) -> None:
        imp, r2 = feature_importance_energy(df)
        assert isinstance(plot_feature_importance_interactive(imp, r2), go.Figure)

    def test_sales_margin(self, df: pd.DataFrame) -> None:
        assert isinstance(plot_sales_margin_interactive(df), go.Figure)


class TestGenerateAllStaticFigures:
    def test_generates_all_10(self, df: pd.DataFrame, tmp_path: object) -> None:
        roi = compute_roi(df)
        # Don't save during test; just verify all 10 keys are returned
        result = generate_all_static_figures(df, roi, save=False, close_after=True)
        assert len(result) == 10
        assert set(result.keys()) == set(FIGURE_FILENAMES.keys())
