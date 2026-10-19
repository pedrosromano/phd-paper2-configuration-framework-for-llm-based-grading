"""Bloco C analyses (advisor review, user-approved 2026-10-15). No API calls; re-run after the C arms.

  C7  human ceiling on Mohler: the two graders against each other, and each model against each grader
  C8  SemEval cut-off sensitivity: accuracy across label thresholds (the paper fixes 0.5 in advance)
  C9  statistics: Holm-adjusted significance for the RQ1/RQ2/RQ3 contrasts, and TOST equivalence at the
      PRE-REGISTERED margin of +/-0.05 QWK (CLAUDE.md S11, fixed before any C-arm data was run)
  C10 regret of the configuration guide: per dataset, the agreement lost and the cost saved by
      following the guide's default instead of the best configuration in hindsight

Same engine and conventions as the paper tables (make_phase5_tables: K=5, _qwk_items, SEED bootstrap,
PT-CS = the teacher-validated answers). Run:

  python -m experiments.analysis.bloco_c            # all
  python -m experiments.analysis.bloco_c c9         # one
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, cohen_kappa_score, roc_auc_score

from experiments.analysis import phase5
from experiments.analysis.make_phase5_tables import K, NB, SEED, _boot_dist, _point, _qwk_items

MARGIN = 0.05            # pre-registered equivalence margin (QWK), user 2026-10-15
INTERV = set(pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "_ptcs_strata.parquet")
             .query("stratum=='intervened'").item_id)
MODELS = ["qwen3.5", "glm-5.1", "deepseek-v4-flash", "gpt-5.1"]


def _paper(df: pd.DataFrame) -> pd.DataFrame:
    """The paper's analysis basis: PT-CS restricted to its teacher-validated answers."""
    return df[(df.dataset != "ptcs") | df.item_id.isin(INTERV)]


def _bins(x):
    return (np.asarray(x) * K).round().clip(0, K).astype(int)


def _qwk(p, g):
    return cohen_kappa_score(_bins(g), _bins(p), weights="quadratic", labels=list(range(K + 1)))


def _boot(sA: pd.DataFrame, sB: pd.DataFrame) -> tuple[np.ndarray, float] | None:
    """(bootstrap distribution, point estimate) of dQWK = QWK(B) - QWK(A) over common items: the paper's own
    procedure (make_phase5_tables._boot_dist and _point, same seed and number of resamples)."""
    ds = _boot_dist(sA, sB, NB)
    return None if ds is None else (ds, _point(sA, sB))


def _summ(name: str, bp: tuple[np.ndarray, float] | None, n: int) -> dict:
    if bp is None:
        return {"contrast": name, "N": n}
    ds, point = bp
    lo95, hi95 = np.percentile(ds, [2.5, 97.5])
    lo90, hi90 = np.percentile(ds, [5, 95])
    p = max(2 * min((ds <= 0).mean(), (ds >= 0).mean()), 1 / len(ds))  # two-sided bootstrap p
    return {"contrast": name, "N": n, "dQWK": round(point, 3), "ci95": (round(lo95, 3), round(hi95, 3)),
            "sig95": bool(lo95 > 0 or hi95 < 0), "p_boot": round(p, 4),
            "ci90": (round(lo90, 3), round(hi90, 3)),
            "equivalent": bool(-MARGIN < lo90 and hi90 < MARGIN)}         # TOST at alpha=0.05


def _holm(rows: list[dict]) -> list[dict]:
    ps = [(i, r["p_boot"]) for i, r in enumerate(rows) if "p_boot" in r]
    m = len(ps)
    adj, running = {}, 0.0
    for rank, (i, p) in enumerate(sorted(ps, key=lambda t: t[1])):
        running = max(running, min(1.0, (m - rank) * p))
        adj[i] = running
    for i, r in enumerate(rows):
        if i in adj:
            r["p_holm"] = round(adj[i], 4)
            r["sig_holm"] = bool(adj[i] < 0.05)
    return rows


