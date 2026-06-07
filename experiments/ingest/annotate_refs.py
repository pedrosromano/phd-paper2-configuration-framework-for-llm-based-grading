"""Annotate the merged library with relevance / theme / extracted performance (Phase 1.3).

Reads refs_merged.csv, reads each title+abstract+keywords, and adds:
  - relevance   : high | med | low | exclude  (rule-based first pass; hand-refined after)
  - reason      : short justification
  - theme       : reasoning | code | consistency | dataset-specific | grading | other
  - perf        : best-effort extracted "metric=value" pairs found in the abstract
  - perf_dataset: any of our/benchmark datasets named in the abstract

This is a TRANSPARENT, reproducible triage so a human can inspect and correct the
shortlist (the high/med set) rather than reading 1093 abstracts blind. Relevance turns on
whether the paper is about *automated grading/assessment of student responses* (our topic),
not LLMs-in-general. Noise (medical/chem/industrial/security LLM papers from the broad
ScienceDirect query) is pushed to `exclude`.

Run:  python -m experiments.ingest.annotate_refs
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
CSV = REPO_ROOT / "article" / "related" / "library" / "refs_merged.csv"

# --- keyword vocabularies (lowercase substring match) ---
GRADING_CORE = [
    "grading", "grade ", "graded", "grader", "scoring", "score ", "scored", "marking",
    "automated assessment", "automatic assessment", "auto-grad", "autograd", "autograder",
    "short answer", "short-answer", "essay scor", "essay grad", "answer grad", "answer scor",
    " aes", "asag", "rubric", "partial credit", "exam grad", "assessment of student",
    "student response", "constructed response", "open-ended response", "open response",
]
EDU_CTX = [
    "student", "education", "classroom", "course", "learner", "teacher", "instructor",
    "exam", "assignment", "university", "school", "mooc", "formative", "summative",
    "pedagog", "curriculum", "e-learning", "tutor", "academic",
]
ASSESS_ADJ = ["feedback", "rubric", "intelligent tutor", "assessment", "evaluat", "proctor"]
LLM_ML = [
    "llm", "large language model", "gpt", "language model", "bert", "transformer",
    "fine-tun", "fine tun", "machine learning", "deep learning", "neural", "prompt",
    "generative ai", "genai", "roberta", "llama", "gemini", "claude", "qwen", "mistral",
]
EXCLUDE_DOMAIN = [
    "medical", "clinical", "patient", "disease", "diagnos", "chemical", "emission",
    "manufactur", "defect", "materials science", "molecul", "protein", "drug", "battery",
    "energy", "traffic", "intrusion", "malware", "vulnerabilit", "phishing", "agricultur",
    "crop", "financial", "stock market", "remote sensing", "wireless", "antenna", "uav",
    "autonomous driving", "supply chain", "wastewater", "seismic", "geolog", "biomed",
    "radiolog", "cancer", "covid", "power grid", "fault detection", "cybersecurit",
]
# themes
THEME_REASONING = ["reasoning", "chain-of-thought", "chain of thought", "step-by-step",
                   "deliberat", "thinking model", "o1", "o3", "extended thinking", "cot "]
THEME_CODE = ["code", "programming", "program grad", "source code", "java", "python ",
              "sql", "computer science", "cs1", "cs2", "compiler", "unit test"]
THEME_CONSISTENCY = ["consisten", "reliab", "repeatab", "reproducib", "variance", "stability",
                     "intra-rater", "inter-rater", "icc", "agreement across", "temporal drift"]

# keys are matched as substrings; chosen to avoid false hits (e.g. bare "texas" caught a
# chemical-emissions paper; "roar" caught a medical "grade group" paper -> require "roars").
DATASETS = {
    "mohler": "Mohler", "asap-sas": "ASAP-SAS", "asap": "ASAP", "semeval": "SemEval",
    "scientsbank": "SciEntsBank", "sciensbank": "SciEntsBank", "beetle": "Beetle",
    "dt-grade": "DT-Grade", "roars dataset": "ROARs", "wikisql": "WikiSQL",
    "riayn": "RIAYN", "rubric is all you need": "RIAYN",
}

METRIC_RE = re.compile(
    r"\b(qwk|quadratic weighted kappa|cohen'?s?\s*kappa|kappa|κ|mae|rmse|mse|"
    r"macro[- ]?f1|weighted[- ]?f1|f1|accuracy|acc|pearson|spearman|icc|r2|r\^2|within[- ]?±?1)"
    r"\b[^.;,\n]{0,18}?(\d{1,3}(?:\.\d+)?\s*%|0?\.\d+|\d{1,3}\s*%)",
    re.I,
)


def has(text: str, vocab: list[str]) -> bool:
    return any(k in text for k in vocab)


def count(text: str, vocab: list[str]) -> int:
    return sum(text.count(k) for k in vocab)


def extract_perf(abstract: str) -> str:
    pairs = []
    for m in METRIC_RE.finditer(abstract):
        metric = re.sub(r"\s+", " ", m.group(1)).strip().upper()
        val = m.group(2).replace(" ", "")
        pairs.append(f"{metric}={val}")
        if len(pairs) >= 6:
            break
    # dedupe preserving order
    seen, out = set(), []
    for p in pairs:
        if p not in seen:
            seen.add(p); out.append(p)
    return "; ".join(out)


def detect_datasets(text: str) -> str:
    found = []
    for k, label in DATASETS.items():
        if k in text and label not in found:
            found.append(label)
    return "; ".join(found)


def theme_of(text: str, is_grading: bool) -> str:
    if has(text, THEME_REASONING):
        return "reasoning"
    if has(text, THEME_CONSISTENCY):
        return "consistency"
    if count(text, THEME_CODE) >= 1 and is_grading:
        return "code"
    if detect_datasets(text):
        return "dataset-specific"
    return "grading" if is_grading else "other"


def annotate_row(r: pd.Series) -> dict:
    text = f"{r.title} {r.abstract} {r.keywords}".lower()
    title = str(r.title).lower()
    grading = has(text, GRADING_CORE)
    edu = has(text, EDU_CTX)
    excl = has(text, EXCLUDE_DOMAIN)
    llm = has(text, LLM_ML)
    perf = extract_perf(str(r.abstract))
    ds = detect_datasets(text)
    grading_in_title = has(title, GRADING_CORE)

    # --- relevance rules (topical: is the paper ABOUT grading student responses?) ---
    if excl and not grading_in_title and not (grading and edu):
        rel, reason = "exclude", "non-education domain (LLM applied elsewhere)"
    elif grading_in_title and edu:
        # grading is the subject of the paper -> core Related Work material
        evid = "; ".join(x for x in [("metric:" + perf) if perf else "",
                                      ("data:" + ds) if ds else ""] if x)
        rel = "high"
        reason = "grading-focused (title) + edu" + (f" [{evid}]" if evid else "")
    elif grading and edu:
        # grading appears but is not the paper's headline -> a component / partial relevance
        rel = "high" if (perf and ds) else "med"
        reason = ("grading+edu in abstract; "
                  + ("has metric+dataset" if (perf and ds) else "grading not central / no benchmark"))
    elif edu and has(text, ASSESS_ADJ) and llm:
        rel, reason = "low", "education+assessment-adjacent (feedback/rubric/ITS), not core grading"
    elif not edu:
        rel, reason = "exclude", "no education/assessment context"
    else:
        rel, reason = "low", "education+LLM but tangential to grading"

    if bool(r.in_slr):
        reason += " [in SLR]"

    return {
        "relevance": rel,
        "reason": reason,
        "theme": theme_of(text, grading and edu),
        "perf": perf,
        "perf_dataset": ds,
    }


def main() -> int:
    df = pd.read_csv(CSV).fillna("")
    ann = df.apply(annotate_row, axis=1, result_type="expand")
    for c in ["relevance", "reason", "theme", "perf", "perf_dataset"]:
        df[c] = ann[c]
    df.to_csv(CSV, index=False)

    print(f"Annotated {len(df)} rows -> {CSV.relative_to(REPO_ROOT)}\n")
    print("Relevance:")
    print(df["relevance"].value_counts().reindex(["high", "med", "low", "exclude"]).to_string())
    print("\nTheme (relevance != exclude):")
    print(df[df.relevance != "exclude"]["theme"].value_counts().to_string())
    print("\nHigh/med by cutoff flag:")
    sub = df[df.relevance.isin(["high", "med"])]
    print(sub["cutoff_flag"].value_counts().to_string())
    print(f"\nRows with extracted perf: {(df['perf'] != '').sum()}")
    print(f"Rows naming a dataset: {(df['perf_dataset'] != '').sum()}")
    print(f"High-relevance & in_slr (already covered): {((df.relevance=='high') & (df.in_slr)).sum()}")
    print("\nDataset mentions among non-excluded:")
    ds_counts = (df[df.relevance != "exclude"]["perf_dataset"]
                 .str.split("; ").explode().value_counts())
    print(ds_counts.to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
