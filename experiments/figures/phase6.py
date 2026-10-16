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
import matplotlib.ticker
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from experiments.analysis import phase5

OUT = phase5.REPO_ROOT / "article" / "figures"
COL = 3.3      # IEEE Access column width is 85.29 mm (3.36 in)
WIDE = 6.9     # IEEE Access text width is 177.53 mm (6.99 in)
K = 5
RNG = np.random.default_rng(20260610)
MARK = {"qwen3.5": "o", "glm-5.1": "s", "deepseek-v4-flash": "^", "gpt-5.1": "D"}   # the four families of RQ1
COLOR = {"code": "#c0392b", "short_answer": "#2471a3"}
MCOL = {"qwen3.5": "#1f77b4", "deepseek-v4-flash": "#ff7f0e", "glm-5.1": "#2ca02c", "gpt-5.1": "#d62728",
        "claude-sonnet-4-6": "#9467bd", "glm-5.1-or": "#2ca02c"}
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
    h1 = [plt.Line2D([], [], marker=m, color="grey", ls="", mec="k", mew=0.3, label=MNAME.get(k, k)) for k, m in MARK.items()]
    # label: "short_answer" -> "short answer" (a raw _ breaks LaTeX text mode in the .pgf; 7.4 fix)
    h2 = [plt.Line2D([], [], marker="o", color=c, ls="", mec="k", mew=0.3, label=d.replace("_", " ")) for d, c in COLOR.items()]
    # legend below the plot, so no point is hidden behind it (advisor comment, p6)
    ax.legend(handles=h1 + h2, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, framealpha=0.9)
    _save(fig, "fig1_rq1_twodim")


def fig2(rc):
    fig, ax = plt.subplots(figsize=(COL, COL * 0.78))
    ax.axhline(0, color="k", lw=0.5)
    for r in rc.itertuples():
        ax.scatter(r.premium_x, r.dQWK, s=34, marker=MARK.get(r.model, "o"), c=COLOR[r.domain], edgecolor="k", lw=0.3, alpha=0.85)
    ax.set_xscale("log")
    ax.set_xlabel("reasoning cost: ON/OFF token premium ($\\times$, log)")
    ax.set_ylabel("agreement change ($\\Delta$QWK)")
    _save(fig, "fig2_cost_vs_agreement")


def fig_panels(rc):
    """6.2b -- RQ1 trade as three aligned bar panels (replaces the fig1/fig2 scatters).
    One bar per model in each dataset group; read a vertical slice = one cell across all
    three metrics: agreement change, consistency change, token cost. Deterministic (no boot)."""
    order = [("mohler", "short_answer", "Mohler"), ("semeval", "short_answer", "SemEval"),
             ("riayn", "code", "RIAYN"), ("ptcs", "code", "PT-CS code"),
             ("ptcs", "short_answer", "PT-CS short")]
    models = list(MARK)  # qwen3.5, glm-5.1, deepseek-v4-flash, gpt-5.1
    lbl = [t[2] for t in order]
    x = np.arange(len(order)); w = 0.2

    def cell(ds, dom, m, col):
        r = rc[(rc.dataset == ds) & (rc.domain == dom) & (rc.model == m)]
        return float(r[col].iloc[0]) if len(r) else np.nan

    fig, axes = plt.subplots(1, 3, figsize=(WIDE, COL * 0.74))
    specs = [("dQWK", "agreement change, $\\Delta$QWK\n(above 0 = reasoning helps)", False),
             ("dSD", "consistency change\n(below 0 = less consistent)", False),
             ("premium_x", "output tokens, on/off ($\\times$)\nlog scale", True)]
    for ax, (col, ttl, logy), letter in zip(axes, specs, "abc"):
        for i, m in enumerate(models):
            # dSD plotted as stability change (off SD minus on SD): below 0 = reasoning is LESS
            # consistent, so it reads like the agreement panel (up = better, down = worse).
            vals = [cell(ds, dom, m, "SDk_off") - cell(ds, dom, m, "SDk_on") if col == "dSD"
                    else cell(ds, dom, m, col) for ds, dom, _ in order]
            ax.bar(x + (i - 1.5) * w, vals, w, color=MCOL[m], edgecolor="k", lw=0.3,
                   alpha=0.9, label=MNAME[m])
        ax.set_xticks(x); ax.set_xticklabels(lbl, rotation=30, ha="right")
        ax.set_ylabel(ttl)
        ax.set_title(f"({letter})", loc="left", fontsize=7.5)
        if logy:
            ax.set_yscale("log")
            ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        else:
            ax.axhline(0, color="k", lw=0.6)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, framealpha=0.9, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _save(fig, "fig_rq1_panels")