# --------------------------------------------------------------------------- C7
def c7(df: pd.DataFrame) -> pd.DataFrame:
    """Mohler: grader-vs-grader QWK, and each config's item-mean score against the mean of the two
    graders (the paper's gold) and against each grader alone (the like-for-like ceiling comparison)."""
    corpus = pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "corpus.parquet")
    mo = corpus[corpus.dataset == "mohler"].set_index("item_id")
    meta = mo.source_meta.map(json.loads)
    ga = meta.map(lambda x: x["score_me"]) / 5
    gb = meta.map(lambda x: x["score_other"]) / 5
    rows = [{"config": "human: grader A vs grader B", "vs_mean": np.nan, "vs_A": np.nan,
             "vs_B": round(_qwk(ga.to_numpy(), gb.to_numpy()), 3), "N": len(mo)}]
    base = df[(df.dataset == "mohler") & (df.context_level == "with_guidance")
              & (df.scope == "question_by_question") & (df.decomposition == "holistic")]
    for (m, r), g in base.groupby(["model", "reasoning"]):
        q, s = _qwk_items(g)
        ids = s.index.intersection(ga.index)
        rows.append({"config": f"{m}|{r}", "vs_mean": round(q, 3),
                     "vs_A": round(_qwk(s.p.loc[ids], ga.loc[ids]), 3),
                     "vs_B": round(_qwk(s.p.loc[ids], gb.loc[ids]), 3), "N": len(ids)})
    out = pd.DataFrame(rows)
    print("\n=== C7 Mohler human ceiling (QWK, K=5) ===\n" + out.to_string(index=False))
    return out


# --------------------------------------------------------------------------- C8
def c8(df: pd.DataFrame) -> pd.DataFrame:
    """SemEval, reasoning off, with guidance: accuracy at label cut-offs 0.30..0.70 per model; the
    paper fixes 0.5 in advance. AUROC is threshold-free and printed alongside."""
    se = df[(df.dataset == "semeval") & (df.context_level == "with_guidance") & (df.reasoning == "off")
            & df.pred_norm.notna()].copy()
    se["gold"] = (pd.to_numeric(se.gold_score, errors="coerce") >= 0.5).astype(int)
    ths = np.round(np.arange(0.30, 0.701, 0.05), 2)
    rows = []
    for m, g in se.groupby("model"):
        r = {"model": m, "AUROC": round(roc_auc_score(g.gold, g.pred_norm), 3)}
        accs = {t: accuracy_score(g.gold, (g.pred_norm >= t).astype(int)) for t in ths}
        r.update({f"{t:.2f}": round(a, 3) for t, a in accs.items()})
        best = max(accs, key=accs.get)
        r["best_cut"], r["acc_at_0.5_minus_best"] = best, round(accs[0.5] - accs[best], 3)
        rows.append(r)
    out = pd.DataFrame(rows)
    print("\n=== C8 SemEval accuracy by cut-off (reasoning off, with guidance) ===\n" + out.to_string(index=False))
    return out


