# Getting Started

## Prerequisites

- **Python 3.10 or newer** (3.10, 3.11, 3.12 are tested in CI)
- **pip** for package management
- (Recommended) **make** for the convenience commands

## Installation

=== "With Make (recommended)"

    ```bash
    git clone https://github.com/anthoadc-AI/panificadora-chask-analysis.git
    cd panificadora-chask-analysis
    make install-dev
    ```

=== "Manual"

    ```bash
    git clone https://github.com/anthoadc-AI/panificadora-chask-analysis.git
    cd panificadora-chask-analysis

    # (Optional but recommended) Virtual environment
    python -m venv .venv
    source .venv/bin/activate

    # Install dependencies
    pip install -r requirements-dev.txt
    pip install -e .
    ```

## Quick verification

Run the test suite to confirm the install:

```bash
make test
```

You should see all tests passing:

```text
================== test session starts ==================
collected 105 items

tests/test_anomaly.py ................         [ 15%]
tests/test_dashboard.py .                      [ 16%]
tests/test_data_loader.py ........................ [ 39%]
tests/test_eda.py ............                 [ 50%]
tests/test_roi.py ............                 [ 62%]
tests/test_stats.py ..................         [ 79%]
tests/test_viz.py .....................        [100%]

=================== 105 passed in 9s ====================
```

## First analysis

The simplest way to see the headline result:

```python
from panificadora import load_dataset
from panificadora.eda import describe_by_period, summarize_change

df = load_dataset()
stats = describe_by_period(df)
print(summarize_change(stats, "consumo_kwh"))
# → consumo_kwh: 49,703 → 42,023 (-15.5%)
```

## Available entry points

| Command | What it does |
| --- | --- |
| `make notebook` | Launch Jupyter and open the four analysis notebooks |
| `make dashboard` | Launch the Streamlit dashboard at `http://localhost:8501` |
| `make figures` | Re-run the four notebooks end-to-end to regenerate all 10 static figures |
| `make test` | Run the full pytest suite with coverage |
| `make lint` | Run ruff + mypy |
| `make docs` | Serve this documentation site locally with hot reload |

!!! tip "Editor setup"
    The project ships with a `pyproject.toml` configured for `ruff` (linting + formatting)
    and `mypy` (type checking). Most modern Python editors will pick up these settings
    automatically.
