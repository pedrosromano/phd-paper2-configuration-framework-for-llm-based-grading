# A Configuration Framework for LLM-Based Grading

**Article 2** of a PhD compilation (Q1 venues). An empirical study of the *design space* for LLM-based
automated assessment in Computer Science — reasoning, evaluation guidance, scope, decomposition, model
family, fine-tuning — and the **decision guide** that results: for a given CS assessment task, which
configuration should you use?

This is a study and a framework, **not** another grading pipeline and **not** a leaderboard.

- **Article 1** = published PRISMA SLR (IEEE ToE). Foundation for everything ≤ Jul 2025.
- **Article 2** = this repository.
- **Article 3** = the improved *GradeGenie* platform (design decisions fixed here flow there).
- Arc: **Map (SLR) → Analyse (this) → Build (GradeGenie)**.

Primary venue: **IEEE Transactions on Learning Technologies (TLT)**; fallback **IEEE Transactions on
Education (ToE)**. Both Q1.

> The working spec lives in [CLAUDE.md](CLAUDE.md); the step-by-step playbook in [PHASES.md](PHASES.md).
> Open design decisions are tracked in **CLAUDE.md §11 Living Uncertainties** — read it before assuming
> anything is settled.

## Repository layout

```
/data
  /raw         untouched source datasets (gitignored; large/sensitive — never commit PT-CS PII)
  /processed   normalised, anonymised, analysis-ready corpus + per-run model outputs
/experiments
  /ingest      dataset parsers → common schema
  /harness     model-agnostic grading interface + adapters + parser + cache
  /configs     the pruned factorial config matrix
  /run         experiment runners (local / paid, resumable)
  /analysis    metrics, consistency, stats, framework synthesis → tidy tables
  /figures     plotting scripts → article/figures
/article       LaTeX (IEEEtran); Related Work + results
```

**Data flow:** `data/raw → experiments/ingest → data/processed/corpus.parquet → experiments/run →
data/processed/runs → experiments/analysis → experiments/figures → article/`.

## Datasets

Develop on public datasets, confirm/transfer on PT-CS.

| Dataset | Domain | Role |
|---|---|---|
| PT-CS (GradeGenie export) | code (Java) + theory, PT | primary code; transfer validation (not released — student data) |
| Rubric Is All You Need | code (Java/DSA), EN | public code comparator (external validity) |
| Mohler | short-answer (CS), EN | primary short-answer |
| SemEval-2013 Task 7 | short-answer (science), EN | development |
| Menagerie | code (Java CS1), EN | optional robustness only |

## Status

Phase 0 — repository & environment scaffolding. See [PHASES.md](PHASES.md) for the roadmap.

## Ethics & integrity (non-negotiable — CLAUDE.md §2)

- **COI:** the author owns/built GradeGenie (source of PT-CS, target of Article 3) — declared in the paper.
- **GDPR/Iscte:** PT-CS is pseudonymised; no direct identifiers in the processed set; publication is gated on
  the legal basis / ethics opinion.
- **Ground-truth honesty:** PT-CS grades are a **two-teacher consensus** over human-validated, AI-seeded
  suggestions — *not* independent double annotation; no measured human ceiling / inter-rater kappa is reported.
- **No circularity:** Article-2 evaluation data stays conceptually separate from the Article-3 system.
