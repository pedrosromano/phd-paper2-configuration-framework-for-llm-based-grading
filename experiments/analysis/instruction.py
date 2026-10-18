"""Grading-instruction experiment (RQ6; Pedro's review, 2026-10-16): the engine for its prose, table and figure.

Variants (prompts_instruction.yaml): standard = the original strict instruction, re-run in the same batch
(drift guard); partial_credit = explicit partial credit; partial_credit_justified = partial credit plus a
justification of at most two sentences written before the score. All with guidance, reasoning off, one
question per call, holistic, k=5; PT-CS on the teacher-validated answers.

Decision rule, fixed before any variant was run (E1 in article/review/REVISAO_PR_ESTADO.md, now in git history: dcc1c22): a variant enters
the guide if it raises QWK significantly (95% CI, Holm within this family) for the models that give too many
zeros (Qwen3.5, GPT-5.1) without lowering it significantly for the one that does not (DeepSeek-V4-Flash).

Run:  python -m experiments.analysis.instruction
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from experiments.analysis import phase5
from experiments.analysis.make_phase5_tables import _boot_dist, _holm, _p_boot, _qwk_items

VARIANTS = ["standard", "partial_credit", "partial_credit_justified"]
MAIN_MODEL = {"glm-5.1-or": "glm-5.1"}     # the same model served elsewhere: its main-store (DeepInfra) rows
VNAME = {"standard": "strict", "partial_credit": "partial credit", "partial_credit_justified": "partial credit + justification"}
MODELS = ["qwen3.5", "gpt-5.1", "deepseek-v4-flash"]
_INTERV = set(pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "_ptcs_strata.parquet")
              .query("stratum=='intervened'").item_id)


def load() -> pd.DataFrame:
    """Instruction-store rows; for a model with no same-batch strict re-run (GPT-5.1, whose re-run was skipped
    to save cost after the open models' re-runs reproduced their original rows), the strict cells are its
    main-store rows on the same items, marked source='main'."""
    d = phase5.load_instruction()
    d = d[(d.dataset != "ptcs") | d.item_id.isin(_INTERV)]
    if "instruction" not in d:
        d["instruction"] = "standard"
    d = d[~((d.model == "glm-5.1-or") & (d.domain != "code"))]   # GLM-5.1 (OpenRouter) ran on code only; 60 aborted Mohler rows out
    d = d.assign(source="instruction")
    # cells with a partial-credit run but no same-batch strict run take the main-store strict rows of the same
    # model on the same items: GPT-5.1 (its strict re-run was skipped to save cost) and GLM-5.1 served through
    # OpenRouter on PT-CS code (its strict re-run on RIAYN reproduced the June DeepInfra rows: QWK 0.726 on both,
    # the same grade in 77% of item-repetitions)
    have = set(map(tuple, d[d.instruction == "standard"][["model", "dataset", "domain"]].drop_duplicates().to_numpy()))
    need = d[(d.instruction != "standard")][["model", "dataset", "domain"]].drop_duplicates()
    need = need[[tuple(r) not in have for r in need.to_numpy()]]
    if len(need):
        main = phase5.load_main()
        base = main[(main.reasoning == "off") & (main.context_level == "with_guidance")
                    & (main.scope == "question_by_question") & (main.decomposition == "holistic")]
        parts = []
        for m, ds, dom in need.to_numpy():
            items = set(d[(d.model == m) & (d.dataset == ds) & (d.domain == dom)].item_id)
            b = base[(base.model == MAIN_MODEL.get(m, m)) & (base.dataset == ds) & (base.domain == dom) & base.item_id.isin(items)]
            parts.append(b.assign(model=m, instruction="standard", source="main"))
        d = pd.concat([d] + parts, ignore_index=True)
    return d


def levels(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (ds, dom, m, v), g in d.groupby(["dataset", "domain", "model", "instruction"]):
        q, s = _qwk_items(g)
        gold0 = g.groupby("item_id").gold_norm.first()
        rows.append({"dataset": ds, "domain": dom, "model": m, "instruction": v, "N": len(s), "QWK": q,
                     "zero_pct": 100 * float((g.pred_norm < 1e-9).mean()), "teacher_zero_pct": 100 * float((gold0 < 1e-9).mean()),
                     "mean_pred": float(g.pred_norm.mean()), "mean_gold": float(gold0.mean()),
                     "SDk": float(g.groupby("item_id").pred_norm.std().mean()),
                     "out_tok": float(pd.to_numeric(g.completion_tokens, errors="coerce").mean()),
                     "eur_1000": 1000 * float(pd.to_numeric(g.cost_eur, errors="coerce").mean()),
                     "pi": float(g.parse_ok.mean())})
    return pd.DataFrame(rows)


def contrasts(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (ds, dom, m), g in d.groupby(["dataset", "domain", "model"]):
        cells = {v: g[g.instruction == v] for v in VARIANTS if (g.instruction == v).any()}
        for a, b in [("standard", "partial_credit"), ("standard", "partial_credit_justified"),
                     ("partial_credit", "partial_credit_justified")]:
            if a not in cells or b not in cells:
                continue
            _, sA = _qwk_items(cells[a]); _, sB = _qwk_items(cells[b])
            dist = _boot_dist(sA, sB)
            if dist is None:
                continue
            lo, md, hi = np.percentile(dist, [2.5, 50, 97.5])
            lo90, hi90 = np.percentile(dist, [5, 95])
            rows.append({"dataset": ds, "domain": dom, "model": m, "contrast": f"{VNAME[b]} vs {VNAME[a]}",
                         "dQWK": md, "lo": lo, "hi": hi, "p": _p_boot(dist), "sig": bool(lo > 0 or hi < 0),
                         "equivalent": bool(lo90 > -0.05 and hi90 < 0.05), "N": len(set(sA.index) & set(sB.index))})
    out = pd.DataFrame(rows)
    if len(out):
        prim = out.contrast.str.endswith("vs strict")          # the family Holm runs over: each variant vs strict
        out["p_holm"] = np.nan
        out.loc[prim, "p_holm"] = _holm(list(out.loc[prim, "p"]))
        out["sig_holm"] = out.p_holm < 0.05
    return out


def drift(d: pd.DataFrame) -> pd.DataFrame:
    """The same-batch standard re-run against the original baseline rows (same config): QWK of each, and the
    share of (item, repetition) grades that are identical."""
    main = phase5.load_main()
    main = main[(main.dataset != "ptcs") | main.item_id.isin(_INTERV)]
    rows = []
    for (ds, dom, m), g in d[(d.instruction == "standard") & (d.source == "instruction")].groupby(["dataset", "domain", "model"]):
        o = main[(main.dataset == ds) & (main.domain == dom) & (main.model == MAIN_MODEL.get(m, m)) & (main.reasoning == "off")
                 & (main.context_level == "with_guidance") & (main.scope == "question_by_question")
                 & (main.decomposition == "holistic") & main.item_id.isin(set(g.item_id))]
        if o.empty:
            continue
        j = g.merge(o[["item_id", "run_index", "pred_norm"]], on=["item_id", "run_index"], suffixes=("", "_orig"))
        rows.append({"dataset": ds, "domain": dom, "model": m, "QWK_rerun": _qwk_items(g)[0],
                     "QWK_original": _qwk_items(o)[0], "same_grade_pct": 100 * float((abs(j.pred_norm - j.pred_norm_orig) < 1e-9).mean()),
                     "n_pairs": len(j)})
    return pd.DataFrame(rows)


def versus_reasoning(d: pd.DataFrame) -> pd.DataFrame:
    """Each variant against the same model with reasoning on (original prompt), on the reasoning samples."""
    main = phase5.load_main()
    main = main[(main.dataset != "ptcs") | main.item_id.isin(_INTERV)]
    rows = []
    for (ds, dom, m), g in d.groupby(["dataset", "domain", "model"]):
        on = main[(main.dataset == ds) & (main.domain == dom) & (main.model == m) & (main.reasoning == "on")
                  & (main.context_level == "with_guidance") & (main.scope == "question_by_question")
                  & (main.decomposition == "holistic")]
        if on.empty:
            continue
        items = set(on.item_id)
        rec = {"dataset": ds, "domain": dom, "model": m, "N": len(items), "QWK_reasoning_on": _qwk_items(on)[0],
               "eur_1000_on": 1000 * float(pd.to_numeric(on.cost_eur, errors="coerce").mean())}
        for v in VARIANTS:
            c = g[(g.instruction == v) & g.item_id.isin(items)]
            if len(c):
                rec[f"QWK_{v}"] = _qwk_items(c)[0]
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> int:
    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
    d = load()
    print(f"instruction store: {len(d)} rows, models {sorted(d.model.unique())}")
    print("\n=== levels per variant (reasoning off, with guidance, one question per call, holistic) ===")
    print(levels(d).round(3).to_string(index=False))
    print("\n=== contrasts (dQWK, bootstrap 95% CI, Holm over the 'vs strict' family, TOST +/-0.05) ===")
    print(contrasts(d).round(4).to_string(index=False))
    print("\n=== drift guard: same-batch strict re-run vs the original rows ===")
    print(drift(d).round(3).to_string(index=False))
    print("\n=== against reasoning on (original prompt), on the reasoning samples ===")
    print(versus_reasoning(d).round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
