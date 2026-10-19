"""Audit helper: regenerate the percent-of-baseline figures quoted in the Results prose.

Phase-7 writing added relative-magnitude readings to the paper that are NOT in any generated
table or figure (those carry the absolute dQWK and CIs):

  - RQ1 (Section IV-A): for each cited reasoning gain, the gain as a percent of that cell's
    reasoning-OFF QWK   (percent = dQWK / QWK_off).
  - RQ2 (Section IV-B): the guidance benefit as a percent of the no-guidance QWK per dataset
    (percent = dQWK / QWK_none), full and (PT-CS) verified strata.
  - RQ3 (Section IV-C): the baseline QWK level (question-by-question, holistic) and each contrast
    as a percent of it   (percent = dQWK / QWK_baseline), full and verified strata.
  - RQ4 (Section IV-D): per-task QWK spread across the eight configs, and the cost-quality numbers
    behind the two-panel Fig. agreement-vs-cost (per-config QWK + euro cost per 1000 grades, for
    short-answer = Mohler+SemEval and code = RIAYN).

This script recomputes them from the run stores so they can be re-verified in a later audit. It
reuses the SAME engine and conventions as the table generator (`_qwk_items`, `_boot_ci`, K=5, the
SEED), so the dQWK values match `tab_rq1_reasoning` / the RQ3 figure exactly, and the percentages
divide the bootstrap-median dQWK (the value the prose quotes) by the point QWK baseline.

Run:
    python -m experiments.analysis.audit_pct_baselines

Cell definitions are copied verbatim from make_phase5_tables.py (RQ1 T1 loop; RQ3 T2 contrasts):
PT-CS code, Qwen3.5 reasoning off, with_guidance, holistic, question-by-question is the baseline;
scope alt = whole_exam; decomposition alt = criterion. RQ1 pairs on every sampled item (overflowed reasoning runs carry the reasoning-off grade, phase5.apply_reasoning_fallback, 2026-10-16).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from experiments.analysis import phase5
from experiments.analysis.make_phase5_tables import _qwk_items, _boot_ci

_INTERV = set(pd.read_parquet(phase5.REPO_ROOT / "data" / "processed" / "_ptcs_strata.parquet")
              .query("stratum=='intervened'").item_id)


def _pct(d, base):
    return 100 * d / base if base else float("nan")


def rq1():
    """RQ1: dQWK as a percent of the reasoning-off QWK, for the cells cited in Section IV-A."""
    df = phase5.load_main()
    rp = phase5.reasoning_paired(df)
    base = rp[(rp.context_level == "with_guidance") & (rp.scope == "question_by_question")
              & (rp.decomposition == "holistic")]
    cited = {("mohler", "short_answer", "qwen3.5"), ("semeval", "short_answer", "qwen3.5"),
             ("riayn", "code", "qwen3.5"), ("ptcs", "code", "qwen3.5"),
             ("ptcs", "short_answer", "qwen3.5"), ("ptcs", "short_answer", "glm-5.1"),
             ("ptcs", "short_answer", "gpt-5.1"), ("riayn", "code", "gpt-5.1")}
    print("=== RQ1: reasoning gain as % of reasoning-off QWK (Section IV-A) ===")
    print(f"{'dataset':8} {'dom':5} {'model':18} {'QWK_off':>8} {'dQWK':>7} {'%off':>6}   verified (off, dQWK, %)")
    for (ds, dom, m), g in sorted(base.groupby(["dataset", "domain", "model"])):
        if (ds, dom, m) not in cited:
            continue
        o, n = g[g.reasoning == "off"], g[g.reasoning == "on"]
        if o.empty or n.empty:
            continue
        clean = set(n.item_id.unique())          # every paired item (fallback rule, phase5.apply_reasoning_fallback)
        qoff, sA = _qwk_items(o[o.item_id.isin(clean)]); _, sB = _qwk_items(n[n.item_id.isin(clean)])
        _, md, _ = _boot_ci(sA, sB)
        extra = ""
        if ds == "ptcs":
            cv = clean & _INTERV
            qoffv, sAv = _qwk_items(o[o.item_id.isin(cv)]); _, sBv = _qwk_items(n[n.item_id.isin(cv)])
            _, mdv, _ = _boot_ci(sAv, sBv)
            extra = f"   ({qoffv:.3f}, {mdv:+.3f}, {_pct(mdv, qoffv):+.0f}%, N={len(cv)})"
        print(f"{ds:8} {dom[:5]:5} {m:18} {qoff:8.3f} {md:+7.3f} {_pct(md, qoff):+5.0f}%{extra}")


def rq2():
    """RQ2: guidance benefit as % of the no-guidance QWK per dataset (Section IV-B). Qwen3.5 off,
    q-by-q, holistic; none -> with_guidance. PT-CS code also on the verified stratum."""
    df = phase5.load_main()
    q = df[(df.model == "qwen3.5") & (df.reasoning == "off")
           & (df.scope == "question_by_question") & (df.decomposition == "holistic")]
    specs = [("mohler", "short_answer"), ("semeval", "short_answer"),
             ("riayn", "code"), ("ptcs", "code")]
    print("\n=== RQ2: guidance benefit as % of no-guidance QWK (Section IV-B) ===")
    print(f"{'dataset':8} {'dom':5} {'QWK_none':>8} {'dQWK':>7} {'%none':>6} {'N':>5}   verified (none, dQWK, %, N)")
    for ds, dom in specs:
        c = q[(q.dataset == ds) & (q.domain == dom)]
        A = c[c.context_level == "none"]; B = c[c.context_level == "with_guidance"]
        qnone, sA = _qwk_items(A); _, sB = _qwk_items(B)
        _, md, _ = _boot_ci(sA, sB)
        n = len(set(sA.index) & set(sB.index))
        extra = ""
        if ds == "ptcs":
            qnv, sAv = _qwk_items(A[A.item_id.isin(_INTERV)]); _, sBv = _qwk_items(B[B.item_id.isin(_INTERV)])
            _, mdv, _ = _boot_ci(sAv, sBv)
            nv = len(set(sAv.index) & set(sBv.index))
            extra = f"   ({qnv:.3f}, {mdv:+.3f}, {_pct(mdv, qnv):+.0f}%, N={nv})"
        print(f"{ds:8} {dom[:5]:5} {qnone:8.3f} {md:+7.3f} {_pct(md, qnone):+5.0f}% {n:5d}{extra}")


def rq2_consistency():
    """RQ2 consistency (Section IV-B, 2026-10-15): within-item SD across the k repetitions without and with
    guidance, per model x dataset (reasoning off, one question per call, holistic; PT-CS validated, code and
    short answers apart). The paper quotes how many rise and the largest change."""
    df = phase5.load_main()
    q = df[((df.dataset != "ptcs") | df.item_id.isin(_INTERV)) & (df.reasoning == "off")
           & (df.scope == "question_by_question") & (df.decomposition == "holistic")]
    ch = []
    for m in ["qwen3.5", "deepseek-v4-flash", "gpt-5.1"]:
        for ds, dom in [("mohler", "short_answer"), ("semeval", "short_answer"), ("riayn", "code"),
                        ("ptcs", "code"), ("ptcs", "short_answer")]:
            c = q[(q.model == m) & (q.dataset == ds) & (q.domain == dom)]
            sd = [c[c.context_level == l].groupby("item_id").pred_norm.std().mean() for l in ["none", "with_guidance"]]
            ch.append(sd[1] - sd[0])
    ch = np.array(ch)
    print("\n=== RQ2 consistency: SD with guidance minus without (Section IV-B) ===")
    print(f"  SD rises in {int((ch > 0).sum())} of {len(ch)}; changes {ch.min():+.3f} to {ch.max():+.3f}")


def rq3():
    """RQ3: baseline QWK (q-by-q, holistic) and each contrast as % of it (Section IV-C)."""
    df = phase5.load_main()
    q = df[(df.model == "qwen3.5") & (df.reasoning == "off")]
    WQ = (df.scope == "whole_exam") & (df.model == "qwen3.5")    # C3 adds GLM whole-exam rows: keep the Qwen contrast
    we = set(df[WQ].item_id)
    sc = q[(q.dataset == "ptcs") & (q.domain == "code") & (q.context_level == "with_guidance") & (q.decomposition == "holistic")]
    dd = q[(q.dataset == "ptcs") & (q.domain == "code") & (q.context_level == "with_guidance") & (q.scope == "question_by_question")]
    rows = [("scope qbq->whole_exam", sc[(sc.scope == "question_by_question") & sc.item_id.isin(we)], df[WQ]),
            ("decomp holistic->criterion", dd[dd.decomposition == "holistic"], dd[dd.decomposition == "criterion"])]
    print("\n=== RQ3: contrast as % of question-by-question holistic baseline (Section IV-C) ===")
    print(f"{'contrast':28} {'stratum':9} {'baseQWK':>8} {'dQWK':>7} {'%base':>6} {'N':>5}")
    for name, A, B in rows:
        for stratum, sub in [("full", None), ("verified", _INTERV)]:
            a, b = (A, B) if sub is None else (A[A.item_id.isin(sub)], B[B.item_id.isin(sub)])
            qbase, sA = _qwk_items(a); _, sB = _qwk_items(b)
            _, md, _ = _boot_ci(sA, sB)
            n = len(set(sA.index) & set(sB.index))
            print(f"{name:28} {stratum:9} {qbase:8.3f} {md:+7.3f} {_pct(md, qbase):+5.0f}% {n:5d}")


def rq3_cost():
    """RQ3 scope cost (advisor review 2026-10-15): per question and per repetition, what grading the
    whole exam in one call costs versus one call per question, on the 252 whole-exam questions
    (Qwen3.5 off, with guidance, holistic). Whole-exam cost is deduplicated by call_group (one call
    covers several questions). Backs the framework's 'per question by default' choice."""
    df = phase5.load_main()
    print("\n=== RQ3 scope cost per question (Section IV-C / framework) ===")
    for m in ["qwen3.5", "deepseek-v4-flash", "gpt-5.1"]:   # each model on its own whole-exam questions
        we = df[(df.scope == "whole_exam") & (df.model == m)]
        items = set(we.item_id)
        calls = phase5.dedupe_call_groups(we).copy()
        qb = df[(df.model == m) & (df.reasoning == "off") & (df.dataset == "ptcs") & (df.domain == "code")
                & (df.context_level == "with_guidance") & (df.scope == "question_by_question")
                & (df.decomposition == "holistic") & df.item_id.isin(items)].copy()
        for name, d in [("whole exam", calls), ("per question", qb)]:
            k = d.run_index.nunique()
            tot = {c: pd.to_numeric(d[c], errors="coerce").sum() / k / len(items)
                   for c in ["prompt_tokens", "completion_tokens", "cost_eur"]}
            print(f"  {m:18} {name:12} in={tot['prompt_tokens']:.0f}  out={tot['completion_tokens']:.0f}  "
                  f"EUR/question={tot['cost_eur']:.6f}")
        eur = lambda d: pd.to_numeric(d.cost_eur, errors="coerce").sum() / d.run_index.nunique() / len(items)
        print(f"  {m:18} -> whole exam changes the cost per question by {100 * (eur(calls) / eur(qb) - 1):+.1f}%")
    dd = df[(df.model == "qwen3.5") & (df.reasoning == "off") & (df.dataset == "ptcs") & (df.domain == "code")
            & (df.context_level == "with_guidance") & (df.scope == "question_by_question")]
    for dec, g in dd.groupby("decomposition"):
        print(f"  {dec:12} out={pd.to_numeric(g.completion_tokens, errors='coerce').mean():.0f} tokens  "
              f"EUR/1000 answers={1000 * pd.to_numeric(g.cost_eur, errors='coerce').mean():.3f}")


