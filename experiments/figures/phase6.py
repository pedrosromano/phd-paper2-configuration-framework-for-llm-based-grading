"""Phase 6 figures (PHASES.md), built from the Phase-5 engine so the §5.0 conventions hold.

PT-CS is the VERIFIED stratum everywhere (intervened gold), consistent with the 5.7 tables;
the full-vs-verified gold lesson lives in fig6 (6.7) only. Low-N bars carry bootstrap CIs so
the figures self-defend like the tables. IEEEtran single-column; .pdf + .pgf (pdflatex).

  6.2/5.5a fig1 -- RQ1 two-dimensional (dQWK vs d-SD): reasoning trades consistency for agreement
  6.3      fig2 -- cost (token premium, log) vs agreement gain
  6.5      fig3 -- QWK by model x reasoning per dataset (+CIs) -- the framework visual
  6.4      fig4 -- consistency (within-item SD) off vs on -- the sacrificed axis
  6.6      fig5 -- conversation sub-study (order vs state, per model) + scope
  6.7      fig6 -- full-vs-verified gold sensitivity (the gold lesson, most persuasive)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pgf.texsystem"] = "pdflatex"
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from experiments.analysis import phase5

OUT = phase5.REPO_ROOT / "article" / "figures"
COL = 3.4
K = 5
RNG = np.random.default_rng(20260610)
MARK = {"qwen3.5": "o", "glm-5.1": "s", "deepseek-v4-flash": "^", "gpt-5.1": "D"}
COLOR = {"code": "#c0392b", "short_answer": "#2471a3"}
MCOL = {"qwen3.5": "#1f77b4", "deepseek-v4-flash": "#ff7f0e", "glm-5.1": "#2ca02c", "gpt-5.1": "#d62728"}
_INTERV = set(pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "_ptcs_strata.parquet")
              .query("stratum=='intervened'").item_id)


def load_verified() -> pd.DataFrame:
    df = phase5.load_main()
    return df[(df.dataset != "ptcs") | df.item_id.isin(_INTERV)].copy()


def _style():
    plt.rcParams.update({"font.size": 7, "axes.titlesize": 8, "axes.labelsize": 7.5,
                         "legend.fontsize": 5.4, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
                         "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150, "savefig.bbox": "tight"})


def _save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf")
    try:
        fig.savefig(OUT / f"{name}.pgf")
    except (RuntimeError, FileNotFoundError) as e:
        # pgf needs latex on PATH (CLAUDE.md §9: /Library/TeX/texbin). Warn LOUDLY rather than
        # silently leaving a stale .pgf — that trap shipped stale pgf once already.
        print(f"  !! {name}.pgf NOT written ({type(e).__name__}: {e}). "
              f"Run with latex on PATH:  eval \"$(/usr/libexec/path_helper)\"", flush=True)
    plt.close(fig)
    print(f"  {name}.pdf")


def _itemmeans(d):
    return d[d.pred_norm.notna() & d.gold_norm.notna()].groupby("item_id").agg(p=("pred_norm", "mean"), g=("gold_norm", "mean"))


def _qwk(s):
    if len(s) < 8:
        return np.nan
    return cohen_kappa_score((s.g * K).round().clip(0, K).astype(int), (s.p * K).round().clip(0, K).astype(int),
                             weights="quadratic", labels=list(range(K + 1)))


def _qwk_ci(d, nb=300):
    s = _itemmeans(d)
    q = _qwk(s)
    if np.isnan(q):
        return np.nan, np.nan, np.nan, len(s)
    idx = s.index.to_numpy()
    boot = [_qwk(s.loc[RNG.choice(idx, len(idx), True)]) for _ in range(nb)]
    lo, hi = np.nanpercentile(boot, [2.5, 97.5])
    return q, lo, hi, len(s)


def _ptcs_n(df):
    return df[df.dataset == "ptcs"].item_id.nunique()


def fig1(rc):
    fig, ax = plt.subplots(figsize=(COL, COL * 0.82))
    ax.axhline(0, color="k", lw=0.5); ax.axvline(0, color="k", lw=0.5)
    for r in rc.itertuples():
        ax.scatter(r.dQWK, r.SDk_on - r.SDk_off, s=34, marker=MARK.get(r.model, "o"),
                   c=COLOR[r.domain], edgecolor="k", lw=0.3, alpha=0.85)
    ax.set_xlabel("agreement change  $\\Delta$QWK (off$\\to$on)")
    ax.set_ylabel("consistency WORSE $\\to$\n$\\Delta$ within-item SD")
    ax.set_title("RQ1: reasoning trades consistency for agreement")
    h1 = [plt.Line2D([], [], marker=m, color="grey", ls="", mec="k", mew=0.3, label=k) for k, m in MARK.items()]
    h2 = [plt.Line2D([], [], marker="o", color=c, ls="", mec="k", mew=0.3, label=d) for d, c in COLOR.items()]
    ax.legend(handles=h1 + h2, loc="lower right", ncol=2, framealpha=0.9)
    _save(fig, "fig1_rq1_twodim")


def fig2(rc):
    fig, ax = plt.subplots(figsize=(COL, COL * 0.78))
    ax.axhline(0, color="k", lw=0.5)
    for r in rc.itertuples():
        ax.scatter(r.premium_x, r.dQWK, s=34, marker=MARK.get(r.model, "o"), c=COLOR[r.domain], edgecolor="k", lw=0.3, alpha=0.85)
    ax.set_xscale("log")
    ax.set_xlabel("reasoning cost: ON/OFF token premium ($\\times$, log)")
    ax.set_ylabel("agreement gain  $\\Delta$QWK")
    ax.set_title("RQ1: cost vs agreement of reasoning")
    _save(fig, "fig2_cost_vs_agreement")


def fig3(df):
    base = df[(df.context_level == "with_guidance") & (df.scope == "question_by_question") & (df.decomposition == "holistic")]
    dsets = ["mohler", "semeval", "riayn", "ptcs"]; models = list(MARK)
    fig, ax = plt.subplots(figsize=(COL * 1.6, COL * 0.72))
    x = np.arange(len(dsets)); w = 0.1
    for i, m in enumerate(models):
        for j, rs in enumerate(["off", "on"]):
            qs, los, his = [], [], []
            for d in dsets:
                q, lo, hi, n = _qwk_ci(base[(base.dataset == d) & (base.model == m) & (base.reasoning == rs)])
                qs.append(q); los.append(q - lo if q == q else 0); his.append(hi - q if q == q else 0)
            pos = x + (i * 2 + j - 3.5) * w
            ax.bar(pos, qs, w, color=MCOL[m], alpha=0.55 if rs == "off" else 1.0, edgecolor="k", lw=0.3,
                   hatch="" if rs == "off" else "//", label=f"{m.split('-')[0]}|{rs}")
            ax.errorbar(pos, qs, yerr=[los, his], fmt="none", ecolor="k", elinewidth=0.5, capsize=1.2)
    ax.set_xticks(x); ax.set_xticklabels([d if d != "ptcs" else "ptcs*" for d in dsets]); ax.set_ylabel("QWK (K=5)")
    ax.set_title("RQ4: agreement by model $\\times$ reasoning, per dataset")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.13), framealpha=0.9)
    ax.text(0.99, 0.97, f"*PT-CS verified, N={_ptcs_n(base)}", transform=ax.transAxes, ha="right", va="top", fontsize=5, color="#555")
    _save(fig, "fig3_per_dataset_config")


def fig4(df):
    """6.4 -- within-item SD (consistency, lower=better) off vs on, per dataset (mean over models)."""
    base = df[(df.context_level == "with_guidance") & (df.scope == "question_by_question") & (df.decomposition == "holistic") & df.pred_norm.notna()]
    dsets = ["mohler", "semeval", "riayn", "ptcs"]
    fig, ax = plt.subplots(figsize=(COL, COL * 0.72))
    x = np.arange(len(dsets)); w = 0.36
    for j, rs in enumerate(["off", "on"]):
        sd = [base[(base.dataset == d) & (base.reasoning == rs)].groupby("item_id").pred_norm.std().dropna().mean() for d in dsets]
        ax.bar(x + (j - 0.5) * w, sd, w, label=f"reasoning {rs}", color="#888" if rs == "off" else "#c0392b",
               edgecolor="k", lw=0.3, alpha=0.85)
    ax.set_xticks(x); ax.set_xticklabels([d if d != "ptcs" else "ptcs*" for d in dsets])
    ax.set_ylabel("within-item SD across $k$\n(lower = more consistent)")
    ax.set_title("RQ1: reasoning reduces consistency (the sacrificed axis)")
    ax.legend(framealpha=0.9)
    ax.text(0.99, 0.97, f"*PT-CS verified, N={_ptcs_n(base)}", transform=ax.transAxes, ha="right", va="top", fontsize=5, color="#555")
    _save(fig, "fig4_consistency")


def fig5(df):
    """6.6 -- conversation: order (shared nat vs inv) and state (clean vs shared) per model; + scope."""
    cv = phase5.load_conversation()
    cs = phase5.conversation_stats(cv)                     # computed p-values (no hand-typed strings)
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(COL * 1.7, COL * 0.66))
    # A: state effect (clean vs shared mean) + order spread, per model
    mods = sorted(cv.model.unique()); x = np.arange(len(mods)); w = 0.36
    for j, st in enumerate(["clean", "shared"]):
        means = [cv[(cv.model == m) & (cv.conversation_state == st)].pred_norm.mean() for m in mods]
        axA.bar(x + (j - 0.5) * w, means, w, label=st, color="#888" if st == "clean" else "#8e44ad", edgecolor="k", lw=0.3, alpha=0.85)
    axA.set_xticks(x); axA.set_xticklabels([m.split("-")[0] for m in mods]); axA.set_ylabel("mean normalised grade")
    _sp = [v["state_p"] for v in cs.values() if "state_p" in v]
    _slbl = "p$<$.01" if _sp and max(_sp) < 0.01 else f"p$=${max(_sp):.2f}"
    axA.set_title(f"RQ5 state: shared $\\to$ stricter ({_slbl})"); axA.legend(framealpha=0.9)
    # B: order effect = mean|nat-inv| per model (variance, not bias)
    for i, m in enumerate(mods):
        sh = cv[(cv.model == m) & (cv.conversation_state == "shared")]
        piv = sh.pivot_table(index=["item_id", "run_index"], columns="order_id", values="pred_norm", aggfunc="first").dropna()
        dif = (piv["natural"] - piv["inverse"]).abs()
        axB.bar(i, dif.mean(), 0.5, color=MCOL.get(m, "#555"), edgecolor="k", lw=0.3, alpha=0.85)
    axB.set_xticks(range(len(mods))); axB.set_xticklabels([m.split("-")[0] for m in mods])
    _glm = [m for m in mods if m.startswith("glm")]          # GLM = the cleaner read (§11); cite its order p
    _op = cs[_glm[0]]["order_p"] if _glm and "order_p" in cs[_glm[0]] else max((v.get("order_p", 1.0) for v in cs.values()), default=1.0)
    axB.set_ylabel("mean |natural $-$ inverse|"); axB.set_title(f"RQ5 order: variance, not bias (p$=${_op:.2f})")
    fig.tight_layout()
    _save(fig, "fig5_conversation")


def fig6(df):
    """6.7 -- full vs verified PT-CS: the gold lesson (most persuasive). Two panels."""
    full = phase5.load_main()
    code = lambda d: d[(d.dataset == "ptcs") & (d.domain == "code") & (d.model == "qwen3.5") & (d.reasoning == "off")
                       & (d.context_level == "with_guidance") & (d.scope == "question_by_question") & (d.decomposition == "holistic")]
    cf = code(full)
    qf, _, _, nf = _qwk_ci(cf); qv, _, _, nv = _qwk_ci(cf[cf.item_id.isin(_INTERV)])
    # rubric dQWK full vs verified
    def rub(d, sub):
        b = d[(d.dataset == "ptcs") & (d.domain == "code") & (d.model == "qwen3.5") & (d.reasoning == "off")
              & (d.scope == "question_by_question") & (d.decomposition == "holistic") & sub]
        return _qwk(_itemmeans(b[b.context_level == "with_guidance"])) - _qwk(_itemmeans(b[b.context_level == "none"]))
    rf = rub(full, full.item_id.notna()); rv = rub(full, full.item_id.isin(_INTERV))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(COL * 1.5, COL * 0.62))
    a1.bar([0, 1], [qf, qv], 0.55, color=["#aaa", "#c0392b"], edgecolor="k", lw=0.3)
    a1.set_xticks([0, 1]); a1.set_xticklabels([f"full\nN={nf}", f"verified\nN={nv}"]); a1.set_ylabel("Qwen OFF code QWK")
    a1.set_title("Unvalidated gold understates agreement")
    a2.bar([0, 1], [rf, rv], 0.55, color=["#aaa", "#2471a3"], edgecolor="k", lw=0.3)
    a2.axhline(0, color="k", lw=0.5); a2.set_xticks([0, 1]); a2.set_xticklabels(["full", "verified"])
    a2.set_ylabel("rubric benefit  $\\Delta$QWK"); a2.set_title("...and masks the rubric benefit")
    fig.suptitle("The gold lesson: validated reference matters (PT-CS)", fontsize=8)
    fig.tight_layout()
    _save(fig, "fig6_gold_sensitivity")


def main() -> int:
    _style()
    print("Phase 6 figures ->", OUT)
    df = load_verified()                 # PT-CS = verified stratum everywhere
    rc = phase5.reasoning_contrast(df)
    rp = phase5.reasoning_paired(df)
    b = rp[(rp.context_level == "with_guidance") & (rp.scope == "question_by_question") & (rp.decomposition == "holistic")]
    prem = {}
    for (ds, dom, m), g in b.groupby(["dataset", "domain", "model"]):
        o = pd.to_numeric(g[g.reasoning == "off"].completion_tokens, errors="coerce").mean()
        n = pd.to_numeric(g[g.reasoning == "on"].completion_tokens, errors="coerce").mean()
        prem[(ds, dom, m)] = n / max(o, 1)
    rc["premium_x"] = rc.apply(lambda r: prem.get((r.dataset, r.domain, r.model), np.nan), axis=1)
    fig1(rc); fig2(rc); fig3(df); fig4(df); fig5(df); fig6(df)
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
