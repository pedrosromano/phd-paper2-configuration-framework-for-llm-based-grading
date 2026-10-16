"""The guide in use (Pedro's review 2026-10-16, item P6): apply the guide's configuration to every set and
compare it with every configuration the study ran, on agreement (QWK), consistency (within-item SD), the
share of zero grades, and cost. The engine for the guide section's table and figure.

Configurations, all with guidance, one question per call, holistic, clean conversation:
  - main store: each model with reasoning off and on, strict instruction (RQ1/RQ4 cells);
  - instruction store: the partial-credit instruction per model, and Claude Sonnet 4.6 with both instructions.
The same-batch strict re-runs of the instruction store are left out (they duplicate main-store cells).

Two bases, as in the rest of the paper:
  A. the sampled items every configuration graded (the reasoning samples): all configurations;
  B. the items every reasoning-off configuration graded (all items; Mohler: the 800 Claude Sonnet 4.6 graded):
     the reasoning-off configurations only (reasoning on was sampled).

Run:  python -m experiments.analysis.guide_eval
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from experiments.analysis import phase5
from experiments.analysis.make_phase5_tables import _qwk_items

GUIDE = ("deepseek-v4-flash", "off", "partial_credit")      # the recipe's model, reasoning, instruction
BASELINE = ("qwen3.5", "off", "standard")                  # the study's starting configuration
SETS = [("mohler", "short_answer", "Mohler"), ("semeval", "short_answer", "SemEval"), ("riayn", "code", "RIAYN"),
        ("ptcs", "code", "PT-CS code"), ("ptcs", "short_answer", "PT-CS short")]
_INTERV = set(pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "_ptcs_strata.parquet")
              .query("stratum=='intervened'").item_id)


def rows() -> pd.DataFrame:
    main = phase5.load_main()
    main = main[(main.context_level == "with_guidance") & (main.scope == "question_by_question")
                & (main.decomposition == "holistic")].assign(instruction="standard")
    ins = phase5.load_instruction()
    ins = ins[(ins.instruction != "standard") | (ins.model == "claude-sonnet-4-6")]
    ins = ins[ins.instruction != "partial_credit_justified"]
    # GLM-5.1 via OpenRouter ran on code only (rate-limited account); 60 Mohler rows of an aborted full run stay out
    ins = ins[~((ins.model == "glm-5.1-or") & (ins.domain != "code"))]
    d = pd.concat([main, ins], ignore_index=True)
    d = d[(d.dataset != "ptcs") | d.item_id.isin(_INTERV)]
    if "fallback" not in d:
        d["fallback"] = False
    d["fallback"] = d["fallback"].fillna(False).astype(bool)
    d["cfg"] = d.model + "|" + d.reasoning + "|" + d.instruction
    return d


def _cell(g: pd.DataFrame) -> dict:
    q, s = _qwk_items(g)
    own = g[~g.fallback]
    return {"QWK": q, "N": len(s), "SDk": float(own.groupby("item_id").pred_norm.std().mean()),
            "zero_pct": 100 * float((own.pred_norm < 1e-9).mean()),
            "eur_1000": 1000 * float(pd.to_numeric(g.cost_eur, errors="coerce").mean())}


def evaluate(d: pd.DataFrame) -> pd.DataFrame:
    out = []
    for ds, dom, lbl in SETS:
        s = d[(d.dataset == ds) & (d.domain == dom)]
        cfgs = sorted(set(s.cfg))
        # basis A: items every configuration graded
        common = set.intersection(*[set(s[s.cfg == c].item_id) for c in cfgs])
        off = [c for c in cfgs if c.split("|")[1] == "off"]
        common_off = set.intersection(*[set(s[s.cfg == c].item_id) for c in off])
        for basis, items, pool in [("A", common, cfgs), ("B", common_off, off)]:
            for c in pool:
                g = s[(s.cfg == c) & s.item_id.isin(items)]
                if g.empty:
                    continue
                m_, r_, i_ = c.split("|")
                out.append({"set": lbl, "basis": basis, "model": m_, "reasoning": r_, "instruction": i_, **_cell(g)})
    r = pd.DataFrame(out)
    r["rank"] = r.groupby(["set", "basis"]).QWK.rank(ascending=False, method="min")
    r["n_cfg"] = r.groupby(["set", "basis"]).QWK.transform("size")
    return r


def summary(r: pd.DataFrame) -> pd.DataFrame:
    rows_ = []
    for (lbl, basis), g in r.groupby(["set", "basis"], sort=False):
        gd = g[(g.model == GUIDE[0]) & (g.reasoning == GUIDE[1]) & (g.instruction == GUIDE[2])]
        bl = g[(g.model == BASELINE[0]) & (g.reasoning == BASELINE[1]) & (g.instruction == BASELINE[2])]
        best = g.loc[g.QWK.idxmax()]
        if gd.empty:
            continue
        gd = gd.iloc[0]
        cheaper = g[g.eur_1000 < gd.eur_1000 - 1e-12]
        dominated_by = g[(g.QWK > gd.QWK + 1e-9) & (g.eur_1000 <= gd.eur_1000)]
        rows_.append({"set": lbl, "basis": basis, "N": int(gd.N), "configs": int(gd.n_cfg),
                      "guide_QWK": gd.QWK, "guide_rank": int(gd["rank"]), "guide_eur": gd.eur_1000,
                      "guide_SD": gd.SDk, "guide_zero": gd.zero_pct,
                      "baseline_QWK": float(bl.QWK.iloc[0]) if len(bl) else np.nan,
                      "best": f"{best.model}|{best.reasoning}|{best.instruction}", "best_QWK": best.QWK,
                      "best_eur": best.eur_1000, "gap_to_best": best.QWK - gd.QWK,
                      "cheaper_x_than_best": best.eur_1000 / gd.eur_1000 if gd.eur_1000 else np.nan,
                      "n_cheaper": len(cheaper), "pareto": dominated_by.empty})
    return pd.DataFrame(rows_)


MNAME = {"qwen3.5": "Qwen3.5", "deepseek-v4-flash": "DeepSeek-V4-Flash", "glm-5.1": "GLM-5.1", "gpt-5.1": "GPT-5.1",
         "claude-sonnet-4-6": "Claude Sonnet 4.6", "glm-5.1-or": "GLM-5.1 (OpenRouter)"}


def _name(cfg: str) -> str:
    m, r, i = cfg.split("|")
    if (m, r, i) == GUIDE:
        return "the recipe"
    extra = [", reasoning on"] if r == "on" else []
    extra += [", partial credit"] if i == "partial_credit" else []
    return MNAME.get(m, m) + "".join(extra)


def write_table(ge: pd.DataFrame) -> None:
    """tab_guide_use (the guide in use, Section VI): per set, the recipe's agreement and cost, its rank among the
    configurations without reasoning (basis B), the best of those, the best configuration of any kind on the
    sampled items (basis A) with its cost relative to the recipe, and the study's baseline configuration."""
    from experiments.analysis.make_phase5_tables import _tex
    B = ge[ge.basis == "B"].set_index("set"); A = ge[ge.basis == "A"].set_index("set")
    rows_ = []
    for _, _, lbl in SETS:
        b, a = B.loc[lbl], A.loc[lbl]
        rows_.append({"Dataset": lbl, "Recipe QWK": f"{b.guide_QWK:.3f}", "\\euro/1000": f"{b.guide_eur:.2f}",
                      "Rank": f"{int(b.guide_rank)} of {int(b.configs)}",
                      "Best without reasoning": ("the recipe" if b.gap_to_best < 1e-9 else f"{_name(b.best)}, {b.best_QWK:.3f}"),
                      "Best on the sampled items": (f"{_name(a.best)}, {a.best_QWK:.3f} "
                                                    f"(recipe {a.guide_QWK:.3f}; {a.cheaper_x_than_best:.0f}$\\times$ cost)"),
                      "Baseline": f"{b.baseline_QWK:.3f}"})
    _tex(pd.DataFrame(rows_), "tab_guide_use.tex",
         "The guide in use: the recipe (DeepSeek-V4-Flash, reasoning off, guidance, partial credit, one question per "
         "call, holistic, clean conversation) against every configuration in the study. Rank is among the "
         "configurations without reasoning, all scored on the same items (Mohler: the 800 that every one of them "
         "graded). The best configuration on the sampled items includes reasoning on; the recipe's QWK on the same "
         "items and the cost multiple of the best are in brackets. Baseline is the study's starting configuration, "
         "Qwen3.5 with the strict instruction. Costs are euros per 1000 grades.",
         "tab:guideuse", star=True, colspec="lrrlllr", size="\\footnotesize")


def main() -> int:
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    r = evaluate(rows())
    print("=== every configuration, per set and basis ===")
    print(r.sort_values(["set", "basis", "rank"]).round(3).to_string(index=False))
    print("\n=== the guide against the field ===")
    print(summary(r).round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