def zero_collapse():
    """RQ1 zero-collapse (advisor review 2026-10-15): share of Qwen3.5 reasoning-off runs scored exactly 0
    on PT-CS-verified code (paired reasoning items), against the teachers' share of zero grades on the
    same items."""
    df = phase5.load_main()
    rp = phase5.reasoning_paired(df[(df.dataset != "ptcs") | df.item_id.isin(_INTERV)])
    b = rp[(rp.dataset == "ptcs") & (rp.domain == "code") & (rp.model == "qwen3.5")
           & (rp.context_level == "with_guidance") & (rp.scope == "question_by_question")
           & (rp.decomposition == "holistic")]
    o, n = b[b.reasoning == "off"], b[(b.reasoning == "on") & ~b.fallback]   # the model's own grades only
    gold = o.groupby("item_id").gold_norm.first()
    print("\n=== RQ1 zero-collapse, Qwen3.5, PT-CS-verified code (Section IV-A) ===")
    print(f"  model zeros: off {100 * (o.pred_norm < 1e-9).mean():.0f}%  on {100 * (n.pred_norm < 1e-9).mean():.0f}%"
          f"  | teacher zeros on the same {len(gold)} items: {100 * (gold < 1e-9).mean():.0f}%")


def zero_rates():
    """RQ1 / guide (2026-10-15): share of exact-zero grades per model with reasoning off on code (with
    guidance, one question per call, holistic; PT-CS = validated answers), against the teachers' share on
    the same items. Backs the 'collapse' reading: the graders far above the teachers are the ones reasoning
    helps on code."""
    df = phase5.load_main()
    d = df[(df.context_level == "with_guidance") & (df.scope == "question_by_question") & (df.decomposition == "holistic")
           & (df.domain == "code") & (df.reasoning == "off")]
    d = d[(d.dataset != "ptcs") | d.item_id.isin(_INTERV)]
    print("\n=== Zero rates with reasoning off on code (Section IV-A / guide) ===")
    for (ds, m), g in d.groupby(["dataset", "model"]):
        gold = g.groupby("item_id").gold_norm.first()
        it = g.groupby("item_id").agg(z=("pred_norm", lambda s: (s < 1e-9).mean()), gold=("gold_norm", "first"))
        zz = it[it.z >= 0.6]                       # items the model scores zero in at least 3 of 5 runs
        print(f"  {ds:6} {m:18} model zeros {100 * (g.pred_norm < 1e-9).mean():4.0f}%   teachers {100 * (gold < 1e-9).mean():3.0f}%"
              f"   | on its zeroed items ({len(zz)}) the teachers gave {100 * zz.gold.mean():.0f}% of the marks")


