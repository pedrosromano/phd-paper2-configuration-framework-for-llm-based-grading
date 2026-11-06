"""The zero-collapse and the prompt that removes it (2026-11-05): the engine for the follow-up's second part (prompt
engineering), its supplementary tables and the code prompt of the guide (internally CODE_WORDING). Protocol, variants, decision rules and Pedro's decisions are in
CLAUDE.md (S11, "Prompt-engineering pilot against the zero-collapse", steps 1 and 2), each fixed before the runs it
governs.

  diagnosis()   the written justifications behind zeros on half-right code answers (partial credit with a justification
                first; Qwen3.5 and DeepSeek-V4-Flash, PT-CS code and RIAYN): how many name something correct, and the
                reasons they give (keyword counts; a justification can give several).
  pilot()       development: six wordings against the same-batch partial-credit control (Qwen3.5, DeepSeek-V4-Flash;
                PT-CS code and RIAYN; k = 5): zeros, zeros on answers the human graders credited, QWK, MAE.
  all_models()  the chosen wording against the partial-credit wording for all five models on every rubric set of the
                study (RIAYN, PT-CS code, PT-CS short).
  human_zeros() whose zeros are deserved on Mohler: the grade of each of the two graders on the answers the models
                scored zero.

Pedro (2026-11-06): HARMOGEN-R and SAF are validation datasets and appear only in the guide's validation
(verification.py); the code wording's runs on HARMOGEN-R are the validation's guide cells, and no development step on
them is reported (the former heldout() table and the HARMOGEN-R rows of all_models and human_zeros were removed).

Run:  python -m experiments.analysis.zero_collapse
"""

from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from experiments.analysis import phase5
from experiments.analysis.make_phase5_tables import _boot_dist, _point, _qwk_items

RUNS = phase5.REPO_ROOT / "data" / "processed" / "runs"
CODE_WORDING = "partial_credit_teacher_credit_first"
WORDINGS = [  # (instruction key, label as in Fig. 1 of the paper, round); internal names keep "wording", the paper says "prompt"
    ("partial_credit_substance", "A: judge each rubric item on its own", 1),
    ("partial_credit_items", "B: A, and list each item's marks before the total", 1),
    ("partial_credit_credit_first", "C: A, and state what earns marks before the score", 1),
    ("partial_credit_subtractive", "D: A, starting from full marks and deducting", 1),
    ("partial_credit_teacher", "E: A, and grade as a teacher grades a written exam", 1),
    (CODE_WORDING, "the code prompt: C and E joined", 2),
]
MODELS = ["qwen3.5", "deepseek-v4-flash", "glm-5.1", "gpt-5.1", "claude-sonnet-4-6"]
UNDESERVED = 0.2          # a zero on an answer the human graders gave at least 20% of the marks
REASONS = {"another approach, other names, or not as the rubric specifies":
               r"instead|does not use|not use any|as required|specified|specific|required by the rubric|similarly named|different",
           "missing or incomplete parts": r"incomplete|cut off|cutting off|missing|fails to implement|lacks|not implement|absent",
           "syntax errors, or would not compile": r"syntax|compil|invalid|typo|misspel"}
_INTERV = set(pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "_ptcs_strata.parquet")
              .query("stratum=='intervened'").item_id)


def _keep(d: pd.DataFrame) -> pd.DataFrame:
    d = d[(d.dataset != "ptcs") | d.item_id.isin(_INTERV)].copy()
    d["model"] = d.model.replace({"glm-5.1-or": "glm-5.1"})
    return d


def _cell(g: pd.DataFrame) -> dict:
    q, s = _qwk_items(g)
    return {"N": len(s), "QWK": q, "zeros": 100 * float((g.pred_norm < 1e-9).mean()),
            "undeserved": 100 * float(((g.pred_norm < 1e-9) & (g.gold_norm >= UNDESERVED)).mean()),
            "MAE": float((s.p - s.g).abs().mean()), "bias": float((s.p - s.g).mean()),
            "out_tok": float(pd.to_numeric(g.completion_tokens, errors="coerce").mean()),
            "eur_1000": 1000 * float(pd.to_numeric(g.cost_eur, errors="coerce").mean())}


def _vs(A: pd.DataFrame, B: pd.DataFrame) -> dict:
    """B minus A on the answers both graded: dQWK with its 95% bootstrap interval, and dMAE."""
    _, sA = _qwk_items(A); _, sB = _qwk_items(B)
    dist = _boot_dist(sA, sB)
    lo, hi = np.percentile(dist, [2.5, 97.5])
    it = sorted(set(sA.index) & set(sB.index))
    mae = lambda s: float((s.loc[it].p - s.loc[it].g).abs().mean())
    return {"dQWK": _point(sA, sB), "lo": lo, "hi": hi, "higher": bool(lo > 0), "lower": bool(hi < 0),
            "dMAE": mae(sB) - mae(sA)}