def _dims(full):
    """Bloco C contrasts from the table generator (one source for tables, figures and prose)."""
    from experiments.analysis.make_phase5_tables import dim_contrasts
    return dim_contrasts(full, _INTERV)


MNAME = {"qwen3.5": "Qwen3.5", "deepseek-v4-flash": "DeepSeek-V4-Flash", "gpt-5.1": "GPT-5.1", "glm-5.1": "GLM-5.1",
         "claude-sonnet-4-6": "Claude Sonnet 4.6", "glm-5.1-or": "GLM-5.1"}


def _grouped(ax, groups, models, get):
    """Grouped bars with 95% CI: one group per x label, one bar per model."""
    x = np.arange(len(groups)); w = 0.8 / len(models)
    for i, m in enumerate(models):
        vals = [get(g, m) for g in groups]
        md = [v["dQWK"] if v else np.nan for v in vals]
        lo = [v["dQWK"] - v["lo"] if v else 0 for v in vals]
        hi = [v["hi"] - v["dQWK"] if v else 0 for v in vals]
        pos = x + (i - (len(models) - 1) / 2) * w
        ax.bar(pos, md, w, color=MCOL[m], edgecolor="k", lw=0.3, alpha=0.9, label=MNAME[m])
        ax.errorbar(pos, md, yerr=[lo, hi], fmt="none", ecolor="k", elinewidth=0.6, capsize=1.5)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xticks(x)


def fig_rq2(full):
    """RQ2 evaluation-guidance benefit (dQWK none -> with guidance, 95% CI) per dataset and model
    (Qwen3.5, DeepSeek-V4-Flash, GPT-5.1; reasoning off). PT-CS = validated answers."""
    dc = _dims(full); g = dc[dc.family == "guidance"]
    groups = [("mohler", "Mohler"), ("semeval", "SemEval"), ("ptcs-short", "PT-CS\nshort"), ("riayn", "RIAYN"),
              ("ptcs", "PT-CS\ncode")]
    models = ["qwen3.5", "deepseek-v4-flash", "gpt-5.1"]
    get = lambda grp, m: (lambda r: r.iloc[0].to_dict() if len(r) else None)(g[(g.dataset == grp[0]) & (g.model == m)])
    fig, ax = plt.subplots(figsize=(COL, COL * 0.72))
    _grouped(ax, groups, models, get)
    ax.set_xticklabels([lbl for _, lbl in groups])
    ax.set_ylabel("agreement gain ($\\Delta$QWK)\nwith guidance vs none")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), framealpha=0.9, ncol=3)
    _save(fig, "fig_rq2_guidance")