def overflow():
    """RQ1 overflow exclusion (Section IV-A): reasoning-on runs whose output never parsed because the
    reasoning overflowed the token ceiling, with PT-CS restricted to its validated answers (the paper's
    PT-CS). Prints run rows, distinct items, and items per dataset; set full=True for the whole export."""
    df = phase5.load_main()
    rp = phase5.reasoning_paired(df)
    on = rp[(rp.reasoning == "on") & (rp.context_level == "with_guidance")
            & (rp.scope == "question_by_question") & (rp.decomposition == "holistic") & ~rp.parse_ok]
    print("\n=== RQ1 overflow exclusion (Section IV-A) ===")
    for name, d in [("whole export", on), ("paper PT-CS", on[(on.dataset != "ptcs") | on.item_id.isin(_INTERV)])]:
        print(f"  {name:12} rows={len(d)} items={d.item_id.nunique()} models={sorted(d.model.unique())} "
              f"per dataset={d.groupby('dataset').item_id.nunique().to_dict()}")


def temp0_variation():
    """Threats (Section VII): share of items whose grade differs across the k repetitions at temperature 0,
    per (dataset, domain, model, reasoning), with guidance, one question per call, holistic; PT-CS = its
    validated answers. The paper quotes the reasoning-off range."""
    df = phase5.load_main()
    d = df[(df.context_level == "with_guidance") & (df.scope == "question_by_question")
           & (df.decomposition == "holistic") & df.pred_norm.notna() & ~df.fallback]   # model's own grades only
    d = d[(d.dataset != "ptcs") | d.item_id.isin(_INTERV)]
    print("\n=== Temperature-0 variation: % of items whose grade varies across repetitions (Section VII) ===")
    # 2026-10-16 (second pass): GPT-5.1 rejects a temperature setting, so the harness never sends one and it
    # samples at the API default; only the open models ran at temperature 0. The paper quotes the open models'
    # range as the temperature-0 figure and GPT-5.1's separately.
    for who, sel in [("open models, temperature 0", d.model != "gpt-5.1"), ("GPT-5.1, API default", d.model == "gpt-5.1")]:
        for r in ["off", "on"]:
            pct = [100 * g.groupby("item_id").pred_norm.agg(lambda x: x.nunique() > 1).mean()
                   for _, g in d[sel & (d.reasoning == r)].groupby(["dataset", "domain", "model"])]
            print(f"  {who}, reasoning {r}: {min(pct):.0f}% to {max(pct):.0f}% across {len(pct)} model-dataset combinations")