_NEG = re.compile(r"\b(not|fails?|failing|without|n't|never|nor|unable)\b")


def _names_correct(t: str) -> bool:
    """A justification names something the answer does correctly: "correct(ly)", "identif..." or "properly", not as
    part of "incorrect(ly)" and not negated in the six words before it within the same clause ("does not ... correctly",
    "fails to implement ... correctly"). Fixed 2026-11-06: the published count matched "correct" anywhere, so
    "incorrectly" counted as naming something correct (90.9% instead of 52.2%)."""
    for m in re.finditer(r"(?<!in)correct\w*|identif\w*|properly", t):
        before = re.split(r"[.;,]| but | and | however ", " ".join(t[:m.start()].split()[-6:]))[-1]
        if not _NEG.search(before):
            return True
    return False


def diagnosis() -> dict:
    """Zeros on answers the teachers credited (>= 20% of the marks), in the partial-credit-with-justification runs."""
    rows = []
    for line in open(RUNS / "instruction.jsonl"):
        if '"partial_credit_justified"' not in line:
            continue
        r = json.loads(line)
        try:
            score = float(r.get("score"))
        except (TypeError, ValueError):
            continue
        if r.get("gold_score") is None or score != 0 or (r["dataset"] == "ptcs" and r["item_id"] not in _INTERV):
            continue
        if float(r["gold_score"]) / float(r["gold_scale_max"]) < UNDESERVED:
            continue
        m = re.search(r"\{.*\}", str(r.get("raw")), re.S)
        try:
            j = json.loads(m.group())["justification"] if m else str(r.get("raw"))
        except (ValueError, KeyError):
            j = str(r.get("raw"))
        rows.append({"model": r["model"], "dataset": r["dataset"], "text": j.lower()})
    d = pd.DataFrame(rows)
    out = {"runs": len(d), "names_something_correct": 100 * float(d.text.map(_names_correct).mean())}
    out.update({k: 100 * float(d.text.str.contains(p).mean()) for k, p in REASONS.items()})
    out["by_model_set"] = d.groupby(["model", "dataset"]).size().to_dict()
    return out


def pilot() -> pd.DataFrame:
    """Development: every wording against the same-batch partial-credit control."""
    d = _keep(phase5.prepare(phase5._read(RUNS / "instruction_substance.jsonl")))
    d = d[d.model.isin(["qwen3.5", "deepseek-v4-flash"]) & (d.domain == "code")]
    rows = []
    for (ds, m), g in d.groupby(["dataset", "model"]):
        ctrl = g[g.instruction == "partial_credit"]
        rows.append({"dataset": ds, "model": m, "wording": "partial_credit", "round": 0, **_cell(ctrl)})
        for key, _, rnd in WORDINGS:
            c = g[g.instruction == key]
            if c.empty:
                continue
            rows.append({"dataset": ds, "model": m, "wording": key, "round": rnd, **_cell(c), **_vs(ctrl, c)})
    return pd.DataFrame(rows)


def pilot_verdicts(t: pd.DataFrame) -> pd.DataFrame:
    """The rule fixed before the runs: WORKS if Qwen3.5 on PT-CS code has at most 20% zeros and a QWK gain whose 95%
    interval is above zero, with no significant loss for DeepSeek-V4-Flash (either set) or Qwen3.5 on RIAYN."""
    out = []
    for key, label, rnd in WORDINGS:
        s = t[t.wording == key].set_index(["dataset", "model"])
        if len(s) < 4:
            continue
        q = s.loc[("ptcs", "qwen3.5")]
        ctrl0 = t[(t.wording == "partial_credit") & (t.dataset == "ptcs") & (t.model == "qwen3.5")].zeros.iloc[0]
        no_loss = not any(s.loc[k].lower for k in [("ptcs", "deepseek-v4-flash"), ("riayn", "deepseek-v4-flash"),
                                                     ("riayn", "qwen3.5")])
        works = (q.zeros <= 20) and q.higher and no_loss
        out.append({"wording": key, "label": label, "round": rnd, "qwen_ptcs_zeros": q.zeros, "qwen_ptcs_dQWK": q.dQWK,
                    "lo": q.lo, "hi": q.hi, "no_loss": no_loss, "mean_QWK": s.QWK.mean(),
                    "verdict": "works" if works else ("partial" if (q.zeros < ctrl0 and no_loss) else "fails")})
    return pd.DataFrame(out)


