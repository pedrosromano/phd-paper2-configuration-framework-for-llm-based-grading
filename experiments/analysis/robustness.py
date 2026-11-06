"""Robustness checks asked for by the second independent review (2026-10-19), in the supplementary material and one
sentence each in the paper's Threats:

  1. Resampling whole questions instead of answers (a cluster bootstrap): answers to the same question may be alike,
     so the paper's intervals, which resample answers, may be too narrow. Every engine's bootstrap is swapped for one
     that resamples the questions of the common answers with replacement (same seed and number of resamples) and
     the RQ1, guidance, scope, decomposition and Test 1 counts are recomputed. HARMOGEN-R has only three questions,
     so the validation is not recomputed this way (three clusters give no usable interval).
  2. QWK on single runs instead of on the mean of the k grades: the guide makes one call per answer. For Test 1 and
     the validation, the guide and each alternative are scored run by run (run r against run r) and the differences
     averaged over the runs.

  3. Reasoning runs that fell back (third independent review, 2026-10-19): the RQ1 contrast with the runs that
     reached the output limit left out, instead of carrying the same model's reasoning-off grade.
  4. Discretisation of the agreement measure: RQ1 significance with halves rounded up instead of to the even
     level, and with five or seven levels instead of six.

  python -m experiments.analysis.robustness
"""

from __future__ import annotations

from contextlib import contextmanager

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from experiments.analysis import bloco_c, guide_eval, make_phase5_tables as mpt, phase5, verification

K = mpt.K
L2 = (K + 1) ** 2


def _clusters() -> dict:
    cols = ["item_id", "question_id"]
    c = pd.concat([pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / f)[cols]
                   for f in ("corpus.parquet", "corpus_verification.parquet")])
    return dict(zip(c.item_id, c.question_id.astype(str)))


def _cluster_boot_factory(cl: dict):
    def boot(sA, sB, nb=mpt.NB):
        """Bootstrap distribution of dQWK = QWK(B) - QWK(A), resampling the questions of the common answers."""
        items, ca, cb = mpt._common(sA, sB)
        if len(items) < 8:
            return None
        q = pd.Series([cl[i] for i in items]).to_numpy()
        groups = [np.flatnonzero(q == u) for u in pd.unique(q)]
        rng = np.random.default_rng(mpt.SEED)
        out = np.empty(nb)
        for b in range(nb):
            idx = np.concatenate([groups[j] for j in rng.integers(0, len(groups), len(groups))])
            cnt = np.stack([np.bincount(ca[idx], minlength=L2), np.bincount(cb[idx], minlength=L2)])
            qa, qb = mpt._kappas(cnt.reshape(2, K + 1, K + 1).astype(float))
            out[b] = qb - qa
        return out
    return boot


@contextmanager
def by_question():
    """Swap the answer bootstrap for the question bootstrap in every engine that uses it, then restore it."""
    mods = (mpt, bloco_c, verification)
    old = [m._boot_dist for m in mods]
    new = _cluster_boot_factory(_clusters())
    for m in mods:
        m._boot_dist = new
    try:
        yield
    finally:
        for m, f in zip(mods, old):
            m._boot_dist = f


def _counts(df, interv) -> pd.DataFrame:
    rows = []
    r1 = mpt.rq1_cells(df, interv)
    rows.append({"result": "Reasoning on (RQ1), significant gains", "of": len(r1), "sig": int((r1.lo > 0).sum()),
                 "holm": int((r1.sig_holm & (r1.dQWK > 0)).sum())})
    dc = mpt.dim_contrasts(df, interv)
    for fam, lbl in [("guidance", "Evaluation guidance (RQ2), significant gains"),
                     ("scope", "Whole exam (RQ3), significant losses"),
                     ("decomp", "Criterion scoring (RQ3), significant changes")]:
        g = dc[dc.family == fam]
        sig = g.sig if fam == "decomp" else ((g.lo > 0) if fam == "guidance" else (g.hi < 0))
        rows.append({"result": lbl, "of": len(g), "sig": int(sig.sum()), "holm": int((g.sig_holm & sig).sum())})
    t = guide_eval.within_model(guide_eval.rows())
    off = t[t.kind != "reasoning on"]
    rows.append({"result": "Every other configuration of the same model, guide significantly better", "of": len(off), "sig": int(off.worse.sum()), "holm": None})
    rows.append({"result": "Every other configuration of the same model, alternative significantly better", "of": len(off), "sig": int(off.better.sum()),
                 "holm": None})
    # the paper's comparison of the guide since 2026-11-06: against the baseline and against reasoning on (tests)
    for kind, ref in [("strict instruction", "the baseline"), ("reasoning on", "reasoning on")]:
        g = t[t.kind == kind]
        rows.append({"result": f"The guide against {ref}, guide significantly better", "of": len(g),
                     "sig": int(g.worse.sum()), "holm": None})
        rows.append({"result": f"The guide against {ref}, {ref} significantly better", "of": len(g),
                     "sig": int(g.better.sum()), "holm": None})
    return pd.DataFrame(rows)