def k_sensitivity():
    """Method, QWK binning (2026-10-15): the largest change in a baseline-configuration QWK (reasoning off,
    with guidance, one question per call, holistic; every model x dataset, PT-CS validated) when the ordinal
    scale is K=4 or K=6 instead of K=5."""
    from sklearn.metrics import cohen_kappa_score
    df = phase5.load_main()
    b = df[(df.context_level == "with_guidance") & (df.scope == "question_by_question") & (df.decomposition == "holistic")
           & (df.reasoning == "off") & df.pred_norm.notna()]
    b = b[(b.dataset != "ptcs") | b.item_id.isin(_INTERV)]
    mx = 0.0
    for _, g in b.groupby(["dataset", "domain", "model"]):
        s = g.groupby("item_id").agg(p=("pred_norm", "mean"), g=("gold_norm", "mean"))
        q = {K: cohen_kappa_score((s.g * K).round().clip(0, K).astype(int), (s.p * K).round().clip(0, K).astype(int),
                                  weights="quadratic", labels=list(range(K + 1))) for K in (4, 5, 6)}
        mx = max(mx, abs(q[4] - q[5]), abs(q[6] - q[5]))
    print(f"\n=== QWK binning sensitivity (Section III-E) ===\n  largest baseline change with K=4 or K=6: {mx:.3f}")