def fig_rq3(full):
    """RQ3 scope (whole exam vs one question per call, PT-CS code) and decomposition (criterion vs
    holistic, RIAYN and PT-CS code), dQWK with 95% CI, per model (Qwen3.5, DeepSeek-V4-Flash; reasoning
    off). Dashed lines: the pre-registered equivalence margin of +/-0.05 QWK."""
    dc = _dims(full)
    groups = [("scope", "ptcs", "scope\nPT-CS code"), ("decomp", "riayn", "decomposition\nRIAYN"),
              ("decomp", "ptcs", "decomposition\nPT-CS code")]
    models = ["qwen3.5", "deepseek-v4-flash"]
    get = lambda grp, m: (lambda r: r.iloc[0].to_dict() if len(r) else None)(
        dc[(dc.family == grp[0]) & (dc.dataset == grp[1]) & (dc.model == m)])
    fig, ax = plt.subplots(figsize=(COL, COL * 0.62))
    _grouped(ax, groups, models, get)
    for y in (-0.05, 0.05):
        ax.axhline(y, color="#777", lw=0.6, ls="--")
    ax.set_xticklabels([lbl for _, _, lbl in groups])
    ax.set_ylabel("agreement change ($\\Delta$QWK)\n(below 0 = worse than baseline)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.27), framealpha=0.9, ncol=2)
    _save(fig, "fig_rq3_scope_decomp")


SETS = [("mohler", "short_answer", "Mohler"), ("semeval", "short_answer", "SemEval"),
        ("riayn", "code", "RIAYN"), ("ptcs", "code", "PT-CS code"), ("ptcs", "short_answer", "PT-CS short")]


def _paired_levels(ax, groups, models, get):
    """Absolute QWK on one common 0-1 axis (Pedro's review 2026-10-16): per group and model, a light bar for
    the starting setting and a dark hatched bar for the changed one, so the size of an effect can be compared
    across the RQ1, RQ2, RQ3 and RQ6 figures (bars of differences on per-figure axes had made a +0.07 look
    as large as a +0.30). get(group, model) -> (QWK start, QWK changed) or None."""
    x = np.arange(len(groups)); nb = 2 * len(models); w = 0.84 / nb
    for i, m in enumerate(models):
        for j in (0, 1):
            vals = np.array([(lambda v: v[j] if v else np.nan)(get(g, m)) for g in groups], dtype=float)
            pos = x + (2 * i + j - (nb - 1) / 2) * w
            ok = np.isfinite(vals)                      # a missing cell draws nothing (pgf cannot hatch NaN bars)
            ax.bar(pos[ok], vals[ok], w, color=MCOL[m], alpha=0.45 if j == 0 else 1.0, edgecolor="k", lw=0.3,
                   hatch="" if j == 0 else "///")
    ax.set_xticks(x); ax.set_ylim(0, 1)
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.2))
    ax.set_ylabel("agreement (QWK)")


def _level_legend(fig, models, start, changed, y=0.0, ncol=None):
    from matplotlib.patches import Patch
    h = [Patch(facecolor=MCOL[m], edgecolor="k", lw=0.3, label=MNAME[m]) for m in models]
    h += [Patch(facecolor="#bbb", alpha=0.45, edgecolor="k", lw=0.3, label=start),
          Patch(facecolor="#888", edgecolor="k", lw=0.3, hatch="///", label=changed)]
    fig.legend(handles=h, loc="upper center", ncol=ncol or len(h), bbox_to_anchor=(0.5, y), framealpha=0.9,
               handlelength=1.4, columnspacing=0.9)


def fig_rq1(rc):
    """RQ1 in one row (Pedro's review 2026-10-16; replaces fig_rq1_panels): (a) agreement with reasoning off
    and on, absolute QWK on the 0-1 axis shared with the RQ2, RQ3 and RQ6 figures; (b) what the change cost,
    the agreement change (95% CI) against the output-token multiplier on a log axis, with the +/-0.05
    equivalence band shaded; (c) consistency, within-item SD with reasoning on against off (above the
    diagonal = less consistent with reasoning). Values from rq1_cells: every sampled item, a reasoning run
    that overflowed carries the reasoning-off grade."""
    models = list(MARK)
    fig = plt.figure(figsize=(WIDE, COL * 0.80))
    gs = fig.add_gridspec(1, 3, width_ratios=[2.4, 1, 1], wspace=0.42)
    cell = lambda ds, dom, m: rc[(rc.dataset == ds) & (rc.domain == dom) & (rc.model == m)]
    get = lambda g, m: (lambda r: (float(r.QWK_off.iloc[0]), float(r.QWK_on.iloc[0])) if len(r) else None)(
        cell(g[0], g[1], m))
    ax = fig.add_subplot(gs[0])
    _paired_levels(ax, SETS, models, get)
    ax.set_xticklabels(["Mohler", "SemEval", "RIAYN", "PT-CS\ncode", "PT-CS\nshort"])
    ax.set_title("(a) agreement with the teachers", loc="left", fontsize=7)
    bx = fig.add_subplot(gs[1])
    bx.axhspan(-0.05, 0.05, color="#e3e3e3", lw=0, zorder=0)
    bx.axhline(0, color="k", lw=0.5)
    for r in rc.itertuples():
        bx.errorbar(r.premium_x, r.dQWK, yerr=[[r.dQWK - r.lo], [r.hi - r.dQWK]],
                    fmt="o" if r.domain == "short_answer" else "s", color=MCOL[r.model], mec="k", mew=0.3,
                    ms=3.6, elinewidth=0.5, capsize=1, zorder=3)
    bx.set_xscale("log")
    bx.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    bx.set_xlabel("output tokens, on/off ($\\times$)")
    bx.set_ylabel("agreement change ($\\Delta$QWK)")
    bx.set_title("(b) gain against cost", loc="left", fontsize=7)
    cx = fig.add_subplot(gs[2])
    lim = float(max(rc.SDk_off.max(), rc.SDk_on.max())) * 1.12
    cx.plot([0, lim], [0, lim], color="k", lw=0.5)
    for r in rc.itertuples():
        cx.scatter(r.SDk_off, r.SDk_on, marker="o" if r.domain == "short_answer" else "s", color=MCOL[r.model],
                   edgecolor="k", lw=0.3, s=14, zorder=3)
    cx.set_xlim(0, lim); cx.set_ylim(0, lim); cx.set_aspect("equal")
    cx.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3)); cx.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3))
    cx.set_xlabel("SD$_k$, reasoning off"); cx.set_ylabel("SD$_k$, reasoning on")
    cx.set_title("(c) consistency", loc="left", fontsize=7)
    from matplotlib.patches import Patch
    h = [Patch(facecolor=MCOL[m], edgecolor="k", lw=0.3, label=MNAME[m]) for m in models]
    h += [Patch(facecolor="#bbb", alpha=0.45, edgecolor="k", lw=0.3, label="reasoning off"),
          Patch(facecolor="#888", edgecolor="k", lw=0.3, hatch="///", label="reasoning on"),
          plt.Line2D([], [], marker="o", color="grey", ls="", mec="k", mew=0.3, label="short answers"),
          plt.Line2D([], [], marker="s", color="grey", ls="", mec="k", mew=0.3, label="code")]
    fig.legend(handles=h, loc="upper center", ncol=4, bbox_to_anchor=(0.5, -0.1), framealpha=0.9,
               handlelength=1.6, columnspacing=1.4)
    _save(fig, "fig_rq1")


