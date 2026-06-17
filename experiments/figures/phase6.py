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
    # Single-column figure (sits at the foot of a column on page 6, with the wide panel figure at the
    # top of page 7, so the two never share a page).
    fig, ax = plt.subplots(figsize=(COL, COL * 0.82))
    ax.axhline(0, color="k", lw=0.5); ax.axvline(0, color="k", lw=0.5)
    for r in rc.itertuples():
        # y = consistency change (off SD minus on SD): below 0 = LESS consistent, matching the panel
        # figure's convention so the two RQ1 figures never use opposite directions for the same axis.
        ax.scatter(r.dQWK, r.SDk_off - r.SDk_on, s=34, marker=MARK.get(r.model, "o"),
                   c=COLOR[r.domain], edgecolor="k", lw=0.3, alpha=0.85)
    ax.set_xlabel("agreement change ($\\Delta$QWK): reasoning helps $\\to$")
    ax.set_ylabel("consistency change\n(below 0 = less consistent)")
    ax.set_title("RQ1: reasoning trades consistency for agreement")
    h1 = [plt.Line2D([], [], marker=m, color="grey", ls="", mec="k", mew=0.3, label=k) for k, m in MARK.items()]
    # label: "short_answer" -> "short answer" (a raw _ breaks LaTeX text mode in the .pgf; 7.4 fix)
    h2 = [plt.Line2D([], [], marker="o", color=c, ls="", mec="k", mew=0.3, label=d.replace("_", " ")) for d, c in COLOR.items()]
    ax.legend(handles=h1 + h2, loc="lower right", ncol=2, framealpha=0.9)
    _save(fig, "fig1_rq1_twodim")


def fig2(rc):
    fig, ax = plt.subplots(figsize=(COL, COL * 0.78))
    ax.axhline(0, color="k", lw=0.5)
    for r in rc.itertuples():
        ax.scatter(r.premium_x, r.dQWK, s=34, marker=MARK.get(r.model, "o"), c=COLOR[r.domain], edgecolor="k", lw=0.3, alpha=0.85)
    ax.set_xscale("log")
    ax.set_xlabel("reasoning cost: ON/OFF token premium ($\\times$, log)")
    ax.set_ylabel("agreement change ($\\Delta$QWK)")
    ax.set_title("RQ1: cost vs agreement of reasoning")
    _save(fig, "fig2_cost_vs_agreement")