def sd_length():
    """RQ1 consistency paragraph (Section IV-A): Spearman between an item's output length and its grade
    variability across repetitions, per (dataset, model), reasoning off and on pooled (phase5 basis), with
    PT-CS restricted to its validated answers. The paper quotes the median and the range."""
    df = phase5.load_main()
    t = phase5.sd_length_spearman(df[(df.dataset != "ptcs") | df.item_id.isin(_INTERV)])
    print("\n=== Length vs grade variability, Spearman per model-dataset (Section IV-A) ===")
    print(f"  median {t.spearman.median():.2f}, range {t.spearman.min():.2f} to {t.spearman.max():.2f} over {len(t)}")


def cost_by_period():
    """Section IV-D cost paragraph (2026-10-15): re-priced spend (June 2026 provider rates, phase5.prepare)
    by month and provider, whole-exam deduplicated; June = the main matrix, October = the bloco C arms.
    The a-priori estimate (EUR 16.7: DeepInfra 11.25, OpenAI 5.45) is compared with the June matrix."""
    # all analysed runs: the main store (whole exam counted once per call) plus the conversation sub-study,
    # which the a-priori estimate also included (matrix.estimate prices the conversation cells); 2026-10-15
    d = pd.concat([phase5.dedupe_call_groups(phase5.load_main()), phase5.load_conversation()], ignore_index=True)
    d["month"] = d.ts.astype(str).str[:7]
    d["prov"] = np.where(d.model == "gpt-5.1", "openai", "deepinfra")
    print("\n=== Cost by period, re-priced (Section IV-D) ===")
    print(d.groupby(["month", "prov"]).cost_eur.sum().round(2).to_string())
    j = d[d.month == "2026-06"]
    oa, di = j[j.prov == "openai"].cost_eur.sum(), j[j.prov == "deepinfra"].cost_eur.sum()
    print(f"  June matrix EUR {oa + di:.2f} -> estimate 16.7 was {(oa + di) / 16.7:.1f}x low "
          f"(OpenAI {oa / 5.45:.1f}x, DeepInfra {di / 11.25:.1f}x); all analysed runs EUR {d.cost_eur.sum():.2f}")


# RQ4 covers all five answer sets since Pedro's second review (2026-10-18, comment #28; it had used the public
# datasets only, a leftover of the removed transfer analysis): short answers = Mohler, SemEval and PT-CS short
# answers; code = RIAYN and PT-CS code (PT-CS = the validated answers).
RQ4_SETS = {"mohler": ("mohler", "short_answer"), "semeval": ("semeval", "short_answer"),
            "ptcs_short": ("ptcs", "short_answer"), "riayn": ("riayn", "code"), "ptcs_code": ("ptcs", "code")}
RQ4_TASKS = [("short answers (Mohler, SemEval, PT-CS short)", ["mohler", "semeval", "ptcs_short"]),
             ("code (RIAYN, PT-CS code)", ["riayn", "ptcs_code"])]