def fig_rq2_levels(full):
    """RQ2 on the shared 0-1 axis (2026-10-16; replaces the dQWK bars): QWK without guidance (light) and
    with it (hatched), per set and model, reasoning off, on every item graded both ways. The differences
    with their CIs are in the text (dim_contrasts)."""
    b = full[(full.reasoning == "off") & (full.scope == "question_by_question") & (full.decomposition == "holistic")]
    b = b[(b.dataset != "ptcs") | b.item_id.isin(_INTERV)]
    models = ["qwen3.5", "deepseek-v4-flash", "gpt-5.1"]

    def get(g, m):
        c = b[(b.dataset == g[0]) & (b.domain == g[1]) & (b.model == m)]
        a, z = c[c.context_level == "none"], c[c.context_level == "with_guidance"]
        if a.empty or z.empty:
            return None
        common = set(a.item_id) & set(z.item_id)
        return _qwk(_itemmeans(a[a.item_id.isin(common)])), _qwk(_itemmeans(z[z.item_id.isin(common)]))
    fig, ax = plt.subplots(figsize=(COL, COL * 0.66))
    _paired_levels(ax, SETS, models, get)
    ax.set_xticklabels(["Mohler", "SemEval", "RIAYN", "PT-CS\ncode", "PT-CS\nshort"])
    fig.tight_layout()
    _level_legend(fig, models, "no guidance", "with guidance", y=0.0, ncol=3)
    _save(fig, "fig_rq2_guidance")


def fig_rq3_levels(full):
    """RQ3 on the shared 0-1 axis (2026-10-16): QWK of the baseline shape (one question per call, holistic;
    light) and of the alternative (hatched): the whole exam in one call (PT-CS code) and criterion-by-criterion
    scoring (RIAYN, PT-CS code), per model, reasoning off, on the items graded both ways."""
    b = full[(full.reasoning == "off") & (full.context_level == "with_guidance") & (full.domain == "code")]
    b = b[(b.dataset != "ptcs") | b.item_id.isin(_INTERV)]
    models = [m for m in ["qwen3.5", "deepseek-v4-flash", "gpt-5.1"]
              if ((b.model == m) & ((b.scope == "whole_exam") | (b.decomposition == "criterion"))).any()]
    groups = [("scope", "ptcs"), ("decomp", "riayn"), ("decomp", "ptcs")]

    def get(g, m):
        c = b[(b.dataset == g[1]) & (b.model == m)]
        a = c[(c.scope == "question_by_question") & (c.decomposition == "holistic")]
        z = (c[(c.scope == "whole_exam") & (c.decomposition == "holistic")] if g[0] == "scope"
             else c[(c.scope == "question_by_question") & (c.decomposition == "criterion")])
        if a.empty or z.empty:
            return None
        common = set(a.item_id) & set(z.item_id)
        return _qwk(_itemmeans(a[a.item_id.isin(common)])), _qwk(_itemmeans(z[z.item_id.isin(common)]))
    fig, ax = plt.subplots(figsize=(COL, COL * 0.62))
    _paired_levels(ax, groups, models, get)
    ax.set_xticklabels(["whole exam\nPT-CS code", "per criterion\nRIAYN", "per criterion\nPT-CS code"])
    fig.tight_layout()
    _level_legend(fig, models, "one question, holistic", "alternative", y=0.0, ncol=3)
    _save(fig, "fig_rq3_scope_decomp")


