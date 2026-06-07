# Article 2 task runner. Run `make help` for the list.
# Most targets call entry points that come online in later phases (see PHASES.md);
# `install` and `verify` work from Phase 0.2.

PYTHON := .venv/bin/python
PIP    := .venv/bin/pip

.DEFAULT_GOAL := help
.PHONY: help install verify ingest run-local run-paid analyse figures paper paper-clean clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Create .venv (Python 3.11+) and install deps from pyproject
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

verify: ## Import-check the full dependency stack
	$(PYTHON) -c "import pandas, pyarrow, numpy, scipy, sklearn, statsmodels, matplotlib, yaml, tenacity, tiktoken, bs4, lxml, mysql.connector, pymysql; print('all imports OK')"

ingest: ## Phase 2 — parse datasets -> data/processed/corpus.parquet
	$(PYTHON) -m experiments.ingest

run-local: ## Phase 4 — local (Ollama) grading arms, resumable
	$(PYTHON) -m experiments.run.local

run-paid: ## Phase 4 — paid grading arms (routed through the cost guard)
	$(PYTHON) -m experiments.run.paid

analyse: ## Phase 5 — metrics, consistency, stats -> article/tables
	$(PYTHON) -m experiments.analysis

figures: ## Phase 6 — generate figures -> article/figures
	$(PYTHON) -m experiments.figures

paper: ## Phase 7 — compile the article (latexmk + IEEEtran)
	eval "$$(/usr/libexec/path_helper)"; cd article && \
		latexmk -pdf -synctex=1 -interaction=nonstopmode main.tex

paper-clean: ## Clear LaTeX build state (CLAUDE.md §9)
	cd article && latexmk -C main.tex

clean: ## Remove Python caches
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache
