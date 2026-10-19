"""Phase 5.7 — generate the tidy result tables (LaTeX) into article/tables/.

One table per claim, paired-subset N stated, SemEval per split. Recomputes from the run
stores via the §5.0 conventions (clamp / normalise / K=5 / pairing). NOT hand-edited.

  python -m experiments.analysis.make_phase5_tables
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from experiments.analysis import phase5

K = 5
SEED = 20260610          # every bootstrap call gets a FRESH generator with this seed (2026-06-11):
TABLES = phase5.REPO_ROOT / "article" / "tables"
# call-order independence -- inserting a new table/contrast no longer shifts the CI digits of
# the others (the old module-level rolling RNG made every CI depend on its position in main()).


def _qwk_items(d):
    s = d[d.pred_norm.notna() & d.gold_norm.notna()].groupby("item_id").agg(p=("pred_norm", "mean"), g=("gold_norm", "mean"))
    if len(s) < 8:
        return np.nan, s
    po = phase5.to_levels(s.p, K)
    go = phase5.to_levels(s.g, K)
    return cohen_kappa_score(go, po, weights="quadratic", labels=list(range(K + 1))), s


NB = 10_000              # bootstrap resamples (independent review, 2026-10-18: 800 left the significance of
                         # results near zero, and Holm's smallest thresholds, to one or two resamples)
_W = (np.subtract.outer(np.arange(K + 1), np.arange(K + 1)) ** 2).astype(float)


def _levels(x) -> np.ndarray:
    """Six ordered levels of a 0-1 score; halves go to the even level (numpy's rounding, stated in Method)."""
    return phase5.to_levels(x, K)


def _kappas(counts: np.ndarray) -> np.ndarray:
    """Quadratic weighted kappa of each (L x L) confusion matrix in a (B, L, L) stack (gold rows, grader columns)."""
    n = counts.sum(axis=(1, 2))
    exp = counts.sum(axis=2)[:, :, None] * counts.sum(axis=1)[:, None, :] / n[:, None, None]
    return 1 - (counts * _W).sum(axis=(1, 2)) / (exp * _W).sum(axis=(1, 2))


def _common(sA, sB):
    items = sorted(set(sA.index) & set(sB.index))
    a, b = sA.loc[items], sB.loc[items]
    return items, _levels(a.g) * (K + 1) + _levels(a.p), _levels(a.g) * (K + 1) + _levels(b.p)


def _point(sA, sB) -> float:
    """dQWK = QWK(B) - QWK(A) on the common items: the estimate every table, figure and sentence reports."""
    items, ca, cb = _common(sA, sB)
    if len(items) < 8:
        return np.nan
    L2 = (K + 1) ** 2
    cnt = np.stack([np.bincount(ca, minlength=L2), np.bincount(cb, minlength=L2)]).reshape(2, K + 1, K + 1)
    qa, qb = _kappas(cnt.astype(float))
    return float(qb - qa)


def _boot_dist(sA, sB, nb=NB):
    """Bootstrap distribution of dQWK = QWK(B)-QWK(A) over common items (item means already computed): the items
    are resampled with replacement nb times, with a fresh generator seeded with SEED."""
    items, ca, cb = _common(sA, sB)
    n = len(items)
    if n < 8:
        return None
    rng = np.random.default_rng(SEED)
    L2 = (K + 1) ** 2
    out = []
    for start in range(0, nb, 500):
        m = min(500, nb - start)
        idx = rng.integers(0, n, (m, n))
        off = (np.arange(m) * L2)[:, None]
        qa = _kappas(np.bincount((off + ca[idx]).ravel(), minlength=m * L2).reshape(m, K + 1, K + 1).astype(float))
        qb = _kappas(np.bincount((off + cb[idx]).ravel(), minlength=m * L2).reshape(m, K + 1, K + 1).astype(float))
        out.append(qb - qa)
    return np.concatenate(out)


def _boot_ci(sA, sB, nb=NB):
    """dQWK = QWK(B)-QWK(A) over common items: (2.5% bootstrap bound, point estimate, 97.5% bootstrap bound)."""
    ds = _boot_dist(sA, sB, nb)
    if ds is None:
        return (np.nan, np.nan, np.nan)
    lo, hi = np.percentile(ds, [2.5, 97.5])
    return (lo, _point(sA, sB), hi)


def _sd_change(o, n, nb=NB) -> tuple[float, float]:
    """95% bootstrap interval of the change in mean within-item SD, reasoning on minus off, over the items
    with an SD in both modes (the same resampling as _boot_dist; fallback grades left out, as in SD_k)."""
    def sd(d):
        d = d[d.pred_norm.notna()]
        if "fallback" in d:
            d = d[~d["fallback"].astype(bool)]
        return d.groupby("item_id").pred_norm.std().dropna()
    so, sn = sd(o), sd(n)
    items = sorted(set(so.index) & set(sn.index))
    if len(items) < 8:
        return (np.nan, np.nan)
    diff = (sn.loc[items] - so.loc[items]).to_numpy()
    rng = np.random.default_rng(SEED)
    means = np.concatenate([diff[rng.integers(0, len(items), (min(500, nb - s), len(items)))].mean(axis=1)
                            for s in range(0, nb, 500)])
    lo, hi = np.percentile(means, [2.5, 97.5])
    return (float(lo), float(hi))


def _p_boot(ds) -> float:
    """Two-sided bootstrap p for dQWK = 0: twice the share of resamples on the far side of zero (floor 1/nb)."""
    return float(max(2 * min((ds <= 0).mean(), (ds >= 0).mean()), 1 / len(ds)))


def _holm(ps: list[float]) -> list[float]:
    """Holm-adjusted p-values, in the input order."""
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


MARGIN = 0.05            # pre-registered equivalence margin (QWK), user 2026-10-15 (CLAUDE.md §11)


def _contrast(A, B) -> dict:
    """dQWK B vs A with bootstrap CI, p, N and TOST equivalence at +/-MARGIN (90% CI inside the margin)."""
    _, sA = _qwk_items(A); _, sB = _qwk_items(B)
    if isinstance(sA, float) or isinstance(sB, float) or len(sA) < 8 or len(sB) < 8:
        return {}
    ds = _boot_dist(sA, sB)
    if ds is None:
        return {}
    lo, hi = np.percentile(ds, [2.5, 97.5]); lo90, hi90 = np.percentile(ds, [5, 95])
    return {"dQWK": _point(sA, sB), "lo": lo, "hi": hi, "N": len(set(sA.index) & set(sB.index)), "p": _p_boot(ds),
            "sig": bool(lo > 0 or hi < 0), "equiv": bool(-MARGIN < lo90 and hi90 < MARGIN),
            "QWK_A": _qwk_items(A[A.item_id.isin(set(sA.index) & set(sB.index))])[0]}


def dim_contrasts(df: pd.DataFrame, interv: set) -> pd.DataFrame:
    """Bloco C contrasts on the paper basis (PT-CS = validated answers), reasoning off, one source for the
    RQ2/RQ3 figures, the framework rows and the prose (2026-10-15). Families (Holm within each):
      guidance  none -> with guidance, per model x dataset (Qwen3.5, DeepSeek-V4-Flash, GPT-5.1); PT-CS
                appears twice, code ("ptcs") and short answers ("ptcs-short", added 2026-10-15: the
                runs existed but the contrast had been left out)
      decomp    holistic -> criterion, per model x code dataset (Qwen3.5, DeepSeek-V4-Flash, GPT-5.1)
      scope     question by question -> whole exam, per model (Qwen3.5, DeepSeek-V4-Flash, GPT-5.1), the
                exam questions that belong to PT-CS. GPT-5.1 joined RQ3 on 2026-10-16 (Pedro's review)."""
    d = df[((df.dataset != "ptcs") | df.item_id.isin(interv)) & (df.reasoning == "off")]
    rows = []
    q = d[(d.scope == "question_by_question") & (d.decomposition == "holistic")]
    for m in ["qwen3.5", "deepseek-v4-flash", "gpt-5.1"]:
        for ds, dom, key in [("mohler", "short_answer", "mohler"), ("semeval", "short_answer", "semeval"),
                             ("riayn", "code", "riayn"), ("ptcs", "code", "ptcs"), ("ptcs", "short_answer", "ptcs-short")]:
            c = q[(q.model == m) & (q.dataset == ds) & (q.domain == dom)]
            r = _contrast(c[c.context_level == "none"], c[c.context_level == "with_guidance"])
            if r:
                rows.append({"family": "guidance", "model": m, "dataset": key, **r})
    g = d[(d.context_level == "with_guidance") & (d.scope == "question_by_question") & (d.domain == "code")]
    for m in ["qwen3.5", "deepseek-v4-flash", "gpt-5.1"]:
        for ds in ["riayn", "ptcs"]:
            c = g[(g.model == m) & (g.dataset == ds)]
            r = _contrast(c[c.decomposition == "holistic"], c[c.decomposition == "criterion"])
            if r:
                rows.append({"family": "decomp", "model": m, "dataset": ds, **r})
    for m in ["qwen3.5", "deepseek-v4-flash", "gpt-5.1"]:
        w = d[(d.scope == "whole_exam") & (d.model == m)]
        qb = d[(d.model == m) & (d.dataset == "ptcs") & (d.domain == "code") & (d.context_level == "with_guidance")
               & (d.scope == "question_by_question") & (d.decomposition == "holistic") & d.item_id.isin(set(w.item_id))]
        r = _contrast(qb, w)
        if r:
            rows.append({"family": "scope", "model": m, "dataset": "ptcs", **r})
    out = pd.DataFrame(rows)
    out["p_holm"] = np.nan
    for fam, idx in out.groupby("family").groups.items():
        out.loc[idx, "p_holm"] = _holm(list(out.loc[idx, "p"]))
    out["sig_holm"] = out.p_holm < 0.05
    return out


def rq1_cells(df: pd.DataFrame, interv: set) -> pd.DataFrame:
    """RQ1 per (dataset, domain, model): the single source for the RQ1 values table and figures. PT-CS
    rows use the verified (intervened) stratum.
      - dQWK, CI, QWK_off, N: every paired item (the reasoning samples), bootstrap median. Since
        2026-10-16 (Pedro's review) there is no 'tractable items' exclusion: a reasoning-on run whose
        trace overflowed carries the same model's reasoning-off grade (phase5.apply_reasoning_fallback).
      - fallback_pct: share of reasoning-on runs that fell back (the overflow rate, a cost of reasoning).
      - pct: dQWK as a percent of QWK_off (audit only; the paper quotes no QWK percentages).
      - SDk_off/on and prem_x: all paired items (overflowed runs were still generated and paid for)."""
    dv = df[(df.dataset != "ptcs") | df.item_id.isin(interv)]
    rp = phase5.reasoning_paired(dv)
    base = rp[(rp.context_level == "with_guidance") & (rp.scope == "question_by_question") & (rp.decomposition == "holistic")]
    rc = phase5.reasoning_contrast(dv).set_index(["dataset", "domain", "model"])
    rows = []
    for (ds, dom, m), g in base.groupby(["dataset", "domain", "model"]):
        o, n = g[g.reasoning == "off"], g[g.reasoning == "on"]
        if o.empty or n.empty:
            continue
        items = set(n.item_id.unique())          # every paired item; overflowed runs carry the off grade
        qoff, sA = _qwk_items(o[o.item_id.isin(items)]); qon, sB = _qwk_items(n[n.item_id.isin(items)])
        dist = _boot_dist(sA, sB)
        lo, hi = np.percentile(dist, [2.5, 97.5]); md = _point(sA, sB)
        prem = (pd.to_numeric(n.completion_tokens, errors="coerce").mean()
                / max(pd.to_numeric(o.completion_tokens, errors="coerce").mean(), 1))
        r = rc.loc[(ds, dom, m)]
        sd_lo, sd_hi = _sd_change(o[o.item_id.isin(items)], n[n.item_id.isin(items)])
        rows.append({"dataset": ds, "domain": dom, "model": m, "N": len(items), "QWK_off": qoff, "QWK_on": qon,
                     "sd_sig_up": bool(sd_lo > 0), "sd_sig_down": bool(sd_hi < 0),
                     "fallback_pct": 100 * float(n["fallback"].mean()) if "fallback" in n else 0.0,
                     "dQWK": md, "lo": lo, "hi": hi, "pct": 100 * md / qoff if qoff else np.nan,
                     "sig": bool(lo > 0 or hi < 0), "prem_x": prem, "p": _p_boot(dist),
                     "SDk_off": r.SDk_off, "SDk_on": r.SDk_on})
    out = pd.DataFrame(rows)
    out["p_holm"] = _holm(list(out.p))                  # Holm across all model x dataset combinations
    out["sig_holm"] = out.p_holm < 0.05
    return out


def _tex(df, path, caption, label, star=False, colspec=None, size="\\small", placement=None,
         rowsep=None, rowrule=False, head_pre=None):
    """star=True emits table* (two-column span, IEEEtran) for tables too wide for one column;
    colspec overrides the default all-'l' spec (e.g. p{} columns so long prose cells wrap);
    placement overrides the default float specifier (e.g. '!ht' to let a single-column table sit
    in-column next to its reference instead of only at a page top);
    rowsep (e.g. '3pt') adds vertical space between body rows so multi-line cells in adjacent rows
    stay visually separated (a wrapped line cannot be mistaken for a new row);
    rowrule=True draws a horizontal rule between every body row (same purpose, stronger separation);
    head_pre is a raw LaTeX line set above the column names (e.g. \\multicolumn group heads).
    Layout-only knobs (Phase 7.2): cell CONTENT is unchanged by any of them."""
    cols = list(df.columns)
    rs = f" \\\\[{rowsep}]" if rowsep else " \\\\"
    head = " & ".join(str(c) for c in cols) + " \\\\"
    lines = [" & ".join(str(v) for v in r) + rs for r in df.itertuples(index=False)]
    joiner = "\n\\hline\n" if rowrule else "\n"
    body = ("\\begin{tabular}{" + (colspec or "l" * len(cols)) + "}\n\\hline\n" + (head_pre + "\n" if head_pre else "") + head
            + "\n\\hline\n" + joiner.join(lines) + "\n\\hline\n\\end{tabular}")
    env = "table*" if star else "table"
    # every float follows its first reference: full width at the bottom of that page or the top of the
    # next, one column right after it (Pedro, 2026-10-18; checked by article/tools/check_floats.py)
    plc = placement or ("!tb" if star else "!htb")
    (TABLES / path).write_text(
        f"% auto-generated by make_phase5_tables.py -- do not hand-edit\n"
        f"\\begin{{{env}}}[{plc}]\\centering{size}\n\\caption{{{caption}}}\\label{{{label}}}\n"
        + body + f"\n\\end{{{env}}}\n")
    print(f"  wrote {path} ({len(df)} rows)")


def _assert_framework_ranges(prem_by, sdk_by, r_overall, r_discrim_code, r_qwen_sdk):
    """🟡-3 (§11 2026-06-11): the tab_framework composite ranges are kept as inline literals, but
    this test recomputes each from the engine-captured premiums/SDk and FAILS LOUDLY if a literal
    has drifted from the data. Runs as part of `make analyse` (make_phase5_tables.main)."""
    def fmt(lo, hi):                       # render an integer range the way the table does
        return f"{int(round(lo))}--{int(round(hi))}"
    discrim = [prem_by[k] for k in prem_by if k[1] == "code" and k[2] in ("glm-5.1", "deepseek-v4-flash")]   # the two models that do not collapse
    overall = list(prem_by.values())
    qsdk = [on / off for (ds, dom, m), (off, on) in sdk_by.items()
            if dom == "code" and m == "qwen3.5" and off]                              # Qwen-code SDk on/off
    half = lambda x: round(x * 2) / 2                                                 # round to nearest 0.5
    checks = {
        "overall premium": (r_overall, fmt(min(overall), max(overall))),
        "discriminating-code premium": (r_discrim_code, fmt(min(discrim), max(discrim))),
        "Qwen-code SDk ratio": (r_qwen_sdk, f"{half(min(qsdk)):g}--{half(max(qsdk)):g}"),
    }
    bad = {k: v for k, v in checks.items() if v[0] != v[1]}
    if bad:
        raise AssertionError(f"tab_framework composite literals drifted from the engine: "
                             + "; ".join(f"{k}: literal '{lit}' but engine '{got}'" for k, (lit, got) in bad.items()))
    print(f"  framework range test OK: {', '.join(f'{k}={v[1]}' for k, v in checks.items())}")


def main() -> int:
    TABLES.mkdir(parents=True, exist_ok=True)
    df = phase5.load_main()
    interv = set(pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "_ptcs_strata.parquet")
                 .query("stratum=='intervened'").item_id)
    print("Phase 5.7 tables ->", TABLES)

    # --- T1: RQ1 reasoning contrast (clean-only dQWK + CI, cost premium, consistency).
    #     Hybrid PT-CS rule (§11 2026-06-11): PT-CS contrasts are full-N primary + a verified
    #     (intervened-stratum) robustness column; '--' for the public datasets. ---
    rp = phase5.reasoning_paired(df)
    base = rp[(rp.context_level == "with_guidance") & (rp.scope == "question_by_question") & (rp.decomposition == "holistic")]
    rows = []
    prem_by, sdk_by, dqwk_by = {}, {}, {}     # captured for the framework table + its range test (§11 2026-06-11)
    for (ds, dom, m), g in base.groupby(["dataset", "domain", "model"]):
        o, n = g[g.reasoning == "off"], g[g.reasoning == "on"]
        if o.empty or n.empty:
            continue
        clean = set(n.item_id.unique())          # every paired item (fallback rule, 2026-10-16); name kept
        _, sA = _qwk_items(o[o.item_id.isin(clean)]); _, sB = _qwk_items(n[n.item_id.isin(clean)])
        lo, md, hi = _boot_ci(sA, sB)
        # cost premium on the verified PT-CS stratum, so the framework ranges match the RQ1 prose
        # and figures (both verified); the public datasets have no full/verified split.
        oo, nn = (o, n) if ds != "ptcs" else (o[o.item_id.isin(interv)], n[n.item_id.isin(interv)])
        prem = pd.to_numeric(nn.completion_tokens, errors="coerce").mean() / max(pd.to_numeric(oo.completion_tokens, errors="coerce").mean(), 1)
        sdk_off = o.groupby("item_id").pred_norm.std().mean(); sdk_on = n[~n.fallback].groupby("item_id").pred_norm.std().mean()
        prem_by[(ds, dom, m)] = prem; sdk_by[(ds, dom, m)] = (sdk_off, sdk_on)
        dqwk_by[(ds, dom, m)] = (md, lo, hi)
        ver_cell = "--"
        if ds == "ptcs":
            cleanv = clean & interv
            _, sAv = _qwk_items(o[o.item_id.isin(cleanv)]); _, sBv = _qwk_items(n[n.item_id.isin(cleanv)])
            lov, mdv, hiv = _boot_ci(sAv, sBv)
            dqwk_by[(ds, dom, m, "V")] = (mdv, len(cleanv))
            ver_cell = f"{mdv:+.3f} [{lov:+.2f},{hiv:+.2f}] ({len(cleanv)})" if mdv == mdv else f"-- (N={len(cleanv)}<8)"
        rows.append({"Dataset": ds, "Dom": dom.split("_")[0], "Model": m, "N": len(clean),
                     "dQWK": f"{md:+.3f}", "95\\% CI": f"[{lo:+.2f},{hi:+.2f}]",
                     "Sig": "yes" if (lo > 0 or hi < 0) else "no",
                     "dQWK-V [CI] (N$_V$)": ver_cell,
                     "Tok$\\times$": f"{prem:.0f}",
                     "SDk off$\\to$on": f"{sdk_off:.3f}$\\to${sdk_on:.3f}"})
    _tex(pd.DataFrame(rows), "tab_rq1_reasoning.tex",
         "RQ1: reasoning OFF$\\to$ON on the paired, clean (non-truncated) items: agreement gain (dQWK, K=5), "
         "token cost premium, and within-item SD (consistency). PT-CS rows: full-N primary; the V column repeats "
         "the contrast on the PT-CS-verified (intervened) stratum as robustness.", "tab:rq1",
         star=True)

    # --- T1b: RQ1 values table FOR THE PAPER (advisor review 2026-10-15: every dQWK and percentage
    #     quoted in the RQ1 prose must be checkable in an exhibit). Same engine as the RQ1 figures
    #     (rq1_cells); PT-CS rows on the verified stratum; significant gains in bold. ---
    cells = rq1_cells(df, interv)
    dsorder = [("mohler", "short_answer", "Mohler"), ("semeval", "short_answer", "SemEval"),
               ("riayn", "code", "RIAYN"), ("ptcs", "code", "PT-CS code"),
               ("ptcs", "short_answer", "PT-CS short")]
    mname = {"qwen3.5": "Qwen3.5", "glm-5.1": "GLM-5.1", "deepseek-v4-flash": "DeepSeek-V4-Flash", "gpt-5.1": "GPT-5.1"}
    sgn = lambda x, d: (f"{x:+.{d}f}").replace("-", "$-$")
    vrows = []
    for ds, dom, lbl in dsorder:
        for j, m in enumerate(mname):
            c = cells[(cells.dataset == ds) & (cells.domain == dom) & (cells.model == m)]
            if c.empty:
                continue
            c = c.iloc[0]
            dq = sgn(c.dQWK, 3)
            first = "\\hline " if (j == 0 and vrows) else ""      # rule between dataset groups
            vrows.append({"Dataset": first + lbl if j == 0 else "", "Model": mname[m], "N": int(c.N),
                          "QWK off": f"{c.QWK_off:.3f}",
                          "$\\Delta$QWK": f"\\textbf{{{dq}}}" if c.sig else dq,
                          "95\\% CI": f"[{sgn(c.lo, 3)}, {sgn(c.hi, 3)}]",
                          "Holm": "yes" if c.sig_holm else "",
                          "Tokens": f"{c.prem_x:.0f}$\\times$",
                          "SD off $\\to$ on": (f"{c.SDk_off:.3f} $\\to$ \\textbf{{{c.SDk_on:.3f}}}"
                                                 if (c.sd_sig_up or c.sd_sig_down)
                                                 else f"{c.SDk_off:.3f} $\\to$ {c.SDk_on:.3f}")})
    _tex(pd.DataFrame(vrows), "tab_rq1_values.tex",
         "Reasoning off versus on, per model and dataset. $\\Delta$QWK is QWK with reasoning on minus QWK "
         "off, on the N sampled items; a reasoning run that reached the output limit without returning a "
         "grade counts with the grade the same model gave that answer with reasoning off. Bold marks a 95\\% "
         "bootstrap confidence interval that excludes zero. Holm marks the gains that stay significant after Holm's "
         "correction for the 20 comparisons. Tokens is how many times more output tokens reasoning used, "
         "computed on all paired items, and SD is the mean within-item standard deviation across repetitions "
         "(lower is more consistent), computed on the model's own grades, so runs that fell back are left out. A bold SD with reasoning on marks a change whose 95\\% bootstrap interval "
         "excludes zero.",
         "tab:rq1values", star=True, colspec="llrrrrcrr", size="\\footnotesize")

    # --- T2: dimension contrasts (context per dataset, scope, decomposition).
    #     Hybrid PT-CS rule (§11 2026-06-11): PT-CS contrasts get a verified robustness column. ---
    def contrast_row(A, B, label, nb=NB, verified=None):
        _, sA = _qwk_items(A); _, sB = _qwk_items(B)
        if isinstance(sA, float) or isinstance(sB, float):
            return None
        lo, md, hi = _boot_ci(sA, sB, nb)
        n = len(set(sA.index) & set(sB.index))
        ver_cell = "--"
        if verified is not None:
            _, sAv = _qwk_items(A[A.item_id.isin(verified)]); _, sBv = _qwk_items(B[B.item_id.isin(verified)])
            lov, mdv, hiv = _boot_ci(sAv, sBv, nb)
            nv = len(set(sAv.index) & set(sBv.index))
            ver_cell = f"{mdv:+.3f} [{lov:+.2f},{hiv:+.2f}] ({nv})" if mdv == mdv else f"-- (N={nv}<8)"
        return {"Contrast": label, "N": n, "dQWK": f"{md:+.3f}", "95\\% CI": f"[{lo:+.2f},{hi:+.2f}]",
                "Sig": "yes" if (lo > 0 or hi < 0) else "no", "dQWK-V [CI] (N$_V$)": ver_cell}
    q = df[(df.model == "qwen3.5") & (df.reasoning == "off")]   # decomposition kept (needed below)
    WQ = (df.scope == "whole_exam") & (df.model == "qwen3.5")    # C3 adds GLM whole-exam rows: keep the Qwen contrast
    we = set(df[WQ].item_id)
    drows = []
    ctx_by = {}     # captured for the framework guidance row (§11: context arm = Qwen3.5 only)
    for ds, dom, gt in [("mohler", "short_answer", "ref"), ("semeval", "short_answer", "ref"),
                        ("riayn", "code", "rubric"), ("ptcs", "code", "rubric")]:
        c = q[(q.dataset == ds) & (q.domain == dom) & (q.scope == "question_by_question") & (q.decomposition == "holistic")]
        r = contrast_row(c[c.context_level == "none"], c[c.context_level == "with_guidance"],
                         f"context[{gt}] {ds}:{dom[:4]} none$\\to$guid",
                         verified=interv if ds == "ptcs" else None)
        if r:
            drows.append(r); ctx_by[ds] = r
    sc = q[(q.dataset == "ptcs") & (q.domain == "code") & (q.context_level == "with_guidance") & (q.decomposition == "holistic")]
    scope_row = contrast_row(sc[(sc.scope == "question_by_question") & sc.item_id.isin(we)],
                             df[WQ], "scope ptcs:code qbq$\\to$whole-exam",
                             verified=interv)
    drows.append(scope_row)
    dd = q[(q.dataset == "ptcs") & (q.domain == "code") & (q.context_level == "with_guidance") & (q.scope == "question_by_question")]
    decomp_row = contrast_row(dd[dd.decomposition == "holistic"], dd[dd.decomposition == "criterion"],
                              "decomp ptcs:code holistic$\\to$criterion", verified=interv)
    drows.append(decomp_row)
    # derive the two decomp dQWK literals the framework row quotes (full / verified), from the engine
    decomp_full = float(decomp_row["dQWK"]); decomp_ver = float(decomp_row["dQWK-V [CI] (N$_V$)"].split()[0])
    _tex(pd.DataFrame([r for r in drows if r]), "tab_dimension_contrasts.tex",
         "RQ2/RQ3: context (per dataset; grounding type differs; the context arm ran on Qwen3.5 only), scope, "
         "and decomposition contrasts (dQWK, K=5, bootstrap CI). Qwen3.5, reasoning off. PT-CS rows: full-N "
         "primary; the V column repeats the contrast on PT-CS-verified.", "tab:dims",
         star=True)

    # --- SemEval per-split table REMOVED (2026-06-15). The seen/unseen splits were defined for
    #     SUPERVISED systems relative to a training set; our prompted, zero-shot models have no training
    #     set, so the splits do not denote novelty to our grader and the "generalisation" reading was
    #     invalid (see CLAUDE.md §11). The Results now report only pooled SemEval accuracy/AUROC in prose,
    #     computed as below for verification (reasoning off, with_guidance, pooled over splits):
    #       se = df[(df.dataset=="semeval")&(df.context_level=="with_guidance")&(df.reasoning=="off")]
    #       goldbin=(gold_score>=0.5); predbin=(pred_norm>=0.5); accuracy_score / roc_auc_score per model.
    #     -> acc 0.73-0.79, AUROC 0.81-0.85 across models. phase5.semeval_splits() is kept for audits.

    # --- T4: PT-CS reliability strata ---
    st = pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "_ptcs_strata.parquet")
    sc = (st.stratum.value_counts().rename("n").to_frame())
    sc["pct"] = (100 * sc.n / sc.n.sum()).round(1)
    lab = {"intervened": "intervened (PT-CS-verified)", "exact_sum": "exact-sum (suspected unreviewed)",
           "no_criteria": "no-criteria (unassessable)"}
    total = int(sc.n.sum())
    sc = sc.reset_index()
    sc["stratum"] = sc["stratum"].map(lambda s: lab.get(s, s))
    sc = sc.rename(columns={"stratum": "Stratum", "pct": "\\%"})
    _tex(sc, "tab_ptcs_strata.tex",
         f"PT-CS gold reliability strata. The intervened stratum, the only one with evidence of human "
         f"review, is PT-CS-verified; full PT-CS is all three strata ({total} responses).",
         "tab:strata")

    # --- T4b / T4d REMOVED (2026-06-15): the two RQ6 transfer tables (tab_transfer_verified,
    #     tab_ranking_transfer) were replaced by a single slopegraph, fig_rq6_transfer (phase6.py
    #     6.8): one line per config across {public mean, PT-CS-verified short, PT-CS code},
    #     so the "top transfers, below-top ranking is indeterminate" message reads at a glance instead
    #     of from two dense table* grids. The figure uses the SAME basis (K=5 item means, with-guidance
    #     / q-by-q / holistic; verified = intervened stratum) and the same per-dataset public-mean
    #     construction as these blocks did, so the RQ6 prose numbers (0.795/0.771/0.692/0.667/0.566,
    #     N=84/32/67/295) regenerate from it. Recompute the exact cells via phase6.fig_rq6_transfer's
    #     q_public/q_ver, or git-restore this block, if a numeric table is ever needed again. ---

    # --- T4c: gold full-vs-verified SENSITIVITY (the 'unreliable gold distorts' result) ---
    def qcell(d):
        q, s = _qwk_items(d)
        return (f"{q:.3f}" if not (isinstance(q, float) and np.isnan(q)) else "--"), (len(s) if not isinstance(s, float) else 0)
    qcode = df[(df.dataset == "ptcs") & (df.domain == "code") & (df.model == "qwen3.5") & (df.reasoning == "off")
               & (df.context_level == "with_guidance") & (df.scope == "question_by_question") & (df.decomposition == "holistic")]
    rub = df[(df.dataset == "ptcs") & (df.domain == "code") & (df.model == "qwen3.5") & (df.reasoning == "off")
             & (df.scope == "question_by_question") & (df.decomposition == "holistic")]
    def dq(sub):
        _, a = _qwk_items(rub[(rub.context_level == "none") & sub]); _, b = _qwk_items(rub[(rub.context_level == "with_guidance") & sub])
        lo, md, hi = _boot_ci(a, b)
        return f"{md:+.3f} [{lo:+.2f},{hi:+.2f}]"
    sens = pd.DataFrame([
        {"Metric": "Qwen OFF code QWK", "Full PT-CS": qcell(qcode)[0], "PT-CS-verified": qcell(qcode[qcode.item_id.isin(interv)])[0]},
        {"Metric": "rubric dQWK (Qwen OFF, none$\\to$guid)", "Full PT-CS": dq(rub.item_id.notna()), "PT-CS-verified": dq(rub.item_id.isin(interv))},
        {"Metric": "model$-$gold deviation (OFF)",
         "Full PT-CS": f"{phase5.signed_deviation(qcode):+.3f}",
         "PT-CS-verified": f"{phase5.signed_deviation(qcode[qcode.item_id.isin(interv)]):+.3f}"},
    ])
    # Gold-sensitivity TABLE + FIGURE CUT from the paper body (2026-06-16): a full subsection plus a
    # full-width figure was spent defending the dataset rather than building the framework. The one
    # framework-relevant point (an unreliable reference hides real effects) is now a short paragraph in
    # RQ6 (sec:rq6) + the threats section, and the rubric artifact is already shown in RQ2. The numbers
    # stay engine-backed: this block still recomputes them and prints them for audit instead of emitting
    # a table. (fig6_gold_sensitivity in phase6.py was removed at the same time.)
    print("  [audit] gold sensitivity (Qwen OFF, PT-CS code) full -> verified:")
    for _, row in sens.iterrows():
        print(f"    {row['Metric']}: {row['Full PT-CS']}  ->  {row['PT-CS-verified']}")

    # --- T5: framework decision guide (the deliverable). §11 2026-06-11 (🟡-2 ratified):
    #     the code rows are RE-ANCHORED ON BEHAVIOUR, not model identity. Collapse-at-0 is the
    #     explained case (reasoning is the lever). OFF the collapse the reasoning gain is
    #     INCONSISTENT across cells (ns for GLM/DeepSeek on code; SIG for GPT on RIAYN +0.192 and
    #     for GLM/GPT on PT-CS-short) and not predictable a priori -> default OFF for cost+
    #     consistency, ON only where local validation justifies it; that unpredictability is itself
    #     why the mother rule is "validate locally". Simple literals are DERIVED from the engine
    #     (decomp_full/_ver, the Qwen-code premium, the Qwen-code dQWK); composite ranges stay
    #     literal but are guarded by _assert_framework_ranges below (🟡-3). ---
    q_prem_lo, q_prem_hi = sorted([prem_by[("ptcs", "code", "qwen3.5")], prem_by[("riayn", "code", "qwen3.5")]])
    qwen_code_prem = int(round(np.mean([prem_by[("ptcs", "code", "qwen3.5")],
                                        prem_by[("riayn", "code", "qwen3.5")]]) / 50.0) * 50)
    qc_full = dqwk_by[("ptcs", "code", "qwen3.5")][0]; qc_v, qc_vn = dqwk_by[("ptcs", "code", "qwen3.5", "V")]
    # guidance + scope literals, derived from the T2 engine contrasts (not hand-typed)
    riayn_ctx = float(ctx_by["riayn"]["dQWK"]); ptcs_ctx_full = float(ctx_by["ptcs"]["dQWK"])
    ptcs_ctx_ver = float(ctx_by["ptcs"]["dQWK-V [CI] (N$_V$)"].split()[0]); scope_ver = float(scope_row["dQWK-V [CI] (N$_V$)"].split()[0])
    R_OVERALL, R_DISCRIM_CODE, R_QWEN_SDK = "9--925", "109--192", "2.5--5"   # composite; verified by the test (SD excludes fallback grades, 2026-10-16)
    # scope cost per question: whole exam in one call vs one call per question, on the 252 whole-exam
    # questions (whole-exam cost deduplicated by call_group); backs the 'one question per call' row
    we_items = set(df[WQ].item_id)
    we_calls = phase5.dedupe_call_groups(df[WQ])
    qb_calls = q[(q.dataset == "ptcs") & (q.domain == "code") & (q.context_level == "with_guidance")
                 & (q.scope == "question_by_question") & (q.decomposition == "holistic") & q.item_id.isin(we_items)]
    eur_per_q = lambda d: pd.to_numeric(d.cost_eur, errors="coerce").sum() / d.run_index.nunique() / len(we_items)
    scope_saving = 100 * (1 - eur_per_q(we_calls) / eur_per_q(qb_calls))
    # per model (2026-10-15 audit: the Qwen-only figure had been stated for both models): whole-exam cost
    # per question relative to one call per question, on each model's own whole-exam questions
    # 2026-10-19: on the questions graded both ways, the whole-exam call's cost split over its questions
    # (phase5.scope_cost_change); the earlier basis had left GPT-5.1's uncovered questions out of one side only
    scope_cost = {m: phase5.scope_cost_change(df, m) for m in ["qwen3.5", "deepseek-v4-flash", "gpt-5.1"]}
    print("  scope cost per question, whole exam vs one call per question (%):",
          {k: round(v, 1) for k, v in scope_cost.items()})
    # bloco C literals, derived from the engine (dim_contrasts, conversation_stats), never typed by hand
    dc = dim_contrasts(df, interv)
    gd = dc[dc.family == "guidance"]; dd_ = dc[dc.family == "decomp"]; sc_ = dc[dc.family == "scope"].set_index("model")
    g_ok = gd[gd.sig_holm]
    cvs = phase5.conversation_stats(phase5.load_conversation())
    st_d = [v["state_delta"] for v in cvs.values() if "state_delta" in v]
    or_a = [v["order_abs"] for v in cvs.values() if "order_abs" in v]
    dcost = df[(df.reasoning == "off") & (df.context_level == "with_guidance") & (df.scope == "question_by_question")
               & (df.domain == "code") & df.model.isin(["qwen3.5", "deepseek-v4-flash", "gpt-5.1"]) & df.dataset.isin(["riayn", "ptcs"])]
    _cc = dcost.groupby(["model", "dataset", "decomposition"]).cost_eur.mean().unstack()
    dec_ratio = float((_cc["criterion"] / _cc["holistic"]).mean())   # criterion vs holistic cost per answer
    dec_lo, dec_hi = float((_cc["criterion"] / _cc["holistic"]).min()), float((_cc["criterion"] / _cc["holistic"]).max())
    print(f"  [audit] guidance significant after Holm in {len(g_ok)} of {len(gd)} ({g_ok.dQWK.min():+.3f} to "
          f"{g_ok.dQWK.max():+.3f}); criterion scoring {dec_lo:.1f}-{dec_hi:.1f}x the cost per answer; shared history "
          f"{min(st_d):.3f}-{max(st_d):.3f}, answer order {min(or_a):.2f}-{max(or_a):.2f} of the scale")
    # --- T5: the configuration guide (Pedro's second review, 2026-10-18, comments #39-#48): Table 4 is the guide
    #     itself, its six settings with the evidence for each, every number derived here from the engines above
    #     (dim_contrasts, rq1_cells, instruction.contrasts, conversation_stats, the logged costs). Its tests are
    #     plotted from experiments/analysis/guide_eval.py in phase6.fig_guide_tests, and its validation from
    #     verification.py in phase6.fig_guide_validation. The composite ranges quoted in RQ1 stay guarded. ---
    _assert_framework_ranges(prem_by, sdk_by, R_OVERALL, R_DISCRIM_CODE, R_QWEN_SDK)
    write_guide_table(df, interv, cells, gd, sc_, dd_, scope_cost, dec_lo, dec_hi, st_d, or_a)
    print("done.")
    return 0


