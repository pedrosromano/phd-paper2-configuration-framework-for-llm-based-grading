"""Common corpus schema + validation (Phase 2 foundation, CLAUDE.md §5).

Every dataset parser (PT-CS, Mohler, SemEval, RIAYN, ...) normalises its rows to THIS schema
and calls `validate()` before writing. `unify()` concatenates per-dataset frames into
data/processed/corpus.parquet and asserts cross-dataset consistency.

Design rules baked in here:
  - gold_score is kept on its NATIVE scale; gold_norm (0..1) is derived = gold_score/gold_scale_max.
  - question stem + student answer are ALWAYS present (the minimum to make grading meaningful);
    only the *evaluation guidance* (rubric / reference) varies -> reference_answer & rubric_json
    are nullable and dataset-dependent (rubric: PT-CS/RIAYN; reference: Mohler/SemEval).
  - label_{2,3,5}way carry SemEval ordinal labels; null elsewhere.
  - split marks seen/unseen-answers/unseen-questions (SemEval); 'none' otherwise.
  - NO PII may ever reach this frame (PT-CS parser drops it upstream).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = REPO_ROOT / "data" / "processed"
CORPUS_PARQUET = PROCESSED / "corpus.parquet"

DOMAINS = {"code", "short_answer"}
LANGUAGES = {"en", "pt"}
SPLITS = {"seen", "unseen_ans", "unseen_q", "none"}

# Column order is canonical; parsers should build a frame with exactly these columns.
COLUMNS: list[str] = [
    "item_id",          # globally-unique id, conventionally f"{dataset}:{question_id}:{submission_id|idx}"
    "dataset",          # ptcs | mohler | semeval | riayn | menagerie
    "domain",           # code | short_answer
    "language",         # en | pt
    "question_text",    # ALWAYS present
    "reference_answer", # nullable (Mohler/SemEval grounding)
    "rubric_json",      # nullable JSON string (PT-CS/RIAYN grounding)
    "student_answer",   # ALWAYS present
    "gold_score",       # native-scale teacher/reference score (float)
    "gold_scale_max",   # native max for this item (float, > 0)
    "gold_norm",        # derived gold_score / gold_scale_max in [0,1]
    "label_2way",       # nullable (SemEval)
    "label_3way",       # nullable (SemEval)
    "label_5way",       # nullable (SemEval)
    "split",            # seen | unseen_ans | unseen_q | none
    "question_id",      # per-dataset question identifier
    "submission_id",    # nullable (PT-CS multi-question submissions)
    "source_meta",      # nullable JSON string: provenance (model tag, dates, raw ids ... NO PII)
]

NULLABLE = {"reference_answer", "rubric_json", "label_2way", "label_3way", "label_5way",
            "submission_id", "source_meta"}

# PII column names that must NEVER appear (defence-in-depth check, CLAUDE.md §2).
FORBIDDEN_PII = {"nome", "email", "password", "reset_token", "name", "e_mail"}


class SchemaError(ValueError):
    """Raised when a frame violates the common schema."""


def add_gold_norm(df: pd.DataFrame) -> pd.DataFrame:
    """Derive gold_norm = gold_score / gold_scale_max (clipped to [0,1])."""
    df = df.copy()
    df["gold_norm"] = (df["gold_score"] / df["gold_scale_max"]).clip(0.0, 1.0)
    return df


def validate(df: pd.DataFrame, *, dataset: str | None = None) -> pd.DataFrame:
    """Assert the frame conforms to the common schema. Returns the frame (column-ordered)."""
    # columns present
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise SchemaError(f"[{dataset}] missing columns: {missing}")
    extra = [c for c in df.columns if c not in COLUMNS]
    if extra:
        raise SchemaError(f"[{dataset}] unexpected columns: {extra}")
    # PII defence
    pii = {c for c in df.columns if c.lower() in FORBIDDEN_PII}
    if pii:
        raise SchemaError(f"[{dataset}] forbidden PII column(s) present: {pii}")
    # enums
    bad_dom = set(df["domain"].unique()) - DOMAINS
    if bad_dom:
        raise SchemaError(f"[{dataset}] bad domain values: {bad_dom}")
    bad_lang = set(df["language"].unique()) - LANGUAGES
    if bad_lang:
        raise SchemaError(f"[{dataset}] bad language values: {bad_lang}")
    bad_split = set(df["split"].unique()) - SPLITS
    if bad_split:
        raise SchemaError(f"[{dataset}] bad split values: {bad_split}")
    # always-present fields non-empty
    for col in ("item_id", "question_text", "student_answer"):
        empty = df[col].isna() | (df[col].astype(str).str.strip() == "")
        if empty.any():
            raise SchemaError(f"[{dataset}] '{col}' empty in {int(empty.sum())} row(s)")
    # ids unique
    if df["item_id"].duplicated().any():
        dups = df.loc[df["item_id"].duplicated(), "item_id"].head(3).tolist()
        raise SchemaError(f"[{dataset}] duplicate item_id(s), e.g. {dups}")
    # numeric ranges
    if (df["gold_scale_max"] <= 0).any():
        raise SchemaError(f"[{dataset}] gold_scale_max must be > 0")
    if "gold_norm" in df and ((df["gold_norm"] < 0) | (df["gold_norm"] > 1)).any():
        raise SchemaError(f"[{dataset}] gold_norm outside [0,1]")
    return df[COLUMNS]


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def unify(frames: list[pd.DataFrame], *, out: Path = CORPUS_PARQUET) -> pd.DataFrame:
    """Concatenate per-dataset frames, re-validate the union, write corpus.parquet."""
    for f in frames:
        validate(f)
    corpus = pd.concat(frames, ignore_index=True)
    corpus = validate(corpus, dataset="corpus")
    write_parquet(corpus, out)
    return corpus
