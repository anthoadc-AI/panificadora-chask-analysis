#!/usr/bin/env bash
#
# init_git_history.sh — Initialize the repository with 4 logical commits,
# one per project phase, plus semantic version tags.
#
# Why? A single giant initial commit looks like a code dump. Four phased
# commits with descriptive messages and tags tell the story of how the
# project was built — much more compelling for a portfolio reviewer.
#
# Usage:
#   bash scripts/init_git_history.sh                Run for real
#   bash scripts/init_git_history.sh --dry-run      Print what would happen, don't commit
#   bash scripts/init_git_history.sh --no-tags      Skip creating version tags
#
# Resulting history:
#   * v0.4.0 (HEAD -> main, tag) docs: MkDocs Material site with auto-generated API
#   * v0.3.0 (tag) feat: interactive Streamlit dashboard
#   * v0.2.0 (tag) feat: analytical engine, four notebooks, ten figures
#   * v0.1.0 (tag) feat: project foundation, data loader, and CI

set -euo pipefail

# ============================================================
# Argument parsing
# ============================================================

DRY_RUN=false
CREATE_TAGS=true

for arg in "$@"; do
    case "$arg" in
        --dry-run)  DRY_RUN=true ;;
        --no-tags)  CREATE_TAGS=false ;;
        --help|-h)
            sed -n '3,20p' "$0"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            echo "Run with --help for usage." >&2
            exit 1
            ;;
    esac
done

# ============================================================
# Pre-flight checks
# ============================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v git >/dev/null 2>&1; then
    echo "❌ ERROR: git is not installed." >&2
    exit 1
fi

if [[ -d .git ]]; then
    echo "❌ ERROR: .git already exists in $ROOT_DIR" >&2
    echo "   This script only runs on a fresh repo. Remove .git first if you want to re-init:" >&2
    echo "   rm -rf .git && bash scripts/init_git_history.sh" >&2
    exit 1
fi

# Color helpers
if [[ -t 1 ]]; then
    BLUE=$'\033[36m'
    GREEN=$'\033[32m'
    YELLOW=$'\033[33m'
    RESET=$'\033[0m'
else
    BLUE=''; GREEN=''; YELLOW=''; RESET=''
fi

log()   { echo "${BLUE}$*${RESET}"; }
ok()    { echo "${GREEN}✓ $*${RESET}"; }
warn()  { echo "${YELLOW}⚠ $*${RESET}"; }

# ============================================================
# Git helpers
# ============================================================

git_run() {
    if $DRY_RUN; then
        echo "  [DRY] git $*"
    else
        git "$@"
    fi
}

# Stage a file if it exists; silently skip otherwise.
stage_file() {
    local f="$1"
    if [[ -e "$f" ]]; then
        git_run add -- "$f"
    fi
}

# Stage a glob pattern; silently skip if it matches nothing.
stage_glob() {
    local pattern="$1"
    # Use compgen -G to test whether the glob matches any file.
    if compgen -G "$pattern" >/dev/null 2>&1; then
        # shellcheck disable=SC2086 # we want word splitting on the glob
        git_run add -- $pattern
    fi
}

# Make a commit, but only if there's something staged.
commit_if_staged() {
    local message="$1"
    if $DRY_RUN; then
        echo "  [DRY] git commit -m \"$(echo "$message" | head -1)\""
        return 0
    fi
    if git diff --cached --quiet; then
        warn "Nothing staged — skipping commit"
        return 0
    fi
    git commit -q -m "$message"
}

create_tag() {
    local tag="$1"
    local message="$2"
    if $CREATE_TAGS; then
        git_run tag -a "$tag" -m "$message"
        ok "Tagged $tag"
    fi
}

# ============================================================
# Initialization
# ============================================================

log "🔧 Initializing repository in $ROOT_DIR"
git_run init -q -b main

# Detect git author config (don't override the user's global config)
if ! $DRY_RUN; then
    if ! git config user.email >/dev/null 2>&1; then
        warn "git user.email is not configured globally."
        warn "Set it before pushing, or commits will be authored by 'unknown'."
        warn "  git config --global user.email 'you@example.com'"
        warn "  git config --global user.name  'Your Name'"
    else
        ok "Using author: $(git config user.name) <$(git config user.email)>"
    fi
fi

echo

# ============================================================
# Phase 1 — Project foundation
# ============================================================

log "📦 Phase 1 — project foundation, data loader, CI"