def cluster_table() -> pd.DataFrame:
    """The paper's counts with answers resampled (as published) and with questions resampled."""
    df = phase5.load_main()
    interv = guide_eval._INTERV
    a = _counts(df, interv)
    with by_question():
        b = _counts(df, interv)
    return a.merge(b, on=["result", "of"], suffixes=("_answers", "_questions"))


def _qwk_run(g: pd.DataFrame) -> float:
    g = g[g.pred_norm.notna() & g.gold_norm.notna()]
    return cohen_kappa_score(mpt._levels(g.gold_norm), mpt._levels(g.pred_norm), weights="quadratic",
                             labels=list(range(K + 1)))


def _single(G: pd.DataFrame, A: pd.DataFrame) -> tuple[float, float] | None:
    """(guide's single-run QWK, alternative minus guide), each averaged over the runs both have, on common answers."""
    items = set(G.item_id) & set(A.item_id)
    runs = sorted(set(G.run_index) & set(A.run_index))
    if len(items) < 8 or not runs:
        return None
    pr = np.array([(_qwk_run(G[(G.run_index == r) & G.item_id.isin(items)]),
                    _qwk_run(A[(A.run_index == r) & A.item_id.isin(items)])) for r in runs])
    return float(pr[:, 0].mean()), float((pr[:, 1] - pr[:, 0]).mean())


def single_run() -> pd.DataFrame:
    """Test 1 and the validation, on the mean of the k grades (as published) and on single runs."""
    out = []
    d = guide_eval.rows()
    for fam in guide_eval.MODELS:
        for ds, dom, lbl in guide_eval.SETS:
            s = d[(d.fam == fam) & (d.dataset == ds) & (d.domain == dom)]
            G = s[guide_eval._is_guide(s)]
            if G.empty:
                continue
            _, sG = mpt._qwk_items(G)
            for c in sorted(set(s.cfg) - set(G.cfg)):
                A = s[s.cfg == c]
                r = _single(G, A)
                if r is None:
                    continue
                _, sA = mpt._qwk_items(A)
                kind = guide_eval._kind(A.iloc[0])
                out.append({"part": "Tests", "model": fam, "set": lbl, "kind": kind,
                            "guide_k": mpt._qwk_items(G[G.item_id.isin(sA.index)])[0], "guide_1": r[0],
                            "d_k": mpt._point(sG, sA), "d_1": r[1]})
    v = verification.load()
    for ds, dom, lbl in verification.SETS:
        for m in verification.MODELS:
            s = v[(v.dataset == ds) & (v.domain == dom) & (v.model == m)]
            G = s[s.kind == "guide"]
            _, sG = mpt._qwk_items(G)
            for k in verification.ALTS:
                A = s[s.kind == k]
                r = None if A.empty else _single(G, A)
                if r is None:
                    continue
                _, sA = mpt._qwk_items(A)
                out.append({"part": "Validation", "model": m, "set": lbl.split(" (")[0], "kind": k,
                            "guide_k": mpt._qwk_items(G[G.item_id.isin(sA.index)])[0], "guide_1": r[0],
                            "d_k": mpt._point(sG, sA), "d_1": r[1]})
    return pd.DataFrame(out)


def single_summary(s: pd.DataFrame) -> pd.DataFrame:
    """Per part and alternative: mean dQWK on the mean of k and on single runs, and comparisons whose sign differs."""
    g = s.assign(flip=(np.sign(s.d_k) != np.sign(s.d_1)))
    return (g.groupby(["part", "kind"], sort=False)
            .agg(n=("d_k", "size"), d_k=("d_k", "mean"), d_1=("d_1", "mean"), flips=("flip", "sum")).reset_index())