def _rq4_set(g, key):
    ds, dom = RQ4_SETS[key]
    return g[(g.dataset == ds) & (g.domain == dom)]


def rq4_winners():
    """Section IV-D (2026-10-15; all five sets since 2026-10-18): per-set QWK per configuration on the Fig.
    per-dataset basis (with guidance, one question per call, holistic; item means; PT-CS = validated answers),
    the per-set winner, and each configuration's mean QWK over the five sets."""
    df = phase5.load_main()
    base = df[(df.context_level == "with_guidance") & (df.scope == "question_by_question") & (df.decomposition == "holistic")]
    base = base[(base.dataset != "ptcs") | base.item_id.isin(_INTERV)]
    import experiments.figures.phase6 as P
    base = base[base.item_id.isin(P._common_items(df))]   # items all eight configurations graded (2026-10-16)
    rows = []
    for m in ["qwen3.5", "glm-5.1", "deepseek-v4-flash", "gpt-5.1"]:
        for r in ["off", "on"]:
            g = base[(base.model == m) & (base.reasoning == r)]
            q = {k: _qwk_items(_rq4_set(g, k))[0] for k in RQ4_SETS}
            rows.append({"cfg": f"{m}|{r}", **{k: round(v, 3) for k, v in q.items()},
                         "mean_5": round(float(np.mean(list(q.values()))), 3)})
    t = pd.DataFrame(rows)
    print("\n=== RQ4 per-set QWK and winners (Section IV-D) ===")
    print(t.to_string(index=False))
    for k in RQ4_SETS:
        w = t.sort_values(k, ascending=False).iloc[0]
        print(f"  winner {k}: {w.cfg} {w[k]:.3f}")
    print(f"  five-set mean range: {t.mean_5.min():.3f} to {t.mean_5.max():.3f}")


def rq6_transfer():
    """Section IV-F (2026-10-15): public vs PT-CS QWK per configuration and the rank correlation, computed
    with the transfer figure's own functions (phase6), so the prose quotes exactly what the figure shows."""
    from scipy.stats import spearmanr
    import experiments.figures.phase6 as P
    full = phase5.load_main()
    base = full[(full.context_level == "with_guidance") & (full.scope == "question_by_question") & (full.decomposition == "holistic")]
    base = base[base.item_id.isin(P._common_items(full))]    # items all eight configurations graded (2026-10-16)
    print("\n=== RQ6 transfer (Section IV-F) ===")
    for title, pub, dom in [("short", ["mohler", "semeval"], "short_answer"), ("code", ["riayn"], "code")]:
        rows = []
        for m in ["qwen3.5", "glm-5.1", "deepseek-v4-flash", "gpt-5.1"]:
            for r in ["off", "on"]:
                g = base[(base.model == m) & (base.reasoning == r)]
                rows.append((f"{m}|{r}", float(np.nanmean([P._qwk(P._itemmeans(g[g.dataset == ds])) for ds in pub])),
                             P._qwk(P._itemmeans(g[(g.dataset == "ptcs") & (g.domain == dom) & g.item_id.isin(P._INTERV)]))))
        sp = spearmanr([r[1] for r in rows], [r[2] for r in rows])
        print(f"  {title}: rho={sp.statistic:.2f}  p={sp.pvalue:.3f}")
        for n, a_, b_ in sorted(rows, key=lambda t: -t[1]):
            print(f"    {n:22} public {a_:.3f}  PT-CS {b_:.3f}")


