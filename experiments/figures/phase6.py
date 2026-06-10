"""Phase 6 figures (PHASES.md). Built from the Phase-5 engine (experiments.analysis.phase5)
so the §5.0 conventions (clamp/normalise/K=5/pairing/dedupe) are applied consistently.

6.1 style: IEEEtran single-column width (~3.4in), small fonts, .pdf + .pgf (pdflatex).
6.2/5.5a fig1: RQ1 two-dimensional -- reasoning's effect on agreement (dQWK) vs on
              consistency (dSDk), per (dataset,model). The headline trade-off.
6.3   fig2:   cost-vs-agreement -- token premium (log x) vs agreement gain (dQWK).
6.5   fig3:   per-dataset configuration comparison (QWK by model x reasoning) -- framework visual.

  python -m experiments.figures.phase6
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pgf.texsystem"] = "pdflatex"
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiments.analysis import phase5

OUT = phase5.REPO_ROOT / "article" / "figures"
COL = 3.4                                   # IEEEtran single-column width (inches)
MARK = {"qwen3.5": "o", "glm-5.1": "s", "deepseek-v4-flash": "^", "gpt-5.1": "D"}
COLOR = {"code": "#c0392b", "short_answer": "#2471a3"}


def _style():
    plt.rcParams.update({"font.size": 7, "axes.titlesize": 8, "axes.labelsize": 7.5,
                         "legend.fontsize": 5.6, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
                         "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150,
                         "savefig.bbox": "tight"})


def _save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf")
    try:
        fig.savefig(OUT / f"{name}.pgf")
    except (RuntimeError, FileNotFoundError):
        pass
    plt.close(fig)
    print(f"  {name}.pdf")


def fig1_rq1_twodim(rc):
    """dQWK (agreement) vs dSDk (consistency change). The RQ1 headline: reasoning trades
    consistency for agreement, model-specific."""
    fig, ax = plt.subplots(figsize=(COL, COL * 0.82))
    ax.axhline(0, color="k", lw=0.5); ax.axvline(0, color="k", lw=0.5)
    seen = set()
    for r in rc.itertuples():
        dq = r.dQWK; dsd = r.SDk_on - r.SDk_off
        ax.scatter(dq, dsd, s=34, marker=MARK.get(r.model, "o"), c=COLOR[r.domain],
                   edgecolor="k", lw=0.3, alpha=0.85)
    ax.set_xlabel("agreement change  $\\Delta$QWK (off$\\to$on)")
    ax.set_ylabel("consistency WORSE  $\\to$\n$\\Delta$ within-item SD")
    ax.set_title("RQ1: reasoning trades consistency for agreement")
    # legends: model (marker) + domain (colour)
    h1 = [plt.Line2D([], [], marker=m, color="grey", ls="", mec="k", mew=0.3, label=k)
          for k, m in MARK.items()]
    h2 = [plt.Line2D([], [], marker="o", color=c, ls="", mec="k", mew=0.3, label=d)
          for d, c in COLOR.items()]
    ax.legend(handles=h1 + h2, loc="upper left", ncol=2, framealpha=0.9)
    ax.text(0.98, 0.02, "right = reasoning helps agreement\nup = reasoning hurts consistency",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=5, color="#555")
    _save(fig, "fig1_rq1_twodim")


def fig2_cost_agreement(rc):
    """Token premium (log) vs agreement gain. The cost of the reasoning lever."""
    fig, ax = plt.subplots(figsize=(COL, COL * 0.78))
    ax.axhline(0, color="k", lw=0.5)
    for r in rc.itertuples():
        ax.scatter(r.premium_x, r.dQWK, s=34, marker=MARK.get(r.model, "o"), c=COLOR[r.domain],
                   edgecolor="k", lw=0.3, alpha=0.85)
    ax.set_xscale("log")
    ax.set_xlabel("reasoning cost: ON/OFF completion-token premium ($\\times$, log)")
    ax.set_ylabel("agreement gain  $\\Delta$QWK")
    ax.set_title("RQ1: cost vs agreement of reasoning")
    ax.text(0.98, 0.97, "Qwen: ~800$\\times$ tokens for the gain",
            transform=ax.transAxes, ha="right", va="top", fontsize=5, color="#555")
    _save(fig, "fig2_cost_vs_agreement")


def fig3_per_dataset(df):
    """QWK by model x reasoning, per dataset -- the framework's 'which config wins where'."""
    from sklearn.metrics import cohen_kappa_score
    K = 5
    base = df[(df.context_level == "with_guidance") & (df.scope == "question_by_question")
              & (df.decomposition == "holistic")]
    def qwk(d):
        s = d[d.pred_norm.notna() & d.gold_norm.notna()].groupby("item_id").agg(p=("pred_norm", "mean"), g=("gold_norm", "mean"))
        if len(s) < 8:
            return np.nan
        return cohen_kappa_score((s.g * K).round().clip(0, K).astype(int), (s.p * K).round().clip(0, K).astype(int),
                                 weights="quadratic", labels=list(range(K + 1)))
    dsets = ["mohler", "semeval", "riayn", "ptcs"]
    models = ["qwen3.5", "deepseek-v4-flash", "glm-5.1", "gpt-5.1"]
    fig, ax = plt.subplots(figsize=(COL * 1.55, COL * 0.7))
    x = np.arange(len(dsets)); w = 0.1
    for i, m in enumerate(models):
        for j, rs in enumerate(["off", "on"]):
            vals = [qwk(base[(base.dataset == d) & (base.model == m) & (base.reasoning == rs)]) for d in dsets]
            ax.bar(x + (i * 2 + j - 3.5) * w, vals, w, label=f"{m.split('-')[0]}|{rs}",
                   color=plt.cm.tab10(i / 10), alpha=0.6 if rs == "off" else 1.0,
                   edgecolor="k", lw=0.3, hatch="" if rs == "off" else "//")
    ax.set_xticks(x); ax.set_xticklabels(dsets); ax.set_ylabel("QWK (K=5)")
    ax.set_title("RQ4: agreement by model $\\times$ reasoning, per dataset")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12), framealpha=0.9)
    _save(fig, "fig3_per_dataset_config")


def main() -> int:
    _style()
    OUT.mkdir(parents=True, exist_ok=True)
    print("Phase 6 figures ->", OUT)
    df = phase5.load_main()
    rc = phase5.reasoning_contrast(df)
    # add the token premium per row (for fig2)
    rp = phase5.reasoning_paired(df)
    b = rp[(rp.context_level == "with_guidance") & (rp.scope == "question_by_question") & (rp.decomposition == "holistic")]
    prem = {}
    for (ds, dom, m), g in b.groupby(["dataset", "domain", "model"]):
        o = pd.to_numeric(g[g.reasoning == "off"].completion_tokens, errors="coerce").mean()
        n = pd.to_numeric(g[g.reasoning == "on"].completion_tokens, errors="coerce").mean()
        prem[(ds, dom, m)] = n / max(o, 1)
    rc["premium_x"] = rc.apply(lambda r: prem.get((r.dataset, r.domain, r.model), np.nan), axis=1)
    fig1_rq1_twodim(rc)
    fig2_cost_agreement(rc)
    fig3_per_dataset(df)
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
