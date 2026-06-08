"""RIAYN ("Rubric Is All You Need") ingest -> common schema (Phase 2.5).

Public code comparator (external validity). Source: data/raw/riayn/RubricEval/ (HF
BITS-Pilani-GRC/RubricEval). We ingest the **DSA** part (25 problems x 6 submission
categories = 150 items), which the public release provides completely: question, rubric,
model solution, student code per category, and human consensus scores (per-step + Total).

DSA join:
  - dsa_data/rubric_eval_grader1/extracted_data.csv: one row per PROBLEM with
    question, rubric, solution, and the student CODE per category column
    (correct_1/2/3, TLE, wrong, compilation_error).
  - dsa_data/combined_human_scores.csv: 150 rows = (Problem x Submission-category) with
    per-step marks + 'Total Marks' as "X/Y" (the consensus gold = two graders collaboratively).

OOP NOT INGESTED: the public oop_dataset.csv has student code + two LLM feedback/appraise
texts but NO extractable numeric human gold score and no question/rubric -> cannot be a
graded item in our schema. (The paper's OOP numbers are still in the Phase-1.5 context
table, read from the PDF.) Documented in data_sources.md.

Run:  python -m experiments.ingest.ingest_riayn
"""

from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

import pandas as pd

from experiments.ingest import schema

REPO_ROOT = Path(__file__).resolve().parents[2]
DSA = REPO_ROOT / "data" / "raw" / "riayn" / "RubricEval" / "dsa_data"
GRADER = DSA / "rubric_eval_grader1" / "extracted_data.csv"   # problem-level: question/rubric/solution/code
SCORES = DSA / "combined_human_scores.csv"                     # consensus per (problem, category)
OUT = REPO_ROOT / "data" / "processed" / "corpus_riayn.parquet"

# combined_human_scores 'Submission' -> grader CSV code column
CATEGORY_COL = {
    "Compilation_Error": "compilation_error", "Correct_1": "correct_1",
    "Correct_2": "correct_2", "Correct_3": "correct_3", "TLE": "TLE", "Wrong": "wrong",
}
STEP_COLS = [f"Step {i}" for i in range(1, 13)]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")


def parse_total(tm: str) -> tuple[float | None, float | None]:
    m = re.match(r"\s*(-?\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*", str(tm))
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)


def build() -> pd.DataFrame:
    g = pd.read_csv(GRADER)
    s = pd.read_csv(SCORES)
    # case-insensitive problem lookup, with fuzzy fallback: the scores CSV has truncated/
    # misspelled problem names (e.g. "Palindrom", "...of a Bina") -> match to grader names.
    gmap = {slug(r["name"]): r for _, r in g.iterrows()}
    gkeys = list(gmap)

    def find_problem(prob: str):
        k = slug(prob)
        if k in gmap:
            return gmap[k]
        # prefix match (truncated names) then close-match
        pref = [gk for gk in gkeys if gk.startswith(k) or k.startswith(gk)]
        if len(pref) == 1:
            return gmap[pref[0]]
        close = difflib.get_close_matches(k, gkeys, n=1, cutoff=0.8)
        return gmap[close[0]] if close else None

    rows = []
    for _, r in s.iterrows():
        prob = r["Problem"]
        cat = r["Submission"]
        gp = find_problem(prob)
        if gp is None:
            continue
        code_col = CATEGORY_COL.get(cat)
        code = str(gp.get(code_col, "")).strip() if code_col else ""
        score, scale = parse_total(r["Total Marks"])
        if score is None or scale is None or scale <= 0 or not code:
            continue
        steps = {c: (None if pd.isna(r[c]) else float(r[c])) for c in STEP_COLS if c in s.columns}
        rows.append({
            "item_id": f"riayn:dsa:{slug(prob)}:{slug(cat)}",
            "dataset": "riayn",
            "domain": "code",
            "language": "en",
            "question_text": str(gp["question"]).strip(),
            "reference_answer": str(gp["solution"]).strip() or None,     # RIAYN has a model solution
            "rubric_json": json.dumps({"rubric_text": str(gp["rubric"]).strip()}),  # question-specific rubric
            "student_answer": code,
            "gold_score": score,
            "gold_scale_max": scale,
            "label_2way": None, "label_3way": None, "label_5way": None,
            "split": "none",
            "question_id": f"dsa:{slug(prob)}",
            "submission_id": None,
            "source_meta": json.dumps({
                "subset": "dsa", "problem": str(prob), "category": str(cat),
                "solution_name": (None if pd.isna(r.get("Solution Name/Number"))
                                  else r.get("Solution Name/Number")),
                "step_marks": steps,
            }),
        })
    return schema.add_gold_norm(pd.DataFrame(rows))


def report(out: pd.DataFrame) -> None:
    print(f"\n=== RIAYN (DSA) ingest report ({len(out)} items, {out.question_id.nunique()} problems) ===")
    cats = out.source_meta.map(lambda x: json.loads(x)["category"])
    print("By submission category:\n" + cats.value_counts().to_string())
    print("\nNull rates:")
    for c in ["question_text", "reference_answer", "rubric_json", "student_answer"]:
        empty = out[c].isna() | (out[c].astype(str).str.strip().isin(["", "nan", "None"]))
        print(f"  {c:18}: {empty.mean()*100:5.1f}% empty")
    print(f"\nScale max values: {sorted(out.gold_scale_max.unique())}")
    print(f"gold_score [{out.gold_score.min()}, {out.gold_score.max()}]; gold_norm [{out.gold_norm.min():.2f}, {out.gold_norm.max():.2f}]")
    print("\n2 examples:")
    for _, r in out.sample(2, random_state=1).iterrows():
        print(f"  {r.item_id}  score={r.gold_score}/{r.gold_scale_max}")
        print(f"    Q: {r.question_text[:80]!r}")
        print(f"    code: {r.student_answer[:70]!r}")


def main() -> int:
    out = build()
    out = schema.validate(out, dataset="riayn")
    schema.write_parquet(out, OUT)
    report(out)
    print(f"\nWrote {OUT.relative_to(REPO_ROOT)}")
    print("NOTE: DSA only (150 max). OOP NOT ingested -- public release has no numeric human gold "
          "score / no question+rubric for OOP. Grades = two-grader consensus (combined_human_scores).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