def fig_rq6_instruction():
    """RQ6 grading instruction (Pedro's review 2026-10-16): (a) QWK with the strict instruction (light) and with
    explicit partial credit (hatched), per set and model, reasoning off, on the 0-1 axis shared with Figs.
    rq1-rq3; (b) share of code grades that are exactly zero under each instruction, with the teachers' share.
    Values from experiments.analysis.instruction (GPT-5.1's strict cells are its main-store rows)."""
    from experiments.analysis import instruction as I
    lv = I.levels(I.load())
    lv = lv[lv.instruction.isin(["standard", "partial_credit"])]
    models = [m for m in ["qwen3.5", "deepseek-v4-flash", "glm-5.1-or", "gpt-5.1", "claude-sonnet-4-6"]
              if ((lv.model == m) & (lv.instruction == "partial_credit")).any()]

    def get(g, m):
        c = lv[(lv.dataset == g[0]) & (lv.domain == g[1]) & (lv.model == m)].set_index("instruction")
        return (float(c.QWK["standard"]), float(c.QWK["partial_credit"])) if {"standard", "partial_credit"} <= set(c.index) else None
    fig = plt.figure(figsize=(WIDE, COL * 0.80))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.6, 1], wspace=0.30)
    ax = fig.add_subplot(gs[0])
    _paired_levels(ax, SETS, models, get)
    ax.set_xticklabels(["Mohler", "SemEval", "RIAYN", "PT-CS\ncode", "PT-CS\nshort"])
    ax.set_title("(a) agreement with the teachers", loc="left", fontsize=7)
    bx = fig.add_subplot(gs[1])
    code = [("riayn", "RIAYN"), ("ptcs", "PT-CS code")]
    x = np.arange(len(code)); nb = 2 * len(models); w = 0.84 / nb
    for i, m in enumerate(models):
        for j, ins in enumerate(["standard", "partial_credit"]):
            vals = np.array([(lambda c: float(c.zero_pct.iloc[0]) if len(c) else np.nan)(
                lv[(lv.dataset == ds) & (lv.domain == "code") & (lv.model == m) & (lv.instruction == ins)]) for ds, _ in code])
            pos = x + (2 * i + j - (nb - 1) / 2) * w; ok = np.isfinite(vals)
            bx.bar(pos[ok], vals[ok], w, color=MCOL[m], alpha=0.45 if j == 0 else 1.0,
                   edgecolor="k", lw=0.3, hatch="" if j == 0 else "///")
    for k, (ds, _) in enumerate(code):
        t = lv[(lv.dataset == ds) & (lv.domain == "code")].teacher_zero_pct.iloc[0]
        bx.hlines(t, k - 0.45, k + 0.45, color="k", lw=1.0, ls="--")
    bx.set_xticks(x); bx.set_xticklabels([lbl for _, lbl in code])
    bx.set_ylabel("grades of exactly zero (\\%)")
    bx.set_title("(b) zeros on code (dashed: teachers)", loc="left", fontsize=7)
    _level_legend(fig, models, "strict instruction", "partial credit", y=-0.02, ncol=len(models) + 2)
    _save(fig, "fig_rq6_instruction")


