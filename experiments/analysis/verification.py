"""The guide's validation (2026-10-18): two datasets that played no part in building it. Called the "additional
verification" until Pedro's review of 2026-10-19, which keeps the word "validation" for this alone; the module name
stayed. Its figure is phase6.fig_guide_validation, drawn like the tests' figure; the former table (Table 5) left the
paper, and its values are in the supplementary material (supplementary.verification_section).

Protocol fixed in CLAUDE.md S11 before any call. SAF (300 English short answers; reasoning on the first 150) and
HARMOGEN-R (129 C++ code answers in Portuguese), five models, k = 3, store runs/verification.jsonl, arms v_* in
matrix.yaml. The guide is guidance + partial credit + reasoning off + one question per call + holistic; each
alternative changes one setting:
  no guidance         context none (the prompt then has no guidance block, so no instruction either)
  strict instruction  the original strict wording instead of partial credit
  reasoning on        partial credit, reasoning on (a run that returned no grade takes the guide's grade for that
                      answer and repetition, as in the study)
  criterion scoring   partial credit, a score per rubric criterion and their total (code; not Claude)
Statistics as in the paper: QWK on six levels of the mean of the k grades, dQWK = alternative - guide on the answers
both graded, 10,000 bootstrap resamples over answers, 95% CI, no correction (as Test 1).
Criterion fixed in advance: the guide passes on a dataset if, for every model, no alternative without reasoning
agrees with the teachers significantly better than the guide.
Non-inferiority (second independent review, 2026-10-19; reported beside the criterion, which stays as fixed): with the
equivalence margin fixed in advance (+/-0.05 QWK, bloco_c.MARGIN), the guide is non-inferior to an alternative when
the upper bound of the 90% interval of (alternative - guide) is below 0.05, i.e. the alternative's advantage, if
any, is shown to be smaller than the margin (one-sided test at 5%).

  python -m experiments.analysis.verification          # prints everything
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from experiments.analysis import phase5
from experiments.analysis.bloco_c import MARGIN
from experiments.analysis.make_phase5_tables import _boot_dist, _point, _qwk_items

VERIF = phase5.REPO_ROOT / "data" / "processed" / "runs" / "verification.jsonl"
SETS = [("saf", "short_answer", "SAF (short answers)"), ("harmogenr", "code", "HARMOGEN-R (code)")]
MODELS = ["qwen3.5", "deepseek-v4-flash", "glm-5.1", "gpt-5.1", "claude-sonnet-4-6"]
ALTS = ["no guidance", "strict instruction", "criterion scoring", "reasoning on"]


def _kind(r) -> str:
    if r.reasoning == "on":
        return "reasoning on"
    if r.context_level == "none":
        return "no guidance"
    if r.decomposition == "criterion":
        return "criterion scoring"
    if r.instruction == "standard":
        return "strict instruction"
    return "guide"


def load() -> pd.DataFrame:
    d = phase5.prepare(phase5._read(VERIF))
    d["model"] = d.model.replace({"glm-5.1-or": "glm-5.1"})          # GLM-5.1 served through OpenRouter
    d["kind"] = d.apply(_kind, axis=1)
    # a reasoning-on run that returned no grade (at the output limit, or GLM-5.1 output that does not parse) takes
    # the guide's grade for the same answer and run, as in the study; a failed call is left out (none remain:
    # the 84 DeepInfra read timeouts were all re-graded with regrade_errors)
    d["fallback"] = False
    keys = ["dataset", "domain", "model", "item_id", "run_index"]
    guide = d[(d.kind == "guide") & d.pred_norm.notna()].drop_duplicates(keys).set_index(keys)
    e = d["error"].fillna("").astype(str) if "error" in d else pd.Series("", index=d.index)
    bad = (d.kind == "reasoning on") & d.pred_norm.isna() & (e.str.len() == 0)
    if bad.any():
        vals = guide["pred_norm"].reindex(pd.MultiIndex.from_frame(d.loc[bad, keys])).to_numpy()
        d.loc[bad, "pred_norm"] = vals
        d.loc[bad, "fallback"] = ~pd.isna(vals)
    return d


def _sd(g: pd.DataFrame) -> float:
    own = g[g.pred_norm.notna() & ~g.fallback]
    return float(own.groupby("item_id").pred_norm.std().mean())


def contrasts(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ds, dom, lbl in SETS:
        for m in MODELS:
            s = d[(d.dataset == ds) & (d.domain == dom) & (d.model == m)]
            G = s[s.kind == "guide"]
            if G.empty:
                continue
            qg, sG = _qwk_items(G)
            cost_g = pd.to_numeric(G.cost_eur, errors="coerce").mean()
            rows.append({"set": lbl, "model": m, "kind": "guide", "N": len(sG), "QWK": qg, "SD": _sd(G),
                         "zeros": float((G.pred_norm < 1e-9).mean()), "eur_1000": 1000 * cost_g})
            for k in ALTS:
                A = s[s.kind == k]
                if A.empty:
                    continue
                qa, sA = _qwk_items(A)
                ds_ = _boot_dist(sG, sA)
                if ds_ is None:                                   # fewer than 8 common answers (runs incomplete)
                    continue
                lo, hi = np.percentile(ds_, [2.5, 97.5])
                hi90 = float(np.percentile(ds_, 95))
                items = set(sA.index) & set(sG.index)
                Gi, Ai = G[G.item_id.isin(items)], A[A.item_id.isin(items)]
                rows.append({"set": lbl, "model": m, "kind": k, "N": len(items), "QWK": qa, "dQWK": _point(sG, sA),
                             "lo": lo, "hi": hi, "better": bool(lo > 0), "worse": bool(hi < 0),
                             "hi90": hi90, "noninferior": bool(hi90 < MARGIN),
                             "SD": _sd(Ai), "SD_guide": _sd(Gi), "zeros": float((A.pred_norm < 1e-9).mean()),
                             "cost_x": pd.to_numeric(Ai.cost_eur, errors="coerce").mean()
                             / pd.to_numeric(Gi.cost_eur, errors="coerce").mean(),
                             "fallback_pct": 100 * float(A.fallback.mean())})
    return pd.DataFrame(rows)


def verdict(t: pd.DataFrame) -> pd.DataFrame:
    """The pre-registered criterion, per dataset: no alternative without reasoning significantly better than the
    guide for any model."""
    alt = t[(t.kind != "guide") & (t.kind != "reasoning on")]
    out = []
    for lbl, g in alt.groupby("set", sort=False):
        b, w = g.better.astype(bool), g.worse.astype(bool)
        out.append({"set": lbl, "comparisons": len(g), "alternative better": int(b.sum()),
                    "no difference": int((~b & ~w).sum()), "alternative worse": int(w.sum()),
                    "passes": not bool(b.any())})
    return pd.DataFrame(out)


def across_models(t: pd.DataFrame) -> pd.DataFrame:
    """Every configuration without reasoning of every model on each dataset: the guide with each model against the
    best one (on the answers each pair graded, so levels are read per configuration)."""
    off = t[t.kind != "reasoning on"]
    out = []
    for lbl, g in off.groupby("set", sort=False):
        best = g.loc[g.QWK.idxmax()]
        for r in g[g.kind == "guide"].itertuples():
            out.append({"set": lbl, "model": r.model, "guide_QWK": r.QWK, "best_QWK": best.QWK,
                        "best": f"{best.model} {best.kind}", "shortfall": best.QWK - r.QWK})
    return pd.DataFrame(out)


def instructors() -> dict:
    """HARMOGEN-R: the four instructors' agreement with each other (QWK on the six levels, every pair) and their
    share of zero grades, on the 129 code answers used; a ceiling for the models' agreement with their mean."""
    import itertools
    import json
    from sklearn.metrics import cohen_kappa_score
    c = pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "corpus_verification.parquet")
    h = c[c.dataset == "harmogenr"]
    sc = pd.DataFrame([json.loads(m)["instructor_scores"] for m in h.source_meta]).div(h.gold_scale_max.to_numpy(), axis=0)
    lv = lambda x: phase5.to_levels(x, 5)
    pairs = [cohen_kappa_score(lv(sc[a]), lv(sc[b]), weights="quadratic", labels=list(range(6)))
             for a, b in itertools.combinations(sc.columns, 2)]
    return {"pairs_min": min(pairs), "pairs_max": max(pairs), "gold_zeros": float((h.gold_norm == 0).mean()),
            "N": len(h)}