def fallback_sensitivity() -> pd.DataFrame:
    """RQ1 cells with fallback runs: dQWK and 95% CI with the fallback grades (as published) and on the model's own
    reasoning-on runs only."""
    df = phase5.load_main()
    df = df[(df.dataset != "ptcs") | df.item_id.isin(guide_eval._INTERV)]
    b = df[(df.context_level == "with_guidance") & (df.scope == "question_by_question") & (df.decomposition == "holistic")]
    rows = []
    for (ds, dom, m), g in b.groupby(["dataset", "domain", "model"]):
        on = g[g.reasoning == "on"]
        if on.empty or not on["fallback"].astype(bool).any():
            continue
        off = g[(g.reasoning == "off") & g.item_id.isin(set(on.item_id))]
        own = on[~on["fallback"].astype(bool)]
        _, sA = mpt._qwk_items(off)
        r = {"dataset": ds, "domain": dom, "model": m, "fallback_pct": 100 * float(on["fallback"].astype(bool).mean())}
        for key, d in [("with", on), ("own", own)]:
            _, sB = mpt._qwk_items(d)
            dist = mpt._boot_dist(sA, sB)
            lo, hi = np.percentile(dist, [2.5, 97.5])
            r.update({f"d_{key}": mpt._point(sA, sB), f"lo_{key}": lo, f"hi_{key}": hi})
        rows.append(r)
    return pd.DataFrame(rows)


@contextmanager
def discretised(levels: int, half_up: bool = False):
    """Run the engines with another number of QWK levels or with halves rounded up, then restore."""
    old = (mpt.K, mpt._W, phase5.to_levels)
    k = levels - 1
    mpt.K = k
    mpt._W = (np.subtract.outer(np.arange(k + 1), np.arange(k + 1)) ** 2).astype(float)
    if half_up:
        phase5.to_levels = lambda x, kk=k: np.floor(np.round(np.asarray(x, float) * kk, 9) + 0.5).clip(0, kk).astype(int)
    try:
        yield
    finally:
        mpt.K, mpt._W, phase5.to_levels = old


def discretisation() -> pd.DataFrame:
    """RQ1 under the paper's rule and three alternatives: significant gains (and after Holm), and which cells."""
    df = phase5.load_main()
    rows = []
    for label, lv, up in [("six levels, halves to even (paper)", 6, False), ("six levels, halves up", 6, True),
                          ("five levels", 5, False), ("seven levels", 7, False)]:
        with discretised(lv, up):
            r = mpt.rq1_cells(df, guide_eval._INTERV)
        s = r[(r.lo > 0)]
        rows.append({"rule": label, "significant": len(s), "holm": int((r.sig_holm & (r.dQWK > 0)).sum()),
                     "cells": ", ".join(f"{m} {d}" for m, d in zip(s.model, s.dataset + "-" + s.domain))})
    return pd.DataFrame(rows)


def _mae_boot(a: pd.DataFrame, b: pd.DataFrame, nb=mpt.NB):
    """Paired bootstrap over answers of MAE(b) - MAE(a) on item means (0-1 scale); a and b are item tables p, g."""
    items = a.index.intersection(b.index)
    ea = (a.loc[items, "p"] - a.loc[items, "g"]).abs().to_numpy()
    eb = (b.loc[items, "p"] - b.loc[items, "g"]).abs().to_numpy()
    rng = np.random.default_rng(mpt.SEED)
    idx = rng.integers(0, len(items), (nb, len(items)))
    dist = (eb[idx] - ea[idx]).mean(1)
    lo, hi = np.percentile(dist, [2.5, 97.5])
    return len(items), float(ea.mean()), float(eb.mean()), float(eb.mean() - ea.mean()), float(lo), float(hi)


def mae_rq1() -> pd.DataFrame:
    """Fourth independent review (2026-11-04): a continuous metric beside QWK. RQ1 per combination on the paper's
    basis (rq1_cells: the sampled items, a reasoning run that fell back carries the reasoning-off grade): mean
    absolute error with reasoning off and on, its change with a 95% paired bootstrap interval, the signed bias
    (model minus human) with reasoning off, and on SemEval the accuracy at the 0.5 cut-off."""
    df = phase5.load_main()
    dv = df[(df.dataset != "ptcs") | df.item_id.isin(guide_eval._INTERV)]
    rp = phase5.reasoning_paired(dv)
    base = rp[(rp.context_level == "with_guidance") & (rp.scope == "question_by_question") & (rp.decomposition == "holistic")]
    rows = []
    for (ds, dom, m), g in base.groupby(["dataset", "domain", "model"]):
        o, n = g[g.reasoning == "off"], g[g.reasoning == "on"]
        if o.empty or n.empty:
            continue
        items = set(n.item_id.unique())
        _, sA = mpt._qwk_items(o[o.item_id.isin(items)]); _, sB = mpt._qwk_items(n[n.item_id.isin(items)])
        N, m_off, m_on, d, lo, hi = _mae_boot(sA, sB)
        r = {"dataset": ds, "domain": dom, "model": m, "N": N, "MAE_off": m_off, "MAE_on": m_on, "dMAE": d,
             "lo": lo, "hi": hi, "sig": bool(lo > 0 or hi < 0), "bias_off": float((sA.p - sA.g).mean())}
        if ds == "semeval":
            acc = lambda t: float(((t.p >= 0.5) == (t.g >= 0.5)).mean())
            r.update({"acc_off": acc(sA), "acc_on": acc(sB)})
        rows.append(r)
    return pd.DataFrame(rows)