def _common_items(full):
    """Items graded (with a parseable grade) by all eight configurations, model x reasoning, within each
    (dataset, domain), on the paper basis: with guidance, one question per call, holistic, PT-CS validated.
    The RQ4 and RQ6 figures compare configurations on these items only, the same rule as the guide's regret
    table (bloco_c.c10), so reasoning-off and reasoning-on configurations are never scored on different
    items (audit 2026-10-16: mixing all items with the reasoning samples had shifted levels by up to 0.10)."""
    b = full[(full.context_level == "with_guidance") & (full.scope == "question_by_question")
             & (full.decomposition == "holistic") & full.pred_norm.notna()]
    b = b[(b.dataset != "ptcs") | b.item_id.isin(_INTERV)]
    keep = set()
    for _, g in b.groupby(["dataset", "domain"]):
        sets = [set(h.item_id) for _, h in g.groupby(["model", "reasoning"])]
        if len(sets) == 8:
            keep |= set.intersection(*sets)
    return keep


def fig_rq4_cost(full):
    """RQ4 cost-quality BY TASK: QWK vs euro cost per 1000 grades (log), one point per model x
    reasoning, in two panels (short-answer = Mohler+SemEval; code = RIAYN), shared y so the
    short-answer cluster vs the code spread reads directly. QWK via the table generator's _qwk_items;
    cost from the logged per-call cost_eur (engine-backed). Deterministic. Single column, side by side."""
    from experiments.analysis.make_phase5_tables import _qwk_items as _qi
    base = full[(full.context_level == "with_guidance") & (full.scope == "question_by_question")
                & (full.decomposition == "holistic") & full.dataset.isin(["mohler", "semeval", "riayn"])].copy()
    base["ce"] = pd.to_numeric(base.get("cost_eur"), errors="coerce")   # cost per grade: all graded calls
    common = _common_items(full)                                         # QWK: items all configs graded
    models = ["qwen3.5", "glm-5.1", "deepseek-v4-flash", "gpt-5.1"]
    mk = {"off": "o", "on": "s"}
    fig, axes = plt.subplots(2, 1, figsize=(COL, COL * 1.05), sharey=True, sharex=True)
    panels = [("(a) short answers (Mohler, SemEval)", ["mohler", "semeval"]), ("(b) code (RIAYN)", ["riayn"])]
    for ax, (title, dsets) in zip(axes, panels):
        sub = base[base.dataset.isin(dsets)]
        for m in models:
            for rs in ["off", "on"]:
                cell = sub[(sub.model == m) & (sub.reasoning == rs)]
                qs = [_qi(cell[(cell.dataset == d) & cell.item_id.isin(common)])[0] for d in dsets]
                qs = [q for q in qs if q == q]
                if not qs:
                    continue
                ax.scatter(cell.ce.mean() * 1000, np.mean(qs), s=30, marker=mk[rs], color=MCOL[m],
                           edgecolor="k", lw=0.3, alpha=0.9, zorder=3)
        ax.set_xscale("log"); ax.set_title(title, loc="left", fontsize=7)
        ax.set_ylabel("agreement (QWK)")
        ax.set_xticks([0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30])
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axes[1].set_xlabel("cost of 1000 grades (euros, log scale)")
    h1 = [plt.Line2D([], [], marker="o", color=MCOL[m], ls="", mec="k", mew=0.4, label=MNAME[m])
          for m in models]
    h2 = [plt.Line2D([], [], marker=mk[r], color="grey", ls="", mec="k", mew=0.4, label=f"reasoning {r}")
          for r in ["off", "on"]]
    fig.tight_layout()
    fig.legend(handles=h1 + h2, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 0.0), framealpha=0.9)
    _save(fig, "fig_rq4_cost")