def write_guide_table(df, interv, cells, gd, sc_, dd_, scope_cost, dec_lo, dec_hi, st_d, or_a) -> None:
    """Table 4 (tab_framework): the configuration guide, one row per setting with the evidence for it."""
    from experiments.analysis import guide_eval
    from experiments.analysis import instruction as I
    m3 = ["qwen3.5", "deepseek-v4-flash", "gpt-5.1"]
    # guidance: significant gains (and how many survive Holm, as in the reasoning row and the text) and the cost per
    # grade with guidance relative to none (reasoning off)
    g_sig = gd[gd.sig & (gd.dQWK > 0)]
    g_ok = gd[gd.sig_holm & (gd.dQWK > 0)]
    gq = df[((df.dataset != "ptcs") | df.item_id.isin(interv)) & (df.reasoning == "off") & df.model.isin(m3)
            & (df.scope == "question_by_question") & (df.decomposition == "holistic")]
    gc = (gq.assign(ce=pd.to_numeric(gq.cost_eur, errors="coerce"))
          .groupby(["model", "dataset", "domain", "context_level"]).ce.mean().unstack())
    g_cost = gc["with_guidance"] / gc["none"]
    # grading instruction: partial credit vs strict (follow-up experiment), Holm within its family
    idf = I.load()
    pc = I.contrasts(idf)
    pc = pc[pc.contrast == "partial credit vs strict"]
    pc_code, pc_short = pc[pc.domain == "code"], pc[pc.domain == "short_answer"]
    i_win = pc_code[pc_code.sig_holm & (pc_code.dQWK > 0)]
    prices = guide_eval._prices()
    extra_tok, extra_pct = [], []
    for (m, ds), g in idf[(idf.domain == "code") & idf.instruction.isin(["standard", "partial_credit"])].groupby(["model", "dataset"]):
        a, b = g[g.instruction == "standard"], g[g.instruction == "partial_credit"]
        if a.empty or b.empty:
            continue
        pr = prices[m if m in prices else guide_eval.PRICE_KEY.get(m, m)]
        extra_tok.append(pd.to_numeric(b.prompt_tokens, errors="coerce").mean() - pd.to_numeric(a.prompt_tokens, errors="coerce").mean())
        extra_pct.append(100 * (guide_eval._per_grade(b, pr) / guide_eval._per_grade(a, pr) - 1))
    short_equiv = bool(pc_short[pc_short.dataset != "ptcs"].equivalent.all())
    # reasoning: RQ1 cells (every sampled item)
    r_sig, r_holm, r_n = int(cells.sig.sum()), int(cells.sig_holm.sum()), len(cells)
    r_less = int((cells.SDk_on > cells.SDk_off).sum())
    p_lo, p_hi = float(cells.prem_x.min()), float(cells.prem_x.max())
    # scope and decomposition
    s_low = int((sc_.sig_holm & (sc_.dQWK < 0)).sum()); s_up = int((sc_.sig & (sc_.dQWK > 0)).sum())
    d_up = int((dd_.sig_holm & (dd_.dQWK > 0)).sum())
    sc_lo, sc_hi = min(scope_cost.values()), max(scope_cost.values())
    sg = lambda v: f"{v:+.0f}\\%".replace("-", "$-$").replace("+", "$+$")
    assert s_up == 0, "the guide row says the whole exam never raised agreement"
    rows = [
        ("Evaluation guidance", "Give the rubric or the reference answer",
         f"Raised agreement in {len(g_sig)} of {len(gd)} model-dataset combinations ({len(g_ok)} after correction), "
         f"by {g_sig.dQWK.min():.3f} to {g_sig.dQWK.max():.3f} QWK, for {g_cost.min():.1f} to {g_cost.max():.1f} times "
         f"the cost per grade"),
        ("Grading instruction", "Ask for partial credit",
         f"Raised code agreement for {i_win.model.nunique()} of {pc_code.model.nunique()} models, by "
         f"{i_win.dQWK.min():.2f} to {i_win.dQWK.max():.2f} QWK, for {min(extra_tok):.0f} to {max(extra_tok):.0f} "
         f"extra input tokens ({min(extra_pct):.0f} to {max(extra_pct):.0f}\\% of the cost); "
         + ("on Mohler and SemEval every change lay within $\\pm0.05$" if short_equiv else "mixed on short answers")),
        ("Reasoning", "Off",
         f"Turning it on raised agreement in {r_sig} of {r_n} combinations ({r_holm} after correction), made grades "
         f"less consistent in {r_less}, and multiplied the output tokens by {p_lo:.0f} to {p_hi:.0f}"),
        ("Scope", "One question per call",
         f"The whole exam in one call never raised agreement, lowered it for {s_low} of {len(sc_)} models, and "
         f"changed the cost per question by {sg(sc_lo)} to {sg(sc_hi)}"),
        ("Decomposition", "One holistic score",
         f"Scoring per criterion raised agreement in {d_up} of {len(dd_)} comparisons, at {dec_lo:.1f} to "
         f"{dec_hi:.1f} times the cost per answer"),
        ("Conversation", "A clean conversation per answer",
         f"In one shared conversation per exam, grades fell by {min(st_d):.3f} to {max(st_d):.3f} of the scale, "
         f"and answer order moved them by {100 * min(or_a):.0f} to {100 * max(or_a):.0f}\\% of the marks"),
    ]
    lines = [r"% auto-generated by make_phase5_tables.py (write_guide_table) -- do not hand-edit",
             # [!tb]: every float follows its first reference, at the bottom of that page or the top of
             # the next (Pedro, 2026-10-18; checked by article/tools/check_floats.py).
             r"\begin{table*}[!tb]\centering\footnotesize",
             r"\caption{The configuration guide: its six settings and the evidence behind each, from the comparisons of "
             r"the results. Changes in agreement are in QWK and come from comparisons against the baseline "
             r"configuration, with reasoning off unless stated.}\label{tab:framework}",
             r"\setlength{\tabcolsep}{5pt}",
             r"\begin{tabular}{p{2.6cm}p{3.6cm}p{10.4cm}}",
             r"\hline",
             r"Setting & The guide & Evidence \\",
             r"\hline"]
    lines += [f"{s} & {g} & {e} \\\\[2pt]" for s, g, e in rows]
    lines += [r"\hline", r"\end{tabular}", r"\end{table*}"]
    (TABLES / "tab_framework.tex").write_text("\n".join(lines) + "\n")
    print("  wrote tab_framework.tex (the configuration guide)")
    for s, g, e in rows:
        print(f"    {s}: {e}")


if __name__ == "__main__":
    raise SystemExit(main())
