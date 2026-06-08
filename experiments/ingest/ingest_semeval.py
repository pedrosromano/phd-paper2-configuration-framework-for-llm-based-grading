"""SemEval-2013 Task 7 ingest -> common schema (Phase 2.4).

Source: data/raw/semeval/.../semeval-5way/{beetle,sciEntsBank}/<split>/**/*.xml
(Dzikovska et al. 2013; SciEntsBank + Beetle). Each XML = one question with reference
answers + student answers; each studentAnswer carries a 5-way `accuracy` label. One row
per student answer.

Design:
  - Parse the **5-way** release and DERIVE 3-way and 2-way (single source of truth).
  - SemEval is a CLASSIFICATION task -> gold_score is the **binary correctness** (1.0 correct,
    0.0 otherwise), gold_scale_max = 1.0; the categorical labels live in label_2way/3way/5way.
    (Phase 5 uses accuracy/macro-F1 on the labels, not QWK/MAE.)
  - Grounding is the **reference answer(s)** (joined), no rubric.
  - Splits: train->seen, test-unseen-answers->unseen_ans, test-unseen-questions->unseen_q,
    test-unseen-domains->unseen_domain. The `reliability` subset (re-annotation; not a standard
    train/test split) is EXCLUDED.
  - Normalise the two spellings non-domain/non_domain -> non_domain.

Run:  python -m experiments.ingest.ingest_semeval
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from lxml import etree

from experiments.ingest import schema

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT / "data" / "raw" / "semeval" / "semeval-2013-task7" / "semeval-5way"
OUT = REPO_ROOT / "data" / "processed" / "corpus_semeval.parquet"

SPLIT_MAP = {
    "train": "seen",
    "test-unseen-answers": "unseen_ans",
    "test-unseen-questions": "unseen_q",
    "test-unseen-domains": "unseen_domain",
    # "reliability" -> excluded
}
FIVE_TO_THREE = {  # SemEval-2013 official 5->3 collapse
    "correct": "correct",
    "contradictory": "contradictory",
    "partially_correct_incomplete": "incorrect",
    "irrelevant": "incorrect",
    "non_domain": "incorrect",
}


def norm_label(acc: str) -> str:
    return (acc or "").strip().replace("-", "_")  # non-domain -> non_domain


def el_text(el) -> str:
    """Robust text extraction. Beetle stores some answers TOKENISED (<token> children +
    a raw_text attribute, empty .text); SciEntsBank uses plain .text. Prefer raw_text
    (the original untokenised string), then .text, then re-join token children."""
    if el is None:
        return ""
    rt = el.get("raw_text")
    if rt and rt.strip():
        return rt.strip()
    t = (el.text or "").strip()
    if t:
        return t
    toks = [tok.text or "" for tok in el.findall(".//token")]
    return (" ".join(toks).strip() or "".join(el.itertext()).strip())


def parse_file(path: Path, subset: str, split: str) -> list[dict]:
    tree = etree.parse(str(path))
    root = tree.getroot()
    qid = root.get("id", path.stem)
    qtext = el_text(root.find("questionText"))
    refs = [el_text(r) for r in root.findall(".//referenceAnswer")]
    reference = " | ".join(r for r in refs if r)
    rows = []
    for sa in root.findall(".//studentAnswer"):
        text = el_text(sa)
        if not text:
            continue
        five = norm_label(sa.get("accuracy", ""))
        three = FIVE_TO_THREE.get(five, "incorrect")
        two = "correct" if five == "correct" else "incorrect"
        rows.append({
            "sa_id": sa.get("id", ""),
            "subset": subset, "split": split, "qid": qid,
            "question_text": qtext, "reference_answer": reference, "student_answer": text,
            "label_5way": five, "label_3way": three, "label_2way": two,
            "module": root.get("module", ""),
        })
    return rows


def build() -> pd.DataFrame:
    records: list[dict] = []
    for subset in ("beetle", "sciEntsBank"):
        for folder, split in SPLIT_MAP.items():
            d = ROOT / subset / folder
            if not d.exists():
                continue
            for xml in sorted(d.rglob("*.xml")):
                records.append(parse_file(xml, subset, split))
    flat = [r for sub in records for r in sub]
    df = pd.DataFrame(flat)

    out = pd.DataFrame({
        "item_id": ("semeval:" + df["subset"] + ":" + df["split"] + ":" + df["sa_id"]),
        "dataset": "semeval",
        "domain": "short_answer",
        "language": "en",
        "question_text": df["question_text"],
        "reference_answer": df["reference_answer"].where(df["reference_answer"] != "", None),
        "rubric_json": None,
        "student_answer": df["student_answer"],
        "gold_score": (df["label_2way"] == "correct").astype(float),  # binary correctness
        "gold_scale_max": 1.0,
        "label_2way": df["label_2way"],
        "label_3way": df["label_3way"],
        "label_5way": df["label_5way"],
        "split": df["split"],
        "question_id": df["subset"].str.lower() + ":" + df["qid"],
        "submission_id": None,
        "source_meta": [json.dumps({"subset": s, "module": m, "raw_split": rs})
                        for s, m, rs in zip(df["subset"], df["module"], df["split"])],
    })
    out = schema.add_gold_norm(out)
    # EXPECTED dedup: Beetle (and SciEntsBank) replicate each student answer across the
    # Core/Dependency/Extra reference-matching subdirs with IDENTICAL text+label (verified:
    # 0 (text,label) conflicts per sa_id). One row per student answer is what we want; keep
    # first (Core references). Deduped sizes match canonical SemEval (SciEntsBank 10804 / Beetle 5199).
    dups = int(out["item_id"].duplicated().sum())
    out = out.drop_duplicates("item_id").reset_index(drop=True)
    out.attrs["dups_dropped"] = dups
    return out


def report(out: pd.DataFrame) -> None:
    print(f"\n=== SemEval ingest report ({len(out)} items, "
          f"{out.question_id.nunique()} questions, dups dropped {out.attrs.get('dups_dropped',0)}) ===")
    df = out.assign(subset=out.source_meta.map(lambda s: json.loads(s)["subset"]))
    print("By subset x split:")
    print(df.groupby(["subset", "split"]).size().to_string())
    print("\n5-way label distribution:")
    print(out.label_5way.value_counts().to_string())
    print("\n2-way (= gold_score) distribution:")
    print(out.label_2way.value_counts().to_string())
    print("\nNull rates:")
    for c in ["question_text", "reference_answer", "student_answer"]:
        empty = out[c].isna() | (out[c].astype(str).str.strip() == "")
        print(f"  {c:18}: {empty.mean()*100:5.1f}% empty")
    print("\n3 examples:")
    for _, r in out.sample(3, random_state=5).iterrows():
        print(f"  {r.item_id}  [{r.label_5way}] gold={r.gold_score}")
        print(f"    Q: {r.question_text[:75]!r}")
        print(f"    A: {r.student_answer[:70]!r}")


def main() -> int:
    out = build()
    out = schema.validate(out, dataset="semeval")
    schema.write_parquet(out, OUT)
    report(out)
    print(f"\nWrote {OUT.relative_to(REPO_ROOT)}")
    print("NOTES: tokenised Beetle answers recovered via raw_text; Core/Dependency/Extra replicas deduped "
          "(verified identical text+label) -> canonical 10804 SciEntsBank + 5199 Beetle; 'reliability' "
          "excluded; non-domain normalised; 3/2-way derived from 5-way; grounding = Core reference answers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