def main() -> int:
    d = load()
    print("rows per dataset, model, configuration:")
    print(d.groupby(["dataset", "model", "kind"]).size().unstack(fill_value=0).to_string())
    print(f"unparsed: {int(d.parse_ok.eq(False).sum())} of {len(d)}; reasoning-on fallbacks: {int(d.fallback.sum())}")
    t = contrasts(d)
    pd.set_option("display.width", 220)
    print("\n=== alternative minus guide ===")
    print(t.round(3).to_string(index=False))
    print("\n=== pre-registered verdict (alternatives without reasoning) ===")
    print(verdict(t).to_string(index=False))
    ni = t[(t.kind != "guide") & (t.kind != "reasoning on")]
    print("\n=== non-inferiority at the margin fixed in advance (alternatives without reasoning) ===")
    print(ni.groupby("set", sort=False).noninferior.agg(["sum", "size"]).to_string())
    print("not shown non-inferior: " + "; ".join(f"{r.set.split(' (')[0]} {r.model} {r.kind} (upper 90% {r.hi90:+.3f})"
                                                  for r in ni[~ni.noninferior.astype(bool)].itertuples()))
    r = t[t.kind == "reasoning on"]
    print(f"\nreasoning on: better in {int(r.better.astype(bool).sum())}, worse in {int(r.worse.astype(bool).sum())} of {len(r)}; "
          f"cost x{r.cost_x.min():.1f} to x{r.cost_x.max():.1f}; less consistent in {int((r.SD > r.SD_guide).sum())}")
    print("\n=== the guide with each model against the best configuration without reasoning ===")
    print(across_models(t).round(3).to_string(index=False))
    ins = instructors()
    print(f"\nHARMOGEN-R instructors, every pair: QWK {ins['pairs_min']:.3f} to {ins['pairs_max']:.3f}; "
          f"zero grades (mean of four) {100 * ins['gold_zeros']:.0f}% of {ins['N']} answers")
    print("share of zero grades under the guide: " + ", ".join(
        f"{r.set.split(' (')[0]} {r.model} {100 * r.zeros:.0f}%" for r in t[t.kind == "guide"].itertuples()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