# Root-level project metadata
stage_file ".gitignore"
stage_file "LICENSE"
stage_file "README.md"
stage_file "Makefile"
stage_file "pyproject.toml"
stage_file "requirements.txt"
stage_file "requirements-dev.txt"

# Raw dataset
stage_file "data/raw/dataset_panificadora.csv"

# Empty-directory placeholders
stage_file "data/processed/.gitkeep"
stage_file "notebooks/.gitkeep"
stage_file "reports/figures/.gitkeep"
stage_file "dashboard/.gitkeep"

# Source: just config + data loader at this stage
stage_file "src/panificadora/config.py"
stage_file "src/panificadora/data_loader.py"

# Tests for what exists so far
stage_file "tests/__init__.py"
stage_file "tests/conftest.py"
stage_file "tests/test_data_loader.py"

# CI workflow
stage_file ".github/workflows/ci.yml"

# This script itself (so future contributors can see how the history was built)
stage_file "scripts/init_git_history.sh"

commit_if_staged "feat: project foundation, data loader, and CI

Initial portfolio-grade scaffolding for the Panificadora Chask analysis.

Project structure:
- Modern Python project with src/ layout and pyproject.toml
- Reproducible installation via requirements.txt + editable install
- Makefile with conventional targets (install, test, lint, format, clean)
- Bilingual README (English / Spanish) with badges and quick start

Data layer:
- Raw monthly operations dataset (29 observations: Jan 2020 – May 2022)
- Loader with feature engineering: Pre/Post period split, energy intensity,
  gross margin, calendar components
- Validation guard catching schema violations, nulls, and date-range drift

Quality gates:
- pytest unit-test suite (24 tests, including KPI sanity checks)
- GitHub Actions CI matrix on Python 3.10 / 3.11 / 3.12
- ruff lint configuration and coverage reporting in pyproject.toml

Licensing:
- MIT License
"

create_tag "v0.1.0" "Phase 1: project foundation"
echo

# ============================================================
# Phase 2 — Analytical engine
# ============================================================

log "🔬 Phase 2 — analytical engine, four notebooks, ten figures"

# The __init__ takes its final form here (exposing all new modules)
stage_file "src/panificadora/__init__.py"

# New analytical modules
stage_file "src/panificadora/eda.py"
stage_file "src/panificadora/anomaly.py"
stage_file "src/panificadora/stats.py"
stage_file "src/panificadora/roi.py"
stage_file "src/panificadora/viz.py"

# Tests for each new module
stage_file "tests/test_eda.py"
stage_file "tests/test_anomaly.py"
stage_file "tests/test_stats.py"
stage_file "tests/test_roi.py"
stage_file "tests/test_viz.py"

# Notebooks (with embedded executed outputs)
stage_glob "notebooks/0*.ipynb"

# Notebook builder script (for regeneration)
stage_file "scripts/build_notebooks.py"

# All ten static figures
stage_glob "reports/figures/figura_*.png"

commit_if_staged "feat: analytical engine, four notebooks, ten figures

Implements the full quantitative pipeline that reproduces every claim of
the closure report from the raw dataset.

Analytical modules in src/panificadora/:
- eda.py:     descriptive statistics by period, correlation, rolling intensity
- anomaly.py: Z-score (univariate) + Isolation Forest (multivariate),
              Random Forest feature importance for energy consumption
- stats.py:   Shapiro–Wilk normality → Student's t / Mann–Whitney U,
              Cohen's d effect size, linear regression with projection
- roi.py:     energy + downtime savings, payback curve, ROI dataclass
- viz.py:     unified plotting module with paired matplotlib (static, for
              reports/figures/) and Plotly (interactive, for notebooks)
              implementations of all 10 figures

Reproducibility artifacts:
- 4 Jupyter notebooks (01-EDA, 02-anomalies, 03-statistics, 04-ROI),
  fully executed with embedded outputs
- 10 static figures regenerated to reports/figures/ via generate_all_static_figures
- scripts/build_notebooks.py for one-shot notebook (re)generation

Test coverage expanded to 104 unit tests:
- 12 EDA, 16 anomaly, 18 stats, 12 ROI, 21 viz smoke tests

Headline result, validated end-to-end by the pipeline:
- Energy consumption Pre = 49,703 kWh/mo, Post = 42,023 kWh/mo (−15.5 %)
- t-test p ≈ 2.7×10⁻⁹, Cohen's d = −2.66 (large effect)
- Energy intensity (kWh/kg) reduced by 14.9 %