def mae_validation() -> pd.DataFrame:
    """The validation contrasts (guide against each alternative, per model and dataset) in mean absolute error."""
    d = verification.load()
    rows = []
    for ds, dom, lbl in verification.SETS:
        for m in verification.MODELS:
            s = d[(d.dataset == ds) & (d.domain == dom) & (d.model == m)]
            G = s[s.kind == "guide"]
            if G.empty:
                continue
            _, sG = mpt._qwk_items(G)
            for k in verification.ALTS:
                A = s[s.kind == k]
                if A.empty:
                    continue
                _, sA = mpt._qwk_items(A)
                N, mg, ma, dd, lo, hi = _mae_boot(sG, sA)
                rows.append({"set": lbl, "model": m, "kind": k, "N": N, "MAE_guide": mg, "MAE_alt": ma, "dMAE": dd,
                             "lo": lo, "hi": hi, "alt_better": bool(hi < 0), "alt_worse": bool(lo > 0),
                             "bias_guide": float((sG.p - sG.g).mean())})
    return pd.DataFrame(rows)


def instructors_loo() -> pd.DataFrame:
    """HARMOGEN-R ceiling on a comparable basis (fourth review, M6): each instructor against the mean of the other
    three, and each model's guide grades against that same mean."""
    import json
    from sklearn.metrics import cohen_kappa_score
    c = pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "corpus_verification.parquet")
    h = c[c.dataset == "harmogenr"].reset_index(drop=True)
    sc = pd.DataFrame([json.loads(x)["instructor_scores"] for x in h.source_meta]).div(h.gold_scale_max.to_numpy(), axis=0)
    sc.index = h.item_id
    lv = lambda x: phase5.to_levels(x, mpt.K)
    q = lambda a, b: cohen_kappa_score(lv(a), lv(b), weights="quadratic", labels=list(range(mpt.K + 1)))
    d = verification.load()
    guide = {m: g.groupby("item_id").pred_norm.mean() for m, g in
             d[(d.dataset == "harmogenr") & (d.kind == "guide") & d.pred_norm.notna()].groupby("model")}
    rows = []
    for col in sc.columns:
        rest = sc.drop(columns=col).mean(axis=1)
        r = {"held_out": col, "instructor_vs_rest": q(sc[col], rest)}
        for m, p in guide.items():
            it = p.index.intersection(rest.index)
            r[m] = q(p.loc[it], rest.loc[it])
        rows.append(r)
    return pd.DataFrame(rows)


def main() -> int:
    pd.set_option("display.width", 220)
    print("=== resampling answers (published) vs resampling questions ===")
    print(cluster_table().to_string(index=False))
    s = single_run()
    print("\n=== single runs vs the mean of the k grades ===")
    print(single_summary(s).round(3).to_string(index=False))
    gu = s.drop_duplicates(["part", "model", "set"])
    print(f"guide QWK, mean of k minus single run: {(gu.guide_k - gu.guide_1).mean():.3f} on average "
          f"({(gu.guide_k - gu.guide_1).min():.3f} to {(gu.guide_k - gu.guide_1).max():.3f}); "
          f"|change in dQWK| {np.abs(s.d_1 - s.d_k).mean():.3f} on average; sign changes {int((np.sign(s.d_k) != np.sign(s.d_1)).sum())} of {len(s)}")
    print(s[np.sign(s.d_k) != np.sign(s.d_1)].round(3).to_string(index=False))
    print("\n=== RQ1 with the fallback runs left out ===")
    print(fallback_sensitivity().round(3).to_string(index=False))
    print("\n=== RQ1 under other discretisations ===")
    print(discretisation().to_string(index=False))
    print("\n=== RQ1 in mean absolute error ===")
    print(mae_rq1().round(3).to_string(index=False))
    print("\n=== validation in mean absolute error ===")
    print(mae_validation().round(3).to_string(index=False))
    print("\n=== HARMOGEN-R ceiling, leave one instructor out ===")
    print(instructors_loo().round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