def fig_panels(rc):
    """6.2b -- RQ1 trade as three aligned bar panels (replaces the fig1/fig2 scatters).
    One bar per model in each dataset group; read a vertical slice = one cell across all
    three metrics: agreement change, consistency change, token cost. Deterministic (no boot)."""
    order = [("mohler", "short_answer", "Mohler"), ("semeval", "short_answer", "SemEval"),
             ("riayn", "code", "RIAYN"), ("ptcs", "code", "PT-CS-ver. code"),
             ("ptcs", "short_answer", "PT-CS-ver. short")]
    models = list(MARK)  # qwen3.5, glm-5.1, deepseek-v4-flash, gpt-5.1
    lbl = [t[2] for t in order]
    x = np.arange(len(order)); w = 0.2

    def cell(ds, dom, m, col):
        r = rc[(rc.dataset == ds) & (rc.domain == dom) & (rc.model == m)]
        return float(r[col].iloc[0]) if len(r) else np.nan

    fig, axes = plt.subplots(1, 3, figsize=(COL * 2.1, COL * 0.74))
    specs = [("dQWK", "agreement: $\\Delta$QWK\n(above 0 = reasoning helps)", False),
             ("dSD", "consistency change\n(below 0 = less consistent)", False),
             ("premium_x", "cost: ON/OFF token premium\n($\\times$, log)", True)]
    for ax, (col, ttl, logy) in zip(axes, specs):
        for i, m in enumerate(models):
            # dSD plotted as stability change (off SD minus on SD): below 0 = reasoning is LESS
            # consistent, so it reads like the agreement panel (up = better, down = worse).
            vals = [cell(ds, dom, m, "SDk_off") - cell(ds, dom, m, "SDk_on") if col == "dSD"
                    else cell(ds, dom, m, col) for ds, dom, _ in order]
            ax.bar(x + (i - 1.5) * w, vals, w, color=MCOL[m], edgecolor="k", lw=0.3,
                   alpha=0.9, label=m.split("-")[0])
        ax.set_xticks(x); ax.set_xticklabels(lbl, rotation=30, ha="right")
        ax.set_title(ttl)
        if logy:
            ax.set_yscale("log")
        else:
            ax.axhline(0, color="k", lw=0.6)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, framealpha=0.9, bbox_to_anchor=(0.5, -0.04))
    fig.suptitle("RQ1: what reasoning buys and what it costs, per model and dataset", fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _save(fig, "fig_rq1_panels")


def fig_rq2(full):
    """6.x -- RQ2 evaluation-guidance benefit (dQWK, none -> with guidance) per dataset, with
    bootstrap CIs. Reuses the table generator's _qwk_items/_boot_ci (same SEED) so the bars match
    the prose numbers exactly. Qwen3.5, reasoning off, q-by-q, holistic. PT-CS = verified stratum only."""
    from experiments.analysis.make_phase5_tables import _qwk_items as _qi, _boot_ci as _bci
    q = full[(full.model == "qwen3.5") & (full.reasoning == "off")
             & (full.scope == "question_by_question") & (full.decomposition == "holistic")]
    specs = [("mohler", "short_answer", "Mohler", None, "short_answer"),
             ("semeval", "short_answer", "SemEval", None, "short_answer"),
             ("riayn", "code", "RIAYN", None, "code"),
             ("ptcs", "code", "PT-CS-ver.\ncode", _INTERV, "code")]
    labels, mds, los, his, cols, hatches = [], [], [], [], [], []
    for ds, dom, lbl, sub, dmn in specs:
        c = q[(q.dataset == ds) & (q.domain == dom)]
        A = c[c.context_level == "none"]; B = c[c.context_level == "with_guidance"]
        if sub is not None:
            A = A[A.item_id.isin(sub)]; B = B[B.item_id.isin(sub)]
        _, sA = _qi(A); _, sB = _qi(B)
        lo, md, hi = _bci(sA, sB)
        labels.append(lbl); mds.append(md); los.append(md - lo); his.append(hi - md)
        cols.append(COLOR[dmn]); hatches.append("")
    fig, ax = plt.subplots(figsize=(COL, COL * 0.82))
    x = np.arange(len(labels))
    ax.bar(x, mds, 0.62, color=cols, edgecolor="k", lw=0.3, alpha=0.9, hatch=hatches)
    ax.errorbar(x, mds, yerr=[los, his], fmt="none", ecolor="k", elinewidth=0.6, capsize=2)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel("agreement gain ($\\Delta$QWK)\nwith guidance vs none")
    ax.set_title("RQ2: evaluation-guidance benefit per dataset")
    h = [plt.Line2D([], [], marker="s", color=c, ls="", mec="k", mew=0.3, label=d.replace("_", " "))
         for d, c in COLOR.items()]
    ax.legend(handles=h, loc="upper right", framealpha=0.9)
    _save(fig, "fig_rq2_guidance")


def fig_rq3(full):
    """6.x -- RQ3 scope and decomposition contrasts (dQWK, K=5, bootstrap CI), PT-CS-verified code.
    Same _qwk_items/_boot_ci and subset construction as the table generator, so bars match
    the prose. Qwen3.5, reasoning off. dQWK<0 means the alternative scored worse than the baseline."""
    from experiments.analysis.make_phase5_tables import _qwk_items as _qi, _boot_ci as _bci
    q = full[(full.model == "qwen3.5") & (full.reasoning == "off")]
    we = set(full[full.scope == "whole_exam"].item_id)
    sc = q[(q.dataset == "ptcs") & (q.domain == "code") & (q.context_level == "with_guidance") & (q.decomposition == "holistic")]
    dd = q[(q.dataset == "ptcs") & (q.domain == "code") & (q.context_level == "with_guidance") & (q.scope == "question_by_question")]
    groups = [("scope\n(whole exam\nvs q-by-q)", sc[(sc.scope == "question_by_question") & sc.item_id.isin(we)],
               full[full.scope == "whole_exam"]),
              ("decomposition\n(criterion\nvs holistic)", dd[dd.decomposition == "holistic"], dd[dd.decomposition == "criterion"])]

    def contrast(A, B, sub=None):
        if sub is not None:
            A = A[A.item_id.isin(sub)]; B = B[B.item_id.isin(sub)]
        _, sA = _qi(A); _, sB = _qi(B)
        return _bci(sA, sB)  # (lo, md, hi)

    fig, ax = plt.subplots(figsize=(COL * 0.72, COL * 0.56))
    x = np.arange(len(groups))
    mds, los, his = [], [], []
    for _, A, B in groups:
        lo, md, hi = contrast(A, B, _INTERV)   # verified stratum only
        mds.append(md); los.append(md - lo); his.append(hi - md)
    ax.bar(x, mds, 0.5, color=COLOR["code"], edgecolor="k", lw=0.3, alpha=0.9)
    ax.errorbar(x, mds, yerr=[los, his], fmt="none", ecolor="k", elinewidth=0.6, capsize=2)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xticks(x); ax.set_xticklabels([g[0] for g in groups])
    ax.set_ylabel("agreement change ($\\Delta$QWK)\n(below 0 = worse than baseline)")
    ax.set_title("RQ3: scope and decomposition (PT-CS-verified code)")
    _save(fig, "fig_rq3_scope_decomp")


def fig_rq4_cost(full):
    """RQ4 cost-quality BY TASK: QWK vs euro cost per 1000 grades (log), one point per model x
    reasoning, in two panels (short-answer = Mohler+SemEval; code = RIAYN), shared y so the
    short-answer cluster vs the code spread reads directly. QWK via the table generator's _qwk_items;
    cost from the logged per-call cost_eur (engine-backed). Deterministic. Single column, side by side."""
    from experiments.analysis.make_phase5_tables import _qwk_items as _qi
    base = full[(full.context_level == "with_guidance") & (full.scope == "question_by_question")
                & (full.decomposition == "holistic") & full.dataset.isin(["mohler", "semeval", "riayn"])].copy()
    base["ce"] = pd.to_numeric(base.get("cost_eur"), errors="coerce")
    panels = [("short answer", ["mohler", "semeval"]), ("code", ["riayn"])]
    models = ["qwen3.5", "glm-5.1", "deepseek-v4-flash", "gpt-5.1"]
    mk = {"off": "o", "on": "s"}
    fig, axes = plt.subplots(1, 2, figsize=(COL, COL * 0.6), sharey=True, sharex=True)
    for ax, (title, dsets) in zip(axes, panels):
        sub = base[base.dataset.isin(dsets)]
        for m in models:
            for rs in ["off", "on"]:
                cell = sub[(sub.model == m) & (sub.reasoning == rs)]
                qs = [_qi(cell[cell.dataset == d])[0] for d in dsets]
                qs = [q for q in qs if q == q]
                if not qs:
                    continue
                ax.scatter(cell.ce.mean() * 1000, np.mean(qs), s=30, marker=mk[rs], color=MCOL[m],
                           edgecolor="k", lw=0.3, alpha=0.9, zorder=3)
        ax.set_xscale("log"); ax.set_title(title)
        ax.set_box_aspect(1)   # square plot boxes (equal height and width), both panels identical
    axes[0].set_ylabel("agreement (QWK, K=5)")
    for ax in axes:
        ax.set_xlabel("cost/1000 (EUR, log)")
    fig.suptitle("RQ4: agreement vs cost, by task", fontsize=8)
    h1 = [plt.Line2D([], [], marker="o", color=MCOL[m], ls="", mec="k", mew=0.4, label=m.split("-")[0])
          for m in models]
    h2 = [plt.Line2D([], [], marker=mk[r], color="grey", ls="", mec="k", mew=0.4, label=f"reasoning {r}")
          for r in ["off", "on"]]
    fig.tight_layout()
    fig.legend(handles=h1 + h2, loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.01), framealpha=0.9)
    _save(fig, "fig_rq4_cost")


