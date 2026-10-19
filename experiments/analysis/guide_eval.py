"""The configuration guide and its tests (Section VI). Engine for the tests' figure, phase6.fig_guide_tests: panel
(a) is Test 1 and panel (b) Test 2 (the figure replaced the Test 1 and Test 2 figures on 2026-10-19, Pedro's fourth
review). "Validation" is kept for the two datasets that played no part in building the guide (verification.py).
Table 4, the guide itself, is written by make_phase5_tables.write_guide_table.

The guide is a configuration, not a model (Pedro's review 2026-10-16, second pass): the rubric or the reference
answer, an explicit request for partial credit, reasoning off, one question per call, one holistic score, and a
clean conversation per answer. It is tested with two tests on EVERY configuration the study graded:

  main store          guidance none / with, the whole exam in one call, a score per criterion, reasoning on/off;
  instruction store   partial credit (all five models; GLM-5.1 through OpenRouter on code only), partial credit
                      with a justification first (Qwen3.5, DeepSeek-V4-Flash, code), Claude Sonnet 4.6 strict;
  conversation store  one shared conversation per exam, in the exam's own order and in reverse.

  Test 1, within each model. The guide's configuration against every other configuration of the same model, on
          the answers both graded: paired bootstrap of the QWK difference (bloco_c._boot: SEED, 800 resamples),
          95% interval, NO correction for multiple comparisons (it makes an alternative's advantage easier to
          detect, so it is the stricter test of the guide). Cost per grade relative to the guide is computed from
          the tokens at one price per model (GLM-5.1 ran on two providers; both sides at the OpenRouter price),
          so it measures what the alternative itself adds. -> panel (a) of the tests' figure.
  Test 2, across models. Per answer set, every configuration without reasoning on the answers they all graded
          (Mohler: the 800 Claude Sonnet 4.6 graded; the conversation sub-study, which graded 104 of the PT-CS
          code answers, stays in Test 1): the guide with each model against the best configuration and the
          cost-quality frontier (configurations that no cheaper one beats), at each provider's own price. The
          reasoning samples give the same comparison with reasoning on. -> panel (b) of the tests' figure and the
          Section VI prose.

Run:  python -m experiments.analysis.guide_eval
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from experiments.analysis import phase5
from experiments.analysis.bloco_c import _boot, _summ
from experiments.analysis.make_phase5_tables import _qwk_items

SETS = [("mohler", "short_answer", "Mohler"), ("semeval", "short_answer", "SemEval"), ("riayn", "code", "RIAYN"),
        ("ptcs", "code", "PT-CS code"), ("ptcs", "short_answer", "PT-CS short")]
MODELS = ["deepseek-v4-flash", "glm-5.1", "gpt-5.1", "claude-sonnet-4-6", "qwen3.5"]
MNAME = {"qwen3.5": "Qwen3.5", "deepseek-v4-flash": "DeepSeek-V4-Flash", "glm-5.1": "GLM-5.1", "gpt-5.1": "GPT-5.1",
         "claude-sonnet-4-6": "Claude Sonnet 4.6", "glm-5.1-or": "GLM-5.1"}
FAMILY = {"glm-5.1-or": "glm-5.1"}                    # GLM-5.1 served by Z.ai through OpenRouter is the same model
PRICE_KEY = {"glm-5.1": "glm-5.1-or"}                 # Test 1 prices both GLM-5.1 sides at the guide's provider
GUIDE = {"reasoning": "off", "instruction": "partial_credit", "guid": "guid", "sc": "qbq", "dec": "hol", "conv": "clean"}
# One block per setting of the guide and the alternatives tested against it (kind keys from _kind). Table 4 (the
# guide) is written by make_phase5_tables.
TABLE = [("Evaluation guidance", "The rubric or the reference answer", [("no guidance", "None")]),
         ("Grading instruction", "Ask for partial credit", [("strict instruction", "Strict"),
                                                            ("justification", "Partial credit, with a justification first")]),
         ("Reasoning", "Off", [("reasoning on", "On")]),
         ("Scope", "One question per call", [("whole exam", "The whole exam in one call")]),
         ("Decomposition", "One holistic score", [("criterion scoring", "A score per criterion, summed")]),
         ("Conversation", "A clean conversation per answer", [("shared conversation", "One conversation per exam")])]
_INTERV = set(pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "_ptcs_strata.parquet")
              .query("stratum=='intervened'").item_id)


def _norm(d: pd.DataFrame, instruction: str | None = None) -> pd.DataFrame:
    d = d.copy()
    if instruction is not None:
        d["instruction"] = instruction
    d["guid"] = np.where(d.context_level == "with_guidance", "guid", "noguid")
    d["sc"] = np.where(d.scope == "whole_exam", "exam", "qbq")
    d["dec"] = np.where(d.decomposition == "criterion", "crit", "hol")
    d["conv"] = "clean"
    return d


def rows() -> pd.DataFrame:
    """Every graded configuration, PT-CS restricted to its teacher-validated answers."""
    main = _norm(phase5.load_main(), instruction="standard")
    ins = phase5.load_instruction()
    ins = ins[(ins.instruction != "standard") | (ins.model == "claude-sonnet-4-6")]   # the same-batch strict re-runs
    ins = ins[~((ins.model == "glm-5.1-or") & (ins.domain != "code"))]              # of Qwen/DeepSeek duplicate main
    ins = _norm(ins)                                                                 # cells; GLM via OpenRouter: code
    conv = phase5.load_conversation()
    conv = _norm(conv[conv.conversation_state == "shared"], instruction="standard")
    conv["conv"] = "shared-" + conv.order_id.astype(str)
    d = pd.concat([main, ins, conv], ignore_index=True)
    d = d[(d.dataset != "ptcs") | d.item_id.isin(_INTERV)]
    d["fallback"] = d["fallback"].fillna(False).astype(bool) if "fallback" in d else False
    d["fam"] = d.model.replace(FAMILY)
    d["cfg"] = (d.model + "|" + d.reasoning + "|" + d.instruction + "|" + d.guid + "|" + d.sc + "|" + d.dec
                + "|" + d.conv)
    return d


def _is_guide(d: pd.DataFrame) -> pd.Series:
    m = pd.Series(True, index=d.index)
    for k, v in GUIDE.items():
        m &= d[k] == v
    return m


def _kind(r) -> str:
    if r.reasoning == "on":
        return "reasoning on"
    if r.guid == "noguid":
        return "no guidance"
    if r.sc == "exam":
        return "whole exam"
    if r.dec == "crit":
        return "criterion scoring"
    if r.conv.startswith("shared"):
        return "shared conversation"
    if r.instruction == "partial_credit_justified":
        return "justification"
    if r.instruction == "standard":
        return "strict instruction"
    return "other"


def _per_grade(g: pd.DataFrame, price: dict | None = None) -> float:
    """Euros per grade: whole-exam calls counted once (phase5.dedupe_call_groups); with `price`, re-priced from the
    tokens at that model's rate, else at each row's own provider rate (phase5's cost_eur)."""
    n = len(g)
    c = phase5.apportion_whole_exam(g)        # a whole-exam call's cost split over its questions (2026-10-19)
    if price is None:
        return float(pd.to_numeric(c.cost_eur, errors="coerce").sum()) / n
    tin = pd.to_numeric(c.prompt_tokens, errors="coerce").fillna(0)
    tout = pd.to_numeric(c.completion_tokens, errors="coerce").fillna(0)
    return float((tin * price["in"] + tout * price["out"]).sum()) / 1e6 * price["eur"] / n


def _prices() -> dict:
    from experiments.harness.cost_guard import load_pricing
    pr = load_pricing()
    eur = float(pr.get("eur_per_usd", 0.92))
    return {m: {"in": float(v["input_per_1m_usd"]), "out": float(v["output_per_1m_usd"]), "eur": eur}
            for m, v in pr["models"].items() if "input_per_1m_usd" in v}


def _sd(g: pd.DataFrame) -> float:
    own = g[~g.fallback]
    return float(own.groupby("item_id").pred_norm.std().mean())


def within_model(d: pd.DataFrame) -> pd.DataFrame:
    """Test 1: per model and answer set, the guide's configuration against each other configuration of the model."""
    prices = _prices()
    out = []
    for fam in MODELS:
        price = prices[PRICE_KEY.get(fam, fam)]
        for ds, dom, lbl in SETS:
            s = d[(d.fam == fam) & (d.dataset == ds) & (d.domain == dom)]
            G = s[_is_guide(s)]
            if G.empty:
                continue
            _, sG = _qwk_items(G)
            for c in sorted(set(s.cfg) - set(G.cfg)):
                A = s[s.cfg == c]
                _, sA = _qwk_items(A)
                items = set(sA.index) & set(sG.index)
                r = _summ(c, _boot(sG, sA), len(items))                        # dQWK = alternative - guide
                Ai, Gi = A[A.item_id.isin(items)], G[G.item_id.isin(items)]
                r.update({"model": fam, "set": lbl, "kind": _kind(A.iloc[0]),
                          "cost_x": _per_grade(Ai, price) / _per_grade(Gi, price),
                          "sd_alt": _sd(Ai), "sd_guide": _sd(Gi)})
                out.append(r)
    t = pd.DataFrame(out)
    t["better"] = t.ci95.map(lambda c: c[0] > 0)
    t["worse"] = t.ci95.map(lambda c: c[1] < 0)
    return t


def departures(t: pd.DataFrame) -> pd.DataFrame:
    """Test 1 rows: per alternative, the counts of significantly better / no difference / significantly worse."""
    rows_ = []
    for setting, guide, alts in TABLE:
        for kind, label in alts:
            g = t[t.kind == kind]
            rows_.append({"setting": setting, "guide": guide, "alternative": label, "kind": kind, "n": len(g),
                          "better": int(g.better.sum()), "worse": int(g.worse.sum()),
                          "same": int((~g.better & ~g.worse).sum()), "d_lo": g.dQWK.min(), "d_hi": g.dQWK.max(),
                          "x_lo": g.cost_x.min(), "x_hi": g.cost_x.max(),
                          "less_consistent": int((g.sd_alt > g.sd_guide + 1e-12).sum())})
    return pd.DataFrame(rows_)


def field(d: pd.DataFrame, basis: str = "B") -> pd.DataFrame:
    """Test 2 points. Basis B: every configuration without reasoning, on the answers they all graded. Basis A: every
    configuration, reasoning on included, on the sampled answers they all graded."""
    pts = []
    for ds, dom, lbl in SETS:
        s = d[(d.dataset == ds) & (d.domain == dom) & (d.conv == "clean")]
        cfgs = sorted(set(s.cfg))
        if basis == "B":
            cfgs = [c for c in cfgs if c.split("|")[1] == "off"]
        items = set.intersection(*[set(s[s.cfg == c].item_id) for c in cfgs])
        for c in cfgs:
            g = s[(s.cfg == c) & s.item_id.isin(items)]
            q, si = _qwk_items(g)
            pts.append({"set": lbl, "cfg": c, "model": g.model.iloc[0], "fam": g.fam.iloc[0],
                        "guide": bool(_is_guide(g).all()), "QWK": q, "N": len(si), "eur_1000": 1000 * _per_grade(g)})
    f = pd.DataFrame(pts)
    f["frontier"] = False
    for lbl, g in f.groupby("set"):
        best = -np.inf
        for i, r in g.sort_values(["eur_1000", "QWK"], ascending=[True, False]).iterrows():
            if r.QWK > best + 1e-12:
                f.loc[i, "frontier"], best = True, r.QWK
    return f


def field_summary(f: pd.DataFrame) -> pd.DataFrame:
    """Per answer set: the best configuration, the guide's best model and its gap, the guide with the cheapest model
    and every configuration that agreed better at no higher cost."""
    rows_ = []
    for lbl, g in f.groupby("set", sort=False):
        best = g.loc[g.QWK.idxmax()]
        gg = g[g.guide]
        gb = gg.loc[gg.QWK.idxmax()]
        gc = gg.loc[gg.eur_1000.idxmin()]
        beats = g[(g.QWK > gc.QWK + 1e-12) & (g.eur_1000 <= gc.eur_1000)]
        code = [q for q in gg[gg.fam != "qwen3.5"].QWK] if lbl in ("RIAYN", "PT-CS code") else []
        rows_.append({"set": lbl, "N": int(best.N), "configs": len(g), "best": best.cfg, "best_QWK": best.QWK,
                      "best_eur": best.eur_1000, "guide_best_model": gb.fam, "guide_best_QWK": gb.QWK,
                      "gap": best.QWK - gb.QWK, "guide_cheap_model": gc.fam, "guide_cheap_QWK": gc.QWK,
                      "guide_cheap_eur": gc.eur_1000, "cheap_on_frontier": bool(gc.frontier),
                      "cheaper_and_better": "; ".join(f"{r.cfg} {r.QWK:.3f}" for r in beats.itertuples()),
                      "margin_of_cheaper": float((beats.QWK - gc.QWK).max()) if len(beats) else 0.0,
                      "guide_code_others": (min(code), max(code)) if code else None})
    return pd.DataFrame(rows_)


def fixed_model(f: pd.DataFrame) -> pd.DataFrame:
    """Test 2 with the model fixed in advance (independent review, 2026-10-18): for each model, the guide's shortfall
    from the best configuration of each answer set, averaged and at its worst across the sets the model graded."""
    best = f.groupby("set").QWK.max()
    g = f[f.guide].copy()
    g["gap"] = g.apply(lambda r: best[r.set] - r.QWK, axis=1)
    return (g.groupby("fam").gap.agg(mean="mean", worst="max", sets="size").sort_values("mean"))


def _fmt_x(lo: float, hi: float) -> str:
    f = lambda v: f"{v:.0f}" if v >= 10 else f"{v:.1f}"
    return f"{f(lo)}$\\times$" if f(lo) == f(hi) else f"{f(lo)}--{f(hi)}$\\times$"


def _fmt_d(lo: float, hi: float) -> str:
    f = lambda v: f"${v:+.2f}$"
    return f(lo) if f"{lo:+.2f}" == f"{hi:+.2f}" else f"{f(lo)} to {f(hi)}"


def main() -> int:
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 400)
    d = rows()
    t = within_model(d)
    print("=== Test 1, within each model: alternative minus the guide (95% bootstrap CI, no correction) ===")
    print(t[["model", "set", "contrast", "N", "dQWK", "ci95", "better", "worse", "cost_x", "sd_alt", "sd_guide"]]
          .round(3).to_string(index=False))
    dep = departures(t)
    print("\n=== Test 1 per alternative ===\n" + dep.round(3).to_string(index=False))
    off = dep[dep.kind != "reasoning on"]
    print(f"\nwithout reasoning: {int(off.n.sum())} comparisons, better {int(off.better.sum())}, no difference "
          f"{int(off.same.sum())}, worse {int(off.worse.sum())}; less consistent than the guide in "
          f"{int(dep.less_consistent.sum())} of {int(dep.n.sum())} comparisons (all alternatives)")
    print(t[t.better][["model", "set", "contrast", "N", "dQWK", "ci95", "cost_x"]].round(3).to_string(index=False))
    for b in ["B", "A"]:
        f = field(d, b)
        print(f"\n=== Test 2, basis {b}: every configuration {'without reasoning, all answers' if b == 'B' else 'incl. reasoning on, sampled answers'} ===")
        print(f.sort_values(["set", "QWK"], ascending=[True, False]).round(3).to_string(index=False))
        print(field_summary(f).round(3).to_string(index=False))
        print("  guide with the model fixed in advance, shortfall from the best configuration per set:\n"
              + fixed_model(f).round(3).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
