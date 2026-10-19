"""Ingest of the two datasets for the guide's additional verification -> common schema (2026-10-18).

The guide was built from Mohler, SemEval, RIAYN and PT-CS. Its additional verification grades two datasets
that played no part in building it, so they live in their own corpus file and never enter corpus.parquet:

  SAF (Filighera et al., ACL 2022; CC BY 4.0), data/raw/saf/: English short answers on communication networks,
      scored by two trained annotators in consensus, with partial credit, and a reference answer per question.
      All four published splits are pooled: the models are prompted, not trained, so the splits carry no
      meaning for them (the reason we do not split SemEval either). A question's maximum is the score its
      answers labelled "Correct" received.
  HARMOGEN-R v2.0 (Mendonca et al.; Zenodo 10.5281/zenodo.17284944; CC BY 4.0), data/raw/harmogenr/: the C++
      code answers of a data-structures course, in Portuguese. Each answer was graded by four instructors,
      independently and blind, with the instructors' own rubric (rubric source 1, points per criterion); the
      gold is their mean. Empty answers are left out: they carry no grading decision.

Run:  python -m experiments.ingest.ingest_verification
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

from experiments.ingest import schema

REPO_ROOT = Path(__file__).resolve().parents[2]
SAF = REPO_ROOT / "data" / "raw" / "saf"
HARM = REPO_ROOT / "data" / "raw" / "harmogenr"
OUT = REPO_ROOT / "data" / "processed" / "corpus_verification.parquet"
SAF_SPLITS = {"train": "seen", "validation": "seen", "test_unseen_answers": "unseen_ans",
              "test_unseen_questions": "unseen_q"}
HUMAN_RUBRIC = 1                     # question_criterias.source / evaluations.source_question_criteria


def _html_to_text(s: str) -> str:
    """The question stems are rich text: keep code blocks verbatim and list items on their own lines."""
    soup = BeautifulSoup(str(s), "lxml")
    for li in soup.find_all("li"):
        li.insert_before("\n- ")
    for pre in soup.find_all("pre"):
        pre.insert_before("\n")
        pre.insert_after("\n")
    for p in soup.find_all(["p", "br"]):
        p.insert_after("\n")
    text = html.unescape(soup.get_text())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def saf() -> pd.DataFrame:
    d = pd.concat([pd.read_parquet(SAF / f"{s}.parquet").assign(split=s) for s in SAF_SPLITS], ignore_index=True)
    qid = {q: f"saf:q{i:02d}" for i, q in enumerate(sorted(d.question.unique()))}
    correct = d[d.verification_feedback == "Correct"].groupby("question").score.max()
    qmax = d.groupby("question").score.max().combine(correct, lambda a, c: c if pd.notna(c) else a)
    rows = [{
        "item_id": f"saf:{r.id}", "dataset": "saf", "domain": "short_answer", "language": "en",
        "question_text": str(r.question).strip(), "reference_answer": str(r.reference_answer).strip(),
        "rubric_json": None, "student_answer": str(r.provided_answer).strip(),
        "gold_score": float(r.score), "gold_scale_max": float(qmax[r.question]),
        "label_2way": None, "label_3way": None, "label_5way": None,
        "split": SAF_SPLITS[r.split], "question_id": qid[r.question], "submission_id": None,
        "source_meta": json.dumps({"saf_split": r.split, "verification_feedback": r.verification_feedback}),
    } for r in d.itertuples()]
    out = schema.add_gold_norm(pd.DataFrame(rows))
    over = out[out.gold_score > out.gold_scale_max + 1e-9]
    if len(over):
        raise ValueError(f"SAF: {len(over)} answers score above their question's maximum")
    return out


def harmogenr() -> pd.DataFrame:
    q = pd.read_csv(HARM / "questions.csv", encoding="utf-8-sig")
    q = q[q.type == "code"].rename(columns={"id": "question_id", "score": "qmax"})
    r = pd.read_csv(HARM / "student_responses.csv", encoding="utf-8-sig").rename(columns={"id": "response_id"})
    r = r[r.question_id.isin(q.question_id)]
    r = r[r.response.notna() & (r.response.astype(str).str.strip() != "")]
    crit = pd.read_csv(HARM / "question_criterias.csv", encoding="utf-8-sig")
    crit = crit[(crit.source == HUMAN_RUBRIC) & crit.question_id.isin(q.question_id)].sort_values("id")
    ev = pd.read_csv(HARM / "evaluations.csv", encoding="utf-8-sig",
                     usecols=["student_response_id", "evaluator_type", "evaluator_id", "score",
                              "source_question_criteria"])
    ev = ev[(ev.evaluator_type == "teacher") & (ev.source_question_criteria == HUMAN_RUBRIC)]
    teachers = ev.groupby("student_response_id").score.agg(list)
    def clean(s) -> str:
        return re.sub(r"[ \t]+", " ", str(s).replace("\r\n", "\n").replace("\r", "\n")).strip()

    rubric = {qid: json.dumps([{"points": float(c.score),
                                "criteria": f"{clean(c.title)}. {clean(c.description)} "
                                            f"Pontuação: {clean(c.score_criteria)}"}
                               for c in g.itertuples()], ensure_ascii=False)
              for qid, g in crit.groupby("question_id")}
    qs = q.set_index("question_id")
    rows = []
    for x in r.itertuples():
        sc = teachers.get(x.response_id)
        if not sc or len(sc) != 4:
            raise ValueError(f"HARMOGEN-R response {x.response_id}: expected 4 instructor grades, got {sc}")
        rows.append({
            "item_id": f"harmogenr:{x.response_id}", "dataset": "harmogenr", "domain": "code", "language": "pt",
            "question_text": _html_to_text(qs.loc[x.question_id, "question"]), "reference_answer": None,
            "rubric_json": rubric[x.question_id], "student_answer": str(x.response).strip(),
            "gold_score": float(sum(sc) / len(sc)), "gold_scale_max": float(qs.loc[x.question_id, "qmax"]),
            "label_2way": None, "label_3way": None, "label_5way": None, "split": "none",
            "question_id": f"harmogenr:q{x.question_id}", "submission_id": None,
            "source_meta": json.dumps({"assignment_id": int(qs.loc[x.question_id, "assignment_id"]),
                                       "instructor_scores": [float(s) for s in sc]}),
        })
    return schema.add_gold_norm(pd.DataFrame(rows))


def main() -> int:
    frames = [schema.validate(saf(), dataset="saf"), schema.validate(harmogenr(), dataset="harmogenr")]
    out = pd.concat(frames, ignore_index=True)
    schema.write_parquet(out, OUT)
    print(f"wrote {OUT.relative_to(REPO_ROOT)}: {len(out)} items")
    for ds, g in out.groupby("dataset"):
        print(f"  {ds:10s} {len(g):5d} answers, {g.question_id.nunique():3d} questions, "
              f"gold_norm mean {g.gold_norm.mean():.2f}, zeros {(g.gold_norm == 0).mean():.0%}, "
              f"max per question {sorted(g.gold_scale_max.unique())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
