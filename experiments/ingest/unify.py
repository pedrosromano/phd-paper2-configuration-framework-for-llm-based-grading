"""Unify per-dataset corpora -> data/processed/corpus.parquet (Phase 2.6).

Concatenate the FOUR Article-2 corpora (PT-CS, Mohler, SemEval, RIAYN), re-validate the
union against the common schema, and print a cross-dataset summary + the finalised
context mapping and scope/decomposition applicability.

corpus_en.parquet is DELIBERATELY EXCLUDED here -- it is the master's EN view of PT-CS
(a translation of the same items), not a separate Article-2 dataset; including it would
double-count PT-CS.

Per CLAUDE.md §5:
  - Context (grounding) is dataset-specific: RUBRIC for PT-CS/RIAYN, REFERENCE answer for
    Mohler/SemEval (the question stem + student answer are ALWAYS present; only the added
    guidance varies).
  - Whole-exam scope (D5a) and criterion-by-criterion decomposition (D5b) apply to PT-CS
    ONLY (it has multi-question submissions + rubric criteria). All others are
    question-by-question / holistic by nature.

Run:  python -m experiments.ingest.unify
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from experiments.ingest import schema

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = REPO_ROOT / "data" / "processed"
PARTS = ["corpus_ptcs", "corpus_mohler", "corpus_semeval", "corpus_riayn"]

# Finalised per-dataset design metadata (CLAUDE.md §5/§6).
CONTEXT_MAP = {
    "ptcs":    {"grounding": "rubric",    "scope": "whole-exam + q-by-q", "decomposition": "holistic + criterion", "splits": "none"},
    "riayn":   {"grounding": "rubric (+ model solution available)", "scope": "q-by-q", "decomposition": "holistic", "splits": "none"},
    "mohler":  {"grounding": "reference", "scope": "q-by-q", "decomposition": "holistic", "splits": "none"},
    "semeval": {"grounding": "reference", "scope": "q-by-q", "decomposition": "holistic", "splits": "seen/unseen_ans/unseen_q/unseen_domain"},
}


def load_parts() -> list[pd.DataFrame]:
    frames = []
    for name in PARTS:
        p = PROCESSED / f"{name}.parquet"
        if not p.exists():
            raise FileNotFoundError(f"missing {p.relative_to(REPO_ROOT)} -- run its ingest first")
        frames.append(pd.read_parquet(p))
    return frames


def summary(corpus: pd.DataFrame) -> None:
    print(f"\n=== Unified corpus: {len(corpus)} items across {corpus.dataset.nunique()} datasets ===\n")
    rows = []
    for ds, g in corpus.groupby("dataset"):
        rows.append({
            "dataset": ds,
            "items": len(g),
            "domain": "/".join(sorted(g.domain.unique())),
            "lang": "/".join(sorted(g.language.unique())),
            "questions": g.question_id.nunique(),
            "submissions": g.submission_id.notna().sum() and g.submission_id.nunique() or 0,
            "%ref": round(100 * g.reference_answer.notna().mean()),
            "%rubric": round(100 * g.rubric_json.notna().mean()),
            "scale_max": "/".join(str(x) for x in sorted(g.gold_scale_max.unique())[:6]),
            "labels": "yes" if g.label_5way.notna().any() else "no",
        })
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nGold-norm sanity (0-1 per dataset):")
    print(corpus.groupby("dataset").gold_norm.agg(["min", "max"]).round(3).to_string())

    print("\n=== Per-dataset context mapping + scope/decomposition applicability (CLAUDE.md §5) ===")
    hdr = f"{'dataset':9} {'grounding':40} {'scope':22} {'decomposition':22} splits"
    print(hdr); print("-" * len(hdr))
    for ds, m in CONTEXT_MAP.items():
        print(f"{ds:9} {m['grounding']:40} {m['scope']:22} {m['decomposition']:22} {m['splits']}")
    print("\nNote: whole-exam (D5a) + criterion (D5b) are PT-CS ONLY (multi-question submissions + "
          "rubric criteria). Grounding sent on top of the always-present stem+answer: rubric (PT-CS/RIAYN) "
          "vs reference (Mohler/SemEval).")


def main() -> int:
    frames = load_parts()
    corpus = schema.unify(frames, out=PROCESSED / "corpus.parquet")
    summary(corpus)
    print(f"\nWrote {(PROCESSED / 'corpus.parquet').relative_to(REPO_ROOT)} "
          f"({len(corpus)} items). corpus_en.parquet excluded (master's EN view).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