def rq4():
    """RQ4 cost-quality BY TASK (Section IV-D, Fig. agreement-vs-cost, 2 panels): per-task QWK spread
    across the eight configs, and per-config QWK + euro cost per 1000 grades for short answers (Mohler,
    SemEval, PT-CS short) and code (RIAYN, PT-CS code). QWK on the items all eight configurations graded;
    cost from the logged cost_eur over every graded call of the task."""
    df = phase5.load_main()
    df["ce"] = pd.to_numeric(df.get("cost_eur"), errors="coerce")
    base = df[(df.context_level == "with_guidance") & (df.scope == "question_by_question")
              & (df.decomposition == "holistic")]
    base = base[(base.dataset != "ptcs") | base.item_id.isin(_INTERV)]
    import experiments.figures.phase6 as P
    common = P._common_items(df)          # QWK on items all eight configurations graded; cost on all calls
    models = ["qwen3.5", "glm-5.1", "deepseek-v4-flash", "gpt-5.1"]
    for task, keys in RQ4_TASKS:
        sub = pd.concat([_rq4_set(base, k) for k in keys])
        print(f"\n=== RQ4 {task}: per-config QWK + EUR/1000 grades (Section IV-D) ===")
        res = {}
        for m in models:
            for rs in ["off", "on"]:
                cell = sub[(sub.model == m) & (sub.reasoning == rs)]
                qs = [_qwk_items(_rq4_set(cell, k)[lambda x: x.item_id.isin(common)])[0] for k in keys]
                qs = [q for q in qs if q == q]
                res[(m, rs)] = (float(np.mean(qs)), float(cell.ce.mean() * 1000))
                print(f"  {m:18}|{rs:3}  QWK={res[(m, rs)][0]:.3f}  EUR/1000={res[(m, rs)][1]:.3f}  "
                      f"per set {[round(q, 3) for q in qs]}")
        allq = [v[0] for v in res.values()]
        print(f"  -> QWK spread {max(allq) - min(allq):.3f} (min {min(allq):.3f}, max {max(allq):.3f})")
        for m in models:
            (qo, co), (qn, cn) = res[(m, "off")], res[(m, "on")]
            print(f"  reasoning on - off, {m:18}: dQWK {qn - qo:+.3f} at {cn / co:.1f}x the cost")


def rq5_noise():
    """RQ5 (independent review, 2026-10-18): the order effect against a noise baseline. For each model, the mean
    absolute change of an answer's grade between the exam's own order and the reverse (same repetition), against
    the mean absolute change between two repetitions in the same order; and the within-answer SD across
    repetitions in a shared and in a clean conversation."""
    import itertools
    c = phase5.load_conversation()
    c = c[c.pred_norm.notna()]
    print("\n=== RQ5: answer order against same-order repetition noise (Section IV-E) ===")
    for m, g in c.groupby("model"):
        sh = g[g.conversation_state == "shared"]
        nat = sh[sh.order_id == "natural"].pivot_table(index="item_id", columns="run_index", values="pred_norm")
        inv = sh[sh.order_id == "inverse"].pivot_table(index="item_id", columns="run_index", values="pred_norm")
        common, runs = nat.index.intersection(inv.index), sorted(set(nat.columns) & set(inv.columns))
        order = np.nanmean([np.abs(nat.loc[common, r] - inv.loc[common, r]).mean() for r in runs])
        noise = np.nanmean([np.abs(x[a] - x[b]).mean() for x in (nat, inv)
                            for a, b in itertools.combinations(x.columns, 2)])
        sd_clean = g[g.conversation_state == "clean"].groupby("item_id").pred_norm.std().mean()
        sd_shared = np.nanmean([x.std(axis=1).mean() for x in (nat, inv)])
        print(f"  {m:18s} order {order:.3f}  same-order noise {noise:.3f}  ({order / noise:.1f}x)  "
              f"SD clean {sd_clean:.3f}  shared {sd_shared:.3f}")


def main() -> int:
    rq1()
    rq2()
    rq2_consistency()
    rq3()
    rq3_cost()
    zero_collapse()
    zero_rates()
    overflow()
    temp0_variation()
    k_sensitivity()
    sd_length()
    cost_by_period()
    rq4_winners()
    rq6_transfer()
    rq4()
    rq5_noise()
    print("\nPaper cross-check (Phase 7): RQ1 Mohler +11%, SemEval +18%, RIAYN +45%, PT-CS-verified "
          "code +23%, PT-CS-verified short Qwen +12% (ns), RIAYN GPT +32% (GLM/GPT PT-CS short ns on verified). "
          "RQ2 (verified) RIAYN +29%, PT-CS-verified code +46%. RQ3 (verified) scope -17%, decomp -5%. "
          "RQ4 short-answer spread ~0.07 (cheap-off best ~0.61 @ EUR0.02-0.04, reasoning no help); "
          "code spread 0.259 (GLM 0.726 off @ EUR0.36 / 0.803 on @ EUR1.29; Qwen 0.544->0.754; "
          "GPT-on 0.787 @ EUR24, dominated).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