def fig_rq6_transfer(full):
    """6.8 -- RQ6 transfer slopegraph, WITHIN DOMAIN: does the configuration ranking learned on the
    public datasets hold on the PT-CS deployment data, separately for short answers and for code.
    Left panel: public short-answer (mean over Mohler, SemEval) -> PT-CS-verified short answers. Right
    panel: public code (RIAYN) -> PT-CS-verified code. One line per open config; the GPT-5.1 anchor is
    thin grey (verified cells rest on 11-25 items, corroboration only). The public ranking uses public
    data ONLY -- PT-CS is never in it -- so the comparison is a genuine out-of-public-sample check, and
    domain is matched on both sides (no short/code mixing). Built from the run data, K=5 item means,
    with-guidance / question-by-question / holistic; verified = intervened stratum. Single column."""
    base = full[(full.context_level == "with_guidance") & (full.scope == "question_by_question")
                & (full.decomposition == "holistic")]

    def q_pub(g, dsets):
        return float(np.nanmean([_qwk(_itemmeans(g[g.dataset == ds])) for ds in dsets]))

    def q_ver(g, dom):
        return _qwk(_itemmeans(g[(g.dataset == "ptcs") & (g.domain == dom) & g.item_id.isin(_INTERV)]))

    from scipy.stats import spearmanr
    panels = [("short answer", ["mohler", "semeval"], "short_answer"), ("code", ["riayn"], "code")]
    fig, axes = plt.subplots(1, 2, figsize=(COL, COL * 0.62), sharey=True)
    for ax, (title, pub_ds, dom) in zip(axes, panels):
        pub_open, ver_open = [], []
        for m in ["qwen3.5", "glm-5.1", "deepseek-v4-flash", "gpt-5.1"]:
            for r in ["off", "on"]:
                g = base[(base.model == m) & (base.reasoning == r)]
                ys = [q_pub(g, pub_ds), q_ver(g, dom)]
                anchor = m == "gpt-5.1"
                if not anchor:
                    pub_open.append(ys[0]); ver_open.append(ys[1])
                ax.plot([0, 1], ys, color="#999" if anchor else MCOL[m], ls="-" if r == "on" else "--",
                        lw=0.8 if anchor else 1.4, marker=MARK[m], ms=4.5,
                        mfc=("#999" if anchor else (MCOL[m] if r == "on" else "w")),
                        mec="#999" if anchor else MCOL[m], mew=0.8,
                        alpha=0.55 if anchor else 0.95, zorder=1 if anchor else 2)
        rho = spearmanr(pub_open, ver_open).statistic               # rank transfer over the 6 open configs
        ax.text(0.5, 0.03, f"rank $\\rho={rho:.2f}$", transform=ax.transAxes, ha="center", va="bottom",
                fontsize=6.5, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#bbb", lw=0.4))
        ax.set_xticks([0, 1]); ax.set_xticklabels(["public", "PT-CS\nverified"])
        ax.set_xlim(-0.3, 1.3); ax.set_title(title); ax.set_box_aspect(1)
    axes[0].set_ylabel("agreement (QWK, K=5)")
    fig.suptitle("RQ6: does the public ranking transfer?", fontsize=8)
    mh = [plt.Line2D([], [], color=MCOL[m], marker=MARK[m], ls="-", mec=MCOL[m], label=m.split("-")[0])
          for m in ["qwen3.5", "glm-5.1", "deepseek-v4-flash"]]
    rh = [plt.Line2D([], [], color="grey", ls="-", label="reasoning on"),
          plt.Line2D([], [], color="grey", ls="--", label="reasoning off"),
          plt.Line2D([], [], color="#999", ls="-", lw=0.8, label="gpt-5.1 anchor (small $N$)")]
    fig.tight_layout()
    fig.legend(handles=mh + rh, loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.01), framealpha=0.9, fontsize=5)
    _save(fig, "fig_rq6_transfer")


