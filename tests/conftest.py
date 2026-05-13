"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pandas as pd
import pytest

from panificadora.data_loader import load_dataset


@pytest.fixture(scope="session")
def df() -> pd.DataFrame:
    """Full validated dataset, loaded once per test session."""
    return load_dataset()