def all_models() -> pd.DataFrame:
    """The code wording against the partial-credit wording (the guide before this change), all five models, every
    rubric set of the study. GLM-5.1 has no partial-credit cell on the PT-CS short answers: there it is compared with the strict
    instruction (flagged)."""
    new = _keep(phase5.prepare(phase5._read(RUNS / "instruction_substance.jsonl")))
    new = new[(new.instruction == CODE_WORDING) & (new.reasoning == "off") & (new.decomposition == "holistic")]
    ins = _keep(phase5.prepare(phase5._read(RUNS / "instruction.jsonl")))
    ins = ins[ins.instruction == "partial_credit"]
    main = _keep(phase5.load_main())
    main = main[(main.reasoning == "off") & (main.context_level == "with_guidance") & (main.scope == "question_by_question")
                & (main.decomposition == "holistic")]
    rows = []
    for (m, ds, dom), g in new.groupby(["model", "dataset", "domain"]):
        cur, against = ins[(ins.model == m) & (ins.dataset == ds) & (ins.domain == dom)], "partial credit"
        if cur.empty:
            cur, against = main[(main.model == m) & (main.dataset == ds) & (main.domain == dom)], "strict"
        c0, c1 = _cell(cur), _cell(g)
        rows.append({"model": m, "dataset": ds, "domain": dom, "against": against, "QWK_before": c0["QWK"],
                     "QWK_after": c1["QWK"], "zeros_before": c0["zeros"], "zeros_after": c1["zeros"],
                     "MAE_before": c0["MAE"], "MAE_after": c1["MAE"], "out_tok_before": c0["out_tok"],
                     "out_tok_after": c1["out_tok"], "cost_x": c1["eur_1000"] / c0["eur_1000"], **_vs(cur, g)})
    return pd.DataFrame(rows)


def human_zeros() -> dict:
    """Whose zeros are deserved on Mohler (reasoning off, with the reference answer, strict instruction): on the
    answers each model scored zero, the share the first grader scored 0 or 1 of 5, and the share both graders scored
    2.5 or more."""
    mo = pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "corpus_mohler.parquet").set_index("item_id")
    meta = mo.source_meta.map(json.loads)
    A, B = meta.map(lambda x: x["score_me"]), meta.map(lambda x: x["score_other"])
    main = phase5.load_main()
    mm = main[(main.dataset == "mohler") & (main.reasoning == "off") & (main.context_level == "with_guidance")
              & (main.scope == "question_by_question") & (main.decomposition == "holistic")]
    moh = []
    for m, g in mm.groupby("model"):
        z = g[g.pred_norm < 1e-9]
        a, b = A.reindex(z.item_id).to_numpy(), B.reindex(z.item_id).to_numpy()
        moh.append({"model": m, "zeros": 100 * len(z) / len(g), "first_grader_0_or_1": 100 * float((a <= 1).mean()),
                    "both_2.5_or_more": 100 * float(((a >= 2.5) & (b >= 2.5)).mean())})
    return {"mohler": pd.DataFrame(moh),
            "mohler_grader_zero_pct": (100 * float((A == 0).mean()), 100 * float((B == 0).mean()),
                                       100 * float((mo.gold_norm == 0).mean())),
            "mohler_spreadsheet_errors": int((mo.student_answer.astype(str).str.strip() == "#NAME?").sum())}


def main() -> int:
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    dg = diagnosis()
    print("=== diagnosis: zeros on answers the teachers credited (>= 20%), justification runs ===")
    print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in dg.items()})
    t = pilot()
    print("\n=== development: every wording against the same-batch partial-credit control ===")
    print(t.round(3).to_string(index=False))
    print(pilot_verdicts(t).round(3).to_string(index=False))
    a = all_models()
    print("\n=== the code wording against partial credit, all models, every rubric set of the study ===")
    print(a.round(3).to_string(index=False))
    code = a[a.domain == "code"]
    print(f"code: {len(code)} cells, mean dQWK {code.dQWK.mean():+.3f}; higher {int(code.higher.sum())}, lower "
          f"{int(code.lower.sum())}; MAE lower in {int((code.dMAE < 0).sum())}; output tokens x{(code.out_tok_after / code.out_tok_before).min():.1f}"
          f" to x{(code.out_tok_after / code.out_tok_before).max():.1f}; cost x{code.cost_x.min():.2f} to x{code.cost_x.max():.2f}")
    sh = a[a.domain == "short_answer"]
    print(f"PT-CS short answers: dQWK {sh.dQWK.min():+.3f} to {sh.dQWK.max():+.3f}; lower {int(sh.lower.sum())} of {len(sh)}; "
          f"zeros {sh.zeros_after.min():.1f} to {sh.zeros_after.max():.1f}%; MAE higher in {int((sh.dMAE > 0).sum())}")
    hz = human_zeros()
    print("\n=== whose zeros are deserved ===")
    print(hz["mohler"].round(1).to_string(index=False))
    print("Mohler zero grades: first grader %.1f%%, second %.1f%%, their mean %.1f%%" % hz["mohler_grader_zero_pct"],
          "| answers that are spreadsheet errors (#NAME?):", hz["mohler_spreadsheet_errors"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
