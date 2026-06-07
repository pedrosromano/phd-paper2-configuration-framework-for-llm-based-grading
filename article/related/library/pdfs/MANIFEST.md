# Full-text manifest (Phase 1.4)

The PDFs themselves are **gitignored** (copyrighted full-text + working artifacts; the
global `*.pdf` rule covers this folder). This manifest is the tracked record of what was
acquired and what stays locked. Central subset only — justified per CLAUDE.md §8 / PHASES 1.4.

## Acquired (legitimate open sources) — present in this folder locally

| File | Paper | Source | Why fetched |
|---|---|---|---|
| `riayn_2503.23989.pdf` | **Rubric Is All You Need: Improving LLM-based Code Evaluation with Question-Specific Rubrics** (Pathak et al., ICER 2025; arXiv 2503.23989 v3, 6 Aug 2025) | arXiv (open) | **Our code comparator's own paper** — DSA 150 + OOP 80 ≈ 230 subs; metrics Spearman, Cohen's κ, + a *Leniency* metric. Not in the library exports. Critical for 1.5 + the code arm. |
| `sasbench_2505.07247.pdf` | **SAS-Bench: A Fine-Grained Benchmark for Short Answer Scoring with LLMs** (Lai et al., arXiv 2505.07247; Neural Networks 2026) | arXiv (open) | New benchmark to position against (1,030 Q / 4,109 responses, Gaokao, step-wise + error categories). Avoid overlap; cite as related. |
| `cemft_aaai40275.pdf` | **Learning from Scoring Disagreements: Contrastive Error Mining for Robust LLM-based Assessment** (Chen et al., AAAI 2026) | AAAI OJS (open) | Reports on **Mohler + SciEntsBank + Beetle** (our short-answer sets); few-shot reasoning *stability* claim. |

## Locked — BATCH LIST for the user (log in, download into this folder, then resume 1.5)

Only three; each justified (the abstract withholds numbers we'd want for the 1.5 context table,
or it's open-access but bot-blocked). Try the link, save the PDF here with a sensible name.

1. **iAttention Transformer: An Inter-Sentence Attention Mechanism for Automated Grading**
   (Dada et al., *Mathematics* 2025). DOI **10.3390/math13182991**.
   Link: https://www.mdpi.com/2227-7390/13/18/2991
   *Status:* MDPI **open access**, but Cloudflare blocks automated download (curl/WebFetch 403).
   *Want:* per-dataset values on **Mohler / SemEval / SciEntsBank / Beetle** (all four of our
   short-answer sets in one paper). Save as `iattention_mdpi.pdf`.

2. **Automatic Short Answer Grading with LLMs: From Memorization to Reasoning**
   (Cong et al., LAK '26). DOI **10.1145/3785022.3785031**.
   Link: https://dl.acm.org/doi/10.1145/3785022.3785031
   *Status:* ACM paywall; no clean arXiv preprint found (a related arXiv 2605.00200 is a
   *different* paper — "Confidence Estimation in ASAG with LLMs").
   *Want:* the closest external RQ1 evidence (reasoning vs memorization in ASAG) for positioning
   in Related Work (1.6). Save as `from_memorization_to_reasoning_lak26.pdf`.

3. **Evaluating the Effectiveness of Open-Source LLMs for Automatic Short Answer Scoring**
   (Aminah et al., IEEE AIMS 2025). DOI **10.1109/aims66189.2025.11229661**.
   Link: https://doi.org/10.1109/aims66189.2025.11229661
   *Status:* IEEE Xplore paywall; no open version found.
   *Want:* exact per-model QWK/MAE on **Mohler** (abstract already gives **QWK 0.948 / MAE 0.30**
   for GPT-3.5T / LLaMA3-70B / DeepSeek, which may suffice — fetch only if we want the breakdown).
   Save as `opensource_llms_asag_ieee.pdf`. *Lowest priority — abstract may be enough.*

> One interruption, not many: drop any of the above into this folder and tell me; I'll read the
> exact numbers in Phase 1.5. None of the three blocks progress — the acquired three + the
> already-extracted abstract numbers are enough to start the 1.5 context table.