def fig_rq6_transfer(full):
    """6.8 -- RQ6 transfer slopegraph, WITHIN DOMAIN: does the configuration ranking learned on the
    public datasets hold on the PT-CS deployment data, separately for short answers and for code.
    Left panel: public short-answer (mean over Mohler, SemEval) -> PT-CS-verified short answers. Right
    panel: public code (RIAYN) -> PT-CS-verified code. One line per configuration; since C5 (2026-10-15)
    GPT-5.1 covers the same items as the open models and is ranked like them. The public ranking uses public
    data ONLY -- PT-CS is never in it -- so the comparison is a genuine out-of-public-sample check, and
    domain is matched on both sides (no short/code mixing). Built from the run data, K=5 item means,
    with-guidance / question-by-question / holistic; verified = intervened stratum. Single column."""
    base = full[(full.context_level == "with_guidance") & (full.scope == "question_by_question")
                & (full.decomposition == "holistic")]

    common = _common_items(full)

    def q_pub(g, dsets):
        return float(np.nanmean([_qwk(_itemmeans(g[(g.dataset == ds) & g.item_id.isin(common)])) for ds in dsets]))

    def q_ver(g, dom):
        return _qwk(_itemmeans(g[(g.dataset == "ptcs") & (g.domain == dom) & g.item_id.isin(_INTERV)
                                 & g.item_id.isin(common)]))

    from scipy.stats import spearmanr
    panels = [("(a) short answers", ["mohler", "semeval"], "short_answer"), ("(b) code", ["riayn"], "code")]
    fig, axes = plt.subplots(1, 2, figsize=(COL, COL * 0.62), sharey=True)
    for ax, (title, pub_ds, dom) in zip(axes, panels):
        pub_all, ver_all = [], []
        for m in ["qwen3.5", "glm-5.1", "deepseek-v4-flash", "gpt-5.1"]:
            for r in ["off", "on"]:
                g = base[(base.model == m) & (base.reasoning == r)]
                ys = [q_pub(g, pub_ds), q_ver(g, dom)]
                pub_all.append(ys[0]); ver_all.append(ys[1])
                ax.plot([0, 1], ys, color=MCOL[m], ls="-" if r == "on" else "--", lw=1.4, marker=MARK[m],
                        ms=4.5, mfc=(MCOL[m] if r == "on" else "w"), mec=MCOL[m], mew=0.8, alpha=0.95)
        rho = spearmanr(pub_all, ver_all).statistic                 # rank transfer over the 8 configurations
        ax.text(0.04, 0.03, f"rank $\\rho={rho:.2f}$", transform=ax.transAxes, ha="left", va="bottom",
                fontsize=6.5, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#bbb", lw=0.4))
        ax.set_xticks([0, 1]); ax.set_xticklabels(["public", "PT-CS"])
        ax.set_xlim(-0.3, 1.3); ax.set_title(title, loc="left", fontsize=7); ax.set_box_aspect(1)
    axes[0].set_ylabel("agreement (QWK, K=5)")
    mh = [plt.Line2D([], [], color=MCOL[m], marker=MARK[m], ls="-", mec=MCOL[m], label=MNAME[m])
          for m in ["qwen3.5", "glm-5.1", "deepseek-v4-flash", "gpt-5.1"]]
    rh = [plt.Line2D([], [], color="grey", ls="-", label="reasoning on"),
          plt.Line2D([], [], color="grey", ls="--", label="reasoning off")]
    fig.tight_layout()
    fig.legend(handles=mh + rh, loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.01), framealpha=0.9, fontsize=5)
    _save(fig, "fig_rq6_transfer")


def fig3(df):
    # Single-column (figure, not figure*): compact enough to sit by its RQ4 text. 32 bars (4 datasets
    # x 4 models x off/on), so it runs tall to keep the bars and CIs legible. (A full-width variant
    # was tried but always drifted to the next page, away from RQ4 -- §11 / git.)
    base = df[(df.context_level == "with_guidance") & (df.scope == "question_by_question") & (df.decomposition == "holistic")]
    base = base[base.item_id.isin(_common_items(df))]     # items every configuration graded (as RQ6, Table V)
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
                   hatch="" if rs == "off" else "//", label=f"{MNAME[m]} {rs}")
            ax.errorbar(pos, qs, yerr=[los, his], fmt="none", ecolor="k", elinewidth=0.5, capsize=1.2)
    ax.set_xticks(x); ax.set_xticklabels([{"mohler": "Mohler", "semeval": "SemEval", "riayn": "RIAYN", "ptcs": "PT-CS"}[d] for d in dsets]); ax.set_ylabel("agreement (QWK, K=5)")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.13), framealpha=0.9, fontsize=5,
              columnspacing=0.8, handlelength=1.6)
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
    ax.set_xticks(x); ax.set_xticklabels([{"mohler": "Mohler", "semeval": "SemEval", "riayn": "RIAYN", "ptcs": "PT-CS"}[d] for d in dsets])
    ax.set_ylabel("within-item SD across $k$\n(lower = more consistent)")
    ax.legend(framealpha=0.9)
    _save(fig, "fig4_consistency")


