"""Panificadora Chask — Data analysis package.

This package contains the analytical engine for the Panificadora Chask
plant modernization project (2020-2022). It exposes reusable functions
for data loading, exploratory analysis, anomaly detection, statistical
testing, ROI quantification, and visualization.

Modules:
    config: Project-wide constants and paths.
    data_loader: Dataset loading, validation, and feature engineering.
    eda: Descriptive statistics and correlation analysis.
    anomaly: Z-score and Isolation Forest anomaly detection.
    stats: Hypothesis testing, Cohen's d, linear regression.
    roi: Return on investment quantification.
    viz: All plotting (matplotlib static + Plotly interactive).
"""
from panificadora import anomaly, config, eda, roi, stats, viz
from panificadora.data_loader import load_dataset, split_pre_post, validate_dataset

__version__ = "1.0.0"

__all__ = [
    "anomaly",
    "config",
    "eda",
    "load_dataset",
    "roi",
    "split_pre_post",
    "stats",
    "validate_dataset",
    "viz",
]
