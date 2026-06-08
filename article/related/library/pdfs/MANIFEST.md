# Full-text manifest (Phase 1.4)

The PDFs themselves are **gitignored** (copyrighted full-text + working artifacts; the
global `*.pdf` rule covers this folder). This manifest is the tracked record of what was
acquired and what stays locked. Central subset only — justified per CLAUDE.md §8 / PHASES 1.4.

## Acquired automatically (legitimate open sources)

| File | Paper | Source | Why fetched |
|---|---|---|---|
| `riayn_2503.23989.pdf` | **Rubric Is All You Need: Improving LLM-based Code Evaluation with Question-Specific Rubrics** (Pathak et al., ICER 2025; arXiv 2503.23989 v3, 6 Aug 2025) | arXiv (open) | **Our code comparator's own paper** — DSA 150 + OOP 80 ≈ 230 subs; metrics Spearman, Cohen's κ, + a *Leniency* metric. Not in the library exports. Critical for 1.5 + the code arm. |
| `sasbench_2505.07247.pdf` | **SAS-Bench: A Fine-Grained Benchmark for Short Answer Scoring with LLMs** (Lai et al., arXiv 2505.07247; Neural Networks 2026) | arXiv (open) | New benchmark to position against (1,030 Q / 4,109 responses, Gaokao, step-wise + error categories). Avoid overlap; cite as related. |
| `cemft_aaai40275.pdf` | **Learning from Scoring Disagreements: Contrastive Error Mining for Robust LLM-based Assessment** (Chen et al., AAAI 2026) | AAAI OJS (open) | Reports on **Mohler + SciEntsBank + Beetle** (our short-answer sets); few-shot reasoning *stability* claim. |
| `canai_grade_2411.16337.pdf` | **Can AI grade your essays? A comparative analysis of LLMs and teacher ratings in multidimensional essay scoring** (Bewersdorff et al., LAK 2025; arXiv 2411.16337) | arXiv (open) | **Multi-LLM comparison** (GPT-3.5/GPT-4/**o1**/LLaMA3-70B/Mixtral): o1 best (Spearman .74, ICC .80); LLMs more lenient than teachers. Directly informs the intro LLM-comparison table + RQ1 (reasoning) + leniency. |

## Provided by the user (paywalled / bot-blocked — downloaded manually 2026-06-08)

| File | Paper | Lock reason |
|---|---|---|
| `iattention_mdpi.pdf` | iAttention Transformer (Dada et al., *Mathematics* 2025) | MDPI open-access but Cloudflare-blocked to bots. Per-dataset values on **Mohler/SemEval/SciEntsBank/Beetle**. |
| `from_memorization_to_reasoning_lak26.pdf` | Automatic Short Answer Grading with LLMs: From Memorization to Reasoning (Cong et al., LAK '26) | ACM paywall; closest external **RQ1** evidence. |
| `opensource_llms_asag_ieee.pdf` | Evaluating Open-Source LLMs for ASAG (Aminah et al., IEEE AIMS 2025) | IEEE paywall; per-model QWK/MAE on **Mohler**. |

## Locked — none remaining

All seven central-subset PDFs are now in this folder. Nothing is blocked.

## How the LLM-comparison table (article intro / Phase 1.5) is actually sourced

The breadth of the LLM-vs-LLM grading comparison does **not** depend on PDF count. It is built from:
- **~40 grading papers that name a specific LLM AND report a metric in the abstract** (out of 237
  that name an LLM) — e.g. GPT-4/3.5/o1/Llama/Mixtral, ChatGPT/Llama (Arabic), GPT-4/ChatGPT/
  Claude/Gemini (programming, Pearson 0.91), biology ChatGPT-4o/Gemini (ICC 0.68), Mohler open-
  source LLMs (QWK 0.948), etc. These come straight from `refs_merged.csv` — no PDF needed.
- the **~12 LLM-comparison rows already tabulated in the SLR** (`slr_foundation.md`: Pack, Moazzez,
  Tate, Mello, Agyemang, Duong …).
- the **7 PDFs above**, used only to read **exact results-table breakdowns** for the most central
  papers (our comparator RIAYN; per-dataset iAttention/CEM-FT; the o1 comparison).

So the intro comparison can cite dozens of model×dataset×metric data points; PDFs are reserved for
exact numbers where the abstract is silent. Auto-extracted `perf` values carry regex noise (e.g. a
spurious "QWK=0.99" / "ACCURACY=99.99%") and **every value is re-verified in Phase 1.5** before it
enters a table.