def fig5(df):
    """RQ5 conversation sub-study, two panels with 95% bootstrap CIs over items, per model:
    (a) shared minus clean conversation (item-mean grade; below 0 = shared history lowers grades);
    (b) answer order within the shared conversation: the typical size of the change, mean |natural minus
    inverse| (solid), and the average shift, mean (natural minus inverse) (hatched).
    Qwen3.5 and DeepSeek-V4-Flash: 80 exams, k=5 (2026-10-15); GLM-5.1: the first 20 of those exams, k=3
    (June 2026). PT-CS code, baseline configuration; no teacher grades are involved."""
    cv = phase5.load_conversation()
    cv = cv[cv.pred_norm.notna()]
    mods = ["qwen3.5", "deepseek-v4-flash", "glm-5.1"]
    lab = {"qwen3.5": "Qwen3.5", "deepseek-v4-flash": "DeepSeek-V4-Flash", "glm-5.1": "GLM-5.1 (20 exams)"}
    rng = np.random.default_rng(20260610)

    def boot(v):
        v = np.asarray(v); b = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(800)]
        return v.mean(), *np.percentile(b, [2.5, 97.5])

    st, oa, osg = [], [], []
    for m in mods:
        d = cv[cv.model == m]
        pv = d.pivot_table(index="item_id", columns="conversation_state", values="pred_norm", aggfunc="mean").dropna()
        st.append(boot(pv["shared"] - pv["clean"]))
        sh = d[d.conversation_state == "shared"]
        po = sh.pivot_table(index=["item_id", "run_index"], columns="order_id", values="pred_norm", aggfunc="first").dropna()
        oa.append(boot((po["natural"] - po["inverse"]).abs())); osg.append(boot(po["natural"] - po["inverse"]))
    fig, axes = plt.subplots(1, 2, figsize=(COL, COL * 0.62), gridspec_kw={"width_ratios": [1, 1.2]})
    x = np.arange(len(mods))

    def bars(ax, vals, pos, w, **kw):
        md = [v[0] for v in vals]
        ax.bar(pos, md, w, edgecolor="k", lw=0.3, **kw)
        ax.errorbar(pos, md, yerr=[[v[0] - v[1] for v in vals], [v[2] - v[0] for v in vals]],
                    fmt="none", ecolor="k", elinewidth=0.6, capsize=1.5)

    bars(axes[0], st, x, 0.6, color=[MCOL[m] for m in mods], alpha=0.9)
    axes[0].axhline(0, color="k", lw=0.6)
    axes[0].set_ylabel("grade change (fraction of scale)")
    axes[0].set_title("(a) shared minus clean", loc="left", fontsize=7)
    bars(axes[1], oa, x - 0.18, 0.34, color=[MCOL[m] for m in mods], alpha=0.9, label="typical size")
    bars(axes[1], osg, x + 0.18, 0.34, color="white", hatch="////", label="average shift")
    axes[1].axhline(0, color="k", lw=0.6)
    axes[1].set_title("(b) answer order", loc="left", fontsize=7)
    axes[1].set_ylim(-0.03, 0.16)
    axes[1].legend(loc="upper left", framealpha=0.9, fontsize=5, ncol=2)
    for ax in axes:
        ax.set_xticks(x); ax.set_xticklabels([lab[m] for m in mods], rotation=30, ha="right", fontsize=5.5)
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
    # RQ1 cells come from the table generator's rq1_cells, so the RQ1 figure plots exactly the values of
    # the RQ1 table and prose (every sampled item; an overflowed reasoning run carries the reasoning-off
    # grade, phase5.apply_reasoning_fallback), PT-CS on the verified stratum.
    # Pedro's review (2026-10-16): fig_rq1 replaces fig_rq1_panels; RQ2/RQ3 show absolute QWK on the same
    # 0-1 axis; fig3 (per dataset) became panel (a) of fig_rq1; fig_rq6_transfer left the paper with RQ6.
    from experiments.analysis.make_phase5_tables import rq1_cells
    _full = phase5.load_main()
    rc = rq1_cells(_full, _INTERV).rename(columns={"prem_x": "premium_x"})
    fig_rq1(rc); fig_rq2_levels(_full); fig_rq3_levels(_full); fig_rq4_cost(_full); fig5(df)
    fig_rq6_instruction()
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
