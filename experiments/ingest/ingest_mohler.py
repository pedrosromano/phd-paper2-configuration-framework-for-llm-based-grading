"""Mohler short-answer ingest -> common schema (Phase 2.3).

Source: data/raw/mohler/.../mohler_dataset_edited.csv (Mohler & Mihalcea 2011 "Texas" set;
2,273 answers, 81 CS questions, ~31 students). Columns: id, question, desired_answer,
student_answer, score_me, score_other, score_avg.

Mapping: reference_answer = desired_answer (Mohler's grounding is a REFERENCE, not a rubric);
gold = score_avg on a 0-5 scale; question_id = id (read as STRING to avoid float collisions
like 1.10 vs 1.1). The two independent grader scores (score_me/score_other) are kept in
source_meta -> unlike PT-CS, a human-human ceiling IS reportable for Mohler.

Run:  python -m experiments.ingest.ingest_mohler
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from experiments.ingest import schema

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = (REPO_ROOT / "data" / "raw" / "mohler" / "asag-mirror"
       / "comparative_evaluation_on_mohler_dataset" / "dataset" / "mohler_dataset_edited.csv")
OUT = REPO_ROOT / "data" / "processed" / "corpus_mohler.parquet"
SCALE_MAX = 5.0


def build() -> pd.DataFrame:
    df = pd.read_csv(SRC, dtype={"id": str})  # id as string (1.10 != 1.1)
    df["ans_idx"] = df.groupby("id").cumcount()  # distinguish answers within a question
    out = pd.DataFrame({
        "item_id": "mohler:" + df["id"] + ":" + df["ans_idx"].astype(str),
        "dataset": "mohler",
        "domain": "short_answer",
        "language": "en",
        "question_text": df["question"].astype(str).str.strip(),
        "reference_answer": df["desired_answer"].astype(str).str.strip(),
        "rubric_json": None,                    # Mohler grounding is a reference answer, no rubric
        "student_answer": df["student_answer"].astype(str).str.strip(),
        "gold_score": pd.to_numeric(df["score_avg"], errors="coerce"),
        "gold_scale_max": SCALE_MAX,
        "label_2way": None, "label_3way": None, "label_5way": None,
        "split": "none",                        # Mohler has no seen/unseen split
        "question_id": df["id"],
        "submission_id": None,                  # no student/submission grouping in Mohler
        "source_meta": [json.dumps({"score_me": float(a), "score_other": float(b)})
                        for a, b in zip(df["score_me"], df["score_other"])],
    })
    return schema.add_gold_norm(out)


def report(out: pd.DataFrame, df_raw: pd.DataFrame) -> None:
    print(f"\n=== Mohler ingest report ({len(out)} items, {out.question_id.nunique()} questions) ===")
    print("Null/empty rates:")
    for c in ["question_text", "reference_answer", "student_answer", "rubric_json"]:
        empty = out[c].isna() | (out[c].astype(str).str.strip().isin(["", "nan"]))
        print(f"  {c:18}: {empty.mean()*100:5.1f}% empty")
    print(f"\nScale: gold_score [{out.gold_score.min()}, {out.gold_score.max()}] / {SCALE_MAX}; "
          f"gold_norm [{out.gold_norm.min():.2f}, {out.gold_norm.max():.2f}]")
    # human-human ceiling (the two graders) -- NOT available for PT-CS, IS here
    me = pd.to_numeric(df_raw["score_me"], errors="coerce")
    other = pd.to_numeric(df_raw["score_other"], errors="coerce")
    print("Human-human (two graders): "
          f"Pearson r={me.corr(other):.3f}, mean|diff|={ (me-other).abs().mean():.3f} (0-5 scale) "
          "-> a reportable human ceiling for Mohler")
    print("\n3 examples:")
    for _, r in out.sample(3, random_state=3).iterrows():
        print(f"  {r.item_id} score={r.gold_score}/{r.gold_scale_max}")
        print(f"    Q: {r.question_text[:80]!r}")
        print(f"    ref: {r.reference_answer[:70]!r}")
        print(f"    A: {r.student_answer[:70]!r}")


def main() -> int:
    df_raw = pd.read_csv(SRC, dtype={"id": str})
    out = build()
    out = schema.validate(out, dataset="mohler")
    schema.write_parquet(out, OUT)
    report(out, df_raw)
    print(f"\nWrote {OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