# --------------------------------------------------------------------------- C9
def c9(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Holm across each family of contrasts, and TOST at +/-MARGIN for every contrast."""
    d = _paper(df)
    fams: dict[str, list[dict]] = {"RQ1 reasoning": [], "RQ2 guidance": [], "RQ3 scope/decomposition": []}
    rp = phase5.reasoning_paired(d)
    base = rp[(rp.context_level == "with_guidance") & (rp.scope == "question_by_question")
              & (rp.decomposition == "holistic")]
    for (ds, dom, m), g in base.groupby(["dataset", "domain", "model"]):
        o, n = g[g.reasoning == "off"], g[g.reasoning == "on"]
        if o.empty or n.empty:
            continue
        clean = set(n.item_id.unique())          # every paired item (fallback rule, phase5.apply_reasoning_fallback)
        _, sA = _qwk_items(o[o.item_id.isin(clean)]); _, sB = _qwk_items(n[n.item_id.isin(clean)])
        fams["RQ1 reasoning"].append(_summ(f"{ds}:{dom[:5]} {m}", _boot(sA, sB), len(clean)))
    q = d[(d.reasoning == "off") & (d.scope == "question_by_question") & (d.decomposition == "holistic")]
    for m in MODELS:
        for ds, dom in [("mohler", "short_answer"), ("semeval", "short_answer"), ("riayn", "code"), ("ptcs", "code"), ("ptcs", "short_answer")]:
            c = q[(q.model == m) & (q.dataset == ds) & (q.domain == dom)]
            A, B = c[c.context_level == "none"], c[c.context_level == "with_guidance"]
            if A.empty or B.empty:
                continue
            _, sA = _qwk_items(A); _, sB = _qwk_items(B)
            fams["RQ2 guidance"].append(_summ(f"{ds}:{dom[:5]} {m}", _boot(sA, sB), len(set(sA.index) & set(sB.index))))
    we = d[d.scope == "whole_exam"]
    for m in MODELS:
        w = we[we.model == m]
        if not w.empty:
            qb = d[(d.model == m) & (d.reasoning == "off") & (d.dataset == "ptcs") & (d.domain == "code")
                   & (d.context_level == "with_guidance") & (d.scope == "question_by_question")
                   & (d.decomposition == "holistic") & d.item_id.isin(set(w.item_id))]
            _, sA = _qwk_items(qb); _, sB = _qwk_items(w)
            fams["RQ3 scope/decomposition"].append(_summ(f"scope ptcs {m}", _boot(sA, sB), len(set(sA.index) & set(sB.index))))
        for ds in ["ptcs", "riayn"]:
            dd = d[(d.model == m) & (d.reasoning == "off") & (d.dataset == ds) & (d.domain == "code")
                   & (d.context_level == "with_guidance") & (d.scope == "question_by_question")]
            A, B = dd[dd.decomposition == "holistic"], dd[dd.decomposition == "criterion"]
            if A.empty or B.empty:
                continue
            _, sA = _qwk_items(A); _, sB = _qwk_items(B)
            fams["RQ3 scope/decomposition"].append(_summ(f"decomp {ds} {m}", _boot(sA, sB), len(set(sA.index) & set(sB.index))))
    out = {}
    for name, rows in fams.items():
        t = pd.DataFrame(_holm(rows))
        out[name] = t
        print(f"\n=== C9 {name}: bootstrap p, Holm, TOST at +/-{MARGIN} ===\n" + t.to_string(index=False))
    return out


# --------------------------------------------------------------------------- C10
# D13 (user 2026-10-15): the guide's default is reasoning off with the strongest model that does not
# collapse to zeros (GLM-5.1 here), on both tasks; "cheapest" = the cheapest model with reasoning off on
# that dataset, shown as the budget alternative.
GUIDE = {"short_answer": ["glm-5.1", "cheapest"], "code": ["glm-5.1", "cheapest"]}


def c10(df: pd.DataFrame) -> pd.DataFrame:
    """Per dataset, among the graded configurations (model x reasoning; with guidance, one question per
    call, holistic): the best in hindsight vs each pick in GUIDE, always with reasoning off ("cheapest" is
    resolved per dataset to the cheapest model with reasoning off). Regret = QWK lost; cost ratio = how many
    times cheaper the pick is than the best configuration. Only configurations graded on at least 90% of
    the largest reasoning-on sample compete, all scored on the items they share."""
    d = _paper(df)
    d = d[(d.context_level == "with_guidance") & (d.scope == "question_by_question") & (d.decomposition == "holistic")]
    cost = phase5.dedupe_call_groups(d).assign(ce=lambda x: pd.to_numeric(x.cost_eur, errors="coerce"))
    rows = []
    for (ds, dom), g in d.groupby(["dataset", "domain"]):
        # every competing configuration is scored on the SAME items: those graded by all configurations
        # that cover at least 90% of the largest reasoning-on sample (so a 60-item subset cannot compete)
        ok = g[g.pred_norm.notna()]
        n_by = ok.groupby(["model", "reasoning"]).item_id.nunique()
        n_on = n_by.xs("on", level="reasoning").max() if "on" in n_by.index.get_level_values(1) else n_by.max()
        keep = [ix for ix, n in n_by.items() if n >= 0.9 * n_on]
        common = set.intersection(*[set(ok[(ok.model == m) & (ok.reasoning == r)].item_id) for m, r in keep])
        cfg = []
        for m, r in keep:
            h = g[(g.model == m) & (g.reasoning == r) & g.item_id.isin(common)]
            q, s = _qwk_items(h)
            eur = cost[(cost.dataset == ds) & (cost.domain == dom) & (cost.model == m) & (cost.reasoning == r)].ce.mean() * 1000
            cfg.append({"m": m, "r": r, "qwk": q, "n": len(s), "eur": eur})
        cf = pd.DataFrame(cfg)
        best = cf.sort_values("qwk", ascending=False).iloc[0]
        for role in GUIDE[dom]:
            pick = cf[cf.r == "off"].sort_values("eur").iloc[0].m if role == "cheapest" else role
            gp = cf[(cf.m == pick) & (cf.r == "off")].iloc[0]
            rows.append({"dataset": f"{ds}:{dom[:5]}", "role": role, "N_common": int(best.n), "best": f"{best.m}|{best.r}", "best_qwk": round(best.qwk, 3),
                         "guide": f"{pick}|off", "guide_qwk": round(gp.qwk, 3), "regret": round(best.qwk - gp.qwk, 3),
                         "best_eur/1000": round(best.eur, 3), "guide_eur/1000": round(gp.eur, 3),
                         "cheaper_x": round(best.eur / gp.eur, 1) if gp.eur else np.nan})
    out = pd.DataFrame(rows)
    print("\n=== C10 regret of the guide's default vs the best configuration in hindsight ===\n" + out.to_string(index=False))
    return out


def regret_all(df: pd.DataFrame) -> pd.DataFrame:
    """Every configuration's regret per dataset (same items and rule as c10), for the guide's budget ladder
    (2026-10-16): worst-case and mean shortfall from the best configuration, and cost per 1000 grades."""
    d = _paper(df)
    d = d[(d.context_level == "with_guidance") & (d.scope == "question_by_question") & (d.decomposition == "holistic")]
    cost = phase5.dedupe_call_groups(d).assign(ce=lambda x: pd.to_numeric(x.cost_eur, errors="coerce"))
    rows = []
    for (ds, dom), g in d.groupby(["dataset", "domain"]):
        ok = g[g.pred_norm.notna()]
        n_by = ok.groupby(["model", "reasoning"]).item_id.nunique()
        n_on = n_by.xs("on", level="reasoning").max()
        keep = [ix for ix, n in n_by.items() if n >= 0.9 * n_on]
        common = set.intersection(*[set(ok[(ok.model == m) & (ok.reasoning == r)].item_id) for m, r in keep])
        for m, r in keep:
            q, _ = _qwk_items(g[(g.model == m) & (g.reasoning == r) & g.item_id.isin(common)])
            e = cost[(cost.dataset == ds) & (cost.domain == dom) & (cost.model == m) & (cost.reasoning == r)].ce.mean() * 1000
            rows.append({"set": f"{ds}:{dom[:5]}", "model": m, "reasoning": r, "qwk": q, "eur": e})
    t = pd.DataFrame(rows)
    t["regret"] = t.groupby("set").qwk.transform("max") - t.qwk
    return t


# --------------------------------------------------------------------------- per-step conclusions
# Short, factual read-outs computed from the run data the moment each C step finishes; the launcher
# (experiments/run/bloco_c_run.py) stores them for the live monitor. Written in Portuguese for the
# author. They are a first read, not paper text.
NAMES = {"qwen3.5": "Qwen3.5", "glm-5.1": "GLM-5.1", "deepseek-v4-flash": "DeepSeek", "gpt-5.1": "GPT-5.1"}
DSN = {"mohler": "Mohler", "semeval": "SemEval", "riayn": "RIAYN", "ptcs": "PT-CS"}


def _contrast(A: pd.DataFrame, B: pd.DataFrame) -> dict | None:
    _, sA = _qwk_items(A); _, sB = _qwk_items(B)
    if isinstance(sA, float) or isinstance(sB, float):
        return None
    ds = _boot(sA, sB)
    return _summ("", ds, len(set(sA.index) & set(sB.index))) if ds is not None else None


def _fmt(r: dict | None) -> str:
    if not r or "dQWK" not in r:
        return "sem dados suficientes"
    lo, hi = r["ci95"]
    sig = "significativo" if r["sig95"] else "não significativo"
    eq = "; equivalente a zero (±0.05)" if r["equivalent"] else ""
    return f"ΔQWK {r['dQWK']:+.3f} [{lo:+.2f}, {hi:+.2f}], N={r['N']}, {sig}{eq}"


def conclude_c1(df: pd.DataFrame) -> list[str]:
    d = _paper(df)
    q = d[(d.reasoning == "off") & (d.scope == "question_by_question") & (d.decomposition == "holistic")]
    out = []
    for ds, dom in [("mohler", "short_answer"), ("semeval", "short_answer"), ("riayn", "code"), ("ptcs", "code")]:
        parts = []
        for m in ["qwen3.5", "deepseek-v4-flash", "gpt-5.1"]:
            c = q[(q.model == m) & (q.dataset == ds) & (q.domain == dom)]
            r = _contrast(c[c.context_level == "none"], c[c.context_level == "with_guidance"])
            parts.append(f"{NAMES[m]} {r['dQWK']:+.3f}{'*' if r and r.get('sig95') else ''}" if r and "dQWK" in r else f"{NAMES[m]} –")
        out.append(f"{DSN[ds]}: guidance {' · '.join(parts)}")
    out.append("* = significativo (IC 95% exclui zero). Ganho de QWK ao acrescentar rubrica/resposta de referência.")
    return out


def conclude_c2(df: pd.DataFrame) -> list[str]:
    d = _paper(df)
    out = []
    for ds in ["riayn", "ptcs"]:
        for m in ["qwen3.5", "deepseek-v4-flash"]:
            dd = d[(d.model == m) & (d.reasoning == "off") & (d.dataset == ds) & (d.domain == "code")
                   & (d.context_level == "with_guidance") & (d.scope == "question_by_question")]
            r = _contrast(dd[dd.decomposition == "holistic"], dd[dd.decomposition == "criterion"])
            out.append(f"{DSN[ds]} {NAMES[m]}: critério a critério vs holístico, {_fmt(r)}")
    return out


def conclude_c3(df: pd.DataFrame) -> list[str]:
    d = _paper(df)
    out = []
    for m in ["qwen3.5", "deepseek-v4-flash"]:
        w = d[(d.scope == "whole_exam") & (d.model == m)]
        if w.empty:
            continue
        qb = d[(d.model == m) & (d.reasoning == "off") & (d.dataset == "ptcs") & (d.domain == "code")
               & (d.context_level == "with_guidance") & (d.scope == "question_by_question")
               & (d.decomposition == "holistic") & d.item_id.isin(set(w.item_id))]
        out.append(f"{NAMES[m]}: exame inteiro vs pergunta a pergunta, {_fmt(_contrast(qb, w))}")
    return out


def conclude_c4() -> list[str]:
    cv = phase5.load_conversation()
    st = phase5.conversation_stats(cv)
    n_ex = cv.submission_id.nunique() if "submission_id" in cv else None
    out = [f"{n_ex} exames, k={cv.run_index.nunique()}"]
    for m, r in st.items():
        out.append(f"{NAMES.get(m, m)}: conversa partilhada baixa a nota em {r.get('state_delta', float('nan')):+.3f} "
                   f"(Wilcoxon p={r.get('state_p', float('nan')):.4f}); ordem inversa muda a nota em média "
                   f"{r.get('order_abs', float('nan')):.3f} (p sinal={r.get('order_p', float('nan')):.3f})")
    return out


def conclude_c5_off(df: pd.DataFrame) -> list[str]:
    d = _paper(df)
    d = d[(d.reasoning == "off") & (d.context_level == "with_guidance") & (d.scope == "question_by_question")
          & (d.decomposition == "holistic")]
    out = []
    for (ds, dom), g in d.groupby(["dataset", "domain"]):
        qs = {m: _qwk_items(h)[0] for m, h in g.groupby("model")}
        rank = sorted(qs, key=qs.get, reverse=True)
        out.append(f"{DSN[ds]} {dom[:5]}: GPT-5.1 {qs.get('gpt-5.1', float('nan')):.3f}, posição {rank.index('gpt-5.1') + 1}/4 "
                   f"(melhor: {NAMES[rank[0]]} {qs[rank[0]]:.3f})")
    return out


def conclude_c5_on(df: pd.DataFrame) -> list[str]:
    d = _paper(df)
    rp = phase5.reasoning_paired(d[d.model == "gpt-5.1"])
    base = rp[(rp.context_level == "with_guidance") & (rp.scope == "question_by_question") & (rp.decomposition == "holistic")]
    out = []
    for (ds, dom), g in base.groupby(["dataset", "domain"]):
        o, n = g[g.reasoning == "off"], g[g.reasoning == "on"]
        clean = set(n.item_id.unique())          # every paired item (fallback rule, phase5.apply_reasoning_fallback)
        r = _contrast(o[o.item_id.isin(clean)], n[n.item_id.isin(clean)])
        prem = pd.to_numeric(n.completion_tokens, errors="coerce").mean() / max(pd.to_numeric(o.completion_tokens, errors="coerce").mean(), 1)
        out.append(f"{DSN[ds]} {dom[:5]}: reasoning no GPT-5.1, {_fmt(r)}; {prem:.0f}× tokens")
    return out


CONCLUDE = {"c1": conclude_c1, "c2": conclude_c2, "c3": conclude_c3, "c4": lambda df: conclude_c4(),
            "c5_off": conclude_c5_off, "c5_on": conclude_c5_on}


def main(argv: list[str]) -> int:
    df = phase5.load_main()
    which = argv or ["c7", "c8", "c9", "c10"]
    for w in which:
        {"c7": c7, "c8": c8, "c9": c9, "c10": c10}[w](df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