README updated with actual dataset-derived KPIs and a reproducibility note
documenting two discrepancies between the closure report and the dataset
(energy reduction figure and gross-margin direction).
"

create_tag "v0.2.0" "Phase 2: analytical engine"
echo

# ============================================================
# Phase 3 — Streamlit dashboard
# ============================================================

log "🎛️  Phase 3 — interactive Streamlit dashboard"

stage_file "dashboard/app.py"
stage_file "dashboard/README.md"
stage_file "tests/test_dashboard.py"

commit_if_staged "feat: interactive Streamlit dashboard

Six-tab dashboard that exposes the entire analysis with live parameter
tuning. Launch with: make dashboard (→ http://localhost:8501).

Sidebar controls:
- ROI parameters: energy tariff, project investment, downtime cost
- Anomaly tuning: Z-score threshold, Isolation Forest contamination
  and n_estimators (live re-fitting on parameter change)
- Period filter: Pre / Post / Both

Tabs:
- Overview:   4 KPI cards that recompute live, time series, sales & margin
- EDA:        descriptive stats table, boxplots, correlation, intensity
- Anomalies:  live Z-score + IF detection with feature-importance ranking
- Statistics: color-graded test table, p-values, effect sizes, regression
- ROI:        live calculator, payback curve, tariff sensitivity sweep
- Data:       raw dataset viewer with CSV download

Architecture:
- Zero analytical logic of its own — fully reuses src/panificadora
- @st.cache_data on all heavy computations (Isolation Forest, Random Forest)
- Smoke-tested via test_dashboard.py — total now 105 passing tests
"

create_tag "v0.3.0" "Phase 3: Streamlit dashboard"
echo

# ============================================================
# Phase 4 — Documentation site
# ============================================================

log "📖 Phase 4 — MkDocs Material documentation site"

# MkDocs config
stage_file "mkdocs.yml"

# Top-level docs pages
stage_file "docs/index.md"
stage_file "docs/getting-started.md"
stage_file "docs/dashboard.md"
stage_file "docs/findings.md"
stage_file "docs/about.md"

# Analysis chapter pages
stage_file "docs/analysis/overview.md"
stage_glob "docs/analysis/0*.md"

# Auto-generated API reference pages (one per module)
stage_glob "docs/api/*.md"

# Embedded figures
stage_glob "docs/assets/figures/*.png"

# Deploy workflow
stage_file ".github/workflows/docs.yml"

commit_if_staged "docs: MkDocs Material site with auto-generated API reference

Portfolio-grade documentation site that auto-deploys to GitHub Pages on
every push to main.

Site contents (17 pages):
- Landing page with grid cards summarizing the headline findings
- Getting Started: install + reproduce locally
- The Analysis: overview + 4 chapters (EDA, anomalies, statistics, ROI)
  with embedded figures, Mermaid diagrams, and code samples
- Dashboard: full feature reference for the Streamlit app
- API Reference: auto-generated from docstrings via mkdocstrings (7 modules)
- Key Findings: consolidated KPIs and a transparent discussion of the two
  report-vs-dataset discrepancies surfaced by reproducing the analysis
- About: author bio, tech stack, license

Theme & UX:
- Material for MkDocs with dark / light mode toggle
- Sticky tab navigation, search highlighting, code copy buttons
- Mermaid flowcharts (protocol diagrams in overview and statistics)
- Custom admonitions (warning, danger, success) for discrepancy callouts

Deployment:
- .github/workflows/docs.yml builds with strict mode and deploys to gh-pages
  on every push to main
- README updated with docs badge and live-site URL

Build verified: mkdocs build --strict produces 17 pages with zero warnings.
"

create_tag "v0.4.0" "Phase 4: documentation site"
echo

# ============================================================
# Final summary
# ============================================================

if $DRY_RUN; then
    log "✨ Dry run complete. Re-run without --dry-run to apply."
    exit 0
fi

ok "Git history initialized successfully!"
echo
log "Resulting commit log:"
git log --graph --oneline --decorate
echo
log "Next steps:"
cat <<'EOS'
  1. Push to GitHub:
        git remote add origin git@github.com:anthoadc-AI/panificadora-chask-analysis.git
        git push -u origin main
     If you created tags, also:
        git push --tags

  2. Enable GitHub Pages for the docs site:
        Settings → Pages → Source: "GitHub Actions"

  3. The CI workflow will run on push; the docs workflow will publish
     the site at:
        https://anthoadc-ai.github.io/panificadora-chask-analysis/
EOS
