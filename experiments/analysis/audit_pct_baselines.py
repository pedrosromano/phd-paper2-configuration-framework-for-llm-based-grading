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
scope alt = whole_exam; decomposition alt = criterion. RQ1 pairs on the clean (non-truncated) items.
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
        k = n.run_index.nunique(); ppi = n[n.parse_ok].groupby("item_id").size()
        clean = set(ppi[ppi == k].index) if n.parse_ok.mean() < 1 else set(n.item_id.unique())
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


def rq3():
    """RQ3: baseline QWK (q-by-q, holistic) and each contrast as % of it (Section IV-C)."""
    df = phase5.load_main()
    q = df[(df.model == "qwen3.5") & (df.reasoning == "off")]
    we = set(df[df.scope == "whole_exam"].item_id)
    sc = q[(q.dataset == "ptcs") & (q.domain == "code") & (q.context_level == "with_guidance") & (q.decomposition == "holistic")]
    dd = q[(q.dataset == "ptcs") & (q.domain == "code") & (q.context_level == "with_guidance") & (q.scope == "question_by_question")]
    rows = [("scope qbq->whole_exam", sc[(sc.scope == "question_by_question") & sc.item_id.isin(we)], df[df.scope == "whole_exam"]),
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


def rq4():
    """RQ4 cost-quality BY TASK (Section IV-D, Fig. agreement-vs-cost, 2 panels): per-task QWK spread
    across the eight configs, and per-config QWK + euro cost per 1000 grades for short-answer
    (Mohler+SemEval) and code (RIAYN). Cost from the logged cost_eur."""
    df = phase5.load_main()
    df["ce"] = pd.to_numeric(df.get("cost_eur"), errors="coerce")
    base = df[(df.context_level == "with_guidance") & (df.scope == "question_by_question")
              & (df.decomposition == "holistic") & df.dataset.isin(["mohler", "semeval", "riayn"])]
    models = ["qwen3.5", "glm-5.1", "deepseek-v4-flash", "gpt-5.1"]
    for task, dsets in [("short-answer (Mohler+SemEval)", ["mohler", "semeval"]), ("code (RIAYN)", ["riayn"])]:
        sub = base[base.dataset.isin(dsets)]
        print(f"\n=== RQ4 {task}: per-config QWK + EUR/1000 grades (Section IV-D) ===")
        allq = []
        for m in models:
            for rs in ["off", "on"]:
                cell = sub[(sub.model == m) & (sub.reasoning == rs)]
                qs = [_qwk_items(cell[cell.dataset == d])[0] for d in dsets]
                qs = [q for q in qs if q == q]
                q = np.mean(qs); allq.append(q)
                print(f"  {m:18}|{rs:3}  QWK={q:.3f}  EUR/1000={cell.ce.mean() * 1000:.3f}")
        print(f"  -> QWK spread {max(allq) - min(allq):.3f} (min {min(allq):.3f}, max {max(allq):.3f})")


def main() -> int:
    rq1()
    rq2()
    rq3()
    rq4()
    print("\nPaper cross-check (Phase 7): RQ1 Mohler +11%, SemEval +18%, RIAYN +45%, PT-CS-verified "
          "code +23%, PT-CS-verified short Qwen +12% (ns), RIAYN GPT +32% (GLM/GPT PT-CS short ns on verified). "
          "RQ2 (verified) RIAYN +29%, PT-CS-verified code +46%. RQ3 (verified) scope -17%, decomp -5%. "
          "RQ4 short-answer spread ~0.07 (cheap-off best ~0.61 @ EUR0.02-0.04, reasoning no help); "
          "code spread 0.259 (GLM 0.726 off @ EUR0.36 / 0.803 on @ EUR1.29; Qwen 0.544->0.754; "
          "GPT-on 0.787 @ EUR24, dominated).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