def fig3(df):
    # Single-column (figure, not figure*): compact enough to sit by its RQ4 text. 32 bars (4 datasets
    # x 4 models x off/on), so it runs tall to keep the bars and CIs legible. (A full-width variant
    # was tried but always drifted to the next page, away from RQ4 -- §11 / git.)
    base = df[(df.context_level == "with_guidance") & (df.scope == "question_by_question") & (df.decomposition == "holistic")]
    dsets = ["mohler", "semeval", "riayn", "ptcs"]; models = list(MARK)
    fig, ax = plt.subplots(figsize=(COL, COL * 1.0))
    x = np.arange(len(dsets)); w = 0.1
    for i, m in enumerate(models):
        for j, rs in enumerate(["off", "on"]):
            qs, los, his = [], [], []
            for d in dsets:
                q, lo, hi, n = _qwk_ci(base[(base.dataset == d) & (base.model == m) & (base.reasoning == rs)])
                qs.append(q); los.append(q - lo if q == q else 0); his.append(hi - q if q == q else 0)
            pos = x + (i * 2 + j - 3.5) * w
            ax.bar(pos, qs, w, color=MCOL[m], alpha=0.55 if rs == "off" else 1.0, edgecolor="k", lw=0.3,
                   hatch="" if rs == "off" else "//", label=f"{m.split('-')[0]}$|${rs}")
            ax.errorbar(pos, qs, yerr=[los, his], fmt="none", ecolor="k", elinewidth=0.5, capsize=1.2)
    ax.set_xticks(x); ax.set_xticklabels([d if d != "ptcs" else "ptcs*" for d in dsets]); ax.set_ylabel("agreement (QWK, K=5)")
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
    """6.6 -- conversation STATE only: mean grade per model, clean vs shared. The order effect is a
    noise result with no level difference to plot (mean natural == mean inverse), so it is reported in
    prose, not here. Single panel, single column."""
    cv = phase5.load_conversation()
    mods = sorted(cv.model.unique()); x = np.arange(len(mods)); w = 0.36
    fig, ax = plt.subplots(figsize=(COL, COL * 0.7))
    for j, st in enumerate(["clean", "shared"]):
        means = [cv[(cv.model == m) & (cv.conversation_state == st)].pred_norm.mean() for m in mods]
        ax.bar(x + (j - 0.5) * w, means, w, label=st, color="#888" if st == "clean" else "#8e44ad",
               edgecolor="k", lw=0.3, alpha=0.85)
    ax.set_xticks(x); ax.set_xticklabels([m.split("-")[0] for m in mods]); ax.set_ylabel("mean grade")
    ax.set_title("RQ5: clean vs shared conversation"); ax.legend(framealpha=0.9)
    fig.tight_layout()
    _save(fig, "fig5_conversation")


# fig6 (gold full-vs-verified sensitivity) REMOVED 2026-06-16: the gold-sensitivity subsection, its
# table and this full-width figure were cut from the paper body (they defended the dataset more than they
# built the framework). The one framework-relevant point is now a short paragraph in RQ6, and the numbers
# stay engine-backed via the audit print in make_phase5_tables.py (the former tab_gold_sensitivity block).


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
    _full = phase5.load_main()
    fig1(rc); fig2(rc); fig_panels(rc); fig_rq2(_full); fig_rq3(_full); fig_rq4_cost(_full)
    fig_rq6_transfer(_full); fig3(df); fig4(df); fig5(df)
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
